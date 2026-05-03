from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.analytics import AnalyticsOverviewResponse, CategoryAnalyticsItem, StaleContactItem
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return AnalyticsService.get_overview(db, user_id=current_user.id)


@router.get("/categories", response_model=list[CategoryAnalyticsItem])
def get_category_distribution(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return AnalyticsService.get_category_distribution(db, user_id=current_user.id)


@router.get("/stale-contacts", response_model=list[StaleContactItem])
def get_stale_contacts(
    days: int = Query(default=21, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return AnalyticsService.get_stale_contacts(db, user_id=current_user.id, days=days)
