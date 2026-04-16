import os
import uuid

import httpx

DEFAULT_AZURE_TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com"
AZURE_TRANSLATOR_API_VERSION = "3.0"
AZURE_TRANSLATOR_TIMEOUT_SECONDS = 20.0


class AzureTranslationConfigError(RuntimeError):
    pass


class AzureTranslationProviderError(RuntimeError):
    pass


def _get_azure_translator_settings() -> tuple[str, str, str]:
    endpoint = os.getenv(
        "AZURE_TRANSLATOR_ENDPOINT", DEFAULT_AZURE_TRANSLATOR_ENDPOINT
    ).strip()
    endpoint = endpoint.rstrip("/")

    key = os.getenv("AZURE_TRANSLATOR_KEY", "").strip()
    region = os.getenv("AZURE_TRANSLATOR_REGION", "").strip()

    missing_variables = []
    if not key:
        missing_variables.append("AZURE_TRANSLATOR_KEY")
    if not region:
        missing_variables.append("AZURE_TRANSLATOR_REGION")

    if missing_variables:
        joined = ", ".join(missing_variables)
        raise AzureTranslationConfigError(
            "Azure Translator is not configured. "
            f"Set the following environment variables: {joined}."
        )

    return endpoint, key, region


def translate_text_batch(texts: list[str], target_language: str) -> list[str]:
    if not texts:
        return []

    endpoint, key, region = _get_azure_translator_settings()

    request_url = f"{endpoint}/translate"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Ocp-Apim-Subscription-Region": region,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }
    params = {
        "api-version": AZURE_TRANSLATOR_API_VERSION,
        "to": target_language,
    }
    payload = [{"text": text} for text in texts]

    try:
        with httpx.Client(timeout=AZURE_TRANSLATOR_TIMEOUT_SECONDS) as client:
            response = client.post(
                request_url,
                headers=headers,
                params=params,
                json=payload,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error_body = exc.response.text
        raise AzureTranslationProviderError(
            "Azure Translator request failed with "
            f"status {exc.response.status_code}: {error_body}"
        ) from exc
    except httpx.HTTPError as exc:
        raise AzureTranslationProviderError(
            "Azure Translator request failed due to a network or transport error."
        ) from exc

    try:
        response_data = response.json()
    except ValueError as exc:
        raise AzureTranslationProviderError(
            "Azure Translator returned a non-JSON response."
        ) from exc

    if not isinstance(response_data, list) or len(response_data) != len(texts):
        raise AzureTranslationProviderError(
            "Azure Translator returned an unexpected response length."
        )

    translated_texts: list[str] = []
    for item in response_data:
        if not isinstance(item, dict):
            raise AzureTranslationProviderError(
                "Azure Translator returned an invalid response item."
            )

        translations = item.get("translations")
        if not isinstance(translations, list) or not translations:
            raise AzureTranslationProviderError(
                "Azure Translator response did not include translations."
            )

        first_translation = translations[0]
        if not isinstance(first_translation, dict):
            raise AzureTranslationProviderError(
                "Azure Translator returned an invalid translation entry."
            )

        translated_text = first_translation.get("text")
        if not isinstance(translated_text, str):
            raise AzureTranslationProviderError(
                "Azure Translator returned a non-text translation value."
            )

        translated_texts.append(translated_text)

    return translated_texts