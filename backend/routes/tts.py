import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from middleware.auth import get_current_user
from models.user import User
from services.tts_service import text_to_speech, cleanup_file

router = APIRouter(prefix="/api/tts", tags=["Text-to-Speech"])

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    lang: str = Field(default="yo")

@router.post("")
async def synthesize_speech(
    req: TTSRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    result = await asyncio.to_thread(text_to_speech, text=req.text, lang=req.lang)
    if not result:
        raise HTTPException(status_code=500, detail="Text-to-speech synthesis failed")

    background_tasks.add_task(cleanup_file, result["audio_path"])

    return FileResponse(
        result["audio_path"],
        media_type="audio/mpeg",
        filename="speech.mp3",
        headers={
            "X-TTS-Engine": result["engine"],
        },
    )
