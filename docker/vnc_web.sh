#!/bin/bash

# 设置 VNC 密码，如果环境变量 VNC_PASSWORD 存在的话
if [ -n "$VNC_PASSWORD" ]; then
    echo "设置 VNC 密码..."
    mkdir -p /root/.vnc
    echo "$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd
    chmod 600 /root/.vnc/passwd
else
    echo "警告：未设置 VNC_PASSWORD 环境变量，将无法连接。"
fi

# 启动 VNC 服务器
vncserver ${DISPLAY} -depth 24 -geometry ${VNC_RESOLUTION} -localhost no

# 启动 noVNC WebSocket 代理，将 Web 端口流量转发到 VNC 端口
/usr/share/novnc/utils/launch.sh --listen ${NO_VNC_PORT} --vnc localhost:${VNC_PORT}