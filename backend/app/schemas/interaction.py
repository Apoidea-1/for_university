from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InteractionType


class InteractionCreate(BaseModel):
    type: InteractionType
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    interaction_date: datetime


class InteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contact_id: int
    type: InteractionType
    title: str
    description: str | None = None
    interaction_date: datetime
    created_at: datetime
