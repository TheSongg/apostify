#!/bin/bash
set -e

echo "Waiting for database '${POSTGRES_APOSTIFY_DB}' at postgres..."
until pg_isready -h "postgres" -U "${POSTGRES_APOSTIFY_USER}" -d "${POSTGRES_APOSTIFY_DB}"; do
  echo "Database not ready, sleeping 2s..."
  sleep 2
done
echo "Database is ready!"

echo "Running Django migrations..."
python manage.py makemigrations --settings=core.settings
python manage.py migrate --settings=core.settings

echo "Starting uWSGI..."
exec uwsgi --ini uwsgi.ini