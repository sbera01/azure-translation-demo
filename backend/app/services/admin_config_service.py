from app.services.sqlite_service import get_sqlite_connection

_AUTO_TRANSLATE_ENABLED_KEY = "auto_translate_enabled"


def _ensure_default_auto_translate_flag() -> None:
    with get_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO app_config (config_key, config_value)
            VALUES (?, ?)
            """,
            (_AUTO_TRANSLATE_ENABLED_KEY, "1"),
        )


def get_auto_translate_enabled() -> bool:
    _ensure_default_auto_translate_flag()
    with get_sqlite_connection() as connection:
        row = connection.execute(
            "SELECT config_value FROM app_config WHERE config_key = ?",
            (_AUTO_TRANSLATE_ENABLED_KEY,),
        ).fetchone()

    if row is None:
        return True

    return str(row["config_value"]).strip() == "1"


def get_admin_config() -> dict[str, bool]:
    return {"auto_translate_enabled": get_auto_translate_enabled()}


def set_auto_translate_enabled(enabled: bool) -> dict[str, bool]:
    _ensure_default_auto_translate_flag()
    value = "1" if enabled else "0"

    with get_sqlite_connection() as connection:
        connection.execute(
            """
            UPDATE app_config
            SET config_value = ?
            WHERE config_key = ?
            """,
            (value, _AUTO_TRANSLATE_ENABLED_KEY),
        )

    return {"auto_translate_enabled": enabled}