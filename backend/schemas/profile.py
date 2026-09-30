from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserStats(BaseModel):
    total_transcriptions: int
    total_translations: int
    total_words_translated: int
    account_created: datetime
