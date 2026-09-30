from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AdminActivityItem(BaseModel):
    id: int
    user: str
    user_id: int
    activity_type: str
    summary: str
    engine: Optional[str] = None
    created_at: datetime


class AdminUserItem(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_admin: bool
    created_at: datetime
    transcription_count: int = 0
    translation_count: int = 0
    last_active: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminUserDetail(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_admin: bool
    created_at: datetime
    transcription_count: int = 0
    translation_count: int = 0
    total_words_transcribed: int = 0
    total_words_translated: int = 0
    last_active: Optional[datetime] = None
    recent_activity: List[AdminActivityItem] = []


class AdminUserList(BaseModel):
    items: List[AdminUserItem]
    total: int
    page: int
    per_page: int


class AdminCreateUser(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    is_admin: bool = False


class AdminUpdateUser(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    is_admin: Optional[bool] = None


class AdminStats(BaseModel):
    total_users: int
    total_transcriptions: int
    total_translations: int
    active_users_7d: int
    recent_signups: int
    total_words_transcribed: int = 0
    total_words_translated: int = 0
    daily_activity: List[dict] = []


class AdminActivityList(BaseModel):
    items: List[AdminActivityItem]
    total: int
    page: int
    per_page: int


class AdminSystemHealth(BaseModel):
    status: str
    db_connected: bool
    asr_model_loaded: bool
    translation_engine: str
    total_storage_mb: float
    uptime_seconds: float


class AuditLogItem(BaseModel):
    id: int
    admin_id: int
    admin_username: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    items: List[AuditLogItem]
    total: int
    page: int
    per_page: int
