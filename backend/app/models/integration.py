from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, JSON
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import IntegrationProvider, IntegrationStatus


class Integration(Base):
    __tablename__ = "integrations"
    __table_args__ = (
        Index("ix_integrations_user_id_provider", "user_id", "provider", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(SqlEnum(IntegrationProvider, name="integration_provider"), nullable=False)
    status: Mapped[IntegrationStatus] = mapped_column(
        SqlEnum(IntegrationStatus, name="integration_status"),
        default=IntegrationStatus.not_connected,
        nullable=False,
    )
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="integrations")
