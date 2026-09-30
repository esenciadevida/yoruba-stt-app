from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Correction(Base):
    __tablename__ = "corrections"
    __table_args__ = (
        Index("ix_corrections_user_id", "user_id"),
        Index("ix_corrections_transcription_id", "transcription_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    transcription_id: Mapped[int] = mapped_column(ForeignKey("transcriptions.id", ondelete="CASCADE"), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="corrections")
    transcription = relationship("Transcription")
