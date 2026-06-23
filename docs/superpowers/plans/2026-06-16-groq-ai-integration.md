# Groq AI Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Groq as the primary AI provider (text + vision), keeping OpenRouter as automatic fallback.

**Architecture:** Extract a single `_call_api` method in `LightweightContactAgent` that tries Groq first, falls back to OpenRouter on any exception, and raises if both fail. `__init__` reads both keys; `is_remote_available` returns True if either key is set.

**Tech Stack:** Python 3, `urllib.request` (stdlib), Groq REST API, OpenRouter REST API (fallback), Docker Compose for env config.

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Modify | `services/ai_agent.py` | Add Groq config + `_call_api`; refactor two methods |
| Modify | `docker-compose.yml` | Pass `GROQ_API_KEY` into the odoo container |
| Modify | `.gitignore` | Ignore `.env` file |
| Create | `.env` | Store actual `GROQ_API_KEY` value (not committed) |
| Create | `tests/test_ai_agent.py` | Unit tests for `_call_api` and `is_remote_available` |

---

### Task 1: Protect the secret — add `.env` to `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add `.env` to `.gitignore`**

Open `.gitignore` (project root) and append:

```
.env
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore .env file"
```

---

### Task 2: Pass GROQ_API_KEY into the Docker container

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add the env var to the odoo service**

In `docker-compose.yml`, find the `odoo:` service's `environment:` block and add one line:

```yaml
  odoo:
    image: odoo:18
    container_name: team8-odoo
    depends_on:
      - db
    ports:
      - "8076:8069"
    environment:
      HOST: db
      USER: odoo
      PASSWORD: odoo
      GROQ_API_KEY: "${GROQ_API_KEY}"
    volumes:
      - team8_odoo_data:/var/lib/odoo
      - .:/mnt/extra-addons/networkPilotNew
    restart: unless-stopped
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: pass GROQ_API_KEY env var into odoo container"
```

---

### Task 3: Write failing unit tests

**Files:**
- Create: `tests/test_ai_agent.py`

- [ ] **Step 1: Create the test file**

```python
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.ai_agent import LightweightContactAgent


def _mock_response(content_dict):
    body = json.dumps({
        "choices": [{"message": {"content": json.dumps(content_dict)}}]
    }).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestIsRemoteAvailable(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": ""})
    def test_true_when_groq_key_set(self):
        agent = LightweightContactAgent()
        self.assertTrue(agent.is_remote_available)

    @patch.dict(os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": "or_test"})
    def test_true_when_openrouter_key_set(self):
        agent = LightweightContactAgent()
        self.assertTrue(agent.is_remote_available)

    @patch.dict(os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": ""})
    def test_false_when_no_keys(self):
        agent = LightweightContactAgent()
        self.assertFalse(agent.is_remote_available)


class TestCallApi(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": ""})
    def test_uses_groq_when_key_present(self):
        agent = LightweightContactAgent()
        messages = [{"role": "user", "content": "test"}]
        with patch("urllib.request.urlopen", return_value=_mock_response({"ok": True})) as mock_open:
            result = agent._call_api(messages)
        url = mock_open.call_args[0][0].get_full_url()
        self.assertIn("groq.com", url)
        self.assertIn("ok", result)

    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": "or_test"})
    def test_falls_back_to_openrouter_when_groq_fails(self):
        agent = LightweightContactAgent()
        messages = [{"role": "user", "content": "test"}]
        call_count = 0

        def side_effect(req, timeout=30):
            nonlocal call_count
            call_count += 1
            if "groq.com" in req.get_full_url():
                raise Exception("Groq unavailable")
            return _mock_response({"fallback": True})

        with patch("urllib.request.urlopen", side_effect=side_effect):
            result = agent._call_api(messages)

        self.assertEqual(call_count, 2)
        self.assertIn("fallback", result)

    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": "or_test"})
    def test_raises_when_both_fail(self):
        agent = LightweightContactAgent()

        def always_fail(req, timeout=30):
            raise Exception("network error")

        with patch("urllib.request.urlopen", side_effect=always_fail):
            with self.assertRaises(RuntimeError) as ctx:
                agent._call_api([{"role": "user", "content": "test"}])
        self.assertIn("Groq", str(ctx.exception))
        self.assertIn("OpenRouter", str(ctx.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": ""})
    def test_raises_no_provider_configured(self):
        agent = LightweightContactAgent()
        with self.assertRaises(RuntimeError) as ctx:
            agent._call_api([{"role": "user", "content": "test"}])
        self.assertIn("No AI provider configured", str(ctx.exception))

    @patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "OPENROUTER_API_KEY": ""})
    def test_uses_vision_model_when_use_vision_true(self):
        agent = LightweightContactAgent()

        captured = {}

        def capture(req, timeout=30):
            captured["body"] = json.loads(req.data.decode())
            return _mock_response({"vision": True})

        with patch("urllib.request.urlopen", side_effect=capture):
            agent._call_api([{"role": "user", "content": "img"}], use_vision=True)

        self.assertEqual(captured["body"]["model"], agent.groq_vision_model)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests — expect failures (method `_call_api` doesn't exist yet)**

```bash
cd c:\Users\вахта\Desktop\for_university-main
python -m pytest tests/test_ai_agent.py -v
```

Expected: `AttributeError: 'LightweightContactAgent' object has no attribute '_call_api'` on most tests, `is_remote_available` tests may fail too because `api_key` rename hasn't happened yet.

---

### Task 4: Implement `_call_api` and update `__init__` + `is_remote_available`

**Files:**
- Modify: `services/ai_agent.py`

- [ ] **Step 1: Replace `__init__`, `is_remote_available`, and add `_call_api`**

Replace the `LightweightContactAgent` class definition up to (but not including) `process_contact_data`) with:

```python
class LightweightContactAgent:
    def __init__(self):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.groq_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.groq_text_model = "llama-3.3-70b-versatile"
        self.groq_vision_model = "llama-3.2-90b-vision-preview"
        self.openrouter_endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_model = "google/gemma-4-31b-it:free"
        self.system_prompt = """
Вы — умный AI-ассистент для персональной CRM системы "Network Pilot".
Ваша задача — извлекать информацию о контактах из неструктурированного текста или распознанного текста с визитки и возвращать валидный JSON.
ПРАВИЛА ИЗВЛЕЧЕНИЯ И ТЕГИРОВАНИЯ:
1. Выделите Имя (first_name), Фамилию (last_name), Должность (role), Компанию (company), Email (email), Телефон (phone), Индустрию (industry).
2. Назначьте теги на основе должности (обязательно выберите хотя бы один подходящий из списка):
   - "bridge_contact": для топ-менеджмента (CEO, Founder, Director, Product Manager).
   - "mentor": для опытных специалистов (Senior, Lead, Head).
   - "recruiter": для HR и рекрутеров.
   - "peer": для равных (Junior, Студент, Стажер, Specialist).
3. Сгенерируйте напоминание (suggested_reminder) по правилу:
   - Если контакт имеет тег "bridge_contact" или "mentor" (статус Target по умолчанию) -> "priority": "high", "title": "Запланировать встречу/звонок с [Имя]", "due_in_days": 2.
   - Если это "peer" -> "priority": "medium", "title": "Связаться с [Имя]", "due_in_days": 7.
ФОРМАТ ОТВЕТА СТРОГО JSON БЕЗ МАРКДАУН-РАЗМЕТКИ (никаких ```json):
{
  "first_name": "Имя",
  "last_name": "Фамилия",
  "role": "Должность",
  "company": "Компания",
  "industry": "Сфера деятельности",
  "phone": "Телефон",
  "email": "Email",
  "tags": ["тег1", "тег2"],
  "suggested_reminder": {
    "title": "Текст напоминания",
    "due_in_days": 2,
    "priority": "high"
  }
}
Если данных нет, передавайте null.
"""

    @property
    def is_remote_available(self):
        return bool(self.groq_api_key or self.openrouter_api_key)

    def _call_api(self, messages, use_vision=False, temperature=0.1):
        groq_err = None
        if self.groq_api_key:
            model = self.groq_vision_model if use_vision else self.groq_text_model
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib_request.Request(
                self.groq_endpoint,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.groq_api_key}",
                },
                method="POST",
            )
            try:
                with urllib_request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                groq_err = e

        if self.openrouter_api_key:
            payload = {
                "model": self.openrouter_model,
                "messages": messages,
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib_request.Request(
                self.openrouter_endpoint,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "HTTP-Referer": "https://networkpilot.app",
                },
                method="POST",
            )
            try:
                with urllib_request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
            except Exception as or_err:
                if groq_err:
                    raise RuntimeError(f"Groq: {groq_err}; OpenRouter: {or_err}")
                raise RuntimeError(f"OpenRouter: {or_err}")

        if groq_err:
            raise RuntimeError(f"Groq: {groq_err}")
        raise RuntimeError("No AI provider configured: set GROQ_API_KEY or OPENROUTER_API_KEY")
```

- [ ] **Step 2: Run tests — all should pass**

```bash
python -m pytest tests/test_ai_agent.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add services/ai_agent.py tests/test_ai_agent.py
git commit -m "feat: add Groq as primary AI provider with OpenRouter fallback"
```

---

### Task 5: Refactor `process_contact_data` and `suggest_network_reminders`

**Files:**
- Modify: `services/ai_agent.py`

- [ ] **Step 1: Replace `process_contact_data`**

Replace the entire `process_contact_data` method with:

```python
def process_contact_data(self, input_data: str, is_image: bool = False) -> Contact:
    messages = [{"role": "system", "content": self.system_prompt}]
    if is_image:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "Извлеки информацию с этой визитки."},
                {"type": "image_url", "image_url": {"url": input_data}}
            ]
        })
    else:
        messages.append({"role": "user", "content": f"Извлеки данные из текста: {input_data}"})

    content = self._call_api(messages, use_vision=is_image)

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.S)
    if fenced:
        content = fenced.group(1)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise RuntimeError(f"Failed to parse JSON: {content}")

    first_name = parsed.get("first_name") or ""
    last_name = parsed.get("last_name") or ""
    contact_name = " ".join(filter(None, [first_name, last_name]))
    if not contact_name:
        contact_name = "Неизвестный Контакт"
    return Contact(
        name=contact_name,
        first_name=first_name if first_name else None,
        last_name=last_name if last_name else None,
        industry=parsed.get("industry") or "Unknown",
        role=parsed.get("role"),
        company=parsed.get("company"),
        phone=parsed.get("phone"),
        email=parsed.get("email"),
        tags=parsed.get("tags") or [],
        suggested_reminder=parsed.get("suggested_reminder")
    )
```

- [ ] **Step 2: Replace `suggest_network_reminders`**

Replace the entire `suggest_network_reminders` method with:

```python
def suggest_network_reminders(self, contacts_data: List[dict]) -> List[dict]:
    system_prompt = """
Вы — эксперт по нетворкингу. Пользователь передаст вам список своих контактов в формате JSON.
Определите 3-5 самых важных контактов, с которыми пользователю стоит связаться прямо сейчас (например, статус "Dormant" (затухающие) или важные контакты, с которыми давно не было общения).
Для каждого из них предложите конкретное напоминание-действие.

Отвечайте СТРОГО в формате JSON без разметки markdown:
{
  "reminders": [
    {
      "contact_id": 123,
      "title": "Короткое действие, например: Написать в TG, поздравить с новым проектом",
      "due_in_days": 1,
      "priority": "high",
      "reminder_type": "reconnect"
    }
  ]
}
Где "reminder_type" может быть "follow_up", "congratulation", "reconnect" или "custom". "priority" может быть "high", "medium" или "low".
"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Вот список контактов:\n{json.dumps(contacts_data, ensure_ascii=False)}"}
    ]

    content = self._call_api(messages, temperature=0.3)

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.S)
    if fenced:
        content = fenced.group(1)
    try:
        parsed = json.loads(content)
        return parsed.get("reminders", [])
    except json.JSONDecodeError:
        raise RuntimeError(f"Failed to parse JSON: {content}")
```

- [ ] **Step 3: Run tests to confirm nothing is broken**

```bash
python -m pytest tests/test_ai_agent.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add services/ai_agent.py
git commit -m "refactor: replace inlined HTTP blocks with _call_api in process_contact_data and suggest_network_reminders"
```

---

### Task 6: Create `.env` and restart Docker

**Files:**
- Create: `.env` (project root)

- [ ] **Step 1: Create `.env` with your Groq key**

Create file `.env` in `c:\Users\вахта\Desktop\for_university-main\`:

```
GROQ_API_KEY=your_actual_groq_key_here
```

Replace `your_actual_groq_key_here` with the real key from console.groq.com.

- [ ] **Step 2: Restart the Docker stack to pick up the new env var**

```powershell
docker compose down
docker compose up -d
```

- [ ] **Step 3: Verify the key is visible inside the container**

```powershell
docker exec team8-odoo printenv GROQ_API_KEY
```

Expected: your Groq key printed to stdout.

---

### Task 7: Smoke test in the UI

- [ ] **Step 1: Test text parsing**

Open [http://localhost:8076/app/](http://localhost:8076/app/), go to **Новый контакт**, paste text in the "Создать с помощью ИИ" field:

```
Иван Петров, Senior Engineer в Yandex, telegram @ivanp, ivan@yandex.ru
```

Click **Разобрать текст**. Fields should populate: Имя=Иван, Фамилия=Петров, Компания=Yandex, роль=Senior Engineer.

- [ ] **Step 2: Test business card scanning**

In the same form, click **Выбрать изображение** and upload a photo of any business card (real or test image). The fields should populate from the card contents.

- [ ] **Step 3: Confirm in Docker logs which provider responded**

```powershell
docker logs team8-odoo --tail 50
```

If Groq worked, there will be no fallback errors. If you see OpenRouter errors, Groq failed and the fallback was used — check the key in `.env`.
