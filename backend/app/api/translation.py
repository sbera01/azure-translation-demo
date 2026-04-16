from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.admin_config_service import get_auto_translate_enabled
from app.services.azure_translation_service import (
    AzureTranslationConfigError,
    AzureTranslationProviderError,
)
from app.services.provider_settings_service import get_provider_for_language
from app.services.translation_service import translate_with_cache

router = APIRouter(tags=["translation"])


class TranslationRequest(BaseModel):
    source_text: str
    target_language: str


class TranslationResponse(BaseModel):
    translated_text: str
    cached: bool


@router.post("/translate", response_model=TranslationResponse)
def auto_translate(request: TranslationRequest) -> TranslationResponse:
    if not get_auto_translate_enabled():
        raise HTTPException(
            status_code=403,
            detail="Auto-translate is disabled by admin configuration.",
        )

    configured_provider = get_provider_for_language(request.target_language)
    if configured_provider is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No translation provider is configured for the selected language. "
                "Update language providers in Admin Panel."
            ),
        )

    if configured_provider == "off":
        raise HTTPException(
            status_code=403,
            detail=(
                "Auto-Translate is turned off for the selected language in Admin Panel."
            ),
        )

    if configured_provider != "azure":
        raise HTTPException(
            status_code=400,
            detail="Configured translation provider is not supported in this prototype.",
        )

    try:
        translated_text, cached = translate_with_cache(
            source_text=request.source_text,
            target_language=request.target_language,
            provider=configured_provider,
        )
    except AzureTranslationConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except AzureTranslationProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return TranslationResponse(
        translated_text=translated_text,
        cached=cached,
    )
