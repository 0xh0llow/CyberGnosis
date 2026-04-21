"""
Central Server - FastAPI Backend
=================================

Server API per ricevere metriche, alert, snippet da agents.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import os
from sqlalchemy import text

# Import moduli locali
from central_server.db.database import SessionLocal, engine, Base
from central_server.db import models, crud
from central_server.vector_search.vector_db import VectorSearchEngine
from central_server.security.auth import verify_api_token, verify_hmac_signature
from central_server.security.audit import AuditLogger

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="Linux Security AI - Central Server",
    description="API per monitoraggio sicurezza centralizzato",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_engine = VectorSearchEngine()
audit_logger = AuditLogger()

# ============================================
# REQUEST MODELS
# ============================================

class MetricsRequest(BaseModel):
    host_id: str
    timestamp: str
    metrics: Dict[str, Any]

class AlertRequest(BaseModel):
    host_id: str
    alert_type: str = Field(..., description="performance, malware, ids, code")
    severity: str = Field(..., description="low, medium, high, critical")
    title: str
    description: str
    metadata: Optional[Dict[str, Any]] = {}
    timestamp: str

class CodeSnippetRequest(BaseModel):
    host_id: str
    code_snippet: str
    vulnerability_type: str
    severity: str
    file_path_hash: str
    line_number: Optional[int] = None
    timestamp: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    collection: str = Field("alerts", description="alerts, code_snippets, knowledge")


class AlertStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="open, investigating, resolved, false_positive")
    resolution_notes: Optional[str] = None

# ============================================
# DEPENDENCY: Database Session
# ============================================

def get_db():
    """Dependency per DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Linux Security AI Central Server",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = "connected"
    vector_status = "connected"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "error"
    if vector_engine.client is None:
        vector_status = "not_initialized"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "vector_db": vector_status
    }

@app.post("/api/metrics")
async def receive_metrics(
    request: MetricsRequest,
    authorization: str = Header(...),
    x_hmac_signature: Optional[str] = Header(None),
    db = Depends(get_db)
):
    """
    Riceve metriche performance da agent.
    """
    # Verifica autenticazione
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    # Verifica HMAC (integrità)
    # if x_hmac_signature and not verify_hmac_signature(request.dict(), x_hmac_signature):
    #     raise HTTPException(status_code=401, detail="Invalid HMAC signature")
    
    try:
        # Salva metriche in DB
        crud.register_host(db, host_id=request.host_id)
        metric_entry = crud.create_metric(
            db,
            host_id=request.host_id,
            timestamp=request.timestamp,
            metrics=request.metrics
        )
        
        logger.info(f"✓ Received metrics from {request.host_id}")
        
        # Audit log
        audit_logger.log_action(
            action="metrics_received",
            user="agent",
            resource=f"host:{request.host_id}",
            details={"metric_count": len(request.metrics)}
        )
        
        return {"status": "success", "metric_id": metric_entry.id}
    
    except Exception as e:
        logger.error(f"Error saving metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alerts")
async def receive_alert(
    request: AlertRequest,
    authorization: str = Header(...),
    db = Depends(get_db)
):
    """
    Riceve alert da agent.
    """
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    try:
        # Salva alert in DB
        crud.register_host(db, host_id=request.host_id)
        alert_entry = crud.create_alert(
            db,
            host_id=request.host_id,
            alert_type=request.alert_type,
            severity=request.severity,
            title=request.title,
            description=request.description,
            metadata=request.metadata,
            timestamp=request.timestamp
        )
        
        # Indicizza in vector DB per ricerca semantica
        vector_engine.index_alert(
            alert_id=str(alert_entry.id),
            text=f"{request.title}. {request.description}",
            metadata={
                "host_id": request.host_id,
                "alert_type": request.alert_type,
                "severity": request.severity,
                "timestamp": request.timestamp
            }
        )
        
        logger.info(f"✓ Received alert from {request.host_id}: {request.title}")
        
        audit_logger.log_action(
            action="alert_received",
            user="agent",
            resource=f"host:{request.host_id}",
            details={"alert_type": request.alert_type, "severity": request.severity}
        )
        
        return {"status": "success", "alert_id": alert_entry.id}
    
    except Exception as e:
        logger.error(f"Error saving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/code-snippets")
async def receive_code_snippet(
    request: CodeSnippetRequest,
    authorization: str = Header(...),
    db = Depends(get_db)
):
    """
    Riceve snippet di codice sospetto da code scanner.
    """
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    try:
        # Salva snippet in DB
        crud.register_host(db, host_id=request.host_id)
        snippet_entry = crud.create_code_snippet(
            db,
            host_id=request.host_id,
            code_snippet=request.code_snippet,
            vulnerability_type=request.vulnerability_type,
            severity=request.severity,
            file_path_hash=request.file_path_hash,
            line_number=request.line_number,
            timestamp=request.timestamp
        )
        
        # Indicizza in vector DB
        vector_engine.index_code_snippet(
            snippet_id=str(snippet_entry.id),
            code=request.code_snippet,
            metadata={
                "vulnerability_type": request.vulnerability_type,
                "severity": request.severity,
                "host_id": request.host_id
            }
        )
        
        logger.info(f"✓ Received code snippet from {request.host_id}")
        
        return {"status": "success", "snippet_id": snippet_entry.id}
    
    except Exception as e:
        logger.error(f"Error saving code snippet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/similar-alerts")
async def search_similar_alerts(
    request: SearchRequest,
    authorization: str = Header(...),
    db = Depends(get_db)
):
    """
    Ricerca semantica di alert simili.
    """
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    try:
        results = vector_engine.search_alerts(
            query=request.query,
            top_k=request.top_k
        )
        
        audit_logger.log_action(
            action="search_alerts",
            user="dashboard_user",
            resource="vector_db",
            details={"query": request.query, "results_count": len(results)}
        )
        
        return {"results": results}
    
    except Exception as e:
        logger.error(f"Error searching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/similar-snippets")
async def search_similar_code(
    request: SearchRequest,
    authorization: str = Header(...),
    db = Depends(get_db)
):
    """
    Ricerca semantica di snippet di codice simili.
    """
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    try:
        results = vector_engine.search_code_snippets(
            query=request.query,
            top_k=request.top_k
        )
        
        return {"results": results}
    
    except Exception as e:
        logger.error(f"Error searching code snippets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts(
    authorization: str = Header(...),
    host_id: Optional[str] = None,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db = Depends(get_db)
):
    """
    Ottiene lista alert con filtri opzionali.
    """
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    try:
        alerts = crud.get_alerts(
            db,
            host_id=host_id,
            alert_type=alert_type,
            severity=severity,
            status=status,
            limit=limit
        )
        
        return {"count": len(alerts), "alerts": alerts}
    
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/{alert_id}")
async def get_alert_by_id(
    alert_id: int,
    authorization: str = Header(...),
    db=Depends(get_db)
):
    """Ottiene dettaglio singolo alert."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    alert = crud.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.patch("/api/alerts/{alert_id}")
async def patch_alert_status(
    alert_id: int,
    request: AlertStatusUpdateRequest,
    authorization: str = Header(...),
    db=Depends(get_db)
):
    """Aggiorna stato alert."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    alert = crud.update_alert_status(db, alert_id, request.status)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success", "alert_id": alert.id, "new_status": alert.status}


@app.get("/api/metrics")
async def get_metrics(
    authorization: str = Header(...),
    host_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    db=Depends(get_db)
):
    """Ottiene metriche con filtri opzionali."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    metrics = crud.get_metrics(
        db,
        host_id=host_id,
        limit=limit,
        start_time=start_time,
        end_time=end_time
    )
    return [
        {
            "id": metric.id,
            "host_id": metric.host_id,
            "timestamp": metric.timestamp.isoformat(),
            "metrics": metric.metrics
        }
        for metric in metrics
    ]


@app.get("/api/hosts")
async def get_hosts(
    authorization: str = Header(...),
    host_id: Optional[str] = None,
    db=Depends(get_db)
):
    """Lista host monitorati."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    return crud.get_hosts(db, host_id=host_id)


@app.get("/api/code-snippets")
async def get_code_snippets(
    authorization: str = Header(...),
    host_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    db=Depends(get_db)
):
    """Lista snippet di codice rilevati."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    snippets = crud.get_code_snippets(db, host_id=host_id, severity=severity, limit=limit)
    return {"count": len(snippets), "snippets": snippets}


@app.post("/api/search/knowledge")
async def search_knowledge_base(
    request: SearchRequest,
    authorization: str = Header(...),
):
    """Ricerca semantica nella knowledge base."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    results = vector_engine.search_knowledge(query=request.query, top_k=request.top_k)
    return {"results": results}

@app.get("/api/stats")
async def get_statistics(
    authorization: str = Header(...),
    db = Depends(get_db)
):
    """
    Statistiche globali sistema.
    """
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    try:
        stats = crud.get_system_stats(db)
        return stats
    
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# STARTUP / SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Inizializzazione al startup."""
    logger.info("🚀 Central Server starting up...")
    
    # Inizializza vector DB
    vector_engine.initialize()
    
    logger.info("✓ Vector search engine initialized")
    logger.info("✓ Server ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup allo shutdown."""
    logger.info("👋 Server shutting down...")
    vector_engine.close()

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
