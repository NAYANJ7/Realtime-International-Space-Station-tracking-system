#!/bin/bash

echo "========================================="
echo "ISS Data Platform - Troubleshooting"
echo "========================================="
echo ""

echo "1. Checking MySQL container status..."
docker ps -a --filter name=mysql

echo ""
echo "2. MySQL container logs (last 50 lines)..."
docker logs iss-data-platform-mysql-1 --tail 50

echo ""
echo "3. Checking if init.sql exists..."
if [ -f "./db/init.sql" ]; then
    echo "✓ init.sql found"
    echo "File contents:"
    cat ./db/init.sql
else
    echo "✗ init.sql NOT FOUND - This is the problem!"
    echo "Creating db directory and init.sql..."
    mkdir -p ./db
    cat > ./db/init.sql << 'EOF'
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
EOF
    echo "✓ Created init.sql"
fi

echo ""
echo "4. Checking MySQL data volume..."
docker volume inspect mysql_data 2>/dev/null || echo "Volume doesn't exist yet (normal on first run)"

echo ""
echo "5. Checking disk space..."
df -h | grep -E "Filesystem|/var/lib/docker"

echo ""
echo "========================================="
echo "QUICK FIXES:"
echo "========================================="
echo ""
echo "If MySQL keeps exiting, try these in order:"
echo ""
echo "Fix 1: Remove old volumes and restart"
echo "  docker-compose down -v"
echo "  docker volume rm mysql_data 2>/dev/null"
echo "  docker-compose up -d mysql"
echo ""
echo "Fix 2: Check MySQL logs for specific error"
echo "  docker logs iss-data-platform-mysql-1 2>&1 | grep -i error"
echo ""
echo "Fix 3: Manual MySQL start for debugging"
echo "  docker run --rm --name test-mysql -e MYSQL_ROOT_PASSWORD=password mysql:8.0"
echo ""
echo "Fix 4: Check permissions on db/ directory"
echo "  ls -la ./db/"
echo "  chmod 755 ./db/"
echo "  chmod 644 ./db/init.sql"
echo ""