#!/bin/bash
set -e

CONFIG_PATH=/data/options.json

# 读取 HA 前端配置（缺省值保证单独运行也可工作）
VDEVICE_GROUP_ID=$(jq -r '.vdevice_group_id // "HAILO_SHARED"' "$CONFIG_PATH" 2>/dev/null || echo "HAILO_SHARED")
LANGUAGE=$(jq -r '.language // "auto"' "$CONFIG_PATH" 2>/dev/null || echo "auto")
HW_ARCH=$(jq -r '.hw_arch // "auto"' "$CONFIG_PATH" 2>/dev/null || echo "auto")
MODEL_VARIANT=$(jq -r '.model_variant // "base"' "$CONFIG_PATH" 2>/dev/null || echo "base")
MODEL_AUTO_DOWNLOAD=$(jq -r '.model_auto_download // true' "$CONFIG_PATH" 2>/dev/null || echo "true")
MULTI_PROCESS=$(jq -r '.multi_process_service // false' "$CONFIG_PATH" 2>/dev/null || echo "false")

echo "=========================================="
echo " Hailo Whisper 语音识别加载项"
echo "=========================================="
echo "硬件架构:      $HW_ARCH (auto=自动检测 hailo8/8l/10h)"
echo "模型:          $MODEL_VARIANT"
echo "默认语言:      $LANGUAGE"
echo "自动下载模型:  $MODEL_AUTO_DOWNLOAD"
echo "多进程共享:    $MULTI_PROCESS"
echo "服务端口:      10300"
echo "=========================================="

# ----------------------------------------------------------------------------
# 模型持久化配置（保存到 HA 媒体目录 /media/hailo，重启不丢失，可在「媒体」中查看/备份）
# ----------------------------------------------------------------------------
export MODELS_DIR=/media/hailo/hailo-whisper
mkdir -p "$MODELS_DIR"/hefs "$MODELS_DIR"/decoder_assets
# HuggingFace tokenizer 缓存也持久化（首次下载后复用）
export HF_HOME="$MODELS_DIR/hf"
export TRANSFORMERS_CACHE="$MODELS_DIR/hf"
export HF_HUB_DISABLE_TELEMETRY=1
mkdir -p "$HF_HOME"

# ----------------------------------------------------------------------------
# 修复 Hailo 设备权限（HA 容器环境必备）
# ----------------------------------------------------------------------------
for dev in /dev/hailo* /dev/h1x*; do
  if [ -e "$dev" ]; then
    chmod 666 "$dev" 2>/dev/null || true
    echo "已修复设备权限: $dev"
  fi
done
udevadm trigger --subsystem-match=char 2>/dev/null || true

if [ -e /dev/hailo0 ] || [ -e /dev/h1x-0 ] || [ -e /dev/hailo10 ]; then
    echo "✓ 检测到 Hailo 设备节点"
else
    echo "⚠ 警告: 未检测到 Hailo 设备节点，请确认宿主机已加载 Hailo 内核驱动且 config.yaml 已正确映射设备"
fi

# ----------------------------------------------------------------------------
# 环境变量注入
# ----------------------------------------------------------------------------
export HAILO_VDEVICE_GROUP_ID="$VDEVICE_GROUP_ID"
export DEFAULT_LANGUAGE="$LANGUAGE"
export HW_ARCH_OVERRIDE="$HW_ARCH"
export MODEL_VARIANT="$MODEL_VARIANT"
export MODEL_AUTO_DOWNLOAD="$MODEL_AUTO_DOWNLOAD"
export MULTI_PROCESS_SERVICE="$MULTI_PROCESS"

echo "正在启动 Whisper 服务（首次启动会自动下载模型，请耐心等待）..."

# 前台启动 FastAPI 服务，保持容器运行
cd /opt/hailo-whisper
exec python3 -m app.api_server
