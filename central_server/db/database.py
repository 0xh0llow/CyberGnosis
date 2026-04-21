"""
Database Configuration - SQLAlchemy
====================================
"""

from sqlalchemy import create_engine
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
