from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import IntegrationProvider
from app.models.integration import Integration


class IntegrationRepository:
    @staticmethod
    def list_for_user(db: Session, *, user_id: int) -> list[Integration]:
        statement = select(Integration).where(Integration.user_id == user_id).order_by(Integration.provider.asc())
        return list(db.scalars(statement).all())

    @staticmethod
    def get_by_provider(db: Session, *, user_id: int, provider: IntegrationProvider) -> Integration | None:
        statement = select(Integration).where(Integration.user_id == user_id, Integration.provider == provider)
        return db.scalar(statement)
