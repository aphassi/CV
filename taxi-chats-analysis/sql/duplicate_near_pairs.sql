CREATE SCHEMA IF NOT EXISTS cdm;

CREATE TABLE IF NOT EXISTS cdm.duplicate_near_pairs (
    message_id_1 TEXT NOT NULL,
    message_id_2 TEXT NOT NULL,
    similarity_score DOUBLE PRECISION NOT NULL,
    rule_name TEXT,
    dt DATE NOT NULL,
    CONSTRAINT pk_duplicate_near_pairs
        PRIMARY KEY (message_id_1, message_id_2, dt)
);

CREATE INDEX IF NOT EXISTS idx_duplicate_near_pairs_dt
    ON cdm.duplicate_near_pairs (dt);

CREATE INDEX IF NOT EXISTS idx_duplicate_near_pairs_score
    ON cdm.duplicate_near_pairs (similarity_score);
