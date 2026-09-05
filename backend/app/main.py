"""TrafficVision FastAPI application entry point."""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import get_session

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(title=settings.app_name, version="0.1.0")

    # CORS origins from env (comma-separated) or default to local dev
    cors_origins = os.getenv("TV_CORS_ORIGINS", "http://localhost:5173").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.routes import processing, videos
    from app.core.errors import register_error_handlers

    register_error_handlers(app)
    app.include_router(videos.router)
    app.include_router(processing.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/ready")
    def readiness() -> JSONResponse:
        """Report whether the database and required storage are available."""
        try:
            with get_session() as session:
                session.execute(text("SELECT 1"))
            settings.input_path
            settings.output_path
        except Exception as exc:
            logger.warning("Readiness check failed: %s", exc)
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready"},
            )
        return JSONResponse(status_code=200, content={"status": "ready"})

    logger.info("Application created: %s", settings.app_name)
    return app


app = create_app()
