FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy AS playwright

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    VNC_PORT=${VNC_PORT:-5901} \
    NO_VNC_PORT=${NO_VNC_PORT:-6080} \
    VNC_RESOLUTION=${VNC_RESOLUTION:-1280x800} \
    VNC_PASS=${VNC_PASSWORD:-vncpass}

EXPOSE ${NO_VNC_PORT} ${VNC_PORT}

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        xfce4 \
        xfce4-goodies \
        tigervnc-standalone-server \
        tigervnc-common \
        tigervnc-tools \
        novnc \
        supervisor \
        fonts-wqy-zenhei \
        dbus-x11 \
        curl unzip wget gnupg ca-certificates git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN playwright install --with-deps chromium

COPY docker/entrypoint.sh /app/entrypoint.sh
COPY utils/start_browser.py /app/start_browser.py
COPY docker/pw_supervisord.conf /etc/supervisor/conf.d/pw_supervisord.conf
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]

FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy AS apostify

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        postgresql-client \
        libgl1 \
        libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . /app
COPY docker/*.sh /app/docker
RUN chmod +x /app/docker/*.sh

RUN useradd -m appuser && chown -R appuser /app
USER appuser

# 默认启动命令
CMD ["bash", "/app/docker/start.sh"]
