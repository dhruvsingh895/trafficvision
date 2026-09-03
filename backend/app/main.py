"""TrafficVision FastAPI application entry point."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
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

    logger.info("Application created: %s", settings.app_name)
    return app


app = create_app()
