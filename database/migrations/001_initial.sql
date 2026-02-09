-- Migration 001: Initial schema
-- Applied: 2026-02-09
-- Description: Create core tables for customer support platform

BEGIN;

-- Track migrations
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    applied_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO schema_migrations (version, name) VALUES (1, '001_initial');

COMMIT;
