from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.contact import Contact
from app.models.enums import ReminderStatus
from app.models.reminder import Reminder


class ReminderRepository:
    @staticmethod
    def list(db: Session, *, user_id: int, status: str | None = None) -> list[Reminder]:
        statement = (
            select(Reminder)
            .options(joinedload(Reminder.contact))
            .where(Reminder.user_id == user_id)
            .order_by(Reminder.due_date.asc())
        )
        now = datetime.utcnow()
        if status == "active":
            statement = statement.where(Reminder.status == ReminderStatus.active, Reminder.due_date >= now)
        elif status == "overdue":
            statement = statement.where(Reminder.status == ReminderStatus.active, Reminder.due_date < now)
        elif status == "completed":
            statement = statement.where(Reminder.status == ReminderStatus.completed)
        return list(db.scalars(statement).all())

    @staticmethod
    def create(db: Session, *, user_id: int, payload: dict) -> Reminder:
        reminder = Reminder(user_id=user_id, **payload)
        db.add(reminder)
        db.flush()
        return reminder

    @staticmethod
    def get_by_id(db: Session, *, user_id: int, reminder_id: int) -> Reminder | None:
        statement = (
            select(Reminder)
            .options(joinedload(Reminder.contact))
            .where(Reminder.id == reminder_id, Reminder.user_id == user_id)
        )
        return db.scalar(statement)

    @staticmethod
    def delete(db: Session, reminder: Reminder) -> None:
        db.delete(reminder)

    @staticmethod
    def validate_contact_ownership(db: Session, *, user_id: int, contact_id: int | None) -> bool:
        if contact_id is None:
            return True
        statement = select(Contact.id).where(Contact.id == contact_id, Contact.user_id == user_id)
        return db.scalar(statement) is not None
