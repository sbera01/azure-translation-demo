import json
from pathlib import Path
from threading import Lock
from typing import TypedDict

_PROVIDER_OPTIONS = ["off", "azure"]
_SUPPORTED_LANGUAGES = [
    {"code": "ar", "name": "Arabic"},
    {"code": "bn", "name": "Bengali"},
    {"code": "de", "name": "German"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "hi", "name": "Hindi"},
]
_CONFIG_FILE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "language_provider_settings.json"
)
_PROVIDER_SETTINGS_LOCK = Lock()


class ProviderSetting(TypedDict):
    language_code: str
    language_name: str
    provider: str


def _default_settings() -> list[ProviderSetting]:
    return [
        {
            "language_code": language["code"],
            "language_name": language["name"],
            "provider": "azure",
        }
        for language in _SUPPORTED_LANGUAGES
    ]


def _normalize_provider_setting(raw_setting: dict[str, str]) -> ProviderSetting:
    language_code = str(raw_setting.get("language_code", "")).strip().lower()
    provider = str(raw_setting.get("provider", "")).strip().lower()

    language_name_by_code = {
        language["code"]: language["name"] for language in _SUPPORTED_LANGUAGES
    }

    if language_code not in language_name_by_code:
        raise ValueError(
            "Unsupported language code. Allowed codes: "
            f"{', '.join(language_name_by_code.keys())}."
        )

    if provider not in _PROVIDER_OPTIONS:
        raise ValueError(
            "Unsupported provider. Allowed providers: "
            f"{', '.join(_PROVIDER_OPTIONS)}."
        )

    return {
        "language_code": language_code,
        "language_name": language_name_by_code[language_code],
        "provider": provider,
    }


def _normalize_settings(raw_settings: list[dict[str, str]]) -> list[ProviderSetting]:
    normalized_by_code: dict[str, ProviderSetting] = {}

    for raw_setting in raw_settings:
        normalized_setting = _normalize_provider_setting(raw_setting)
        normalized_by_code[normalized_setting["language_code"]] = normalized_setting

    merged_settings: list[ProviderSetting] = []
    for language in _SUPPORTED_LANGUAGES:
        existing_setting = normalized_by_code.get(language["code"])
        if existing_setting:
            merged_settings.append(existing_setting)
            continue

        merged_settings.append(
            {
                "language_code": language["code"],
                "language_name": language["name"],
                "provider": "azure",
            }
        )

    return merged_settings


def _read_provider_settings_from_file() -> list[ProviderSetting]:
    if not _CONFIG_FILE_PATH.exists():
        default_settings = _default_settings()
        _write_provider_settings_to_file(default_settings)
        return default_settings

    with _CONFIG_FILE_PATH.open("r", encoding="utf-8") as config_file:
        raw_data = json.load(config_file)

    if not isinstance(raw_data, dict) or not isinstance(raw_data.get("settings"), list):
        default_settings = _default_settings()
        _write_provider_settings_to_file(default_settings)
        return default_settings

    raw_settings = raw_data["settings"]
    parsed_settings: list[dict[str, str]] = []
    for raw_setting in raw_settings:
        if not isinstance(raw_setting, dict):
            continue
        parsed_settings.append(raw_setting)

    try:
        return _normalize_settings(parsed_settings)
    except ValueError:
        default_settings = _default_settings()
        _write_provider_settings_to_file(default_settings)
        return default_settings


def _write_provider_settings_to_file(settings: list[ProviderSetting]) -> None:
    _CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"settings": settings}
    with _CONFIG_FILE_PATH.open("w", encoding="utf-8") as config_file:
        json.dump(payload, config_file, indent=2)


def get_provider_options() -> list[str]:
    return list(_PROVIDER_OPTIONS)


def get_provider_settings() -> list[ProviderSetting]:
    with _PROVIDER_SETTINGS_LOCK:
        settings = _read_provider_settings_from_file()
        _write_provider_settings_to_file(settings)
        return settings


def update_provider_settings(
    raw_settings: list[dict[str, str]],
) -> list[ProviderSetting]:
    with _PROVIDER_SETTINGS_LOCK:
        normalized_settings = _normalize_settings(raw_settings)
        _write_provider_settings_to_file(normalized_settings)
        return normalized_settings


def get_provider_for_language(language_code: str) -> str | None:
    normalized_code = language_code.strip().lower()
    settings = get_provider_settings()
    for setting in settings:
        if setting["language_code"] == normalized_code:
            return setting["provider"]
    return None
