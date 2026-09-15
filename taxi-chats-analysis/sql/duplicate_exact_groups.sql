CREATE SCHEMA IF NOT EXISTS cdm;

CREATE TABLE IF NOT EXISTS cdm.duplicate_exact_groups (
    group_id BIGINT NOT NULL,
    text_hash TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    messages_count INTEGER NOT NULL,
    first_message_ts TIMESTAMP,
    last_message_ts TIMESTAMP,
    dt DATE NOT NULL,
    CONSTRAINT pk_duplicate_exact_groups PRIMARY KEY (group_id, dt)
);

CREATE INDEX IF NOT EXISTS idx_duplicate_exact_groups_dt
    ON cdm.duplicate_exact_groups (dt);

CREATE INDEX IF NOT EXISTS idx_duplicate_exact_groups_messages_count
    ON cdm.duplicate_exact_groups (messages_count);
