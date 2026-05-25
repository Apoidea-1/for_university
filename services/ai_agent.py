import base64
import json
import os
import re
from urllib import request as urllib_request


class LightweightContactAgent:
    def __init__(self):
        self.endpoint = os.getenv("NETWORKPILOT_AI_ENDPOINT", "").strip()
        self.api_key = os.getenv("NETWORKPILOT_AI_API_KEY", "").strip()
        self.model = os.getenv("NETWORKPILOT_AI_MODEL", "").strip()

    @property
    def is_remote_available(self):
        return bool(self.endpoint and self.api_key and self.model)

    def plan_contact_strategy(self, snapshot):
        if self.is_remote_available:
            try:
                return self._remote_plan(snapshot)
            except Exception:
                pass
        return self._fallback_plan(snapshot)

    def extract_business_card(self, image_base64):
        payload = self._clean_image_payload(image_base64)
        if not self.is_remote_available:
            raise RuntimeError(
                "OCR provider is not configured. Set NETWORKPILOT_AI_ENDPOINT, NETWORKPILOT_AI_API_KEY and NETWORKPILOT_AI_MODEL."
            )

        prompt = (
            "You extract data from business cards. Return strict JSON with keys: "
            "full_name, first_name, last_name, company, role, email, phone, website, telegram, linkedin, notes, confidence. "
            "Use null for missing values. notes should be a short Russian sentence."
        )
        data = self._call_openai_compatible(
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": payload},
                        },
                    ],
                },
            ],
            temperature=0.1,
            max_tokens=500,
        )
        data["source"] = "remote"
        return data

    def _remote_plan(self, snapshot):
        data = self._call_openai_compatible(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a lightweight relationship strategist for a personal CRM. "
                        "Return strict JSON with keys: summary, recommended_channel, next_action, "
                        "meeting_goal, meeting_window, agenda, message_draft, risk_flags."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(snapshot, ensure_ascii=False),
                },
            ],
            temperature=0.2,
            max_tokens=600,
        )
        data["source"] = "remote"
        return data

    def _fallback_plan(self, snapshot):
        contact = snapshot.get("contact", {})
        interactions = snapshot.get("recent_interactions", [])
        days_since = snapshot.get("days_since_last_interaction")
        importance = contact.get("importance_level") or "medium"
        name = contact.get("full_name") or contact.get("first_name") or "контакт"
        available_channels = [
            ("telegram", contact.get("telegram")),
            ("email", contact.get("email")),
            ("linkedin", contact.get("linkedin")),
            ("phone", contact.get("phone")),
        ]
        recommended_channel = next((label for label, value in available_channels if value), "email")

        if days_since is None:
            urgency = "high" if importance in {"high", "strategic"} else "medium"
        elif days_since <= 14:
            urgency = "low"
        elif days_since <= 35:
            urgency = "medium"
        else:
            urgency = "high"

        if urgency == "high":
            meeting_window = "На этой неделе, 20-30 минут"
            next_action = f"Свяжитесь с {name} в ближайшие 24 часа и предложите короткий созвон."
        elif urgency == "medium":
            meeting_window = "В течение ближайших 7 дней, 20 минут"
            next_action = f"Отправьте {name} аккуратный follow-up и предложите слот на следующей неделе."
        else:
            meeting_window = "Через 1-2 недели, 15-20 минут"
            next_action = f"Поддержите связь с {name} коротким сообщением без жёсткого давления."

        latest_topic = interactions[0]["title"] if interactions else "последний контекст общения"
        agenda = [
            "Коротко напомнить контекст знакомства.",
            f"Обсудить {latest_topic}.",
            "Закрепить следующий конкретный шаг и срок.",
        ]

        risk_flags = []
        if not interactions:
            risk_flags.append("Нет истории взаимодействий, тон лучше держать мягким.")
        if importance == "strategic":
            risk_flags.append("Контакт стратегический, сообщение должно быть конкретным и коротким.")
        if not contact.get("notes"):
            risk_flags.append("Мало контекста по заметкам, перед встречей стоит обновить карточку.")

        return {
            "source": "heuristic",
            "summary": f"{name}: приоритет {importance}, канал {recommended_channel}, уровень срочности {urgency}.",
            "recommended_channel": recommended_channel,
            "next_action": next_action,
            "meeting_goal": "Освежить контакт, обновить контекст и договориться о следующем шаге.",
            "meeting_window": meeting_window,
            "agenda": agenda,
            "message_draft": (
                f"Привет! Хочу коротко вернуться к нашему разговору про {latest_topic}. "
                "Будет удобно созвониться на 20-30 минут в ближайшие дни?"
            ),
            "risk_flags": risk_flags,
        }

    def _call_openai_compatible(self, messages, temperature, max_tokens):
        response = self._post_json(
            self.endpoint,
            {
                "model": self.model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": messages,
            },
        )
        content = response["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
        return self._extract_json(content)

    def _post_json(self, url, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _extract_json(self, raw_text):
        if not raw_text:
            raise RuntimeError("AI provider returned empty content.")
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.S)
        if fenced:
            raw_text = fenced.group(1)
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError("AI provider did not return JSON.")
        return json.loads(raw_text[start : end + 1])

    def _clean_image_payload(self, image_base64):
        raw = image_base64.strip()
        if raw.startswith("data:"):
            return raw
        base64.b64decode(raw)
        return f"data:image/jpeg;base64,{raw}"
