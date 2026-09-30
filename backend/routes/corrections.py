from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from models.transcription import Transcription
from models.correction import Correction
from middleware.auth import get_current_user
from schemas.transcription import CorrectionRequest, CorrectionResponse

router = APIRouter(prefix="/api/corrections", tags=["Corrections"])


@router.post("", response_model=CorrectionResponse)
async def save_correction(
    req: CorrectionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify the transcription exists and belongs to the user
    result = await db.execute(
        select(Transcription).where(
            Transcription.id == req.transcription_id,
            Transcription.user_id == user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Transcription not found")

    correction = Correction(
        user_id=user.id,
        transcription_id=req.transcription_id,
        original_text=record.final_text or record.raw_text or "",
        corrected_text=req.corrected_text,
    )
    db.add(correction)
    await db.commit()
    await db.refresh(correction)

    return CorrectionResponse(
        id=correction.id,
        original_text=correction.original_text,
        corrected_text=correction.corrected_text,
        created_at=correction.created_at,
    )


@router.get("/export")
async def export_corrections(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export all corrections as training data for model fine-tuning."""
    result = await db.execute(
        select(Correction).where(Correction.user_id == user.id)
    )
    corrections = result.scalars().all()

    training_data = []
    for c in corrections:
        training_data.append({
            "input": c.original_text,
            "target": c.corrected_text,
            "source": "user_correction",
        })

    return {
        "total": len(training_data),
        "corrections": training_data,
    }
