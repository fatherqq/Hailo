"""Model downloader with persistent storage support.

All HEF weights and decoder token-embedding assets are downloaded into
``$MODELS_DIR`` (default ``/media/hailo`` inside the HA addon),
so they survive container / addon restarts. On every start we only download
what is missing, making the first boot the only one that needs network access.
"""

import os
import logging
import subprocess

logger = logging.getLogger(__name__)

MODELS_DIR = os.environ.get("MODELS_DIR", "/media/hailo")

BASE_HEF = "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/whisper"
BASE_ASSETS = "https://hailo-csdata.s3.eu-west-2.amazonaws.com/resources/npy%20files/whisper/decoder_assets"

# (hw_arch, variant) -> list of (url, relative_target_path under MODELS_DIR)
HEF_FILES = {
    ("hailo8", "tiny"): [
        (f"{BASE_HEF}/h8/tiny-whisper-decoder-fixed-sequence-matmul-split.hef",
         "hefs/h8/tiny/tiny-whisper-decoder-fixed-sequence-matmul-split.hef"),
        (f"{BASE_HEF}/h8/tiny-whisper-encoder-10s_15dB.hef",
         "hefs/h8/tiny/tiny-whisper-encoder-10s_15dB.hef"),
    ],
    ("hailo8", "base"): [
        (f"{BASE_HEF}/h8/base-whisper-decoder-fixed-sequence-matmul-split.hef",
         "hefs/h8/base/base-whisper-decoder-fixed-sequence-matmul-split.hef"),
        (f"{BASE_HEF}/h8/base-whisper-encoder-5s.hef",
         "hefs/h8/base/base-whisper-encoder-5s.hef"),
    ],
    ("hailo8l", "tiny"): [
        (f"{BASE_HEF}/h8l/tiny-whisper-decoder-fixed-sequence-matmul-split_h8l.hef",
         "hefs/h8l/tiny/tiny-whisper-decoder-fixed-sequence-matmul-split_h8l.hef"),
        (f"{BASE_HEF}/h8l/tiny-whisper-encoder-10s_15dB_h8l.hef",
         "hefs/h8l/tiny/tiny-whisper-encoder-10s_15dB_h8l.hef"),
    ],
    ("hailo8l", "base"): [
        (f"{BASE_HEF}/h8l/base-whisper-decoder-fixed-sequence-matmul-split_h8l.hef",
         "hefs/h8l/base/base-whisper-decoder-fixed-sequence-matmul-split_h8l.hef"),
        (f"{BASE_HEF}/h8l/base-whisper-encoder-5s_h8l.hef",
         "hefs/h8l/base/base-whisper-encoder-5s_h8l.hef"),
    ],
    ("hailo10h", "tiny"): [
        (f"{BASE_HEF}/h10h/tiny-whisper-decoder-fixed-sequence.hef",
         "hefs/h10h/tiny/tiny-whisper-decoder-fixed-sequence.hef"),
        (f"{BASE_HEF}/h10h/tiny-whisper-encoder-10s.hef",
         "hefs/h10h/tiny/tiny-whisper-encoder-10s.hef"),
    ],
    ("hailo10h", "base"): [
        (f"{BASE_HEF}/h10h/base-whisper-decoder-fixed-sequence-matmul-split_h8l.hef",
         "hefs/h10h/base/base-whisper-decoder-fixed-sequence-matmul-split_h8l.hef"),
        (f"{BASE_HEF}/h10h/base-whisper-encoder-5s_h8l.hef",
         "hefs/h10h/base/base-whisper-encoder-5s_h8l.hef"),
    ],
    ("hailo10h", "tiny.en"): [
        (f"{BASE_HEF}/h10h/tiny_en-whisper-decoder-fixed-sequence.hef",
         "hefs/h10h/tiny.en/tiny_en-whisper-decoder-fixed-sequence.hef"),
        (f"{BASE_HEF}/h10h/tiny_en-whisper-encoder-10s.hef",
         "hefs/h10h/tiny.en/tiny_en-whisper-encoder-10s.hef"),
    ],
}

# variant -> list of (url, relative_target_path under MODELS_DIR)
ASSET_FILES = {
    "tiny": [
        (f"{BASE_ASSETS}/tiny/decoder_tokenization/onnx_add_input_tiny.npy",
         "decoder_assets/tiny/decoder_tokenization/onnx_add_input_tiny.npy"),
        (f"{BASE_ASSETS}/tiny/decoder_tokenization/token_embedding_weight_tiny.npy",
         "decoder_assets/tiny/decoder_tokenization/token_embedding_weight_tiny.npy"),
    ],
    "base": [
        (f"{BASE_ASSETS}/base/decoder_tokenization/onnx_add_input_base.npy",
         "decoder_assets/base/decoder_tokenization/onnx_add_input_base.npy"),
        (f"{BASE_ASSETS}/base/decoder_tokenization/token_embedding_weight_base.npy",
         "decoder_assets/base/decoder_tokenization/token_embedding_weight_base.npy"),
    ],
    "tiny.en": [
        (f"{BASE_ASSETS}/tiny.en/decoder_tokenization/onnx_add_input_tiny.en.npy",
         "decoder_assets/tiny.en/decoder_tokenization/onnx_add_input_tiny.en.npy"),
        (f"{BASE_ASSETS}/tiny.en/decoder_tokenization/token_embedding_weight_tiny.en.npy",
         "decoder_assets/tiny.en/decoder_tokenization/token_embedding_weight_tiny.en.npy"),
    ],
}


def _target_path(rel):
    return os.path.join(MODELS_DIR, rel)


def _download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    logger.info("下载: %s -> %s", url, dest)
    subprocess.run(["wget", "-q", "--show-progress", "-O", dest, url], check=True)


def ensure_models(hw_arch, variant, auto_download=True):
    """Ensure HEF + decoder assets for ``(hw_arch, variant)`` exist.

    Returns ``True`` if everything required is present (or was downloaded),
    ``False`` if something is missing and downloading was disabled/failed.
    """
    needed = []
    if (hw_arch, variant) in HEF_FILES:
        needed += HEF_FILES[(hw_arch, variant)]
    if variant in ASSET_FILES:
        needed += ASSET_FILES[variant]

    if not needed:
        logger.error("不支持的模型组合: hw=%s variant=%s", hw_arch, variant)
        return False

    missing = [(url, rel) for (url, rel) in needed if not os.path.exists(_target_path(rel))]

    if not missing:
        logger.info("模型已存在，跳过下载: hw=%s variant=%s", hw_arch, variant)
        return True

    if not auto_download:
        logger.error("缺少模型文件且未开启自动下载: %s", [m[1] for m in missing])
        return False

    ok = True
    for url, rel in missing:
        dest = _target_path(rel)
        try:
            _download(url, dest)
        except subprocess.CalledProcessError as exc:
            logger.error("下载失败: %s (%s)", url, exc)
            ok = False
    return ok


def list_models():
    """Return availability of every supported model in ``MODELS_DIR``."""
    result = {}
    for (hw, variant), files in HEF_FILES.items():
        present = all(os.path.exists(_target_path(rel)) for _, rel in files)
        result.setdefault(hw, {})[variant] = "downloaded" if present else "missing"
    return result


def download_url(url, dest):
    """Download an arbitrary URL to ``dest`` (used by the CLI)."""
    _download(url, dest)
