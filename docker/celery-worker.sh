#!/bin/bash
set -e

celery -A core worker -l INFO --concurrency=8