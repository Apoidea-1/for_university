import base64
import json
import os
import re
import math
from datetime import datetime, timedelta
from typing import List, Optional
from urllib import request as urllib_request

from pydantic import BaseModel, Field


class Interaction(BaseModel):
    type: str
    date: datetime
    notes: Optional[str] = None


class Contact(BaseModel):
    id: str = "new"
    name: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    industry: str = "Unknown"
    role: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    interactions: List[Interaction] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
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


class LightweightContactAgent:
    def __init__(self):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemma-4-31b-it:free"

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
   - (Для статуса Dormant в этой логике считаем, что мы заносим новый контакт, поэтому по умолчанию берем правило для Target).

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
        return bool(self.api_key)

    def process_contact_data(self, input_data: str, is_image: bool = False) -> Contact:
        if not self.is_remote_available:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")

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

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            self.endpoint,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://networkpilot.app",
            },
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"API request failed: {e}")

        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

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

    def plan_contact_strategy(self, snapshot):
        return {"next_action": "Запланировать follow-up", "summary": "Контакт обновлен."}

    def extract_business_card(self, image_base64):
        raw = image_base64.strip()
        if not raw.startswith("data:"):
            import base64
            base64.b64decode(raw)
            raw = f"data:image/jpeg;base64,{raw}"
        
        contact = self.process_contact_data(raw, is_image=True)
        return json.loads(contact.model_dump_json())

if __name__ == "__main__":
    print("Testing AI Agent...")
    agent = LightweightContactAgent()
    if not agent.api_key:
        print("No API key, running mock test...")
        mock_json = '''
        {
          "first_name": "Павел",
          "last_name": "Алексеев",
          "role": "Продукт менеджер",
          "company": null,
          "industry": "IT",
          "phone": null,
          "email": null,
          "tags": ["bridge_contact"],
          "suggested_reminder": {
            "title": "Запланировать встречу/звонок с Павел",
            "due_in_days": 2,
            "priority": "high"
          }
        }
        '''
        parsed = json.loads(mock_json)
        contact = Contact(
            name=f"{parsed['first_name']} {parsed['last_name']}",
            first_name=parsed['first_name'],
            last_name=parsed['last_name'],
            role=parsed['role'],
            industry=parsed['industry'],
            tags=parsed['tags'],
            suggested_reminder=parsed['suggested_reminder']
        )
        print(f"Mock Parsed Contact:\n{contact.model_dump_json(indent=2)}")
        print(f"Status: {contact.get_status()}")
    else:
        test_str = "Павел Алексеев Продукт менеджер"
        try:
            contact = agent.process_contact_data(test_str)
            print(f"Parsed Contact:\n{contact.model_dump_json(indent=2)}")
            print(f"Status: {contact.get_status()}")
        except Exception as e:
            print(f"Test failed: {e}")
