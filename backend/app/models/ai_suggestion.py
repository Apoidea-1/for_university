from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SuggestionType


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"
    __table_args__ = (
        Index("ix_ai_suggestions_contact_id_created_at", "contact_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    suggestion_type: Mapped[SuggestionType] = mapped_column(SqlEnum(SuggestionType, name="suggestion_type"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    contact = relationship("Contact", back_populates="ai_suggestions")
