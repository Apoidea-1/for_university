from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.repositories.user_repository import UserRepository
from app.services.bootstrap_service import BootstrapService


class AuthService:
    @staticmethod
    def register(db: Session, *, full_name: str, email: str, password: str):
        existing_user = UserRepository.get_by_email(db, email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с такой почтой уже существует")

        user = UserRepository.create(
            db,
            full_name=full_name,
            email=email,
            password_hash=get_password_hash(password),
        )
        BootstrapService.create_default_workspace(db, user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, *, email: str, password: str):
        user = UserRepository.get_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверная почта или пароль")
        return user
