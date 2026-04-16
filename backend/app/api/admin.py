from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.admin_config_service import (
    get_admin_config as get_admin_config_state,
    set_auto_translate_enabled,
)
from app.services.provider_settings_service import (
    get_provider_options,
    get_provider_settings as get_provider_settings_state,
    update_provider_settings as update_provider_settings_state,
)

router = APIRouter(tags=["admin"])


class AdminConfig(BaseModel):
    auto_translate_enabled: bool


class ProviderSetting(BaseModel):
    language_code: str
    language_name: str
    provider: str


class ProviderSettingsPayload(BaseModel):
    settings: list[ProviderSetting]
    provider_options: list[str]


class ProviderSettingsUpdateRequest(BaseModel):
    settings: list[ProviderSetting] = Field(default_factory=list)


@router.get("/admin/config", response_model=AdminConfig)
def get_admin_config() -> AdminConfig:
    return AdminConfig(**get_admin_config_state())


@router.patch("/admin/config/auto-translate", response_model=AdminConfig)
def update_auto_translate_flag(config: AdminConfig) -> AdminConfig:
    updated = set_auto_translate_enabled(config.auto_translate_enabled)
    return AdminConfig(**updated)


@router.get("/admin/provider-settings", response_model=ProviderSettingsPayload)
def get_provider_settings() -> ProviderSettingsPayload:
    settings = get_provider_settings_state()
    return ProviderSettingsPayload(
        settings=[ProviderSetting(**setting) for setting in settings],
        provider_options=get_provider_options(),
    )


@router.put("/admin/provider-settings", response_model=ProviderSettingsPayload)
def update_provider_settings(
    request: ProviderSettingsUpdateRequest,
) -> ProviderSettingsPayload:
    try:
        updated_settings = update_provider_settings_state(
            raw_settings=[setting.model_dump() for setting in request.settings]
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ProviderSettingsPayload(
        settings=[ProviderSetting(**setting) for setting in updated_settings],
        provider_options=get_provider_options(),
    )
