from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import IntegrationProvider, IntegrationStatus


class IntegrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    provider: IntegrationProvider
    status: IntegrationStatus
    metadata_json: dict
    created_at: datetime


class IntegrationConnectResponse(BaseModel):
    provider: IntegrationProvider
    status: IntegrationStatus
    message: str
