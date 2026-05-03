from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReminderStatus, ReminderType


class ReminderCreate(BaseModel):
    contact_id: int | None = None
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    due_date: datetime
    status: ReminderStatus = ReminderStatus.active
    reminder_type: ReminderType = ReminderType.follow_up


class ReminderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    due_date: datetime | None = None
    status: ReminderStatus | None = None
    reminder_type: ReminderType | None = None
    contact_id: int | None = None


class ReminderContactSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str | None = None
    company: str | None = None


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contact_id: int | None = None
    user_id: int
    title: str
    description: str | None = None
    due_date: datetime
    status: ReminderStatus
    reminder_type: ReminderType
    created_at: datetime
    updated_at: datetime
    contact: ReminderContactSummary | None = None
