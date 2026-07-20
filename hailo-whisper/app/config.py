import os

class Settings:
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    VDEVICE_GROUP_ID: str = os.getenv("HAILO_VDEVICE_GROUP_ID", "HAILO_SHARED")
    MODELS_DIR: str = os.getenv("MODELS_DIR", "/media/hailo_whisper/models")
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "zh")
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1

settings = Settings()
