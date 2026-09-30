from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, func, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Transcription(Base):
    __tablename__ = "transcriptions"
    __table_args__ = (
        Index("ix_transcriptions_user_id", "user_id"),
        Index("ix_transcriptions_activity_type", "activity_type"),
        Index("ix_transcriptions_created_at", "created_at"),
        Index("ix_transcriptions_user_activity", "user_id", "activity_type"),
        Index("ix_transcriptions_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(20), nullable=False, default="transcription")
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    final_text: Mapped[str] = mapped_column(Text, nullable=True)
    translation: Mapped[str] = mapped_column(Text, nullable=True)
    source_language: Mapped[str] = mapped_column(String(10), nullable=True)
    target_language: Mapped[str] = mapped_column(String(10), nullable=True)
    engine: Mapped[str] = mapped_column(String(50), nullable=True)
    # Server-side stored filename (persisted audio for replay / re-transcription).
    audio_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    # The original filename the user uploaded (for display only).
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    # User-managed label for a history entry.
    title: Mapped[str] = mapped_column(String(200), nullable=True)
    # Pinned entries float to the top of history.
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="transcriptions")
