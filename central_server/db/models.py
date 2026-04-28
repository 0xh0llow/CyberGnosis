"""
SQLAlchemy ORM Models
=====================

Modelli database per metriche, alert, snippet.
"""

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Boolean, Text, Index
from sqlalchemy.sql import func
from .database import Base


class Metric(Base):
    """Metriche performance."""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # Metriche JSON
    metrics = Column(JSON, nullable=False)
    
    # Timestamps automatici
    created_at = Column(DateTime, server_default=func.now())
    
    # Index composito per query veloci
    __table_args__ = (
        Index('idx_host_timestamp', 'host_id', 'timestamp'),
    )


class Alert(Base):
    """Alert di sicurezza."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(String, index=True, nullable=False)
    alert_type = Column(String, index=True, nullable=False)  # performance, malware, ids, code
    severity = Column(String, index=True, nullable=False)     # low, medium, high, critical
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Metadati aggiuntivi (JSON) - rinominato da 'metadata' che è riservato in SQLAlchemy
    alert_metadata = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime, index=True, nullable=False)
    
    # Status alert
    status = Column(String, default='open', index=True)  # open, investigating, resolved, false_positive
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    __table_args__ = (
        Index('idx_alert_composite', 'host_id', 'alert_type', 'severity'),
    )


class Ticket(Base):
    """Ticket di supporto aperti dal portale cliente."""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)

    status = Column(String, default='open', nullable=False, index=True)      # open, in_progress, closed
    priority = Column(String, default='medium', nullable=False, index=True)  # low, medium, high

    host_id = Column(String, nullable=True, index=True)
    alert_id = Column(Integer, nullable=True, index=True)
    support_response = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_ticket_status_priority', 'status', 'priority'),
    )


class CodeSnippet(Base):
    """Snippet di codice con vulnerabilità."""
    __tablename__ = "code_snippets"
    
    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(String, index=True, nullable=False)
    
    code_snippet = Column(Text, nullable=False)
    vulnerability_type = Column(String, index=True, nullable=False)
    severity = Column(String, index=True, nullable=False)
    
    file_path_hash = Column(String, nullable=False)  # Path anonimizzato
    line_number = Column(Integer, nullable=True)
    
    timestamp = Column(DateTime, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Host(Base):
    """Informazioni host monitorati."""
    __tablename__ = "hosts"
    
    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(String, unique=True, index=True, nullable=False)
    hostname = Column(String, nullable=True)
    os_info = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    
    # Timestamps
    registered_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class AuditLog(Base):
    """Log di audit per tracciare accessi."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    action = Column(String, index=True, nullable=False)  # es: metrics_received, search_alerts
    user = Column(String, index=True, nullable=False)    # Utente o agent
    resource = Column(String, nullable=False)            # Risorsa acceduta
    
    details = Column(JSON, nullable=True)
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    timestamp = Column(DateTime, server_default=func.now(), index=True)


class TelegramConfig(Base):
    """Configurazione Telegram per notifiche lato portale."""
    __tablename__ = "telegram_configs"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
