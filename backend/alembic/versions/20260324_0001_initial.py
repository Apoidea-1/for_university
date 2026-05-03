"""initial schema

Revision ID: 20260324_0001
Revises:
Create Date: 2026-03-24 22:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260324_0001"
down_revision = None
branch_labels = None
depends_on = None


importance_level = postgresql.ENUM("low", "medium", "high", "strategic", name="importance_level", create_type=False)
interaction_type = postgresql.ENUM("meeting", "message", "call", "project", "other", name="interaction_type", create_type=False)
reminder_status = postgresql.ENUM("active", "completed", name="reminder_status", create_type=False)
reminder_type = postgresql.ENUM("follow_up", "congratulation", "reconnect", "custom", name="reminder_type", create_type=False)
suggestion_type = postgresql.ENUM("metadata", "next_action", name="suggestion_type", create_type=False)
integration_provider = postgresql.ENUM("google_calendar", "linkedin", "telegram", name="integration_provider", create_type=False)
integration_status = postgresql.ENUM("connected", "not_connected", "coming_soon", name="integration_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    importance_level.create(bind, checkfirst=True)
    interaction_type.create(bind, checkfirst=True)
    reminder_status.create(bind, checkfirst=True)
    reminder_type.create(bind, checkfirst=True)
    suggestion_type.create(bind, checkfirst=True)
    integration_provider.create(bind, checkfirst=True)
    integration_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_categories_user_id_name", "categories", ["user_id", "name"], unique=False)

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_tags_user_id_name", "tags", ["user_id", "name"], unique=False)

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("company", sa.String(length=150), nullable=True),
        sa.Column("role", sa.String(length=150), nullable=True),
        sa.Column("source_where_met", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("telegram", sa.String(length=100), nullable=True),
        sa.Column("linkedin", sa.String(length=255), nullable=True),
        sa.Column("other_social", sa.String(length=255), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("importance_level", importance_level, nullable=False),
        sa.Column("last_interaction_date", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_contacts_email", "contacts", ["email"], unique=False)
    op.create_index("ix_contacts_user_id", "contacts", ["user_id"], unique=False)
    op.create_index("ix_contacts_user_id_category_id", "contacts", ["user_id", "category_id"], unique=False)
    op.create_index("ix_contacts_user_id_created_at", "contacts", ["user_id", "created_at"], unique=False)
    op.create_index(
        "ix_contacts_user_id_last_interaction_date",
        "contacts",
        ["user_id", "last_interaction_date"],
        unique=False,
    )

    op.create_table(
        "contact_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_contact_tags_contact_id_tag_id", "contact_tags", ["contact_id", "tag_id"], unique=True)

    op.create_table(
        "interactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("type", interaction_type, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("interaction_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_interactions_contact_id_interaction_date",
        "interactions",
        ["contact_id", "interaction_date"],
        unique=False,
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=False),
        sa.Column("status", reminder_status, nullable=False),
        sa.Column("reminder_type", reminder_type, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_reminders_user_id_due_date", "reminders", ["user_id", "due_date"], unique=False)
    op.create_index("ix_reminders_user_id_status", "reminders", ["user_id", "status"], unique=False)

    op.create_table(
        "ai_suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("suggestion_type", suggestion_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_ai_suggestions_contact_id_created_at",
        "ai_suggestions",
        ["contact_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", integration_provider, nullable=False),
        sa.Column("status", integration_status, nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_integrations_user_id_provider", "integrations", ["user_id", "provider"], unique=True)

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_activity_logs_entity_type_entity_id", "activity_logs", ["entity_type", "entity_id"], unique=False)
    op.create_index("ix_activity_logs_user_id_created_at", "activity_logs", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_activity_logs_user_id_created_at", table_name="activity_logs")
    op.drop_index("ix_activity_logs_entity_type_entity_id", table_name="activity_logs")
    op.drop_table("activity_logs")

    op.drop_index("ix_integrations_user_id_provider", table_name="integrations")
    op.drop_table("integrations")

    op.drop_index("ix_ai_suggestions_contact_id_created_at", table_name="ai_suggestions")
    op.drop_table("ai_suggestions")

    op.drop_index("ix_reminders_user_id_status", table_name="reminders")
    op.drop_index("ix_reminders_user_id_due_date", table_name="reminders")
    op.drop_table("reminders")

    op.drop_index("ix_interactions_contact_id_interaction_date", table_name="interactions")
    op.drop_table("interactions")

    op.drop_index("ix_contact_tags_contact_id_tag_id", table_name="contact_tags")
    op.drop_table("contact_tags")

    op.drop_index("ix_contacts_user_id_last_interaction_date", table_name="contacts")
    op.drop_index("ix_contacts_user_id_created_at", table_name="contacts")
    op.drop_index("ix_contacts_user_id_category_id", table_name="contacts")
    op.drop_index("ix_contacts_user_id", table_name="contacts")
    op.drop_index("ix_contacts_email", table_name="contacts")
    op.drop_table("contacts")

    op.drop_index("ix_tags_user_id_name", table_name="tags")
    op.drop_table("tags")

    op.drop_index("ix_categories_user_id_name", table_name="categories")
    op.drop_table("categories")

    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    integration_status.drop(bind, checkfirst=True)
    integration_provider.drop(bind, checkfirst=True)
    suggestion_type.drop(bind, checkfirst=True)
    reminder_type.drop(bind, checkfirst=True)
    reminder_status.drop(bind, checkfirst=True)
    interaction_type.drop(bind, checkfirst=True)
    importance_level.drop(bind, checkfirst=True)
