"""
FINRES Database Engine & Session Management.
Wraps SQLAlchemy with connection pooling, init helpers, and dependency injection.
Uses SQLite locally; automatically upgrades to PostgreSQL via DATABASE_URL env var.
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./finres.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, conn_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Create all tables. Idempotent — safe to call on every startup."""
    from src_py.models import db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _seed_if_empty()


def _seed_if_empty() -> None:
    """Seed the database with sample customers on first start."""
    from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA
    from src_py.models.db_models import CustomerDB

    with session_scope() as session:
        existing = session.query(CustomerDB).count()
        if existing > 0:
            return

        for cid, c in SAMPLE_CUSTOMERS_DATA.items():
            row = CustomerDB(
                id=cid,
                name=c.get("name", "Unknown"),
                archetype=c.get("archetype", "SALARIED"),
                pan_masked=c.get("pan_masked", "XXXXX0000X"),
                cluster_region=c.get("cluster_region", "Unknown"),
                occupation_or_industry=c.get("industry", "General"),
            )
            session.add(row)
        session.commit()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for use outside FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
