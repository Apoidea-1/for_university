from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ReminderStatus, ReminderType


class Reminder(TimestampMixin, Base):
    __tablename__ = "reminders"
    __table_args__ = (
        Index("ix_reminders_user_id_due_date", "user_id", "due_date"),
        Index("ix_reminders_user_id_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[ReminderStatus] = mapped_column(
        SqlEnum(ReminderStatus, name="reminder_status"),
        default=ReminderStatus.active,
        nullable=False,
    )
    reminder_type: Mapped[ReminderType] = mapped_column(
        SqlEnum(ReminderType, name="reminder_type"),
        default=ReminderType.follow_up,
        nullable=False,
    )

    contact = relationship("Contact", back_populates="reminders")
    user = relationship("User", back_populates="reminders")
