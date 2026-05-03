from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog


class ActivityLogService:
    @staticmethod
    def log(
        db: Session,
        *,
        user_id: int,
        entity_type: str,
        entity_id: int,
        action: str,
        payload: dict | None = None,
    ) -> None:
        db.add(
            ActivityLog(
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                payload_json=payload or {},
            )
        )
