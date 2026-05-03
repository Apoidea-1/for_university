from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.contact import Contact, ContactTag
from app.models.enums import ImportanceLevel, InteractionType, ReminderStatus, ReminderType, SuggestionType
from app.models.interaction import Interaction
from app.models.reminder import Reminder
from app.models.user import User
from app.repositories.lookup_repository import LookupRepository
from app.repositories.user_repository import UserRepository
from app.services.ai_recommendation_service import AIRecommendationService
from app.services.bootstrap_service import BootstrapService


CONTACT_BLUEPRINTS = [
    {
        "first_name": "Elena",
        "last_name": "Petrova",
        "company": "North HR Lab",
        "role": "HR Partner",
        "source_where_met": "Career Forum 2026",
        "category": "Recruiters",
        "importance_level": ImportanceLevel.high,
        "notes": "Познакомились на карьерном форуме, обсуждали стажировку и карьерный трек в HR.",
        "tags": ["internship", "career", "follow-up"],
        "created_days_ago": 5,
        "last_interaction_days_ago": 3,
    },
    {
        "first_name": "Dmitry",
        "last_name": "Orlov",
        "company": "Launchpad Ventures",
        "role": "Founder",
        "source_where_met": "Startup Weekend",
        "category": "Founders",
        "importance_level": ImportanceLevel.strategic,
        "notes": "Обсуждали идею продукта для студентов и возможную пилотную интеграцию.",
        "tags": ["startup", "product"],
        "created_days_ago": 11,
        "last_interaction_days_ago": 7,
    },
    {
        "first_name": "Anna",
        "last_name": "Kim",
        "company": "Design Crew",
        "role": "Product Designer",
        "source_where_met": "UX Meetup",
        "category": "Peers",
        "importance_level": ImportanceLevel.medium,
        "notes": "Сильный дизайнер, обсуждали совместный кейс-чемпионат и UX ревью.",
        "tags": ["design", "hackathon"],
        "created_days_ago": 2,
        "last_interaction_days_ago": 2,
    },
    {
        "first_name": "Maksim",
        "last_name": "Sokolov",
        "company": "TechCore",
        "role": "Engineering Mentor",
        "source_where_met": "University mentoring session",
        "category": "Mentors",
        "importance_level": ImportanceLevel.high,
        "notes": "Дал советы по backend-архитектуре и подготовке к интервью.",
        "tags": ["career", "university"],
        "created_days_ago": 18,
        "last_interaction_days_ago": 15,
    },
    {
        "first_name": "Irina",
        "last_name": "Belova",
        "company": "Alumni Club",
        "role": "Community Lead",
        "source_where_met": "Alumni dinner",
        "category": "Alumni",
        "importance_level": ImportanceLevel.medium,
        "notes": "Помогает сводить студентов с выпускниками, предложила интро к PM-сообществу.",
        "tags": ["university", "product"],
        "created_days_ago": 21,
        "last_interaction_days_ago": 20,
    },
    {
        "first_name": "Roman",
        "last_name": "Kiselev",
        "company": "Campus VC",
        "role": "Analyst",
        "source_where_met": "Demo day",
        "category": "Investors",
        "importance_level": ImportanceLevel.low,
        "notes": "Интересовался юнит-экономикой и ранними B2B SaaS командами.",
        "tags": ["startup", "product"],
        "created_days_ago": 30,
        "last_interaction_days_ago": 30,
    },
    {
        "first_name": "Sofia",
        "last_name": "Novikova",
        "company": "Bright Talent",
        "role": "Recruiter",
        "source_where_met": "Telegram networking chat",
        "category": "Recruiters",
        "importance_level": ImportanceLevel.high,
        "notes": "Рекрутер по junior product ролям, попросила обновить CV через неделю.",
        "tags": ["career", "follow-up"],
        "created_days_ago": 9,
        "last_interaction_days_ago": 4,
    },
    {
        "first_name": "Kirill",
        "last_name": "Zorin",
        "company": "HackLab",
        "role": "Student Lead",
        "source_where_met": "Hackathon finals",
        "category": "Peers",
        "importance_level": ImportanceLevel.medium,
        "notes": "Организует хакатоны, можно позвать в партнёрство и обмен аудиториями.",
        "tags": ["hackathon", "university"],
        "created_days_ago": 14,
        "last_interaction_days_ago": 12,
    },
    {
        "first_name": "Nina",
        "last_name": "Gromova",
        "company": "Scale PM",
        "role": "Product Manager",
        "source_where_met": "ProductCamp",
        "category": "Mentors",
        "importance_level": ImportanceLevel.high,
        "notes": "Обсудили переход в product management и карьерную стратегию на 6 месяцев.",
        "tags": ["product", "career"],
        "created_days_ago": 6,
        "last_interaction_days_ago": 5,
    },
    {
        "first_name": "Timur",
        "last_name": "Akhmetov",
        "company": "Founders Club",
        "role": "Community Manager",
        "source_where_met": "Startup breakfast",
        "category": "Founders",
        "importance_level": ImportanceLevel.medium,
        "notes": "Открыт к совместным мероприятиям и акселераторским интро.",
        "tags": ["startup", "follow-up"],
        "created_days_ago": 25,
        "last_interaction_days_ago": 23,
    },
    {
        "first_name": "Yulia",
        "last_name": "Mirova",
        "company": "Talent Forge",
        "role": "HR Lead",
        "source_where_met": "Internship fair",
        "category": "Recruiters",
        "importance_level": ImportanceLevel.high,
        "notes": "Работает в HR, обсуждали воронку стажёров и полезные кейсы для отклика.",
        "tags": ["internship", "career", "hr"],
        "created_days_ago": 1,
        "last_interaction_days_ago": 1,
    },
    {
        "first_name": "Oleg",
        "last_name": "Volkov",
        "company": "Alumni Angels",
        "role": "Angel Investor",
        "source_where_met": "University investment panel",
        "category": "Investors",
        "importance_level": ImportanceLevel.medium,
        "notes": "Может дать интро к alumni-фонду, если будет traction.",
        "tags": ["university", "startup"],
        "created_days_ago": 40,
        "last_interaction_days_ago": 35,
    },
]


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        user = UserRepository.get_by_email(db, settings.demo_user_email)
        if not user:
            user = User(
                full_name=settings.demo_user_name,
                email=settings.demo_user_email,
                password_hash=get_password_hash(settings.demo_user_password),
            )
            db.add(user)
            db.flush()
        BootstrapService.create_default_workspace(db, user)
        db.flush()

        categories = {item.name: item for item in LookupRepository.list_categories(db, user.id)}
        existing_contacts = {
            (contact.first_name, contact.last_name, contact.company)
            for contact in db.scalars(select(Contact).where(Contact.user_id == user.id)).all()
        }
        tags = {tag.name: tag for tag in LookupRepository.list_tags(db, user.id)}
        now = datetime.utcnow()
        contact_entities: dict[str, Contact] = {}

        for blueprint in CONTACT_BLUEPRINTS:
            key = (blueprint["first_name"], blueprint["last_name"], blueprint["company"])
            if key in existing_contacts:
                continue
            created_at = now - timedelta(days=blueprint["created_days_ago"])
            last_interaction = now - timedelta(days=blueprint["last_interaction_days_ago"])
            contact = Contact(
                user_id=user.id,
                first_name=blueprint["first_name"],
                last_name=blueprint["last_name"],
                company=blueprint["company"],
                role=blueprint["role"],
                source_where_met=blueprint["source_where_met"],
                category_id=categories[blueprint["category"]].id,
                importance_level=blueprint["importance_level"],
                last_interaction_date=last_interaction,
                notes=blueprint["notes"],
                created_at=created_at,
                updated_at=created_at,
            )
            db.add(contact)
            db.flush()
            for tag_name in blueprint["tags"]:
                tag = tags.get(tag_name)
                if not tag:
                    tag = LookupRepository.create_tag(db, user.id, name=tag_name)
                    tags[tag.name] = tag
                db.add(ContactTag(contact_id=contact.id, tag_id=tag.id))

            AIRecommendationService.persist_suggestion(
                db,
                contact_id=contact.id,
                suggestion_type=SuggestionType.metadata,
                content=blueprint["notes"],
            )
            contact_entities[contact.first_name] = contact

        db.flush()
        all_contacts = list(db.scalars(select(Contact).where(Contact.user_id == user.id)).all())
        if not db.scalar(select(Interaction.id).limit(1)):
            for index, contact in enumerate(all_contacts[:8], start=1):
                interaction_date = now - timedelta(days=index * 2)
                db.add(
                    Interaction(
                        contact_id=contact.id,
                        type=InteractionType.message if index % 2 else InteractionType.meeting,
                        title=f"Follow-up #{index}",
                        description="Короткий контакт после знакомства, договорились держать связь.",
                        interaction_date=interaction_date,
                        created_at=interaction_date,
                    )
                )

        if not db.scalar(select(Reminder.id).limit(1)):
            reminder_contacts = all_contacts[:6]
            offsets = [2, -1, 5, -3, 10, 1]
            for idx, contact in enumerate(reminder_contacts):
                due_date = now + timedelta(days=offsets[idx])
                db.add(
                    Reminder(
                        user_id=user.id,
                        contact_id=contact.id,
                        title=f"Follow-up with {contact.first_name}",
                        description="Поддержать контакт и напомнить о себе.",
                        due_date=due_date,
                        status=ReminderStatus.active if idx != 4 else ReminderStatus.completed,
                        reminder_type=ReminderType.follow_up,
                        created_at=now - timedelta(days=idx + 1),
                        updated_at=now - timedelta(days=idx + 1),
                    )
                )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
