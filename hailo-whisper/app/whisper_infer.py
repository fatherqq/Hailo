import numpy as np
import io
from pydub import AudioSegment
from transformers import WhisperForConditionalGeneration, WhisperProcessor
import hailo
from .hailo_device import device_manager
from .config import settings

class WhisperInferencer:
    def __init__(self):
        self.device = device_manager.device
        self.hef_path = device_manager.get_model_path()
        self.processor = None
        self.model = None
        self.input_vstream = None
        self.output_vstream = None
        self._load_components()

    def _load_components(self):
        # CPU 侧解码器与处理器
        model_name = "openai/whisper-base" if device_manager.device_arch == "hailo10h" else "openai/whisper-tiny"
        self.processor = WhisperProcessor.from_pretrained(model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
        self.model.eval()

        # NPU 侧编码器 HEF 加载
        hef = hailo.Hef(self.hef_path)
        self.input_vstream = hef.configure_input_vstreams(self.device)[0]
        self.output_vstream = hef.configure_output_vstreams(self.device)[0]

    def _preprocess(self, audio_bytes: bytes) -> np.ndarray:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio = audio.set_frame_rate(settings.SAMPLE_RATE).set_channels(settings.CHANNELS)
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        if audio.sample_width == 2:
            samples /= 32768.0
        return self.processor(
            samples, sampling_rate=settings.SAMPLE_RATE, return_tensors="np"
        ).input_features.astype(np.float32)

    def transcribe(self, audio_bytes: bytes, language: str = None) -> str:
        language = language or settings.DEFAULT_LANGUAGE
        input_features = self._preprocess(audio_bytes)
        
        # NPU 执行编码器推理
        self.input_vstream.write(input_features)
        encoder_output = self.output_vstream.read()

        # CPU 解码生成文本
        predicted_ids = self.model.generate(
            encoder_outputs=encoder_output,
            language=language,
            max_length=448
        )
        return self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()

whisper_inferencer = WhisperInferencer()
