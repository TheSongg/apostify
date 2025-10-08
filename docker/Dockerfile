FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy AS playwright-base

RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN playwright install --with-deps chromium


FROM playwright-base AS playwright-final
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    xfce4 \
    xfce4-goodies \
    tigervnc-standalone-server \
    novnc \
    supervisor \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*
ENV DISPLAY=:1 \
    VNC_PORT=5901 \
    NO_VNC_PORT=6901 \
    VNC_RESOLUTION=1280x800
EXPOSE ${NO_VNC_PORT} ${VNC_PORT}
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY vnc_web.sh /vnc_web.sh
RUN chmod +x /vnc_web.sh
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]


FROM python:latest AS apostify-base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

COPY docker/celery-beat.sh /app/docker/celery-beat.sh
RUN chmod +x /app/docker/celery-beat.sh

COPY docker/apostify-back.sh /app/docker/apostify-back.sh
RUN chmod +x /app/docker/apostify-back.sh
