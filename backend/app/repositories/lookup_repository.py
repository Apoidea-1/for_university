from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.tag import Tag


class LookupRepository:
    @staticmethod
    def list_categories(db: Session, user_id: int) -> list[Category]:
        statement = (
            select(Category)
            .where(or_(Category.user_id == user_id, Category.user_id.is_(None)))
            .order_by(Category.name.asc())
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def list_tags(db: Session, user_id: int) -> list[Tag]:
        statement = (
            select(Tag)
            .where(or_(Tag.user_id == user_id, Tag.user_id.is_(None)))
            .order_by(Tag.name.asc())
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def get_category(db: Session, user_id: int, category_id: int | None) -> Category | None:
        if category_id is None:
            return None
        statement = select(Category).where(
            Category.id == category_id,
            or_(Category.user_id == user_id, Category.user_id.is_(None)),
        )
        return db.scalar(statement)

    @staticmethod
    def create_category(db: Session, user_id: int, *, name: str, color: str) -> Category:
        category = Category(user_id=user_id, name=name, color=color)
        db.add(category)
        db.flush()
        return category

    @staticmethod
    def create_tag(db: Session, user_id: int, *, name: str) -> Tag:
        tag = Tag(user_id=user_id, name=name.strip().lower())
        db.add(tag)
        db.flush()
        return tag

    @staticmethod
    def get_tags_by_ids(db: Session, user_id: int, tag_ids: list[int]) -> list[Tag]:
        if not tag_ids:
            return []
        statement = select(Tag).where(
            Tag.id.in_(tag_ids),
            or_(Tag.user_id == user_id, Tag.user_id.is_(None)),
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def get_or_create_tags(db: Session, user_id: int, names: list[str]) -> list[Tag]:
        cleaned = [name.strip().lower() for name in names if name.strip()]
        if not cleaned:
            return []

        existing = list(
            db.scalars(
                select(Tag).where(
                    Tag.name.in_(cleaned),
                    or_(Tag.user_id == user_id, Tag.user_id.is_(None)),
                )
            ).all()
        )
        existing_names = {tag.name for tag in existing}
        created: list[Tag] = []
        for name in cleaned:
            if name in existing_names:
                continue
            created.append(LookupRepository.create_tag(db, user_id, name=name))
        return existing + created
