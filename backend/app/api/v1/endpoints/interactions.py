from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.interaction import Interaction
from app.repositories.contact_repository import ContactRepository
from app.repositories.interaction_repository import InteractionRepository
from app.schemas.interaction import InteractionCreate, InteractionRead
from app.services.activity_log_service import ActivityLogService

router = APIRouter()


@router.get("/contacts/{contact_id}/interactions", response_model=list[InteractionRead])
def list_interactions(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")
    items = InteractionRepository.list_for_contact(db, user_id=current_user.id, contact_id=contact_id)
    return [InteractionRead.model_validate(item) for item in items]


@router.post("/contacts/{contact_id}/interactions", response_model=InteractionRead, status_code=status.HTTP_201_CREATED)
def create_interaction(
    contact_id: int,
    payload: InteractionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")
    interaction = InteractionRepository.create(db, contact_id=contact_id, payload=payload.model_dump())
    if not contact.last_interaction_date or payload.interaction_date > contact.last_interaction_date:
        contact.last_interaction_date = payload.interaction_date
    ActivityLogService.log(
        db,
        user_id=current_user.id,
        entity_type="interaction",
        entity_id=interaction.id,
        action="created",
        payload={"contact_id": contact_id},
    )
    db.commit()
    return InteractionRead.model_validate(interaction)


@router.delete("/interactions/{interaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    interaction = InteractionRepository.get_by_id(db, user_id=current_user.id, interaction_id=interaction_id)
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Взаимодействие не найдено")
    contact = interaction.contact
    ActivityLogService.log(
        db,
        user_id=current_user.id,
        entity_type="interaction",
        entity_id=interaction.id,
        action="deleted",
        payload={"contact_id": interaction.contact_id},
    )
    InteractionRepository.delete(db, interaction)
    db.flush()
    contact.last_interaction_date = db.scalar(
        select(func.max(Interaction.interaction_date)).where(Interaction.contact_id == contact.id)
    )
    db.commit()
