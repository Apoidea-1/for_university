from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.ai_suggestion import AISuggestion
from app.models.enums import SuggestionType


@dataclass
class ContactMetadataSuggestion:
    category: str
    tags: list[str]
    note_summary: str
    next_action: str


class AIRecommendationService:
    CATEGORY_RULES = {
        "Recruiters": ["hr", "recruit", "talent", "internship", "vacancy"],
        "Mentors": ["mentor", "speaker", "coach", "advice"],
        "Founders": ["startup", "founder", "cofounder", "accelerator"],
        "Peers": ["student", "peer", "teammate", "hackathon", "club"],
        "Alumni": ["alumni", "university", "graduate", "faculty"],
        "Investors": ["investor", "vc", "fund", "angel"],
    }

    TAG_KEYWORDS = {
        "internship": ["internship", "стаж", "intern"],
        "career": ["career", "hr", "recruit", "job"],
        "startup": ["startup", "founder", "accelerator"],
        "product": ["product", "pm", "roadmap"],
        "design": ["design", "ux", "ui"],
        "university": ["university", "campus", "student", "alumni"],
        "follow-up": ["follow-up", "followup", "connect", "message"],
        "hackathon": ["hackathon", "case", "competition"],
    }

    STOP_WORDS = {
        "and",
        "with",
        "from",
        "that",
        "this",
        "they",
        "them",
        "about",
        "career",
        "forum",
        "met",
        "talked",
        "обсуждали",
        "познакомились",
        "работает",
        "карьерном",
        "форуме",
    }

    @classmethod
    def suggest_contact_metadata(
        cls,
        *,
        notes: str,
        first_name: str | None = None,
        company: str | None = None,
        role: str | None = None,
    ) -> ContactMetadataSuggestion:
        context = " ".join(filter(None, [notes, first_name, company, role])).lower()
        category = cls._suggest_category(context)
        tags = cls._suggest_tags(context)
        note_summary = cls._build_summary(context, category, company)
        next_action = cls._suggest_next_action(context)
        return ContactMetadataSuggestion(
            category=category,
            tags=tags,
            note_summary=note_summary,
            next_action=next_action,
        )

    @classmethod
    def suggest_next_action(cls, *, notes: str, last_interaction_summary: str | None = None) -> tuple[str, str]:
        context = " ".join(filter(None, [notes, last_interaction_summary])).lower()
        next_action = cls._suggest_next_action(context)
        rationale = (
            "Контакт выглядит тёплым и контекст взаимодействия уже задан, поэтому стоит продолжить диалог конкретным follow-up."
        )
        return next_action, rationale

    @classmethod
    def persist_suggestion(cls, db: Session, *, contact_id: int, suggestion_type: SuggestionType, content: str) -> None:
        db.add(AISuggestion(contact_id=contact_id, suggestion_type=suggestion_type, content=content))

    @classmethod
    def _suggest_category(cls, context: str) -> str:
        best_category = "Peers"
        best_score = 0
        for category, keywords in cls.CATEGORY_RULES.items():
            score = sum(keyword in context for keyword in keywords)
            if score > best_score:
                best_category = category
                best_score = score
        return best_category

    @classmethod
    def _suggest_tags(cls, context: str) -> list[str]:
        matched_tags = [
            tag_name
            for tag_name, keywords in cls.TAG_KEYWORDS.items()
            if any(keyword in context for keyword in keywords)
        ]
        if len(matched_tags) >= 2:
            return matched_tags[:4]

        words = [word.strip(".,!?:;()[]{}") for word in context.split()]
        candidates = [
            word
            for word in words
            if len(word) > 3 and word.isalpha() and word not in cls.STOP_WORDS
        ]
        ranked = [word for word, _count in Counter(candidates).most_common(4)]
        combined = matched_tags + ranked
        unique: list[str] = []
        for tag in combined:
            if tag not in unique:
                unique.append(tag)
        return unique[:4] or ["networking", "follow-up"]

    @classmethod
    def _build_summary(cls, context: str, category: str, company: str | None) -> str:
        if "internship" in context or "стаж" in context:
            return "Перспективный контакт для карьерного развития и follow-up по стажировке."
        if company:
            return f"Контакт категории {category} из {company}, стоит поддерживать регулярную связь."
        return f"Перспективный контакт категории {category} с потенциалом для полезного follow-up."

    @classmethod
    def _suggest_next_action(cls, context: str) -> str:
        if "internship" in context or "стаж" in context:
            return "Написать через 5 дней и уточнить статус стажировки."
        if "speaker" in context or "mentor" in context:
            return "Отправить короткое спасибо и попросить 20-минутный созвон на следующей неделе."
        if "startup" in context or "founder" in context:
            return "Через 3 дня отправить follow-up с конкретной идеей для коллаборации."
        if "hr" in context or "recruit" in context:
            return "Через 5 дней написать и напомнить о себе с кратким обновлением по целям."
        return "Написать через 7 дней, напомнить контекст знакомства и предложить следующий шаг."
