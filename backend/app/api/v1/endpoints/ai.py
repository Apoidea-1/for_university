from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import SuggestionType
from app.repositories.contact_repository import ContactRepository
from app.schemas.ai import (
    ContactMetadataSuggestionRequest,
    ContactMetadataSuggestionResponse,
    NextActionSuggestionRequest,
    NextActionSuggestionResponse,
)
from app.services.ai_recommendation_service import AIRecommendationService

router = APIRouter()


@router.post("/suggest-contact-metadata", response_model=ContactMetadataSuggestionResponse)
def suggest_contact_metadata(
    payload: ContactMetadataSuggestionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.contact_id is not None:
        contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=payload.contact_id)
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")

    suggestion = AIRecommendationService.suggest_contact_metadata(
        notes=payload.notes,
        first_name=payload.first_name,
        company=payload.company,
        role=payload.role,
    )
    if payload.contact_id is not None:
        AIRecommendationService.persist_suggestion(
            db,
            contact_id=payload.contact_id,
            suggestion_type=SuggestionType.metadata,
            content=json.dumps(suggestion.__dict__, ensure_ascii=False),
        )
        db.commit()
    return ContactMetadataSuggestionResponse(**suggestion.__dict__)


@router.post("/suggest-next-action", response_model=NextActionSuggestionResponse)
def suggest_next_action(
    payload: NextActionSuggestionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.contact_id is not None:
        contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=payload.contact_id)
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")

    next_action, rationale = AIRecommendationService.suggest_next_action(
        notes=payload.notes,
        last_interaction_summary=payload.last_interaction_summary,
    )
    if payload.contact_id is not None:
        AIRecommendationService.persist_suggestion(
            db,
            contact_id=payload.contact_id,
            suggestion_type=SuggestionType.next_action,
            content=json.dumps({"next_action": next_action, "rationale": rationale}, ensure_ascii=False),
        )
        db.commit()
    return NextActionSuggestionResponse(next_action=next_action, rationale=rationale)
