from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WordConfidence(BaseModel):
    word: str
    confidence: float = Field(ge=0.0, le=1.0)
    start: Optional[float] = Field(None, description="Word start time in seconds (relative to record start)")
    end: Optional[float] = Field(None, description="Word end time in seconds (relative to record start)")


class AudioQuality(BaseModel):
    duration_sec: float
    rms_energy: float
    is_silent: bool
    is_clipped: bool
    warnings: List[str] = []


class TranscribeResponse(BaseModel):
    raw_text: str
    final_text: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    word_confidences: List[WordConfidence] = []
    quality: Optional[AudioQuality] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    detected_language: Optional[str] = "yo"
    engine: Optional[str] = None
    code_switched: Optional[bool] = False


class PolishRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: str = Field(default="yo", max_length=20)


class PolishResponse(BaseModel):
    text: str


class CorrectionRequest(BaseModel):
    transcription_id: int
    corrected_text: str = Field(..., min_length=1)


class CorrectionResponse(BaseModel):
    id: int
    original_text: str
    corrected_text: str
    created_at: datetime


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    direction: str = Field(default="auto", pattern="^(auto|en2yo|yo2en)$")


class RetranslateRequest(BaseModel):
    direction: str = Field(default="auto", pattern="^(auto|en2yo|yo2en)$")


class TranslateResponse(BaseModel):
    source_text: str
    translated_text: str
    detected_language: str
    target_language: str
    engine: str
    quality: Optional[str] = None  # "high", "medium", "low", "fallback"
    code_switched: Optional[bool] = False


class HistoryItem(BaseModel):
    id: int
    activity_type: str
    raw_text: Optional[str] = None
    final_text: Optional[str] = None
    translation: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    engine: Optional[str] = None
    audio_filename: Optional[str] = None
    original_filename: Optional[str] = None
    title: Optional[str] = None
    pinned: bool = False
    has_audio: bool = False
    created_at: datetime


class HistoryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    pinned: Optional[bool] = None


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    per_page: int
