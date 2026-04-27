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
import requests

# Import moduli locali
from central_server.db.database import SessionLocal, engine, Base, ensure_runtime_schema
from central_server.db import models, crud
from central_server.vector_search.vector_db import VectorSearchEngine
from central_server.security.auth import verify_api_token, verify_hmac_signature
from central_server.security.audit import AuditLogger

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)
ensure_runtime_schema()

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


class TicketCreateRequest(BaseModel):
    title: str
    description: str
    priority: str = Field("medium", description="low, medium, high")
    status: str = Field("open", description="open, in_progress, closed")
    host_id: Optional[str] = None
    alert_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


class TicketUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = Field(None, description="low, medium, high")
    status: Optional[str] = Field(None, description="open, in_progress, closed")
    host_id: Optional[str] = None
    alert_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    support_response: Optional[str] = None
    internal_notes: Optional[str] = None


class SimulateAttackRequest(BaseModel):
    attack_type: str = Field(..., description="malware, bruteforce, cpu, sast")
    host_id: Optional[str] = None


class TelegramConfigRequest(BaseModel):
    chat_id: str

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


def _dump_request_model(model: BaseModel) -> Dict[str, Any]:
    """Compat layer tra Pydantic v1/v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


def _build_attack_template(attack_type: str) -> Optional[Dict[str, str]]:
    """Mappa un attacco demo in un alert realistico."""
    templates = {
        "malware": {
            "alert_type": "malware",
            "severity": "critical",
            "title": "Payload malware di test rilevato",
            "description": "La simulazione demo ha generato una signature sospetta sul client monitorato.",
        },
        "bruteforce": {
            "alert_type": "ids",
            "severity": "high",
            "title": "Tentativi SSH falliti in rapida successione",
            "description": "La demo ha simulato un brute force SSH con pattern anomalo di autenticazione.",
        },
        "cpu": {
            "alert_type": "performance",
            "severity": "high",
            "title": "Picco anomalo di CPU rilevato",
            "description": "Il motore di anomaly detection ha rilevato un carico CPU fuori baseline durante la simulazione.",
        },
        "sast": {
            "alert_type": "code",
            "severity": "high",
            "title": "Pattern di codice vulnerabile rilevato",
            "description": "La simulazione ha emesso un indicatore compatibile con credenziali hardcoded o codice insicuro.",
        },
    }
    return templates.get(attack_type)


def _send_telegram_message(chat_id: str, text: str):
    """Invia un messaggio Telegram, se il bot e' configurato."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        return

    logger.info(f"Sending Telegram notification to chat_id={chat_id}")

    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10,
    ).raise_for_status()


def _severity_emoji(severity: str) -> str:
    return {
        "critical": "🔥",
        "high": "🚨",
        "medium": "⚠️",
        "low": "ℹ️",
    }.get(severity, "🔔")


def _priority_emoji(priority: str) -> str:
    return {
        "high": "🔴",
        "medium": "🟠",
        "low": "🟢",
    }.get(priority, "🎫")


def _ticket_status_emoji(status: str) -> str:
    return {
        "open": "🆕",
        "in_progress": "🛠️",
        "closed": "✅",
    }.get(status, "🎫")


def _notify_telegram_alert(db, alert_payload: Dict[str, Any]):
    """Invia una notifica Telegram best-effort per un alert creato."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        return

    chat_ids = crud.get_active_telegram_chat_ids(db)
    if not chat_ids:
        return

    severity = str(alert_payload.get("severity", "n/d"))
    message = (
        f"{_severity_emoji(severity)} CyberGnosis Alert\n"
        f"Host: {alert_payload.get('host_id', 'n/d')}\n"
        f"Severity: {severity.upper()}\n"
        f"Type: {alert_payload.get('alert_type', 'n/d')}\n"
        f"Title: {alert_payload.get('title', 'n/d')}\n"
        f"Status: {alert_payload.get('status', 'n/d')}\n"
        f"Time: {alert_payload.get('timestamp', alert_payload.get('created_at', 'n/d'))}\n"
        f"Details: {alert_payload.get('description', 'n/d')}"
    )

    for chat_id in chat_ids:
        try:
            _send_telegram_message(chat_id, message)
        except Exception as exc:
            logger.warning(f"Telegram notification failed for {chat_id}: {exc}")


def _notify_telegram_ticket(db, ticket_payload: Dict[str, Any], event: str):
    """Invia notifiche Telegram per nuove richieste e aggiornamenti ticket."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        return

    chat_ids = crud.get_active_telegram_chat_ids(db)
    if not chat_ids:
        return

    status = str(ticket_payload.get("status", "open"))
    priority = str(ticket_payload.get("priority", "medium"))
    support_response = ticket_payload.get("support_response") or "n/d"
    customer = ticket_payload.get("customer_name") or "cliente non specificato"
    customer_email = ticket_payload.get("customer_email") or "email non fornita"

    if event == "created":
        title = f"🎫 Nuovo Ticket Cliente #{ticket_payload.get('id', 'n/d')}"
    elif event == "closed":
        title = f"✅ Ticket Chiuso #{ticket_payload.get('id', 'n/d')}"
    else:
        title = f"🛠️ Ticket Aggiornato #{ticket_payload.get('id', 'n/d')}"

    message = (
        f"{title}\n"
        f"Status: {_ticket_status_emoji(status)} {status}\n"
        f"Priority: {_priority_emoji(priority)} {priority}\n"
        f"Customer: {customer}\n"
        f"Email: {customer_email}\n"
        f"Host: {ticket_payload.get('host_id', 'n/d')}\n"
        f"Title: {ticket_payload.get('title', 'n/d')}\n"
        f"Request: {ticket_payload.get('description', 'n/d')}\n"
        f"Support reply: {support_response}\n"
        f"Updated at: {ticket_payload.get('updated_at', ticket_payload.get('created_at', 'n/d'))}"
    )

    for chat_id in chat_ids:
        try:
            _send_telegram_message(chat_id, message)
        except Exception as exc:
            logger.warning(f"Telegram ticket notification failed for {chat_id}: {exc}")

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
    elif vector_engine.embedding_model is None:
        vector_status = "warming_up"

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
        
        logger.info(
            f"✓ Received metrics from host={request.host_id} metric_id={metric_entry.id} "
            f"keys={sorted(request.metrics.keys())}"
        )
        
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
        if vector_engine.client and vector_engine.alerts_collection is not None:
            try:
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
            except Exception as exc:
                logger.warning(f"Vector indexing skipped for alert {alert_entry.id}: {exc}")
        
        logger.info(
            f"✓ Received alert id={alert_entry.id} host={request.host_id} "
            f"type={request.alert_type} severity={request.severity} title={request.title}"
        )
        
        audit_logger.log_action(
            action="alert_received",
            user="agent",
            resource=f"host:{request.host_id}",
            details={"alert_type": request.alert_type, "severity": request.severity}
        )

        _notify_telegram_alert(db, crud.serialize_alert(alert_entry))
        
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
        if vector_engine.client and vector_engine.snippets_collection is not None:
            try:
                vector_engine.index_code_snippet(
                    snippet_id=str(snippet_entry.id),
                    code=request.code_snippet,
                    metadata={
                        "vulnerability_type": request.vulnerability_type,
                        "severity": request.severity,
                        "host_id": request.host_id
                    }
                )
            except Exception as exc:
                logger.warning(f"Vector indexing skipped for snippet {snippet_entry.id}: {exc}")
        
        logger.info(
            f"✓ Received code snippet id={snippet_entry.id} host={request.host_id} "
            f"vulnerability={request.vulnerability_type} severity={request.severity}"
        )
        
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
        
        return alerts
    
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
    return crud.serialize_alert(alert)


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


@app.get("/api/tickets")
async def get_tickets(
    authorization: str = Header(...),
    status: Optional[str] = None,
    limit: int = 100,
    db=Depends(get_db)
):
    """Lista ticket aperti dal portale cliente."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")

    try:
        return crud.get_tickets(db, status=status, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tickets/{ticket_id}")
async def get_ticket_by_id(
    ticket_id: int,
    authorization: str = Header(...),
    db=Depends(get_db)
):
    """Restituisce il dettaglio di un ticket."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")

    ticket = crud.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/api/tickets")
async def create_ticket(
    request: TicketCreateRequest,
    authorization: str = Header(...),
    db=Depends(get_db)
):
    """Crea un ticket di supporto dal client portal."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")

    try:
        ticket = crud.create_ticket(
            db,
            title=request.title,
            description=request.description,
            priority=request.priority,
            status=request.status,
            host_id=request.host_id,
            alert_id=request.alert_id,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
        )

        serialized_ticket = crud.serialize_ticket(ticket)
        logger.info(
            f"✓ Created ticket id={ticket.id} priority={ticket.priority} status={ticket.status} "
            f"host={ticket.host_id} customer={ticket.customer_name or 'n/d'}"
        )
        audit_logger.log_action(
            action="ticket_created",
            user="portal_user",
            resource=f"ticket:{ticket.id}",
            details={
                "priority": ticket.priority,
                "host_id": ticket.host_id,
                "customer_name": ticket.customer_name,
                "customer_email": ticket.customer_email,
            }
        )

        _notify_telegram_ticket(db, serialized_ticket, event="created")
        return serialized_ticket
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/tickets/{ticket_id}")
async def patch_ticket(
    ticket_id: int,
    request: TicketUpdateRequest,
    authorization: str = Header(...),
    db=Depends(get_db)
):
    """Aggiorna un ticket esistente."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")

    ticket = crud.update_ticket(db, ticket_id, _dump_request_model(request))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    serialized_ticket = crud.serialize_ticket(ticket)
    logger.info(
        f"✓ Updated ticket id={ticket.id} status={ticket.status} priority={ticket.priority} "
        f"has_support_response={bool(ticket.support_response)}"
    )
    audit_logger.log_action(
        action="ticket_updated",
        user="portal_user",
        resource=f"ticket:{ticket.id}",
        details={
            "status": ticket.status,
            "priority": ticket.priority,
            "support_response": bool(ticket.support_response),
            "internal_notes": bool(ticket.internal_notes),
        }
    )

    _notify_telegram_ticket(
        db,
        serialized_ticket,
        event="closed" if ticket.status == "closed" else "updated",
    )
    return serialized_ticket


@app.post("/api/simulate-attack")
async def simulate_attack(
    request: SimulateAttackRequest,
    authorization: str = Header(...),
    db=Depends(get_db)
):
    """Genera un alert demo reale per il portale live demo."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")

    attack = _build_attack_template(request.attack_type)
    if not attack:
        raise HTTPException(status_code=400, detail="Unsupported attack type")

    selected_host = request.host_id
    if not selected_host:
        latest_host = crud.get_latest_host(db)
        selected_host = latest_host.host_id if latest_host else "demo-host"

    try:
        crud.register_host(db, host_id=selected_host)
        timestamp = datetime.utcnow().isoformat() + "Z"
        metadata = {
            "source": "demo",
            "attack_type": request.attack_type,
            "generated_by": "client_portal",
        }

        alert_entry = crud.create_alert(
            db,
            host_id=selected_host,
            alert_type=attack["alert_type"],
            severity=attack["severity"],
            title=attack["title"],
            description=attack["description"],
            metadata=metadata,
            timestamp=timestamp,
        )

        if vector_engine.client and vector_engine.alerts_collection is not None:
            vector_engine.index_alert(
                alert_id=str(alert_entry.id),
                text=f"{alert_entry.title}. {alert_entry.description}",
                metadata={
                    "host_id": selected_host,
                    "alert_type": alert_entry.alert_type,
                    "severity": alert_entry.severity,
                    "timestamp": timestamp,
                    "source": "demo",
                }
            )

        audit_logger.log_action(
            action="attack_simulated",
            user="portal_user",
            resource=f"host:{selected_host}",
            details={"attack_type": request.attack_type, "alert_id": alert_entry.id}
        )

        _notify_telegram_alert(db, crud.serialize_alert(alert_entry))

        return {
            "status": "success",
            "host_id": selected_host,
            "alert": crud.serialize_alert(alert_entry),
        }
    except Exception as e:
        logger.error(f"Error simulating attack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notifications/telegram")
async def save_telegram_config(
    request: TelegramConfigRequest,
    authorization: str = Header(...),
    db=Depends(get_db)
):
    """Salva il chat_id Telegram usato dal portale."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")

    if not request.chat_id.strip():
        raise HTTPException(status_code=400, detail="chat_id is required")

    try:
        config = crud.upsert_telegram_config(db, request.chat_id.strip())

        audit_logger.log_action(
            action="telegram_config_saved",
            user="portal_user",
            resource=f"telegram:{config.chat_id}",
            details={"bot_token_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN"))}
        )

        return {
            **crud.serialize_telegram_config(config),
            "bot_token_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        }
    except Exception as e:
        logger.error(f"Error saving telegram config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/notifications/telegram")
async def get_telegram_configs(
    authorization: str = Header(...),
    db=Depends(get_db)
):
    """Restituisce le configurazioni Telegram attive salvate nel sistema."""
    if not verify_api_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid API token")

    try:
        return {
            "items": crud.get_telegram_configs(db, active_only=True),
            "bot_token_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        }
    except Exception as e:
        logger.error(f"Error loading telegram configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    try:
        vector_engine.initialize()
        logger.info("✓ Vector search engine initialized")
    except Exception as exc:
        logger.warning(f"Vector search engine unavailable at startup: {exc}")

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
