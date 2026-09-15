CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS cdm;

CREATE TABLE IF NOT EXISTS cdm.message_embeddings (
    message_id TEXT NOT NULL,
    group_id TEXT,
    author_id TEXT,
    source_code TEXT,
    message_ts TIMESTAMP,
    message_text TEXT,
    embedding VECTOR(256),
    dt DATE NOT NULL,
    CONSTRAINT pk_message_embeddings PRIMARY KEY (message_id, dt)
);

CREATE INDEX IF NOT EXISTS idx_message_embeddings_dt
    ON cdm.message_embeddings (dt);

CREATE INDEX IF NOT EXISTS idx_message_embeddings_embedding
    ON cdm.message_embeddings
    USING hnsw (embedding vector_cosine_ops);
