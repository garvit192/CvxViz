# app/db/session.py
from __future__ import annotations

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

os.makedirs("data", exist_ok=True)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/cvxviz.db")

class Base(DeclarativeBase):
    pass

def _make_engine(url: str):
    is_sqlite = url.startswith("sqlite")
    is_memory = url in ("sqlite://", "sqlite:///:memory:") or ":memory:" in url
    if is_sqlite and is_memory:
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    if is_sqlite:
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
        )
    return create_engine(url)

engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _):
    try:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.close()
    except Exception:
        pass

try:
    from . import models as _models
    Base.metadata.create_all(bind=engine)
except Exception:
    pass
