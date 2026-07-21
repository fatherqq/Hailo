#!/bin/bash
set -e
ONFIG_PATH=/data/options.json

# Read HA config
KEEP_ALIVE=$(jq -r '.keep_alive // "300m"' "$CONFIG_PATH" 2>/dev/null || echo "300m")
AUTO_DOWNLOAD=$(jq -r '.auto_download_model // false' "$CONFIG_PATH" 2>/dev/null || echo "false")

export OLLAMA_KEEP_ALIVE="$KEEP_ALIVE"
export AUTO_DOWNLOAD_MODEL="$AUTO_DOWNLOAD"

echo "=========================================="
echo " Hailo LLM Add-on (Only hailo-ollama service)"
echo "=========================================="
echo "Keep Alive:        $KEEP_ALIVE"
echo "Auto-download:     $AUTO_DOWNLOAD"
echo "Service port:      8000 (hailo-ollama port)"
echo "=========================================="

echo ""
echo "=== Start device status ==="
echo "Date: $(date)"
echo "Devices:"
ls -l /dev/hailo* /dev/h1x* 2>/dev/null || echo "  Detect no hailo/h1x device"
echo "HailoRT scan:"
which hailortcli && hailortcli scan 2>&1 || echo "  hailortcli unavailable"
# ----------------------------------------------------------------------------
# Persistent model core settings
# ----------------------------------------------------------------------------
export XDG_DATA_HOME=/media/hailo
MEDIA_BASE=/media/hailo
BLOB_DIR="$XDG_DATA_HOME/hailo-ollama/models/blob"
MANIFEST_DIR="$MEDIA_BASE/hailo-ollama/models/manifests"

mkdir -p "$BLOB_DIR" "$MANIFEST_DIR"
chmod -R 755 "$MEDIA_BASE/hailo-ollama" 2>/dev/null || true

# 1. Purge Old User Manifests & Model Cache (User Data Only, System Intact)
if [ -d "$MANIFEST_DIR" ]; then
  find "$MANIFEST_DIR" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true
fi
echo "[Persistence] Cleared old user model caches to avoid manifest format incompatibility."

# 2. Copy the syste-included model manifest to the persistence directory (only adds new files; skips existing ones).
if [ -d /usr/share/hailo-ollama/models/manifests ]; then
  cp -a --no-clobber /usr/share/hailo-ollama/models/manifests/* "$MANIFEST_DIR/" 2>/dev/null || true
  echo "[Persistence] System model manifest synced."
fi

# Created a symlink for legacy path compatibility.
mkdir -p /root/.ollama
ln -sfn "$MEDIA_BASE/hailo-ollama/models" /root/.ollama/models 2>/dev/null || true
chmod -R a+w "$BLOB_DIR" 2>/dev/null || true

echo "=== PERSISTENCE_PATH ==="
echo "XDG_DATA_HOME = $XDG_DATA_HOME"
echo "HEF model directory:   $BLOB_DIR"
echo "=========================================="

# Fix Hailo device permissions.
for dev in /dev/hailo* /dev/h1x*; do
  if [ -e "$dev" ]; then
    chmod 666 "$dev" 2>/dev/null || true
    echo "Permissions set 666: $dev"
  fi
done
udevadm trigger --subsystem-match=char 2>/dev/null || true

# Device availability pre-check
if [ -e /dev/hailo0 ]; then
    echo "✓ Detected Hailo device /dev/hailo0"
else
    echo "⚠ Warning: /dev/hailo0 not detected."
fi

# Check if the binary exists.
if ! command -v hailo-ollama >/dev/null 2>&1; then
   echo "ERROR: hailo-ollama executable not found."
echo "Please ensure the hailo_gen_ai_model_zoo package is properly installed."
    exit 1
fi

# ----------------------------------------------------------------------------
# Start hailo-ollama core service (native port 8000)
# ----------------------------------------------------------------------------
export OLLAMA_HOST=0.0.0.0:8000
export HAILO_OLLAMA_VDEVICE_GROUP_ID=HAILO_OLLAMA_SHARED
export HAILO_VDEVICE_GROUP_ID=HAILO_OLLAMA_SHARED

echo "Starting hailo-ollama service, listening on $OLLAMA_HOST ..."

# Fix: Remove nohup and log redirection, run directly in background (output to container logs)
env XDG_DATA_HOME="$XDG_DATA_HOME" \
  OLLAMA_HOST="$OLLAMA_HOST" \
  HAILO_OLLAMA_VDEVICE_GROUP_ID="$HAILO_OLLAMA_VDEVICE_GROUP_ID" \
  HAILO_VDEVICE_GROUP_ID="$HAILO_VDEVICE_GROUP_ID" \
  hailo-ollama &

HAILO_PID=$!
echo "hailo-ollama process PID: $HAILO_PID"

trap 'echo "Stopping hailo-ollama (pid $HAILO_PID)"; kill $HAILO_PID 2>/dev/null; wait $HAILO_PID 2>/dev/null' EXIT INT TERM

# Wait for service to be ready
echo "Waiting for service initialization..."
READY=0
for i in $(seq 1 45); do
    if curl -sf http://127.0.0.1:8000/api/tags >/dev/null 2>&1 || \
       curl -sf http://127.0.0.1:8000/hailo/v1/list >/dev/null 2>&1; then
        echo "✓ hailo-ollama service started successfully (pid $HAILO_PID)"
        READY=1
        break
    fi
    sleep 1
done

if [ "$READY" -ne 1 ]; then
    echo "⚠ Service did not become ready within 45 seconds, startup failed"
    exit 1
fi

echo "=========================================="
echo "  Service is running, API address: http://localhost:8000"
echo "=========================================="

wait $HAILO_PID
