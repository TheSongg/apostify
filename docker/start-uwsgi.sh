#!/bin/bash
set -e

echo "Running Django migrations..."
python manage.py makemigrations --settings=core.settings
python manage.py migrate --settings=core.settings

echo "Starting uWSGI..."
exec uwsgi --ini uwsgi.ini