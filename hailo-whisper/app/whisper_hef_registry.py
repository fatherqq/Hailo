"""HEF file registry resolved against the persistent model directory.

All paths are built from ``$MODELS_DIR`` (default ``/data/hailo-whisper/models``)
so the weights live in HA's persistent storage instead of the ephemeral image.
"""

import os

MODELS_DIR = os.environ.get("MODELS_DIR", "/data/hailo-whisper/models")


def _p(rel):
    return os.path.join(MODELS_DIR, rel)


HEF_REGISTRY = {
    "base": {
        "hailo8": {
            "encoder": _p("hefs/h8/base/base-whisper-encoder-5s.hef"),
            "decoder": _p("hefs/h8/base/base-whisper-decoder-fixed-sequence-matmul-split.hef"),
        },
        "hailo8l": {
            "encoder": _p("hefs/h8l/base/base-whisper-encoder-5s_h8l.hef"),
            "decoder": _p("hefs/h8l/base/base-whisper-decoder-fixed-sequence-matmul-split_h8l.hef"),
        },
        "hailo10h": {
            "encoder": _p("hefs/h10h/base/base-whisper-encoder-5s_h8l.hef"),
            "decoder": _p("hefs/h10h/base/base-whisper-decoder-fixed-sequence-matmul-split_h8l.hef"),
        },
    },
    "tiny": {
        "hailo8": {
            "encoder": _p("hefs/h8/tiny/tiny-whisper-encoder-10s_15dB.hef"),
            "decoder": _p("hefs/h8/tiny/tiny-whisper-decoder-fixed-sequence-matmul-split.hef"),
        },
        "hailo8l": {
            "encoder": _p("hefs/h8l/tiny/tiny-whisper-encoder-10s_15dB_h8l.hef"),
            "decoder": _p("hefs/h8l/tiny/tiny-whisper-decoder-fixed-sequence-matmul-split_h8l.hef"),
        },
        "hailo10h": {
            "encoder": _p("hefs/h10h/tiny/tiny-whisper-encoder-10s.hef"),
            "decoder": _p("hefs/h10h/tiny/tiny-whisper-decoder-fixed-sequence.hef"),
        },
    },
    "tiny.en": {
        "hailo10h": {
            "encoder": _p("hefs/h10h/tiny.en/tiny_en-whisper-encoder-10s.hef"),
            "decoder": _p("hefs/h10h/tiny.en/tiny_en-whisper-decoder-fixed-sequence.hef"),
        }
    },
}
