#!/bin/bash
set -e

celery -A core worker --loglevel=INFO --concurrency=8 --pool=solo