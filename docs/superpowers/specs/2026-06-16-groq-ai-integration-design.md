# Groq AI Integration Design

**Date:** 2026-06-16  
**Status:** Approved

## Goal

Add Groq as the primary AI provider for contact text parsing and business card OCR, keeping OpenRouter as an automatic fallback.

## Scope

One file changes: `services/ai_agent.py`.  
One config change: `docker-compose.yml` (add `GROQ_API_KEY` env var).  
One new file: `.env` (not committed to git) with the actual key value.

## Architecture

`LightweightContactAgent` gains:

- Two new env vars read in `__init__`:
  - `GROQ_API_KEY` → primary provider key
  - `OPENROUTER_API_KEY` → fallback provider key (already exists, renamed from `api_key`)
- Groq config constants:
  - endpoint: `https://api.groq.com/openai/v1/chat/completions`
  - text model: `llama-3.3-70b-versatile`
  - vision model: `llama-3.2-90b-vision-preview`
- New private method `_call_api(messages, use_vision=False) -> str` that owns all HTTP logic
- Existing `process_contact_data` and `suggest_network_reminders` replace their inlined `urllib_request` blocks with a call to `_call_api`

## `_call_api` Logic

```
if groq_api_key:
    try:
        call Groq with text_model or vision_model based on use_vision
        return response content string
    except any exception as groq_err:
        record groq_err, fall through

if openrouter_api_key:
    try:
        call OpenRouter with existing model (google/gemma-4-31b-it:free)
        return response content string
    except any exception as or_err:
        raise RuntimeError(f"Groq: {groq_err}; OpenRouter: {or_err}")

raise RuntimeError("No AI provider configured: set GROQ_API_KEY or OPENROUTER_API_KEY")
```

## `is_remote_available`

Returns `True` if either `groq_api_key` or `openrouter_api_key` is non-empty. Callers (`suggest_network_reminders`, controllers) already gate on this property — no controller changes needed.

## Error Handling

| Scenario | Behaviour |
|---|---|
| Groq succeeds | Return result, OpenRouter never called |
| Groq fails, OpenRouter succeeds | Return result from OpenRouter |
| Both fail | Raise `RuntimeError` with both error messages |
| No keys set | Raise `RuntimeError("No AI provider configured")` |

## Config

`docker-compose.yml` — add one line under `odoo.environment`:
```yaml
GROQ_API_KEY: "${GROQ_API_KEY}"
```

`.env` file (project root, git-ignored):
```
GROQ_API_KEY=your_actual_key_here
```

`.gitignore` exists but does **not** include `.env` — implementation must add `.env` to `.gitignore` before creating the file.

## What Does NOT Change

- All HTTP controllers in `controllers/api.py` — no changes
- Frontend TypeScript — no changes
- Response format / JSON schema — no changes
- OpenRouter fallback model and system prompts — no changes
