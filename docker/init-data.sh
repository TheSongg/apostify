#!/bin/bash
set -e

create_user_if_env() {
  local db="$1"
  local user="$2"
  local pass="$3"

  local db_val="${!db}"
  local user_val="${!user}"
  local pass_val="${!pass}"

  if [ -z "$db_val" ] || [ -z "$user_val" ] || [ -z "$pass_val" ]; then
    echo "SETUP INFO: Missing environment values for $db"
    return
  fi

  echo "Ensuring database '$db_val' and user '$user_val' exist..."

  # 创建数据库
  if ! psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$db_val'" | grep -q 1; then
    echo "Creating database $db_val"
    psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $db_val;"
  else
    echo "Database $db_val already exists"
  fi

  # 创建用户
  if ! psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$user_val'" | grep -q 1; then
    echo "Creating user $user_val"
    psql -U "$POSTGRES_USER" -d postgres -c "CREATE USER $user_val WITH PASSWORD '$pass_val';"
  else
    echo "User $user_val already exists"
  fi

  # 授权数据库访问
  echo "Granting privileges on database $db_val to $user_val"
  psql -U "$POSTGRES_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $db_val TO $user_val;"

  # 检查 public schema 权限
  has_all_privs=$(psql -U "$POSTGRES_USER" -d "$db_val" -tAc \
    "SELECT has_schema_privilege('$user_val', 'public', 'CREATE, USAGE');")

  if [ "$has_all_privs" != "t" ]; then
    echo "Granting schema privileges on public to $user_val"
    psql -U "$POSTGRES_USER" -d "$db_val" -c "GRANT ALL ON SCHEMA public TO $user_val;"
    psql -U "$POSTGRES_USER" -d "$db_val" -c "GRANT CREATE ON SCHEMA public TO $user_val;"
    psql -U "$POSTGRES_USER" -d "$db_val" -c "ALTER SCHEMA public OWNER TO $user_val;"
  else
    echo "User $user_val already has privileges on schema public"
  fi
}

# 创建 n8n 用户和数据库
create_user_if_env POSTGRES_N8N_DB POSTGRES_N8N_USER POSTGRES_N8N_PASSWORD

# 创建 apostify 用户和数据库
create_user_if_env POSTGRES_APOSTIFY_DB POSTGRES_APOSTIFY_USER POSTGRES_APOSTIFY_PASSWORD
