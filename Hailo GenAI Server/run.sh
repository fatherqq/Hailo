#!/usr/bin/env bashio

set -e

# 读取配置
DEVICE=$(bashio::config 'hailo_device')
MODEL=$(bashio::config 'model')
GROUP_ID=$(bashio::config 'vdevice_group_id')
OPEN_WEBUI=$(bashio::config 'open_webui')

bashio::log.info "Starting Hailo-Ollama server..."

# 设置设备共享组 ID（如需与其他 Hailo 应用共享设备）
export HAILO_OLLAMA_VDEVICE_GROUP_ID="${GROUP_ID}"

# 启动 Hailo-Ollama 服务器
hailo-ollama &
SERVER_PID=$!

# 等待服务器就绪
bashio::log.info "Waiting for server to be ready..."
until curl -s http://localhost:8000/hailo/v1/list > /dev/null; do
    sleep 2
done
bashio::log.info "Hailo-Ollama server is ready!"

# 拉取默认模型
bashio::log.info "Pulling model: ${MODEL}"
curl -s http://localhost:8000/api/pull \
    -H 'Content-Type: application/json' \
    -d "{\"model\": \"${MODEL}\", \"stream\": true}" &
PULL_PID=$!

# 可选：启动 Open WebUI
if [ "${OPEN_WEBUI}" == "true" ]; then
    bashio::log.info "Starting Open WebUI..."
    docker run -d \
        --net=host \
        -e OLLAMA_BASE_URL=http://127.0.0.1:8000 \
        -v open-webui:/app/backend/data \
        --name open-webui \
        --restart always \
        ghcr.io/open-webui/open-webui:main
    bashio::log.info "Open WebUI available at http://localhost:8080"
fi

# 等待进程结束
wait $SERVER_PID
