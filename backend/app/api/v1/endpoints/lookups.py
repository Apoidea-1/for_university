from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories.lookup_repository import LookupRepository
from app.schemas.category import CategoryCreate, CategoryRead
from app.schemas.tag import TagCreate, TagRead

router = APIRouter()


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return [CategoryRead.model_validate(item) for item in LookupRepository.list_categories(db, current_user.id)]


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    category = LookupRepository.create_category(db, current_user.id, name=payload.name, color=payload.color)
    db.commit()
    return CategoryRead.model_validate(category)


@router.get("/tags", response_model=list[TagRead])
def list_tags(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return [TagRead.model_validate(item) for item in LookupRepository.list_tags(db, current_user.id)]


@router.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tag = LookupRepository.create_tag(db, current_user.id, name=payload.name)
    db.commit()
    return TagRead.model_validate(tag)
