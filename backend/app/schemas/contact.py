from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ImportanceLevel
from app.schemas.category import CategoryRead
from app.schemas.tag import TagRead


class ContactBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=150)
    role: str | None = Field(default=None, max_length=150)
    source_where_met: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    telegram: str | None = Field(default=None, max_length=100)
    linkedin: str | None = Field(default=None, max_length=255)
    other_social: str | None = Field(default=None, max_length=255)
    category_id: int | None = None
    importance_level: ImportanceLevel = ImportanceLevel.medium
    last_interaction_date: datetime | None = None
    notes: str | None = None
    tag_ids: list[int] = Field(default_factory=list)
    tag_names: list[str] = Field(default_factory=list)


class ContactCreate(ContactBase):
    pass


class QuickContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    source_where_met: str | None = Field(default=None, max_length=255)
    category_id: int | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=150)
    role: str | None = Field(default=None, max_length=150)
    source_where_met: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    telegram: str | None = Field(default=None, max_length=100)
    linkedin: str | None = Field(default=None, max_length=255)
    other_social: str | None = Field(default=None, max_length=255)
    category_id: int | None = None
    importance_level: ImportanceLevel | None = None
    last_interaction_date: datetime | None = None
    notes: str | None = None
    tag_ids: list[int] | None = None
    tag_names: list[str] | None = None


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    first_name: str
    last_name: str | None = None
    company: str | None = None
    role: str | None = None
    source_where_met: str | None = None
    email: str | None = None
    phone: str | None = None
    telegram: str | None = None
    linkedin: str | None = None
    other_social: str | None = None
    category_id: int | None = None
    importance_level: ImportanceLevel
    last_interaction_date: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    category: CategoryRead | None = None
    tags: list[TagRead] = Field(default_factory=list)


class ContactListResponse(BaseModel):
    total: int
    items: list[ContactRead]
