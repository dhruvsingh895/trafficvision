"""Database engine and session management (SQLite)."""
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Base

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        url = get_settings().database_url
        _engine = create_engine(url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(_engine)
        _upgrade_schema(_engine)
    return _engine


def _upgrade_schema(engine: Engine) -> None:
    """Add columns that databases created by older versions are missing."""
    if engine.url.get_backend_name() != "sqlite":
        return
    with engine.begin() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(results)").fetchall()
        cols = {row[1] for row in rows}
        if rows and "processing_fps" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE results ADD COLUMN processing_fps FLOAT"
            )


@contextmanager
def get_session() -> Iterator[Session]:
    session = Session(_get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
