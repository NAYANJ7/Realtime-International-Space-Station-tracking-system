CREATE DATABASE IF NOT EXISTS iss_db;
USE iss_db;

DROP TABLE IF EXISTS iss_positions;

CREATE TABLE iss_positions (
    record_id VARCHAR(50) PRIMARY KEY,
    id BIGINT,
    ts_unix BIGINT NOT NULL,
    ts_utc TIMESTAMP NULL,
    latitude DOUBLE,
    longitude DOUBLE,
    altitude_km DOUBLE,
    velocity_kmh DOUBLE,
    visibility VARCHAR(50),
    ingested_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ts_unix (ts_unix DESC),
    INDEX idx_ts_utc (ts_utc DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;