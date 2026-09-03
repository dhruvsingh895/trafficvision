"""Global error handling for the API."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Attach consistent JSON error handlers."""

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid request", "errors": exc.errors()},
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error("Database error: %s", exc)
        return JSONResponse(
            status_code=500, content={"detail": "Database error"}
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
