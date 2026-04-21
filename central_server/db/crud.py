"""
CRUD Operations
===============

Operazioni database (Create, Read, Update, Delete).
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from . import models


# ============================================
# METRICS
# ============================================

def create_metric(
    db: Session,
    host_id: str,
    timestamp: str,
    metrics: Dict[str, Any]
) -> models.Metric:
    """Crea entry metrica."""
    db_metric = models.Metric(
        host_id=host_id,
        timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
        metrics=metrics
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def get_metrics(
    db: Session,
    host_id: Optional[str] = None,
    limit: int = 100
) -> List[models.Metric]:
    """Ottiene metriche con filtri opzionali."""
    query = db.query(models.Metric)
    
    if host_id:
        query = query.filter(models.Metric.host_id == host_id)
    
    return query.order_by(models.Metric.timestamp.desc()).limit(limit).all()


# ============================================
# ALERTS
# ============================================

def create_alert(
    db: Session,
    host_id: str,
    alert_type: str,
    severity: str,
    title: str,
    description: str,
    metadata: Dict[str, Any],
    timestamp: str
) -> models.Alert:
    """Crea alert."""
    db_alert = models.Alert(
        host_id=host_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description,
        metadata=metadata,
        timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
        status='open'
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_alerts(
    db: Session,
    host_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Ottiene alert con filtri."""
    query = db.query(models.Alert)
    
    if host_id:
        query = query.filter(models.Alert.host_id == host_id)
    
    if severity:
        query = query.filter(models.Alert.severity == severity)
    
    if status:
        query = query.filter(models.Alert.status == status)
    
    alerts = query.order_by(models.Alert.timestamp.desc()).limit(limit).all()
    
    # Convert to dict
    return [
        {
            "id": alert.id,
            "host_id": alert.host_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "metadata": alert.metadata,
            "status": alert.status,
            "timestamp": alert.timestamp.isoformat()
        }
        for alert in alerts
    ]


def update_alert_status(
    db: Session,
    alert_id: int,
    new_status: str
) -> Optional[models.Alert]:
    """Aggiorna status alert."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    
    if alert:
        alert.status = new_status
        db.commit()
        db.refresh(alert)
    
    return alert


# ============================================
# CODE SNIPPETS
# ============================================

def create_code_snippet(
    db: Session,
    host_id: str,
    code_snippet: str,
    vulnerability_type: str,
    severity: str,
    file_path_hash: str,
    line_number: Optional[int],
    timestamp: str
) -> models.CodeSnippet:
    """Crea code snippet entry."""
    db_snippet = models.CodeSnippet(
        host_id=host_id,
        code_snippet=code_snippet,
        vulnerability_type=vulnerability_type,
        severity=severity,
        file_path_hash=file_path_hash,
        line_number=line_number,
        timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    )
    db.add(db_snippet)
    db.commit()
    db.refresh(db_snippet)
    return db_snippet


def get_code_snippets(
    db: Session,
    host_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100
) -> List[models.CodeSnippet]:
    """Ottiene code snippets."""
    query = db.query(models.CodeSnippet)
    
    if host_id:
        query = query.filter(models.CodeSnippet.host_id == host_id)
    
    if severity:
        query = query.filter(models.CodeSnippet.severity == severity)
    
    return query.order_by(models.CodeSnippet.timestamp.desc()).limit(limit).all()


# ============================================
# HOSTS
# ============================================

def register_host(
    db: Session,
    host_id: str,
    hostname: Optional[str] = None,
    os_info: Optional[str] = None
) -> models.Host:
    """Registra nuovo host."""
    # Check se esiste già
    existing = db.query(models.Host).filter(models.Host.host_id == host_id).first()
    
    if existing:
        existing.last_seen = datetime.utcnow()
        db.commit()
        return existing
    
    db_host = models.Host(
        host_id=host_id,
        hostname=hostname,
        os_info=os_info,
        is_active=True,
        last_seen=datetime.utcnow()
    )
    db.add(db_host)
    db.commit()
    db.refresh(db_host)
    return db_host


def get_active_hosts(db: Session) -> List[models.Host]:
    """Ottiene host attivi."""
    return db.query(models.Host).filter(models.Host.is_active == True).all()


# ============================================
# STATISTICS
# ============================================

def get_system_stats(db: Session) -> Dict[str, Any]:
    """Statistiche globali sistema."""
    total_metrics = db.query(models.Metric).count()
    total_alerts = db.query(models.Alert).count()
    open_alerts = db.query(models.Alert).filter(models.Alert.status == 'open').count()
    
    # Alert per severità
    critical_alerts = db.query(models.Alert).filter(models.Alert.severity == 'critical').count()
    high_alerts = db.query(models.Alert).filter(models.Alert.severity == 'high').count()
    
    # Host attivi
    active_hosts = db.query(models.Host).filter(models.Host.is_active == True).count()
    
    return {
        "total_metrics": total_metrics,
        "total_alerts": total_alerts,
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts,
        "high_alerts": high_alerts,
        "active_hosts": active_hosts
    }
