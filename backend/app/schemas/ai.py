from __future__ import annotations

from pydantic import BaseModel


class ContactMetadataSuggestionRequest(BaseModel):
    notes: str
    first_name: str | None = None
    company: str | None = None
    role: str | None = None
    source_where_met: str | None = None
    contact_id: int | None = None


class ContactMetadataSuggestionResponse(BaseModel):
    category: str
    tags: list[str]
    note_summary: str
    next_action: str


class NextActionSuggestionRequest(BaseModel):
    notes: str
    last_interaction_summary: str | None = None
    contact_id: int | None = None


class NextActionSuggestionResponse(BaseModel):
    next_action: str
    rationale: str
