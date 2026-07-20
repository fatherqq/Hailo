import hailo
import os
from .config import settings

class HailoDeviceManager:
    def __init__(self):
        self.device = None
        self.device_arch = None
        self._init_device()

    def _detect_arch(self) -> str:
        """自动检测硬件架构"""
        try:
            info = self.device.get_device_info()
            arch = info.device_architecture.name.lower()
            if "hailo10" in arch:
                return "hailo10h"
            elif "hailo8l" in arch:
                return "hailo8l"
            else:
                return "hailo8"
        except Exception:
            return os.getenv("HAILO_ARCH", "hailo10h")

    def _init_device(self):
        device_params = hailo.DeviceParams()
        device_params.vdevice_group_id = settings.VDEVICE_GROUP_ID
        try:
            self.device = hailo.Device(device_params)
            self.device_arch = self._detect_arch()
        except Exception as e:
            raise RuntimeError(f"Hailo 设备初始化失败: {str(e)}") from e

    def get_model_path(self) -> str:
        """根据硬件自动匹配 HEF 模型"""
        model_dir = os.path.join(settings.MODELS_DIR, self.device_arch)
        model_map = {
            "hailo10h": "whisper_base.hef",
            "hailo8": "whisper_tiny.hef",
            "hailo8l": "whisper_tiny.hef"
        }
        hef_file = model_map[self.device_arch]
        full_path = os.path.join(model_dir, hef_file)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"未找到模型文件: {full_path}，请放入对应目录")
        return full_path

device_manager = HailoDeviceManager()
