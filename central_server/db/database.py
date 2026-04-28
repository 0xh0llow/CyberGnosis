"""
Database Configuration - SQLAlchemy
====================================
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL da environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://securityuser:changeme@postgres:5432/security_monitoring"
)

# Per SQLite (sviluppo locale)
# DATABASE_URL = "sqlite:///./security_monitoring.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica connessione prima di usarla
    echo=False  # Set True per vedere SQL queries
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class per modelli
Base = declarative_base()


def ensure_runtime_schema():
    """Applica piccoli upgrade compatibili sul database esistente."""
    inspector = inspect(engine)
    if "tickets" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("tickets")}
    alterations = []

    if "customer_name" not in columns:
        alterations.append("ALTER TABLE tickets ADD COLUMN customer_name VARCHAR")
    if "customer_email" not in columns:
        alterations.append("ALTER TABLE tickets ADD COLUMN customer_email VARCHAR")
    if "support_response" not in columns:
        alterations.append("ALTER TABLE tickets ADD COLUMN support_response TEXT")
    if "internal_notes" not in columns:
        alterations.append("ALTER TABLE tickets ADD COLUMN internal_notes TEXT")
    if "closed_at" not in columns:
        alterations.append("ALTER TABLE tickets ADD COLUMN closed_at TIMESTAMP")

    if not alterations:
        return

    with engine.begin() as connection:
        for statement in alterations:
            connection.execute(text(statement))
