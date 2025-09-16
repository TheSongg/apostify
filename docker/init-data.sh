#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE DATABASE $POSTGRES_N8N_DB;
  CREATE DATABASE $POSTGRES_APOSTIFY_DB;
EOSQL

echo "All databases ensured."