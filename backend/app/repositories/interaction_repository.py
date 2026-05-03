from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.interaction import Interaction


class InteractionRepository:
    @staticmethod
    def list_for_contact(db: Session, *, user_id: int, contact_id: int) -> list[Interaction]:
        statement = (
            select(Interaction)
            .join(Contact, Contact.id == Interaction.contact_id)
            .where(Contact.user_id == user_id, Contact.id == contact_id)
            .order_by(Interaction.interaction_date.desc())
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def create(db: Session, *, contact_id: int, payload: dict) -> Interaction:
        interaction = Interaction(contact_id=contact_id, **payload)
        db.add(interaction)
        db.flush()
        return interaction

    @staticmethod
    def get_by_id(db: Session, *, user_id: int, interaction_id: int) -> Interaction | None:
        statement = (
            select(Interaction)
            .join(Contact, Contact.id == Interaction.contact_id)
            .where(Contact.user_id == user_id, Interaction.id == interaction_id)
        )
        return db.scalar(statement)

    @staticmethod
    def delete(db: Session, interaction: Interaction) -> None:
        db.delete(interaction)
