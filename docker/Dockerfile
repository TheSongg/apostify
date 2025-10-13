FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy AS apostify

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    VNC_PORT=${VNC_PORT} \
    NO_VNC_PORT=${NO_VNC_PORT} \
    VNC_RESOLUTION=${VNC_RESOLUTION} \
    VNC_PASS=${VNC_PASSWORD}
EXPOSE ${NO_VNC_PORT} ${VNC_PORT}
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    xfce4 \
    xfce4-goodies \
    tigervnc-standalone-server \
    tigervnc-common \
    tigervnc-tools \
    novnc \
    supervisor \
    fonts-wqy-zenhei \
    build-essential \
    python3-dev \
    dbus-x11 \
    postgresql-client \
    libgl1 \
    libglib2.0-0 \
    curl unzip wget gnupg ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv

COPY requirements.txt ./requirements.txt

RUN uv pip install --system --no-cache -r requirements.txt

RUN playwright install --with-deps chromium

COPY . /app

COPY docker/entrypoint.sh /app/docker/entrypoint.sh
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod +x /app/docker/entrypoint.sh

CMD ["/app/docker/entrypoint.sh"]
