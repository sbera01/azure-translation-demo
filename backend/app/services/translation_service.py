from datetime import datetime, timezone
import hashlib
import re

from app.services.azure_translation_service import translate_text_batch
from app.services.sqlite_service import get_sqlite_connection

_PLACEHOLDER_PATTERN = re.compile(
    r"(<math\b[^>]*>.*?</math>|<a\b[^>]*href\s*=\s*['\"][^'\"]*['\"][^>]*>.*?</a>|<img\b[^>]*alt\s*=\s*['\"][^'\"]*['\"][^>]*?/?>)",
    re.IGNORECASE | re.DOTALL,
)
_TOKEN_PATTERN = re.compile(r"(__PH_\d+__)")


def extract_placeholders(text: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}

    def _replace_match(match: re.Match[str]) -> str:
        token = f"__PH_{len(placeholders)}__"
        placeholders[token] = match.group(0)
        return token

    text_with_tokens = _PLACEHOLDER_PATTERN.sub(_replace_match, text)
    return text_with_tokens, placeholders


def restore_placeholders(text: str, placeholders: dict[str, str]) -> str:
    restored_text = text
    for token, original in placeholders.items():
        restored_text = restored_text.replace(token, original)
    return restored_text


def translate_preserving_placeholders(source_text: str, target_language: str) -> str:
    text_with_tokens, placeholders = extract_placeholders(source_text)
    parts = _TOKEN_PATTERN.split(text_with_tokens)

    translatable_indexes: list[int] = []
    translatable_segments: list[str] = []
    for index, part in enumerate(parts):
        if part in placeholders:
            continue

        if not part.strip():
            continue

        translatable_indexes.append(index)
        translatable_segments.append(part)

    translated_segments = translate_text_batch(
        texts=translatable_segments,
        target_language=target_language,
    )
    for index, translated_segment in zip(translatable_indexes, translated_segments):
        parts[index] = translated_segment

    translated_with_tokens = "".join(parts)
    restored_translation = restore_placeholders(translated_with_tokens, placeholders)
    return restored_translation


def build_cache_key(source_text: str, target_language: str, provider: str) -> str:
    payload = f"{provider}\n{target_language}\n{source_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_cached_translation(cache_key: str) -> str | None:
    with get_sqlite_connection() as connection:
        row = connection.execute(
            """
            SELECT translated_text
            FROM translation_cache
            WHERE cache_key = ?
            """,
            (cache_key,),
        ).fetchone()

    if row is None:
        return None

    return str(row["translated_text"])


def _write_cached_translation(
    *,
    cache_key: str,
    provider: str,
    target_language: str,
    source_text: str,
    translated_text: str,
) -> bool:
    created_at = datetime.now(timezone.utc).isoformat()

    with get_sqlite_connection() as connection:
        changes_before_insert = connection.total_changes
        connection.execute(
            """
            INSERT OR IGNORE INTO translation_cache (
                cache_key,
                provider,
                target_language,
                source_text,
                translated_text,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                cache_key,
                provider,
                target_language,
                source_text,
                translated_text,
                created_at,
            ),
        )
        return connection.total_changes > changes_before_insert


def translate_with_cache(
    source_text: str,
    target_language: str,
    provider: str,
) -> tuple[str, bool]:
    cache_key = build_cache_key(
        source_text=source_text,
        target_language=target_language,
        provider=provider,
    )

    cached_translation = _read_cached_translation(cache_key)
    if cached_translation is not None:
        return cached_translation, True

    translated_text = translate_preserving_placeholders(
        source_text=source_text,
        target_language=target_language,
    )

    inserted = _write_cached_translation(
        cache_key=cache_key,
        provider=provider,
        target_language=target_language,
        source_text=source_text,
        translated_text=translated_text,
    )

    if inserted:
        return translated_text, False

    existing_value = _read_cached_translation(cache_key)
    if existing_value is not None:
        return existing_value, True

    return translated_text, False