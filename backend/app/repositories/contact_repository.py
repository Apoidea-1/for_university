from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.contact import Contact, ContactTag
from app.models.tag import Tag


class ContactRepository:
    @staticmethod
    def base_query():
        return select(Contact).options(
            selectinload(Contact.category),
            selectinload(Contact.tag_links).selectinload(ContactTag.tag),
        )

    @staticmethod
    def get_by_id(db: Session, *, user_id: int, contact_id: int) -> Contact | None:
        statement = ContactRepository.base_query().where(Contact.id == contact_id, Contact.user_id == user_id)
        return db.scalar(statement)

    @staticmethod
    def list(
        db: Session,
        *,
        user_id: int,
        search: str | None = None,
        category_id: int | None = None,
        importance_level: str | None = None,
        sort_by: str = "last_interaction_date",
        sort_order: str = "desc",
    ) -> tuple[list[Contact], int]:
        statement = ContactRepository.base_query().where(Contact.user_id == user_id)
        count_statement = select(func.count(Contact.id)).where(Contact.user_id == user_id)

        if search:
            pattern = f"%{search.strip()}%"
            search_filter = or_(
                Contact.first_name.ilike(pattern),
                Contact.last_name.ilike(pattern),
                Contact.company.ilike(pattern),
                Contact.role.ilike(pattern),
                Contact.source_where_met.ilike(pattern),
                Contact.id.in_(
                    select(ContactTag.contact_id)
                    .join(Tag, Tag.id == ContactTag.tag_id)
                    .where(Tag.name.ilike(pattern))
                ),
            )
            statement = statement.where(search_filter)
            count_statement = count_statement.where(search_filter)

        if category_id:
            statement = statement.where(Contact.category_id == category_id)
            count_statement = count_statement.where(Contact.category_id == category_id)

        if importance_level:
            statement = statement.where(Contact.importance_level == importance_level)
            count_statement = count_statement.where(Contact.importance_level == importance_level)

        if sort_by == "name":
            order_by = (
                [Contact.first_name.desc(), Contact.last_name.desc()]
                if sort_order == "desc"
                else [Contact.first_name.asc(), Contact.last_name.asc()]
            )
        elif sort_by == "created_at":
            order_by = [Contact.created_at.asc() if sort_order == "asc" else Contact.created_at.desc()]
        else:
            order_by = (
                [Contact.last_interaction_date.is_(None).asc(), Contact.last_interaction_date.asc()]
                if sort_order == "asc"
                else [Contact.last_interaction_date.is_(None).asc(), Contact.last_interaction_date.desc()]
            )

        statement = statement.order_by(*order_by)
        items = list(db.scalars(statement).unique().all())
        total = db.scalar(count_statement) or 0
        return items, total

    @staticmethod
    def create(db: Session, *, user_id: int, payload: dict) -> Contact:
        contact = Contact(user_id=user_id, **payload)
        db.add(contact)
        db.flush()
        return contact

    @staticmethod
    def delete(db: Session, contact: Contact) -> None:
        db.delete(contact)
