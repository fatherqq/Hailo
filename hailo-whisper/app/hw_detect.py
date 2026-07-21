"""Detect Hailo hardware architecture (hailo8 / hailo8l / hailo10h).

Detection order:
  1. HailoRT ``Device.scan()`` (reads the part number, most reliable).
  2. Device-node heuristic (``/dev/h1x-0`` -> 10H, ``/dev/hailo0`` -> 8/8L).
  3. Fallback to ``hailo8``.
"""

import os
import logging

logger = logging.getLogger(__name__)

VALID = ("hailo8", "hailo8l", "hailo10h")


def _detect_via_hailort():
    """Use HailoRT to enumerate devices and read their part number."""
    try:
        from hailo_platform import Device  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on hailo_platform
        logger.debug("hailo_platform 不可用，跳过 HailoRT 检测: %s", exc)
        return None
    try:
        devices = Device.scan()
    except Exception as exc:
        logger.warning("HailoRT Device.scan() 失败: %s", exc)
        return None

    for dev in devices:
        try:
            pn = str(getattr(dev, "part_number", "") or "").upper()
        except Exception:
            pn = ""
        if not pn:
            continue
        if "10H" in pn:
            return "hailo10h"
        if "8L" in pn:
            return "hailo8l"
        if "8" in pn:
            return "hailo8"
    return None


def _detect_via_nodes():
    """Best-effort detection from device nodes exposed by the kernel driver."""
    if os.path.exists("/dev/h1x-0") or os.path.exists("/dev/hailo10"):
        return "hailo10h"
    if os.path.exists("/dev/hailo0"):
        # hailo8 or hailo8l share the same node; cannot tell apart without HailoRT
        return "hailo8"
    return None


def detect_hw_arch(override=None):
    """Return the hardware arch to use.

    ``override`` may be ``None``/``"auto"``/``""`` (auto-detect) or an explicit
    value from :data:`VALID`.
    """
    if override and str(override).strip().lower() not in ("auto", "", "none"):
        return str(override).strip().lower()

    arch = _detect_via_hailort()
    if arch:
        logger.info("通过 HailoRT 自动识别硬件: %s", arch)
        return arch

    arch = _detect_via_nodes()
    if arch:
        logger.info("通过设备节点识别硬件: %s", arch)
        return arch

    logger.warning("无法自动识别硬件，回退到 hailo8")
    return "hailo8"
