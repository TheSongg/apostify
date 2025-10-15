#!/bin/bash

echo "Waiting for browser to start..."
sleep 5

# pw启动后只能监听127.0.0.1地址，外部无法访问，使用socat进行端口转发
echo "Starting socat to forward port 9222..."
socat TCP-LISTEN:9222,fork,reuseaddr TCP:127.0.0.1:9221 &
