#!/bin/bash
set -e

# 等待 VNC server 启动
echo "检测 VNC 服务是否已启动..."

# 最多等待 60 秒
for i in {1..30}; do
    if vncserver -list 2>/dev/null | grep -qE '^[[:space:]]*1[[:space:]]'; then
        echo "VNC 服务已启动！"
        break
    fi
    echo "等待 VNC 服务启动中... ($i/30)"
    sleep 2
done

# 如果仍未启动，则报错退出
if ! vncserver -list 2>/dev/null | grep -qE '^[[:space:]]*1[[:space:]]'; then
    echo "VNC 服务启动超时，退出。"
    exit 1
fi

echo "Running Django migrations..."
python manage.py makemigrations --settings=core.settings
python manage.py migrate --settings=core.settings

echo "Starting uWSGI..."
exec uwsgi --ini uwsgi.ini