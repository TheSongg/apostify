FROM mcr.microsoft.com/playwright/python:latest AS playwright-base

RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright

RUN playwright install --with-deps chromium


FROM python:3.11-slim AS apostify-base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

COPY docker/celery-beat.sh /app/docker/celery-beat.sh
RUN chmod +x /app/docker/celery-beat.sh