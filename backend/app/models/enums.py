from __future__ import annotations

from enum import Enum


class ImportanceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    strategic = "strategic"


class InteractionType(str, Enum):
    meeting = "meeting"
    message = "message"
    call = "call"
    project = "project"
    other = "other"


class ReminderStatus(str, Enum):
    active = "active"
    completed = "completed"


class ReminderType(str, Enum):
    follow_up = "follow_up"
    congratulation = "congratulation"
    reconnect = "reconnect"
    custom = "custom"


class SuggestionType(str, Enum):
    metadata = "metadata"
    next_action = "next_action"


class IntegrationProvider(str, Enum):
    google_calendar = "google_calendar"
    linkedin = "linkedin"
    telegram = "telegram"


class IntegrationStatus(str, Enum):
    connected = "connected"
    not_connected = "not_connected"
    coming_soon = "coming_soon"
