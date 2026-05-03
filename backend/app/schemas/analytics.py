from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ActivityTimelinePoint(BaseModel):
    date: date
    contacts_added: int
    interactions_logged: int


class AnalyticsOverviewResponse(BaseModel):
    new_contacts_7d: int
    new_contacts_30d: int
    interactions_7d: int
    interactions_30d: int
    active_reminders: int
    overdue_reminders: int
    stale_contacts_count: int
    activity_timeline: list[ActivityTimelinePoint]


class CategoryAnalyticsItem(BaseModel):
    category_name: str
    color: str
    count: int


class StaleContactItem(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    company: str | None = None
    last_interaction_date: datetime | None = None
    days_since_last_interaction: int | None = None
