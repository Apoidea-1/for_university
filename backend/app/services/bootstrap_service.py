from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import IntegrationProvider, IntegrationStatus
from app.models.integration import Integration
from app.models.tag import Tag
from app.models.user import User

DEFAULT_CATEGORIES = [
    ("Mentors", "#0f766e"),
    ("Recruiters", "#2563eb"),
    ("Founders", "#ea580c"),
    ("Peers", "#7c3aed"),
    ("Alumni", "#14b8a6"),
    ("Investors", "#be123c"),
]

DEFAULT_TAGS = [
    "internship",
    "career",
    "hackathon",
    "university",
    "product",
    "startup",
    "design",
    "follow-up",
]


class BootstrapService:
    @staticmethod
    def create_default_workspace(db: Session, user: User) -> None:
        existing_categories = db.query(Category).filter(Category.user_id == user.id).count()
        if existing_categories == 0:
            for name, color in DEFAULT_CATEGORIES:
                db.add(Category(user_id=user.id, name=name, color=color))

        existing_tags = db.query(Tag).filter(Tag.user_id == user.id).count()
        if existing_tags == 0:
            for tag_name in DEFAULT_TAGS:
                db.add(Tag(user_id=user.id, name=tag_name))

        existing_integrations = db.query(Integration).filter(Integration.user_id == user.id).count()
        if existing_integrations == 0:
            db.add_all(
                [
                    Integration(
                        user_id=user.id,
                        provider=IntegrationProvider.google_calendar,
                        status=IntegrationStatus.not_connected,
                        metadata_json={"label": "Google Calendar"},
                    ),
                    Integration(
                        user_id=user.id,
                        provider=IntegrationProvider.linkedin,
                        status=IntegrationStatus.coming_soon,
                        metadata_json={"label": "LinkedIn"},
                    ),
                    Integration(
                        user_id=user.id,
                        provider=IntegrationProvider.telegram,
                        status=IntegrationStatus.coming_soon,
                        metadata_json={"label": "Telegram"},
                    ),
                ]
            )
