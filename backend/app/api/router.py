from fastapi import APIRouter

from app.api.v1.endpoints import ai, analytics, auth, contacts, integrations, interactions, lookups, reminders

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(interactions.router, tags=["interactions"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(lookups.router, tags=["lookups"])
