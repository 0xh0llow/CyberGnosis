"""
CRUD Operations
===============

Operazioni database (Create, Read, Update, Delete).
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from . import models


def _parse_timestamp(timestamp: str) -> datetime:
    """Converte ISO string in datetime compatibile con SQLAlchemy."""
    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


def _to_iso(value: Optional[datetime]) -> Optional[str]:
    """Serializza datetime in ISO string, se presente."""
    return value.isoformat() if value else None


def serialize_alert(alert: models.Alert) -> Dict[str, Any]:
    """Serializza un alert in forma API-friendly."""
    return {
        "id": alert.id,
        "host_id": alert.host_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "metadata": alert.alert_metadata or {},
        "status": alert.status,
        "timestamp": _to_iso(alert.timestamp),
        "created_at": _to_iso(alert.created_at),
        "updated_at": _to_iso(alert.updated_at),
    }


def serialize_ticket(ticket: models.Ticket) -> Dict[str, Any]:
    """Serializza un ticket per le API del portale."""
    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "customer_name": ticket.customer_name,
        "customer_email": ticket.customer_email,
        "status": ticket.status,
        "priority": ticket.priority,
        "host_id": ticket.host_id,
        "alert_id": ticket.alert_id,
        "support_response": ticket.support_response,
        "internal_notes": ticket.internal_notes,
        "created_at": _to_iso(ticket.created_at),
        "updated_at": _to_iso(ticket.updated_at),
        "closed_at": _to_iso(ticket.closed_at),
    }


def serialize_host(host: models.Host) -> Dict[str, Any]:
    """Serializza host monitorati per il frontend."""
    return {
        "id": host.id,
        "host_id": host.host_id,
        "hostname": host.hostname,
        "os_info": host.os_info,
        "is_active": host.is_active,
        "last_seen": _to_iso(host.last_seen),
        "registered_at": _to_iso(host.registered_at),
    }


def serialize_telegram_config(config: models.TelegramConfig) -> Dict[str, Any]:
    """Serializza configurazione Telegram."""
    return {
        "id": config.id,
        "chat_id": config.chat_id,
        "is_active": config.is_active,
        "created_at": _to_iso(config.created_at),
        "updated_at": _to_iso(config.updated_at),
    }


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
        timestamp=_parse_timestamp(timestamp),
        metrics=metrics
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def get_metrics(
    db: Session,
    host_id: Optional[str] = None,
    limit: int = 100,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> List[models.Metric]:
    """Ottiene metriche con filtri opzionali."""
    query = db.query(models.Metric)
    
    if host_id:
        query = query.filter(models.Metric.host_id == host_id)

    if start_time:
        query = query.filter(
            models.Metric.timestamp >= datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        )
    if end_time:
        query = query.filter(
            models.Metric.timestamp <= datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        )
    
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
        alert_metadata=metadata,
        timestamp=_parse_timestamp(timestamp),
        status='open'
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_alerts(
    db: Session,
    host_id: Optional[str] = None,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Ottiene alert con filtri."""
    query = db.query(models.Alert)
    
    if host_id:
        query = query.filter(models.Alert.host_id == host_id)

    if alert_type:
        query = query.filter(models.Alert.alert_type == alert_type)
    
    if severity:
        query = query.filter(models.Alert.severity == severity)
    
    if status:
        query = query.filter(models.Alert.status == status)
    
    alerts = query.order_by(models.Alert.timestamp.desc()).limit(limit).all()
    
    # Convert to dict
    return [serialize_alert(alert) for alert in alerts]


def get_alert_by_id(db: Session, alert_id: int) -> Optional[Dict[str, Any]]:
    """Ottiene singolo alert per ID."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        return None
    return serialize_alert(alert)


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
        timestamp=_parse_timestamp(timestamp)
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
) -> List[Dict[str, Any]]:
    """Ottiene code snippets."""
    query = db.query(models.CodeSnippet)
    
    if host_id:
        query = query.filter(models.CodeSnippet.host_id == host_id)
    
    if severity:
        query = query.filter(models.CodeSnippet.severity == severity)
    
    snippets = query.order_by(models.CodeSnippet.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": snippet.id,
            "host_id": snippet.host_id,
            "code_snippet": snippet.code_snippet,
            "vulnerability_type": snippet.vulnerability_type,
            "severity": snippet.severity,
            "file_path_hash": snippet.file_path_hash,
            "line_number": snippet.line_number,
            "timestamp": snippet.timestamp.isoformat(),
        }
        for snippet in snippets
    ]


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


def get_latest_host(db: Session) -> Optional[models.Host]:
    """Ottiene l'host visto piu' recentemente."""
    return db.query(models.Host).order_by(models.Host.last_seen.desc().nullslast()).first()


def get_hosts(db: Session, host_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Ottiene host attivi o specifico host."""
    query = db.query(models.Host)
    if host_id:
        query = query.filter(models.Host.host_id == host_id)
    hosts = query.order_by(models.Host.last_seen.desc().nullslast()).all()
    return [serialize_host(host) for host in hosts]


# ============================================
# TICKETS
# ============================================

def create_ticket(
    db: Session,
    title: str,
    description: str,
    priority: str = "medium",
    status: str = "open",
    host_id: Optional[str] = None,
    alert_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> models.Ticket:
    """Crea un nuovo ticket di supporto."""
    db_ticket = models.Ticket(
        title=title,
        description=description,
        priority=priority,
        status=status,
        host_id=host_id,
        alert_id=alert_id,
        customer_name=customer_name,
        customer_email=customer_email,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def get_tickets(
    db: Session,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Lista ticket con filtro opzionale per stato."""
    query = db.query(models.Ticket)
    if status:
        query = query.filter(models.Ticket.status == status)
    tickets = query.order_by(models.Ticket.created_at.desc()).limit(limit).all()
    return [serialize_ticket(ticket) for ticket in tickets]


def get_ticket_by_id(db: Session, ticket_id: int) -> Optional[Dict[str, Any]]:
    """Ottiene un ticket per ID."""
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        return None
    return serialize_ticket(ticket)


def update_ticket(
    db: Session,
    ticket_id: int,
    updates: Dict[str, Any],
) -> Optional[models.Ticket]:
    """Aggiorna campi editabili di un ticket."""
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        return None

    for field in (
        "title",
        "description",
        "status",
        "priority",
        "host_id",
        "alert_id",
        "customer_name",
        "customer_email",
        "support_response",
        "internal_notes",
    ):
        if field in updates:
            setattr(ticket, field, updates[field])

    if "status" in updates:
        ticket.closed_at = datetime.utcnow() if updates["status"] == "closed" else None

    db.commit()
    db.refresh(ticket)
    return ticket


# ============================================
# NOTIFICATIONS
# ============================================

def upsert_telegram_config(db: Session, chat_id: str) -> models.TelegramConfig:
    """Crea o riattiva la configurazione Telegram per il portale."""
    config = db.query(models.TelegramConfig).filter(models.TelegramConfig.chat_id == chat_id).first()

    if config:
        config.is_active = True
    else:
        config = models.TelegramConfig(chat_id=chat_id, is_active=True)
        db.add(config)

    db.commit()
    db.refresh(config)
    return config


def get_telegram_configs(db: Session, active_only: bool = True) -> List[Dict[str, Any]]:
    """Lista le configurazioni Telegram salvate."""
    query = db.query(models.TelegramConfig)
    if active_only:
        query = query.filter(models.TelegramConfig.is_active == True)
    configs = query.order_by(models.TelegramConfig.created_at.desc()).all()
    return [serialize_telegram_config(config) for config in configs]


def get_active_telegram_chat_ids(db: Session) -> List[str]:
    """Restituisce i chat_id Telegram attivi."""
    rows = (
        db.query(models.TelegramConfig.chat_id)
        .filter(models.TelegramConfig.is_active == True)
        .all()
    )
    return [chat_id for (chat_id,) in rows]


# ============================================
# STATISTICS
# ============================================

def get_system_stats(db: Session) -> Dict[str, Any]:
    """Statistiche globali sistema."""
    total_metrics = db.query(models.Metric).count()
    total_alerts = db.query(models.Alert).count()
    open_alerts = db.query(models.Alert).filter(models.Alert.status == 'open').count()
    total_hosts = db.query(models.Host).count()
    total_tickets = db.query(models.Ticket).count()
    open_tickets = db.query(models.Ticket).filter(models.Ticket.status != 'closed').count()
    
    # Alert per severità
    critical_alerts = db.query(models.Alert).filter(models.Alert.severity == 'critical').count()
    high_alerts = db.query(models.Alert).filter(models.Alert.severity == 'high').count()
    
    # Host attivi
    active_hosts = db.query(models.Host).filter(models.Host.is_active == True).count()
    
    return {
        "total_metrics": total_metrics,
        "total_alerts": total_alerts,
        "open_alerts": open_alerts,
        "total_hosts": total_hosts,
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "critical_alerts": critical_alerts,
        "high_alerts": high_alerts,
        "active_hosts": active_hosts,
        "tickets_by_status": {
            "open": db.query(models.Ticket).filter(models.Ticket.status == 'open').count(),
            "in_progress": db.query(models.Ticket).filter(models.Ticket.status == 'in_progress').count(),
            "closed": db.query(models.Ticket).filter(models.Ticket.status == 'closed').count(),
        },
        "alerts_by_severity": {
            "critical": critical_alerts,
            "high": high_alerts,
            "medium": db.query(models.Alert).filter(models.Alert.severity == 'medium').count(),
            "low": db.query(models.Alert).filter(models.Alert.severity == 'low').count(),
        }
    }
