#!/bin/bash
set -e

create_user_if_env() {
  local db="$1"
  local user="$2"
  local pass="$3"

  local db_val="${!db}"
  local user_val="${!user}"
  local pass_val="${!pass}"

  if [ -n "$db_val" ] && [ -n "$user_val" ] && [ -n "$pass_val" ]; then
    echo "Creating user $user_val for database $db_val"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
      CREATE DATABASE $db_val;
      CREATE USER $user_val WITH PASSWORD '$pass_val';
      GRANT ALL PRIVILEGES ON DATABASE $db_val TO $user_val;
      GRANT CREATE ON SCHEMA public TO $user_val;
EOSQL
  else
    echo "SETUP INFO: Missing environment values for $db"
  fi
}

create_user_if_env POSTGRES_N8N_DB POSTGRES_N8N_USER POSTGRES_N8N_PASSWORD
create_user_if_env POSTGRES_APOSTIFY_DB POSTGRES_APOSTIFY_USER POSTGRES_APOSTIFY_PASSWORD
