-- PostgreSQL init script for container bootstrap
-- Keeps docker-entrypoint happy when mounted via
-- /docker-entrypoint-initdb.d/init.sql
--
-- NOTE:
-- Actual application tables are created by SQLAlchemy metadata
-- at API startup (central_server/api/main.py).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
