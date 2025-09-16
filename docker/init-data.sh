#!/bin/bash
set -e

create_user_if_env() {
  local db_name=$1
  local user_var=$2
  local pass_var=$3

  local user=${!user_var}
  local pass=${!pass_var}

  if [ -n "$user" ] && [ -n "$pass" ]; then
    echo "Creating user $user for database $db_name ..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db_name" <<-EOSQL
      DO \$\$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${user}') THEN
          CREATE USER ${user} WITH PASSWORD '${pass}';
        END IF;
      END
      \$\$;

      GRANT ALL PRIVILEGES ON DATABASE ${db_name} TO ${user};
      GRANT CREATE ON SCHEMA public TO ${user};
EOSQL
  else
    echo "SETUP INFO: No environment variables for $db_name user given!"
  fi
}

create_user_if_env "$POSTGRES_N8N_DB" "POSTGRES_N8N_USER" "POSTGRES_N8N_PASSWORD"
create_user_if_env "$POSTGRES_APOSTIFY_DB" "POSTGRES_APOSTIFY_USER" "POSTGRES_APOSTIFY_PASSWORD"
