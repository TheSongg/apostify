FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy AS playwright
ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    VNC_PORT=${VNC_PORT} \
    NO_VNC_PORT=${NO_VNC_PORT} \
    VNC_RESOLUTION=${VNC_RESOLUTION} \
    VNC_PASS=${VNC_PASSWORD}
EXPOSE ${NO_VNC_PORT} ${VNC_PORT}

RUN apt-get update && apt-get install -y \
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
    curl unzip wget gnupg ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright

RUN playwright install --with-deps chromium

COPY entrypoint.sh /entrypoint.sh
COPY start_browser.py /start_browser.py
COPY pw_supervisord.conf /etc/supervisor/conf.d/pw_supervisord.conf
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]


FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy AS apostify-base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv

COPY requirements.txt ./requirements.txt

RUN uv pip install --system --no-cache -r requirements.txt

RUN playwright install --with-deps chromium

COPY . /app

COPY docker/*.sh /app/docker
RUN chmod +x /app/docker/*.sh
