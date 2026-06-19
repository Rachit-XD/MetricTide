-- Enable extensions required by MetricTide.
-- This runs once, automatically, on first database initialization.

-- pgvector: similarity search for topic clustering / embeddings.
CREATE EXTENSION IF NOT EXISTS vector;

-- Useful for UUID generation in future migrations.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
