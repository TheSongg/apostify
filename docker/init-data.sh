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
    echo "Ensuring database '$db_val' and user '$user_val' exist..."

    # 检查数据库是否存在，不存在则创建
    if ! psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$db_val'" | grep -q 1; then
      echo "Creating database $db_val"
      psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $db_val;"
    else
      echo "Database $db_val already exists"
    fi

    # 检查用户是否存在，不存在则创建
    if ! psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$user_val'" | grep -q 1; then
      echo "Creating user $user_val"
      psql -U "$POSTGRES_USER" -d postgres -c "CREATE USER $user_val WITH PASSWORD '$pass_val';"
    else
      echo "User $user_val already exists"
    fi

    # 每次执行授权，幂等
    psql -U "$POSTGRES_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $db_val TO $user_val;"
    psql -U "$POSTGRES_USER" -d postgres -c "GRANT CREATE ON SCHEMA public TO $user_val;"

  else
    echo "SETUP INFO: Missing environment values for $db"
  fi
}

create_user_if_env POSTGRES_N8N_DB POSTGRES_N8N_USER POSTGRES_N8N_PASSWORD
create_user_if_env POSTGRES_APOSTIFY_DB POSTGRES_APOSTIFY_USER POSTGRES_APOSTIFY_PASSWORD
