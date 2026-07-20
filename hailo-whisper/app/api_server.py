from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from .whisper_infer import whisper_inferencer
from .hailo_device import device_manager

app = FastAPI(title="Hailo Whisper Service")

@app.get("/health")
async def health():
    return {"status": "ok", "device_arch": device_manager.device_arch}

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = "zh"
):
    try:
        audio_bytes = await file.read()
        text = whisper_inferencer.transcribe(audio_bytes, language)
        return {"code": 0, "text": text, "language": language}
    except Exception as e:
        return JSONResponse({"code": 1, "error": str(e)}, status_code=500)
