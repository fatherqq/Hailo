#!/usr/bin/env python3
"""CLI to pre-download Whisper models into the persistent model directory.

Usage (from /opt/hailo-whisper):
    python3 -m app.download_resources --hw-arch hailo8 --variant base
    python3 -m app.download_resources            # hailo8 / base

Models are stored under $MODELS_DIR (default /data/hailo-whisper/models) and
survive addon restarts.
"""
import argparse
import sys

from app.model_manager import ensure_models


def main():
    parser = argparse.ArgumentParser(description="Whisper 模型下载器 (持久化)")
    parser.add_argument(
        "--hw-arch", type=str, default="hailo8",
        choices=["hailo8", "hailo8l", "hailo10h"],
        help="目标硬件架构 (default: hailo8)",
    )
    parser.add_argument(
        "--variant", type=str, default="base",
        choices=["base", "tiny", "tiny.en"],
        help="Whisper 变体 (default: base)",
    )
    args = parser.parse_args()

    ok = ensure_models(args.hw_arch, args.variant, auto_download=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
