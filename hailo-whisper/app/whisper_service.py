"""Whisper service: owns the Hailo pipeline and turns audio files into text."""

import os
import logging
import threading
from queue import Empty

from app.hailo_whisper_pipeline import HailoWhisperPipeline
from app.hw_detect import detect_hw_arch
from app.model_manager import ensure_models
from app.whisper_hef_registry import HEF_REGISTRY
from common.audio_utils import load_audio
from common.preprocessing import preprocess, improve_input_audio
from common.postprocessing import clean_transcription

logger = logging.getLogger(__name__)

# Variant fallback order when the requested combo is unsupported on the HW.
VARIANT_FALLBACK = ["base", "tiny", "tiny.en"]


class WhisperService:
    def __init__(self):
        self.pipeline = None
        self.hw_arch = None
        self.variant = None
        self.lock = threading.Lock()
        self.ready = False
        self.status_msg = "未初始化"

    def initialize(self, hw_arch=None, variant=None, auto_download=None, multi_process=None):
        """Load the model for the detected HW + selected variant.

        Raises ``RuntimeError`` if the model cannot be prepared.
        """
        hw_arch = hw_arch or os.environ.get("HW_ARCH_OVERRIDE", "auto")
        variant = variant or os.environ.get("MODEL_VARIANT", "base")
        if multi_process is None:
            multi_process = os.environ.get("MULTI_PROCESS_SERVICE", "false").lower() == "true"
        if auto_download is None:
            auto_download = os.environ.get("MODEL_AUTO_DOWNLOAD", "true").lower() != "false"

        detected = detect_hw_arch(hw_arch)
        logger.info("硬件架构: 检测到/指定=%s (请求=%s)", detected, hw_arch)

        # Validate the requested combo; fall back to a supported variant if needed.
        if variant not in HEF_REGISTRY or detected not in HEF_REGISTRY.get(variant, {}):
            for v in VARIANT_FALLBACK:
                if v in HEF_REGISTRY and detected in HEF_REGISTRY[v]:
                    logger.warning("模型 %s 在 %s 上不可用，回退到 %s", variant, detected, v)
                    variant = v
                    break
            else:
                raise RuntimeError(f"硬件 {detected} 上没有任何可用模型组合")

        if not ensure_models(detected, variant, auto_download):
            raise RuntimeError(
                "模型文件缺失且无法下载，请检查网络或将模型放入持久化目录 "
                f"{os.environ.get('MODELS_DIR', '/data/hailo-whisper/models')}"
            )

        enc = HEF_REGISTRY[variant][detected]["encoder"]
        dec = HEF_REGISTRY[variant][detected]["decoder"]
        if not (os.path.exists(enc) and os.path.exists(dec)):
            raise RuntimeError(f"HEF 文件不存在: {enc} / {dec}")

        if self.pipeline is not None:
            try:
                self.pipeline.stop()
            except Exception:
                pass

        self.pipeline = HailoWhisperPipeline(enc, dec, variant, multi_process_service=multi_process)
        self.hw_arch = detected
        self.variant = variant
        self.ready = True
        self.status_msg = f"就绪: {detected} / whisper-{variant}"
        logger.info("Whisper 服务初始化完成: %s / whisper-%s", detected, variant)

    def transcribe(self, audio_path, language=None):
        """Transcribe an audio file path into text.

        Processing is serialized with a lock so concurrent HTTP requests don't
        interleave on the single Hailo pipeline.
        """
        if not self.ready or self.pipeline is None:
            raise RuntimeError("服务未就绪")

        with self.lock:
            try:
                sampled_audio = load_audio(audio_path)
            except Exception as exc:
                raise RuntimeError(f"音频加载失败: {exc}")

            sampled_audio, start_time = improve_input_audio(sampled_audio, vad=True)
            chunk_offset = max(0.0, (start_time or 0.0) - 0.2)
            chunk_length = self.pipeline.get_model_input_audio_length()

            try:
                mel_spectrograms = preprocess(
                    sampled_audio, is_nhwc=True,
                    chunk_length=chunk_length, chunk_offset=chunk_offset,
                )
            except Exception as exc:
                raise RuntimeError(f"音频预处理失败: {exc}")

            parts = []
            for mel in mel_spectrograms:
                self.pipeline.send_data(mel)
                try:
                    transcription = clean_transcription(self.pipeline.get_transcription())
                except Empty:
                    raise RuntimeError("推理超时，请检查 Hailo 设备状态")
                parts.append(transcription)

            text = " ".join(p.strip() for p in parts if p and p.strip())
            return text
