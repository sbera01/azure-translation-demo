# Azure AI-Assisted Translation App

Small FastAPI + vanilla JS app for Azure Translator based content translation with cache, admin controls, and submission validation.

## Tech Stack

- Backend: FastAPI, Uvicorn, Pydantic
- HTTP client: httpx
- Config loading: python-dotenv
- Frontend: HTML, CSS, vanilla JavaScript
- Translation provider: Azure AI Translator Text Translation API
- Data storage:
  - SQLite at backend/app/data/app_state.db for app config, translation cache, and submissions
  - JSON at backend/app/data/language_provider_settings.json for per-language provider settings

## End-to-End Flow

1. User enters source content in input field and can load rotating sample inputs.
2. Auto-Translate in frontend/app.js calls POST /translate.
3. Backend validates admin toggle and selected language provider.
4. Translation service preserves placeholders for math/link/image tags, translates only text segments via Azure, then restores placeholders.
5. Result is cached using SHA-256 of provider + target language + source text in translation_cache.
6. User can edit translated output before submit.
7. Submit calls POST /api/submissions.
8. Backend enforces rules:
  - auto-translate must be enabled by admin
  - if source contains an img tag, alt-text review must be checked
9. Submission is saved in SQLite and success is returned with submission_id.

## Folder Structure

```text
Azure_Translation/
  backend/
    .env
    .env.example
    requirements.txt
    app/
      main.py
      api/
        admin.py
        submission.py
        translation.py
      services/
        admin_config_service.py
        azure_translation_service.py
        content_rules_service.py
        provider_settings_service.py
        sqlite_service.py
        submission_service.py
        translation_service.py
      data/
        app_state.db
        app_state.corrupt-<timestamp>.db
        language_provider_settings.json
  frontend/
    index.html
    app.js
    styles.css
  README.md
  AZURE_TRANSLATOR_FREE_TIER_GUIDE.md
```

## API Endpoints

- GET /health
- POST /translate
- GET /api/admin/config
- PATCH /api/admin/config/auto-translate
- GET /api/admin/provider-settings
- PUT /api/admin/provider-settings
- POST /api/submissions


## Notes

- Supported target languages in current code: ar, bn, de, es, fr, hi.
- Provider options in current code: off, azure.
- SQLite layer includes malformed database recovery by backing up the corrupted DB and recreating schema.
