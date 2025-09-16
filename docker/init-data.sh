#!/bin/bash
set -e

# 环境变量
PGHOST=${PGHOST:-postgres}
PGUSER=${PGUSER:-$POSTGRES_USER}
PGPASSWORD=${PGPASSWORD:-$POSTGRES_PASSWORD}
PGPORT=${PGPORT:-${POSTGRES_POST:-5432}}

# 数据库列表
PGDATABASES="${POSTGRES_APOSTIFY_DB} ${POSTGRES_N8N_DB}"

export PGPASSWORD

for DB in $PGDATABASES; do
  if [ -z "$DB" ]; then
    echo "Skipping empty database name"
    continue
  fi

  echo "Checking if database '$DB' exists..."
  exists=$(psql -h "$PGHOST" -U "$PGUSER" -p "$PGPORT" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB';")
  if [ "$exists" != "1" ]; then
    echo "Database '$DB' does not exist. Creating..."
    psql -h "$PGHOST" -U "$PGUSER" -p "$PGPORT" -c "CREATE DATABASE $DB;"
  else
    echo "Database '$DB' already exists. Skipping."
  fi
done

echo "All databases ensured."
