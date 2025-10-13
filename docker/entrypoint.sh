#!/bin/bash
set -e

VNC_RESOLUTION=${VNC_RESOLUTION:-1280x800}
VNC_PORT=${VNC_PORT:-5901}
NO_VNC_PORT=${NO_VNC_PORT:-6901}
DISPLAY=${DISPLAY:-:1}

echo "设置 VNC 密码..."
if [ -n "$VNC_PASSWORD" ]; then
    mkdir -p /root/.vnc
    echo "$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd
    chmod 600 /root/.vnc/passwd
else
    echo "未设置 VNC_PASSWORD 环境变量，将无法远程连接。"
fi

echo "初始化完成，启动 Supervisor..."
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf