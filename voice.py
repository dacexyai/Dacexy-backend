from __future__ import annotations
import io
import base64
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models.orm_models import User
from src.infrastructure.ai_providers.deepseek import DeepSeekProvider
from src.interfaces.http.dependencies.container import get_deepseek
from src.interfaces.http.routes.auth import _get_current_user

router = APIRouter(prefix="/voice", tags=["voice"])
log = logging.getLogger("voice")


class TTSRequest(BaseModel):
    text: str
    lang: str = "en"


@router.post("/tts")
async def text_to_speech(
    body: TTSRequest,
    user: User = Depends(_get_current_user),
):
    try:
        from gtts import gTTS
        tts = gTTS(text=body.text, lang=body.lang)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        audio_b64 = base64.b64encode(buf.read()).decode()
        return {"audio_base64": audio_b64, "format": "mp3"}
    except ImportError:
        raise HTTPException(503, "TTS service not available — install gTTS")
    except Exception as e:
        raise HTTPException(500, f"TTS failed: {str(e)}")


@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    user: User = Depends(_get_current_user),
):
    try:
        import speech_recognition as sr
        content = await file.read()
        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(io.BytesIO(content))
        with audio_file as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return {"text": text}
    except ImportError:
        raise HTTPException(503, "STT service not available — install SpeechRecognition")
    except Exception as e:
        raise HTTPException(500, f"STT failed: {str(e)}")


@router.post("/chat")
async def voice_chat(
    body: TTSRequest,
    user: User = Depends(_get_current_user),
    ai: DeepSeekProvider = Depends(get_deepseek),
):
    """Convert text to AI response then to speech"""
    try:
        ai_response = await ai.chat(
            [{"role": "user", "content": body.text}],
            stream=False
        )
        try:
            from gtts import gTTS
            tts = gTTS(text=ai_response, lang=body.lang)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            audio_b64 = base64.b64encode(buf.read()).decode()
            return {"text_response": ai_response, "audio_base64": audio_b64, "format": "mp3"}
        except ImportError:
            return {"text_response": ai_response, "audio_base64": None}
    except Exception as e:
        raise HTTPException(500, f"Voice chat failed: {str(e)}")
