from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import IntegrationProvider, IntegrationStatus
from app.schemas.integration import IntegrationConnectResponse, IntegrationRead
from app.services.activity_log_service import ActivityLogService
from app.services.bootstrap_service import BootstrapService
from app.repositories.integration_repository import IntegrationRepository

router = APIRouter()


@router.get("", response_model=list[IntegrationRead])
def list_integrations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    BootstrapService.create_default_workspace(db, current_user)
    db.commit()
    integrations = IntegrationRepository.list_for_user(db, user_id=current_user.id)
    return [IntegrationRead.model_validate(item) for item in integrations]


@router.post("/{provider}/connect-mock", response_model=IntegrationConnectResponse)
def connect_mock(
    provider: IntegrationProvider,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    BootstrapService.create_default_workspace(db, current_user)
    integration = IntegrationRepository.get_by_provider(db, user_id=current_user.id, provider=provider)
    if provider == IntegrationProvider.google_calendar:
        integration.status = IntegrationStatus.connected
        integration.metadata_json = {**integration.metadata_json, "last_sync": "mock-connected"}
        message = "Mock connection established."
    else:
        integration.status = IntegrationStatus.coming_soon
        message = "Provider is prepared in the architecture, but still marked as coming soon."

    ActivityLogService.log(
        db,
        user_id=current_user.id,
        entity_type="integration",
        entity_id=integration.id,
        action="connected_mock",
        payload={"provider": provider.value, "status": integration.status.value},
    )
    db.commit()
    return IntegrationConnectResponse(provider=provider, status=integration.status, message=message)
