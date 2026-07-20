#!/bin/bash
set -e

CONFIG_PATH=/data/options.json

# 读取 HA 前端配置
VDEVICE_GROUP_ID=$(jq -r '.vdevice_group_id // "HAILO_SHARED"' "$CONFIG_PATH" 2>/dev/null || echo "HAILO_SHARED")
LANGUAGE=$(jq -r '.language // "zh"' "$CONFIG_PATH" 2>/dev/null || echo "zh")
MODEL_AUTO_DETECT=$(jq -r '.model_auto_detect // true' "$CONFIG_PATH" 2>/dev/null || echo "true")
CUSTOM_MODEL=$(jq -r '.custom_model // ""' "$CONFIG_PATH" 2>/dev/null || echo "")

echo "=========================================="
echo " Hailo Whisper 语音识别加载项"
echo "=========================================="
echo "硬件共享组:    $VDEVICE_GROUP_ID"
echo "默认语言:      $LANGUAGE"
echo "服务端口:      8001"
echo "=========================================="

# 写入启动日志
{
  echo ""
  echo "=== 启动时间: $(date) ==="
  echo "可见 Hailo 设备:"
  ls -l /dev/hailo* /dev/h1x* 2>/dev/null || echo "  未检测到设备节点"
} >> /data/hailo-whisper.log 2>/dev/null || true

# ----------------------------------------------------------------------------
# 模型持久化配置（映射到 HA media 目录，重启不丢失）
# ----------------------------------------------------------------------------
export MODELS_DIR=/media/hailo_whisper/models
mkdir -p "$MODELS_DIR"/hailo10h "$MODELS_DIR"/hailo8 "$MODELS_DIR"/hailo8l
chmod -R 755 /media/hailo_whisper 2>/dev/null || true

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

# 设备可用性预检
if [ -e /dev/hailo0 ] || [ -e /dev/h1x-0 ]; then
    echo "✓ 检测到 Hailo 硬件设备"
else
    echo "⚠ 警告: 未检测到 Hailo 设备节点，请检查硬件直通与 config.yaml 设备配置"
fi

# ----------------------------------------------------------------------------
# 环境变量注入
# ----------------------------------------------------------------------------
export HAILO_VDEVICE_GROUP_ID="$VDEVICE_GROUP_ID"
export DEFAULT_LANGUAGE="$LANGUAGE"
export MODEL_AUTO_DETECT="$MODEL_AUTO_DETECT"
export CUSTOM_MODEL="$CUSTOM_MODEL"
export XDG_DATA_HOME=/media/hailo_whisper

echo "正在启动语音识别服务..."
echo "运行日志: /data/hailo-whisper.log"

# 前台启动服务，保持容器运行
cd /opt/hailo-whisper
exec python3 -m uvicorn app.api_server:app --host 0.0.0.0 --port 8001 >> /data/hailo-whisper.log 2>&1
