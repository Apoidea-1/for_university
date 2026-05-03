from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def root():
        return RedirectResponse(url="http://localhost:5173", status_code=307)

    @app.get("/api-info")
    def api_info():
        return {
            "name": settings.project_name,
            "status": "ok",
            "docs_url": "/docs",
            "health_url": "/health",
            "api_base": settings.api_v1_prefix,
        }

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
