from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.contact import ContactTag
from app.repositories.contact_repository import ContactRepository
from app.repositories.lookup_repository import LookupRepository
from app.schemas.contact import ContactCreate, ContactListResponse, ContactRead, ContactUpdate, QuickContactCreate
from app.services.activity_log_service import ActivityLogService

router = APIRouter()


def _resolve_tags(db: Session, user_id: int, tag_ids: list[int], tag_names: list[str]):
    tags = LookupRepository.get_tags_by_ids(db, user_id, tag_ids)
    tags += LookupRepository.get_or_create_tags(db, user_id, tag_names)
    unique = {}
    for tag in tags:
        unique[tag.id] = tag
    return list(unique.values())


def _validate_category(db: Session, user_id: int, category_id: int | None):
    if category_id is None:
        return
    category = LookupRepository.get_category(db, user_id, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")


@router.get("", response_model=ContactListResponse)
def list_contacts(
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    importance_level: str | None = Query(default=None),
    sort_by: str = Query(default="last_interaction_date"),
    sort_order: str = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items, total = ContactRepository.list(
        db,
        user_id=current_user.id,
        search=search,
        category_id=category_id,
        importance_level=importance_level,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ContactListResponse(
        total=total,
        items=[ContactRead.model_validate(item) for item in items],
    )


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _validate_category(db, current_user.id, payload.category_id)
    data = payload.model_dump(exclude={"tag_ids", "tag_names"}, exclude_none=True)
    contact = ContactRepository.create(db, user_id=current_user.id, payload=data)
    tags = _resolve_tags(db, current_user.id, payload.tag_ids, payload.tag_names)
    contact.tag_links = [ContactTag(tag_id=tag.id) for tag in tags]
    ActivityLogService.log(db, user_id=current_user.id, entity_type="contact", entity_id=contact.id, action="created")
    db.commit()
    contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=contact.id)
    return ContactRead.model_validate(contact)


@router.post("/quick-add", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def quick_add_contact(
    payload: QuickContactCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _validate_category(db, current_user.id, payload.category_id)
    contact = ContactRepository.create(
        db,
        user_id=current_user.id,
        payload=payload.model_dump(exclude_none=True),
    )
    ActivityLogService.log(db, user_id=current_user.id, entity_type="contact", entity_id=contact.id, action="quick_created")
    db.commit()
    contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=contact.id)
    return ContactRead.model_validate(contact)


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")
    return ContactRead.model_validate(contact)


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")

    data = payload.model_dump(exclude_unset=True, exclude={"tag_ids", "tag_names"})
    if "category_id" in data and data["category_id"] is not None:
        _validate_category(db, current_user.id, data["category_id"])
    for field, value in data.items():
        setattr(contact, field, value)

    if payload.tag_ids is not None or payload.tag_names is not None:
        tags = _resolve_tags(db, current_user.id, payload.tag_ids or [], payload.tag_names or [])
        contact.tag_links = [ContactTag(tag_id=tag.id) for tag in tags]

    ActivityLogService.log(db, user_id=current_user.id, entity_type="contact", entity_id=contact.id, action="updated")
    db.commit()
    contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=contact.id)
    return ContactRead.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contact = ContactRepository.get_by_id(db, user_id=current_user.id, contact_id=contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")
    ActivityLogService.log(db, user_id=current_user.id, entity_type="contact", entity_id=contact.id, action="deleted")
    ContactRepository.delete(db, contact)
    db.commit()
