from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.reminder_repository import ReminderRepository
from app.schemas.reminder import ReminderCreate, ReminderRead, ReminderUpdate
from app.services.activity_log_service import ActivityLogService

router = APIRouter()


@router.get("", response_model=list[ReminderRead])
def list_reminders(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reminders = ReminderRepository.list(db, user_id=current_user.id, status=status_filter)
    return [ReminderRead.model_validate(item) for item in reminders]


@router.post("", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not ReminderRepository.validate_contact_ownership(db, user_id=current_user.id, contact_id=payload.contact_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")
    reminder = ReminderRepository.create(db, user_id=current_user.id, payload=payload.model_dump())
    ActivityLogService.log(db, user_id=current_user.id, entity_type="reminder", entity_id=reminder.id, action="created")
    db.commit()
    reminder = ReminderRepository.get_by_id(db, user_id=current_user.id, reminder_id=reminder.id)
    return ReminderRead.model_validate(reminder)


@router.patch("/{reminder_id}", response_model=ReminderRead)
def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reminder = ReminderRepository.get_by_id(db, user_id=current_user.id, reminder_id=reminder_id)
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Напоминание не найдено")

    if payload.contact_id is not None and not ReminderRepository.validate_contact_ownership(
        db, user_id=current_user.id, contact_id=payload.contact_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Контакт не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(reminder, field, value)
    ActivityLogService.log(db, user_id=current_user.id, entity_type="reminder", entity_id=reminder.id, action="updated")
    db.commit()
    reminder = ReminderRepository.get_by_id(db, user_id=current_user.id, reminder_id=reminder.id)
    return ReminderRead.model_validate(reminder)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reminder = ReminderRepository.get_by_id(db, user_id=current_user.id, reminder_id=reminder_id)
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Напоминание не найдено")
    ActivityLogService.log(db, user_id=current_user.id, entity_type="reminder", entity_id=reminder.id, action="deleted")
    ReminderRepository.delete(db, reminder)
    db.commit()
