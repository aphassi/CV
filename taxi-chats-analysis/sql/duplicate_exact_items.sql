CREATE SCHEMA IF NOT EXISTS cdm;

CREATE TABLE IF NOT EXISTS cdm.duplicate_exact_items (
    group_id BIGINT NOT NULL,
    message_id TEXT NOT NULL,
    author_id TEXT,
    source_code TEXT,
    message_ts TIMESTAMP,
    message_text TEXT,
    normalized_text TEXT,
    dt DATE NOT NULL,
    CONSTRAINT pk_duplicate_exact_items
        PRIMARY KEY (group_id, message_id, dt)
);

CREATE INDEX IF NOT EXISTS idx_duplicate_exact_items_group_id
    ON cdm.duplicate_exact_items (group_id);

CREATE INDEX IF NOT EXISTS idx_duplicate_exact_items_message_id
    ON cdm.duplicate_exact_items (message_id);

CREATE INDEX IF NOT EXISTS idx_duplicate_exact_items_dt
    ON cdm.duplicate_exact_items (dt);
