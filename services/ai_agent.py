import base64
import json
import os
import re
import math
from datetime import datetime
from typing import List, Optional
import ssl
import requests as _requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from urllib import request as urllib_request
from dataclasses import dataclass, field, asdict
@dataclass
class Interaction:
    type: str
    date: datetime
    notes: Optional[str] = None
@dataclass
class Contact:
    id: str = "new"
    name: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    industry: str = "Unknown"
    role: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    interactions: List[Interaction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    suggested_reminder: Optional[dict] = None
    decay_lambda: float = 0.05
    dormant_threshold: float = 10.0
    @property
    def base_weight(self) -> float:
        TAG_WEIGHTS = {
            "mentor": 20.0,
            "recruiter": 15.0,
            "peer": 5.0,
            "bridge_contact": 25.0
        }
        return sum(TAG_WEIGHTS.get(tag, 1.0) for tag in self.tags)
    def calculate_current_value(self) -> float:
        INTERACTION_WEIGHTS = {
            "coffee_meeting": 5.0,
            "email_thread": 3.0,
            "social_like": 1.0
        }
        total_value = self.base_weight
        now = datetime.now()
        for interaction in self.interactions:
            days_passed = max(0, (now - interaction.date).days)
            weight = INTERACTION_WEIGHTS.get(interaction.type, 1.0)
            decayed_weight = weight * math.exp(-self.decay_lambda * days_passed)
            total_value += decayed_weight
        return round(total_value, 2)
    def get_status(self) -> str:
        if not self.interactions:
            return "Target"
        if self.calculate_current_value() < self.dormant_threshold:
            return "Dormant"
        return "Active"
    def model_dump_json(self, indent=None):
        data = asdict(self)
        data["created_at"] = data["created_at"].isoformat()
        for inter in data["interactions"]:
            inter["date"] = inter["date"].isoformat()
        return json.dumps(data, indent=indent)
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
        self.groq_vision_model = "meta-llama/llama-4-scout-17b-16e-instruct"
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
            try:
                resp = _requests.post(
                    self.groq_endpoint,
                    headers={"Authorization": f"Bearer {self.groq_api_key}"},
                    json={"model": model, "messages": messages, "temperature": temperature},
                    verify=False,
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                groq_err = e

        if self.openrouter_api_key:
            try:
                resp = _requests.post(
                    self.openrouter_endpoint,
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "HTTP-Referer": "https://networkpilot.app",
                    },
                    json={
                        "model": self.openrouter_model,
                        "messages": messages,
                        "temperature": temperature,
                        "response_format": {"type": "json_object"},
                    },
                    verify=False,
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as or_err:
                if groq_err:
                    raise RuntimeError(f"Groq: {groq_err}; OpenRouter: {or_err}")
                raise RuntimeError(f"OpenRouter: {or_err}")

        if groq_err:
            raise RuntimeError(f"Groq: {groq_err}")
        raise RuntimeError("No AI provider configured: set GROQ_API_KEY or OPENROUTER_API_KEY")
    def process_contact_data(self, input_data: str, is_image: bool = False) -> Contact:
        messages = [{"role": "system", "content": self.system_prompt}]
        if is_image:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": (
                        "Прочитай ВСЕ слова на этой визитке. "
                        "Найди имя и фамилию владельца визитки: это обычно самый крупный текст, "
                        "может быть написан на русском языке заглавными буквами (например ИВАН ИВАНОВ — "
                        "это first_name=Иван, last_name=Иванов). "
                        "Не путай имя человека с названием компании. "
                        "Верни строго JSON без markdown-разметки."
                    )},
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
    def extract_business_card(self, image_base64):
        raw = image_base64.strip()
        if not raw.startswith("data:"):
            raw = f"data:image/jpeg;base64,{raw}"

        # Step 1: vision model reads all text from the image
        ocr_messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "Прочитай весь текст на этой визитке и перечисли его построчно. "
                    "Просто текст, никакой интерпретации."
                )},
                {"type": "image_url", "image_url": {"url": raw}},
            ],
        }]
        extracted_text = self._call_api(ocr_messages, use_vision=True)

        # Step 2: text model parses extracted text into structured contact
        contact = self.process_contact_data(extracted_text, is_image=False)
        return json.loads(contact.model_dump_json())
    def plan_contact_strategy(self, snapshot):
        return {"next_action": "Запланировать follow-up", "summary": "Контакт обновлен."}
        
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
