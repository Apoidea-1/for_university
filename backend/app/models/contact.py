from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ImportanceLevel


class Contact(TimestampMixin, Base):
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_user_id_created_at", "user_id", "created_at"),
        Index("ix_contacts_user_id_last_interaction_date", "user_id", "last_interaction_date"),
        Index("ix_contacts_user_id_category_id", "user_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    company: Mapped[str | None] = mapped_column(String(150))
    role: Mapped[str | None] = mapped_column(String(150))
    source_where_met: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    telegram: Mapped[str | None] = mapped_column(String(100))
    linkedin: Mapped[str | None] = mapped_column(String(255))
    other_social: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    importance_level: Mapped[ImportanceLevel] = mapped_column(
        SqlEnum(ImportanceLevel, name="importance_level"),
        default=ImportanceLevel.medium,
        nullable=False,
    )
    last_interaction_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    notes: Mapped[str | None] = mapped_column(Text)

    user = relationship("User", back_populates="contacts")
    category = relationship("Category", back_populates="contacts")
    tag_links = relationship("ContactTag", back_populates="contact", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="contact", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="contact", cascade="all, delete-orphan")
    ai_suggestions = relationship("AISuggestion", back_populates="contact", cascade="all, delete-orphan")

    @property
    def tags(self):
        return [link.tag for link in self.tag_links if link.tag is not None]

    @property
    def full_name(self) -> str:
        return " ".join(part for part in [self.first_name, self.last_name] if part)


class ContactTag(Base):
    __tablename__ = "contact_tags"
    __table_args__ = (
        Index("ix_contact_tags_contact_id_tag_id", "contact_id", "tag_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    contact = relationship("Contact", back_populates="tag_links")
    tag = relationship("Tag", back_populates="contact_links")
