from datetime import datetime, timezone
from typing import TypedDict

from app.services.sqlite_service import get_sqlite_connection


class SubmissionRecord(TypedDict):
    submission_id: int
    source_text: str
    target_language: str
    translated_text: str
    alt_text_reviewed: bool
    saved_at: str


def save_submission(
    source_text: str,
    target_language: str,
    translated_text: str,
    alt_text_reviewed: bool,
) -> SubmissionRecord:
    saved_at = datetime.now(timezone.utc).isoformat()

    with get_sqlite_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO submissions (
                source_text,
                target_language,
                translated_text,
                alt_text_reviewed,
                saved_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                source_text,
                target_language,
                translated_text,
                int(alt_text_reviewed),
                saved_at,
            ),
        )
        submission_id = int(cursor.lastrowid)

    saved_record: SubmissionRecord = {
        "submission_id": submission_id,
        "source_text": source_text,
        "target_language": target_language,
        "translated_text": translated_text,
        "alt_text_reviewed": alt_text_reviewed,
        "saved_at": saved_at,
    }

    return saved_record