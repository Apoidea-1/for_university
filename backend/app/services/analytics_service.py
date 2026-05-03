from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.contact import Contact
from app.models.enums import ReminderStatus
from app.models.interaction import Interaction
from app.models.reminder import Reminder
from app.schemas.analytics import ActivityTimelinePoint, AnalyticsOverviewResponse, CategoryAnalyticsItem, StaleContactItem


class AnalyticsService:
    @staticmethod
    def get_overview(db: Session, *, user_id: int) -> AnalyticsOverviewResponse:
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        new_contacts_7d = db.scalar(
            select(func.count(Contact.id)).where(Contact.user_id == user_id, Contact.created_at >= seven_days_ago)
        ) or 0
        new_contacts_30d = db.scalar(
            select(func.count(Contact.id)).where(Contact.user_id == user_id, Contact.created_at >= thirty_days_ago)
        ) or 0
        interactions_7d = db.scalar(
            select(func.count(Interaction.id))
            .join(Contact, Contact.id == Interaction.contact_id)
            .where(Contact.user_id == user_id, Interaction.interaction_date >= seven_days_ago)
        ) or 0
        interactions_30d = db.scalar(
            select(func.count(Interaction.id))
            .join(Contact, Contact.id == Interaction.contact_id)
            .where(Contact.user_id == user_id, Interaction.interaction_date >= thirty_days_ago)
        ) or 0
        active_reminders = db.scalar(
            select(func.count(Reminder.id)).where(
                Reminder.user_id == user_id,
                Reminder.status == ReminderStatus.active,
                Reminder.due_date >= now,
            )
        ) or 0
        overdue_reminders = db.scalar(
            select(func.count(Reminder.id)).where(
                Reminder.user_id == user_id,
                Reminder.status == ReminderStatus.active,
                Reminder.due_date < now,
            )
        ) or 0
        stale_contacts = AnalyticsService.get_stale_contacts(db, user_id=user_id, days=21)
        timeline = AnalyticsService._build_activity_timeline(db, user_id=user_id, days=14)
        return AnalyticsOverviewResponse(
            new_contacts_7d=new_contacts_7d,
            new_contacts_30d=new_contacts_30d,
            interactions_7d=interactions_7d,
            interactions_30d=interactions_30d,
            active_reminders=active_reminders,
            overdue_reminders=overdue_reminders,
            stale_contacts_count=len(stale_contacts),
            activity_timeline=timeline,
        )

    @staticmethod
    def get_category_distribution(db: Session, *, user_id: int) -> list[CategoryAnalyticsItem]:
        statement = (
            select(Category.name, Category.color, func.count(Contact.id))
            .select_from(Contact)
            .join(Category, Category.id == Contact.category_id, isouter=True)
            .where(Contact.user_id == user_id)
            .group_by(Category.name, Category.color)
            .order_by(func.count(Contact.id).desc())
        )
        results = db.execute(statement).all()
        return [
            CategoryAnalyticsItem(
                category_name=name or "Uncategorized",
                color=color or "#94a3b8",
                count=count,
            )
            for name, color, count in results
        ]

    @staticmethod
    def get_stale_contacts(db: Session, *, user_id: int, days: int) -> list[StaleContactItem]:
        threshold = datetime.utcnow() - timedelta(days=days)
        statement = (
            select(Contact)
            .where(Contact.user_id == user_id)
            .where((Contact.last_interaction_date.is_(None)) | (Contact.last_interaction_date < threshold))
            .order_by(Contact.last_interaction_date.is_(None).desc(), Contact.last_interaction_date.asc(), Contact.first_name.asc())
        )
        contacts = list(db.scalars(statement).all())
        items: list[StaleContactItem] = []
        for contact in contacts:
            delta = None
            if contact.last_interaction_date:
                delta = (datetime.utcnow() - contact.last_interaction_date).days
            items.append(
                StaleContactItem(
                    id=contact.id,
                    first_name=contact.first_name,
                    last_name=contact.last_name,
                    company=contact.company,
                    last_interaction_date=contact.last_interaction_date,
                    days_since_last_interaction=delta,
                )
            )
        return items

    @staticmethod
    def _build_activity_timeline(db: Session, *, user_id: int, days: int) -> list[ActivityTimelinePoint]:
        start = datetime.utcnow().date() - timedelta(days=days - 1)
        start_datetime = datetime.combine(start, datetime.min.time())
        contacts_rows = db.execute(
            select(func.date(Contact.created_at), func.count(Contact.id))
            .where(Contact.user_id == user_id, Contact.created_at >= start_datetime)
            .group_by(func.date(Contact.created_at))
        ).all()
        interactions_rows = db.execute(
            select(func.date(Interaction.interaction_date), func.count(Interaction.id))
            .join(Contact, Contact.id == Interaction.contact_id)
            .where(Contact.user_id == user_id, Interaction.interaction_date >= start_datetime)
            .group_by(func.date(Interaction.interaction_date))
        ).all()

        contact_map = defaultdict(int, {AnalyticsService._to_date(key): count for key, count in contacts_rows})
        interaction_map = defaultdict(int, {AnalyticsService._to_date(key): count for key, count in interactions_rows})
        timeline: list[ActivityTimelinePoint] = []
        for offset in range(days):
            current_day = start + timedelta(days=offset)
            timeline.append(
                ActivityTimelinePoint(
                    date=current_day,
                    contacts_added=contact_map[current_day],
                    interactions_logged=interaction_map[current_day],
                )
            )
        return timeline

    @staticmethod
    def _to_date(value: date | str) -> date:
        if isinstance(value, date):
            return value
        return datetime.strptime(value, "%Y-%m-%d").date()
