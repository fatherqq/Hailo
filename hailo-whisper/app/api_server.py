"""FastAPI REST service exposing the Hailo Whisper pipeline.

Endpoints
---------
* ``GET  /health``                       – liveness / readiness
* ``GET  /info``                         – current hw arch, variant, model dir
* ``GET  /models``                       – which models are downloaded
* ``POST /transcribe``                   – multipart audio file -> {"text": ...}
* ``POST /v1/audio/transcriptions``       – OpenAI-compatible transcription
* ``POST /admin/reload``                 – re-initialize (e.g. after hot-plugging)

Run with:  ``python3 -m app.api_server``  (from /opt/hailo-whisper)
"""

import os
import logging
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.whisper_service import WhisperService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("hailo-whisper")

service = WhisperService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在初始化 Hailo Whisper 服务 ...")
    try:
        service.initialize()
    except Exception as exc:  # keep the server up so /health + /admin/reload work
        logger.error("初始化失败（服务将以未就绪状态运行）: %s", exc)
    yield
    if service.pipeline is not None:
        try:
            service.pipeline.stop()
        except Exception:
            pass


app = FastAPI(title="Hailo Whisper Service", version="1.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "status": "ok" if service.ready else "initializing",
        "ready": service.ready,
        "hw_arch": service.hw_arch,
        "variant": service.variant,
        "message": service.status_msg,
    }


@app.get("/info")
def info():
    return {
        "hw_arch": service.hw_arch,
        "variant": service.variant,
        "ready": service.ready,
        "language": os.environ.get("DEFAULT_LANGUAGE", "auto"),
        "models_dir": os.environ.get("MODELS_DIR", "/media/hailo"),
    }


@app.get("/models")
def models():
    from app.model_manager import list_models
    return {
        "models": list_models(),
        "models_dir": os.environ.get("MODELS_DIR", "/media/hailo"),
    }


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), language: str = Form("auto")):
    if not service.ready:
        raise HTTPException(status_code=503, detail="服务尚未就绪，请稍候或查看日志 /admin/reload")

    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(await file.read())
        tmp.close()
        text = service.transcribe(tmp.name, language=language)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

    return {"text": text, "variant": service.variant, "language": language}


@app.post("/v1/audio/transcriptions")
async def openai_transcribe(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str = Form(None),
):
    """OpenAI-compatible transcription endpoint (e.g. for HA Whisper integration)."""
    res = await transcribe(file, language=language or "auto")
    return {"text": res["text"]}


@app.post("/admin/reload")
def reload(hw_arch: str = None, variant: str = None):
    try:
        service.initialize(hw_arch=hw_arch, variant=variant)
        return {"ok": True, "hw_arch": service.hw_arch, "variant": service.variant}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10300)
