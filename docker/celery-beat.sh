#!/bin/bash
set -e

echo "Waiting for database $DB_NAME at $DB_HOST to have at least one table..."

while true; do
  # 查询表数量
  TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")

  if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "Database $DB_NAME has $TABLE_COUNT table(s). Ready!"
    break
  else
    echo "No tables yet, sleeping 2s..."
    sleep 2
  fi
done