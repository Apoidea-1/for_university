# NetWorkPilot

NetWorkPilot — это MVP онлайн-платформы для управления личной сетью деловых контактов. Проект сделан как учебный стартап: с нормальной архитектурой, docker-окружением, backend на FastAPI, frontend на React и демо-данными для быстрого показа.

Платформа помогает:
- хранить контакты в одном месте;
- делить их по категориям и тегам;
- фиксировать историю взаимодействий;
- ставить напоминания на follow-up;
- получать AI-подсказки по заметкам;
- смотреть аналитику по активности нетворкинга.

## Что есть в проекте

### Backend

Backend построен на `FastAPI + SQLAlchemy 2.x + PostgreSQL + Alembic`.

Реализовано:
- регистрация, вход и получение текущего пользователя;
- JWT-аутентификация и защита приватных API;
- CRUD для контактов;
- быстрое добавление контакта;
- история взаимодействий по каждому контакту;
- напоминания с фильтрами по статусу;
- mock AI service для рекомендаций;
- аналитика по контактам, взаимодействиям и stale-контактам;
- mock-интеграции;
- seed-данные для демо;
- базовые backend-тесты на `pytest`.

### Frontend

Frontend построен на `React + TypeScript + Vite + React Router + TanStack Query + Tailwind CSS`.

Реализовано:
- welcome / landing page;
- экран входа и регистрации;
- защищённая рабочая зона;
- dashboard с KPI и быстрым добавлением контакта;
- список контактов с поиском, фильтрами и сортировкой;
- карточка контакта;
- формы добавления/редактирования;
- экран напоминаний;
- экран аналитики с графиками;
- экран интеграций;
- русскоязычный интерфейс.

### AI-слой

В проекте есть сервисный слой `AIRecommendationService`, который пока работает как mock-провайдер. Он умеет:
- предложить категорию;
- сгенерировать теги;
- дать короткий summary по заметке;
- предложить следующее действие.

Архитектурно этот слой изолирован, поэтому его можно заменить на реальный LLM-провайдер без переделки остального приложения.

## Основные возможности

- Аутентификация: регистрация, логин, `me`
- Контакты: создание, просмотр, обновление, удаление
- Фильтрация: поиск, категория, важность, сортировка
- Быстрое добавление: короткая форма для новых знакомств
- Взаимодействия: встреча, сообщение, звонок, проект, другое
- Напоминания: активные, просроченные, выполненные
- AI-подсказки: метаданные контакта и следующее действие
- Аналитика: KPI, категории, таймлайн, stale-контакты
- Интеграции: mock-статусы и connect action

## Стек технологий

### Frontend

- React
- TypeScript
- Vite
- React Router
- React Hook Form
- Zod
- TanStack Query
- Tailwind CSS
- Recharts

### Backend

- Python
- FastAPI
- SQLAlchemy 2.x
- Pydantic
- Alembic
- JWT

### Database / Infra

- PostgreSQL
- Docker Compose
- `.env`

### Testing

- pytest

## Структура проекта

```text
networkpilot/
  backend/
    app/
      api/
      core/
      db/
      models/
      repositories/
      schemas/
      services/
      tests/
      main.py
    alembic/
    alembic.ini
    Dockerfile
    requirements.txt

  frontend/
    src/
      api/
      app/
      components/
      features/
      hooks/
      pages/
      shared/
      types/
      main.tsx
    Dockerfile
    package.json
    vite.config.ts

  docker-compose.yml
  .env.example
  ARCHITECTURE.md
  README.md
```

## Главные сущности

В базе данных есть следующие ключевые сущности:

- `users`
- `contacts`
- `categories`
- `tags`
- `contact_tags`
- `interactions`
- `reminders`
- `ai_suggestions`
- `integrations`
- `activity_logs`

Связи и индексы описаны в миграции Alembic и архитектурном документе.

## Основные API

Все endpoint’ы идут под префиксом `/api/v1`.

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Contacts

- `GET /api/v1/contacts`
- `POST /api/v1/contacts`
- `POST /api/v1/contacts/quick-add`
- `GET /api/v1/contacts/{id}`
- `PATCH /api/v1/contacts/{id}`
- `DELETE /api/v1/contacts/{id}`

### Interactions

- `GET /api/v1/contacts/{id}/interactions`
- `POST /api/v1/contacts/{id}/interactions`
- `DELETE /api/v1/interactions/{id}`

### Reminders

- `GET /api/v1/reminders`
- `POST /api/v1/reminders`
- `PATCH /api/v1/reminders/{id}`
- `DELETE /api/v1/reminders/{id}`

### AI

- `POST /api/v1/ai/suggest-contact-metadata`
- `POST /api/v1/ai/suggest-next-action`

### Analytics

- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/categories`
- `GET /api/v1/analytics/stale-contacts`

### Integrations

- `GET /api/v1/integrations`
- `POST /api/v1/integrations/{provider}/connect-mock`

## Демо-доступ

- Email: `demo@networkpilot.app`
- Password: `DemoPass123!`

## Быстрый запуск через Docker

### 1. Подготовить env-файл

PowerShell:

```powershell
Copy-Item .env.example .env
```

### 2. Поднять проект

```powershell
docker compose up --build -d
```

### 3. Открыть сервисы

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

### Что происходит при старте backend-контейнера

Backend автоматически:
- ждёт PostgreSQL;
- выполняет `alembic upgrade head`;
- заполняет демо-данные через `python -m app.db.seed`;
- запускает Uvicorn.

## Локальный запуск без Docker

### Backend

Перейти в [`backend`](C:/Users/ilyak/Desktop/student_project/networkpilot/backend)

Установить зависимости:

```powershell
pip install -r requirements.txt
```

Применить миграции:

```powershell
alembic upgrade head
```

Заполнить демо-данные:

```powershell
python -m app.db.seed
```

Запустить API:

```powershell
uvicorn app.main:app --reload
```

### Frontend

Перейти в [`frontend`](C:/Users/ilyak/Desktop/student_project/networkpilot/frontend)

Установить зависимости:

```powershell
npm install
```

Запустить dev server:

```powershell
npm run dev
```

## Тесты

Backend-тесты:

```powershell
cd backend
pytest app/tests -q
```

## Что важно посмотреть в коде

- Архитектурное описание: [ARCHITECTURE.md](C:/Users/ilyak/Desktop/student_project/networkpilot/ARCHITECTURE.md)
- Точка входа backend: [main.py](C:/Users/ilyak/Desktop/student_project/networkpilot/backend/app/main.py)
- API router: [router.py](C:/Users/ilyak/Desktop/student_project/networkpilot/backend/app/api/router.py)
- Начальная миграция: [20260324_0001_initial.py](C:/Users/ilyak/Desktop/student_project/networkpilot/backend/alembic/versions/20260324_0001_initial.py)
- Seed-данные: [seed.py](C:/Users/ilyak/Desktop/student_project/networkpilot/backend/app/db/seed.py)
- Роутинг frontend: [router.tsx](C:/Users/ilyak/Desktop/student_project/networkpilot/frontend/src/app/router.tsx)
- Layout рабочей зоны: [AppShell.tsx](C:/Users/ilyak/Desktop/student_project/networkpilot/frontend/src/app/layouts/AppShell.tsx)
- Dashboard: [DashboardPage.tsx](C:/Users/ilyak/Desktop/student_project/networkpilot/frontend/src/pages/DashboardPage.tsx)
- Форма контакта: [ContactForm.tsx](C:/Users/ilyak/Desktop/student_project/networkpilot/frontend/src/features/contacts/ContactForm.tsx)

## Переменные окружения

Основные переменные лежат в [`.env.example`](C:/Users/ilyak/Desktop/student_project/networkpilot/.env.example):

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `DEMO_USER_EMAIL`
- `DEMO_USER_PASSWORD`
- `DEMO_USER_NAME`
- `VITE_API_URL`

## Что показывает проект как MVP

Этот проект демонстрирует не просто набор экранов, а цельный продуктовый сценарий:
- пользователь регистрируется или входит;
- добавляет новый контакт;
- фиксирует взаимодействие;
- ставит напоминание;
- получает AI-подсказку;
- смотрит аналитику по своей активности.

Если нужен более подробный разбор архитектуры, смотри [ARCHITECTURE.md](C:/Users/ilyak/Desktop/student_project/networkpilot/ARCHITECTURE.md).
