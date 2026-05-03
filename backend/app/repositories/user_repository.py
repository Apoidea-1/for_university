from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email.lower()))

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def create(db: Session, *, full_name: str, email: str, password_hash: str) -> User:
        user = User(full_name=full_name, email=email.lower(), password_hash=password_hash)
        db.add(user)
        db.flush()
        return user
