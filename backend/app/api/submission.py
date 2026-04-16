from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.content_rules_service import source_contains_image_tag
from app.services.submission_service import save_submission

router = APIRouter(tags=["submission"])


class SubmissionRequest(BaseModel):
    source_text: str
    target_language: str
    translated_text: str
    alt_text_reviewed: bool


class SubmissionResponse(BaseModel):
    submission_id: int
    saved_at: str
    message: str


@router.post("/submissions", response_model=SubmissionResponse)
def submit_translation(request: SubmissionRequest) -> SubmissionResponse:
    if source_contains_image_tag(request.source_text) and not request.alt_text_reviewed:
        raise HTTPException(
            status_code=400,
            detail="Submission blocked: confirm image alt-text review first.",
        )

    saved = save_submission(
        source_text=request.source_text,
        target_language=request.target_language,
        translated_text=request.translated_text,
        alt_text_reviewed=request.alt_text_reviewed,
    )

    return SubmissionResponse(
        submission_id=int(saved["submission_id"]),
        saved_at=str(saved["saved_at"]),
        message="Final translation saved successfully.",
    )