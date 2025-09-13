#!/usr/bin/env python3
# apply_week4.py — add Week 4 (Persistence + Caching + History APIs) to CvxViz
# Run from your project root (the folder containing app/ and tests/):
#     python apply_week4.py
# This script is idempotent: rerunning it won't duplicate blocks.

from __future__ import annotations
import re, sys, textwrap
from pathlib import Path

ROOT = Path.cwd()

def die(msg: str):
    print(f"[week4] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def info(msg: str):
    print(f"[week4] {msg}")

def ensure_in_requirements(line: str):
    req = ROOT / "requirements.txt"
    if not req.exists():
        req.write_text(line + "\n")
        info("created requirements.txt")
        return
    lines = [l.rstrip("\n") for l in req.read_text().splitlines()]
    if not any(l.strip().startswith("sqlalchemy") for l in lines):
        lines.append(line)
        req.write_text("\n".join(lines) + "\n")
        info("added sqlalchemy to requirements.txt")

def write_file(path: Path, content: str, overwrite: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return False
    path.write_text(content)
    return True

def upsert_block(path: Path, marker_begin: str, marker_end: str, block: str):
    """Insert or replace a named block between markers."""
    s = path.read_text()
    start = s.find(marker_begin)
    end = s.find(marker_end)
    if start != -1 and end != -1 and end > start:
        new = s[:start] + marker_begin + "\n" + block + "\n" + marker_end + s[end+len(marker_end):]
        path.write_text(new)
        return "replaced"
    else:
        with path.open("a") as f:
            f.write("\n" + marker_begin + "\n" + block + "\n" + marker_end + "\n")
        return "appended"

def patch_main():
    main = ROOT / "app" / "main.py"
    if not main.exists():
        die("app/main.py not found")
    s = main.read_text()

    # Ensure DB imports
    if "from app.db.session import engine, Base" not in s:
        s = s.replace(
            "from fastapi import FastAPI",
            "from fastapi import FastAPI\nfrom app.db.session import engine, Base",
            1
        )
        main.write_text(s)
        info("main.py: added DB imports")

    # Startup hook to create tables
    marker_begin = "# WEEK4_STARTUP_DB_BEGIN"
    marker_end = "# WEEK4_STARTUP_DB_END"
    block = (
        '@app.on_event("startup")\n'
        "def _init_db():\n"
        "    # Create tables on startup (SQLite)\n"
        "    Base.metadata.create_all(engine)\n"
    )
    state = upsert_block(main, marker_begin, marker_end, block)
    info(f"main.py: startup hook {state}")

def patch_routes():
    routes = ROOT / "app" / "api" / "v1" / "routes.py"
    if not routes.exists():
        die("app/api/v1/routes.py not found")
    s = routes.read_text()

    # Ensure imports for Query and persistence helpers
    if "from fastapi import APIRouter, Depends, Request, Query" not in s:
        if "from fastapi import APIRouter, Depends, Request" in s:
            s = s.replace(
                "from fastapi import APIRouter, Depends, Request",
                "from fastapi import APIRouter, Depends, Request, Query"
            )
        elif "from fastapi import APIRouter, Depends" in s and ", Request" not in s:
            s = s.replace(
                "from fastapi import APIRouter, Depends",
                "from fastapi import APIRouter, Depends, Request, Query"
            )
        routes.write_text(s)

    s = routes.read_text()
    if "from app.services.persistence import spec_hash" not in s:
        s = s.replace(
            "from app.services.solver_interface import solve_problem",
            "from app.services.solver_interface import solve_problem\n"
            "from app.services.persistence import spec_hash, find_cached_solution_by_hash, persist_problem_and_solution"
        )
        routes.write_text(s)

    # Add use_cache param to solve endpoint
    s = routes.read_text()
    def_sig = re.compile(r"async def solve_endpoint\s*\(.*?payload: ProblemInput\)", re.S)
    if def_sig.search(s) and "use_cache" not in s.split("async def solve_endpoint",1)[1][:200]:
        s = def_sig.sub(
            "async def solve_endpoint(request: Request, payload: ProblemInput, use_cache: bool = Query(True))",
            s, count=1
        )
        routes.write_text(s)
        info("routes.py: added use_cache param")

    # Inject cache prelude
    s = routes.read_text()
    if "WEEK4_CACHE_BEGIN" not in s:
        body_inject = textwrap.dedent("""
            # WEEK4_CACHE_BEGIN
            # Hash-based cache lookup
            shash = spec_hash(payload)
            if use_cache:
                hit = find_cached_solution_by_hash(shash)
                if hit:
                    _sid, sol = hit  # sol has status/objective_value/solution/message
                    return sol
            _t0 = __import__("time").perf_counter()
            # WEEK4_CACHE_END
        """).strip("\n")
        s = re.sub(r"(async def solve_endpoint[^\n]*\):\n)", r"\1    " + body_inject.replace("\n", "\n    ") + "\n", s, count=1)
        routes.write_text(s)
        info("routes.py: injected cache prelude")

    # Inject persistence after res is computed (before return)
    s = routes.read_text()
    if "WEEK4_PERSIST_BEGIN" not in s:
        persist_block = textwrap.dedent("""
            # WEEK4_PERSIST_BEGIN
            _dt_ms = int((__import__("time").perf_counter() - _t0) * 1000)
            try:
                _prob_id, _sol_id = persist_problem_and_solution(payload, res, shash, _dt_ms, cached=False)
                logger.info("persisted", problem_id=_prob_id, solution_id=_sol_id, duration_ms=_dt_ms)
            except Exception as _e:
                logger.warning("persist_failed", error=str(_e))
            # WEEK4_PERSIST_END
        """).strip("\n")
        s = s.replace("        return res", persist_block + "\n        return res")
        routes.write_text(s)
        info("routes.py: injected persistence")

    # Append history/problem/solution endpoints
    s = routes.read_text()
    if "/history" not in s or "get_solution(" not in s:
        extra_endpoints = textwrap.dedent('''
            # WEEK4_HISTORY_API_BEGIN
            @router.get("/history", dependencies=[RequireAPIKey])
            def history(limit: int = 50, offset: int = 0):
                from app.services.persistence import get_session
                with get_session() as db:
                    rows = db.execute(
                        """
                        SELECT p.id as problem_id, p.spec_hash, p.created_at,
                               s.id as solution_id, s.status, s.objective_value, s.duration_ms, s.cached, s.created_at as solved_at
                        FROM problems p
                        JOIN solutions s ON s.problem_id = p.id
                        ORDER BY p.created_at DESC
                        LIMIT :limit OFFSET :offset
                        """,
                        {"limit": limit, "offset": offset}
                    ).mappings().all()
                return {"items": rows, "limit": limit, "offset": offset}

            @router.get("/problems/{problem_id}", dependencies=[RequireAPIKey])
            def get_problem(problem_id: str):
                from app.services.persistence import get_session
                with get_session() as db:
                    row = db.execute(
                        "SELECT id, spec_hash, payload_json, created_at FROM problems WHERE id=:id",
                        {"id": problem_id}
                    ).mappings().first()
                if not row:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=404, detail="Not found")
                return row

            @router.get("/solutions/{solution_id}", dependencies=[RequireAPIKey])
            def get_solution(solution_id: str):
                from app.services.persistence import get_session
                with get_session() as db:
                    row = db.execute(
                        "SELECT id, problem_id, status, objective_value, solution_json, duration_ms, cached, created_at \
                         FROM solutions WHERE id=:id",
                        {"id": solution_id}
                    ).mappings().first()
                if not row:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=404, detail="Not found")
                return row
            # WEEK4_HISTORY_API_END
        ''').strip("\n")
        with routes.open("a") as f:
            f.write("\n\n" + extra_endpoints + "\n")
        info("routes.py: appended history/problem/solution endpoints")

def write_db_and_services():
    # __init__ for db package
    write_file(ROOT / "app" / "db" / "__init__.py", "", overwrite=False)

    session_py = """from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine, event
import os

os.makedirs("data", exist_ok=True)
DATABASE_URL = "sqlite:///./data/cvxviz.db"

class Base(DeclarativeBase):
    pass

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
    except Exception:
        pass
"""
    write_file(ROOT / "app" / "db" / "session.py", session_py, overwrite=False)

    models_py = """from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey, Index
from datetime import datetime
from .session import Base
import uuid

def _uuid() -> str: return str(uuid.uuid4())

class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    spec_hash: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Index("ix_problems_spec_hash_created", Problem.spec_hash, Problem.created_at.desc())

class Solution(Base):
    __tablename__ = "solutions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id"), index=True)
    status: Mapped[str] = mapped_column(String(32))
    objective_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    solution_json: Mapped[str] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer)
    cached: Mapped[int] = mapped_column(Integer, default=0)  # bool as 0/1
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
"""
    write_file(ROOT / "app" / "db" / "models.py", models_py, overwrite=False)

    persistence_py = """import json
from contextlib import contextmanager
from typing import Optional, Tuple
from app.models.schema import ProblemInput, ProblemResult
from app.db.session import SessionLocal
from app.db.models import Problem, Solution

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

def canonical_spec(p: ProblemInput) -> dict:
    return {
        "c": p.c,
        "A": p.A,
        "b": p.b,
        "Q": p.Q,
        "bounds": p.bounds,
        "sense": p.sense,
    }

def spec_hash(p: ProblemInput) -> str:
    s = json.dumps(canonical_spec(p), sort_keys=True, separators=(',', ':'))
    import hashlib as _h
    return _h.sha256(s.encode('utf-8')).hexdigest()

def find_cached_solution_by_hash(shash: str) -> Optional[Tuple[str, dict]]:
    with get_session() as db:
        row = db.execute(
            '''
            SELECT s.id, s.solution_json
            FROM solutions s
            JOIN problems p ON s.problem_id = p.id
            WHERE p.spec_hash = :h AND s.status = 'optimal'
            ORDER BY s.created_at DESC
            LIMIT 1
            ''',
            {'h': shash}
        ).fetchone()
        if not row:
            return None
        return row[0], json.loads(row[1])

def persist_problem_and_solution(p: ProblemInput, res: ProblemResult, shash: str, duration_ms: int, cached: bool):
    payload = json.dumps(canonical_spec(p), sort_keys=True)
    body = {
        "status": res.status,
        "objective_value": res.objective_value,
        "solution": res.solution,
        "message": res.message,
    }
    solution_json = json.dumps(body, default=str)
    with get_session() as db:
        prob = Problem(spec_hash=shash, payload_json=payload)
        db.add(prob); db.flush()
        sol = Solution(problem_id=prob.id, status=res.status,
                       objective_value=res.objective_value, solution_json=solution_json,
                       duration_ms=duration_ms, cached=1 if cached else 0)
        db.add(sol); db.flush()
        return prob.id, sol.id
"""
    write_file(ROOT / "app" / "services" / "persistence.py", persistence_py, overwrite=False)

def write_tests():
    tests_dir = ROOT / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_file = tests_dir / "test_persistence.py"
    if test_file.exists():
        return
    test_code = """from starlette.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.persistence import spec_hash
from app.models.schema import ProblemInput

client = TestClient(app)

def _hdr(ip='11.0.0.1'):
    return {'X-API-Key': settings.API_TOKEN, 'X-Forwarded-For': ip, 'Content-Type': 'application/json'}

def _payload():
    return {'c':[1,2], 'A':[[1,1]], 'b':[5], 'bounds':[[0,None],[0,None]], 'sense':'minimize'}

def _count_for_hash(spec_h):
    r = client.get(f"{settings.API_V1_STR}/history?limit=500", headers=_hdr('11.0.0.2'))
    assert r.status_code == 200
    items = r.json().get('items', [])
    return sum(1 for it in items if it.get('spec_hash') == spec_h)

def test_persist_and_history_smoke():
    p = ProblemInput(**_payload())
    h = spec_hash(p)
    before = _count_for_hash(h)

    r = client.post(f"{settings.API_V1_STR}/solve", json=_payload(), headers=_hdr('11.0.0.3'))
    assert r.status_code < 400

    after = _count_for_hash(h)
    assert after == before + 1

def test_cache_hit_does_not_create_new_row():
    p = ProblemInput(**_payload())
    h = spec_hash(p)
    before = _count_for_hash(h)

    # first call
    r1 = client.post(f"{settings.API_V1_STR}/solve", json=_payload(), headers=_hdr('11.0.0.4'))
    assert r1.status_code < 400

    # second call (same payload) should be served from cache
    r2 = client.post(f"{settings.API_V1_STR}/solve?use_cache=true", json=_payload(), headers=_hdr('11.0.0.5'))
    assert r2.status_code < 400

    after = _count_for_hash(h)
    # only the first call should have persisted a new row
    assert after == before + 1

def test_bypass_cache_creates_new_solution():
    p = ProblemInput(**_payload())
    h = spec_hash(p)
    before = _count_for_hash(h)

    # force bypass
    r = client.post(f"{settings.API_V1_STR}/solve?use_cache=false", json=_payload(), headers=_hdr('11.0.0.6'))
    assert r.status_code < 400

    after = _count_for_hash(h)
    assert after == before + 1
"""
    test_file.write_text(test_code)

def main():
    if not (ROOT / "app" / "main.py").exists():
        die("Run this from the project root that contains app/main.py")

    ensure_in_requirements("sqlalchemy>=2.0")

    write_db_and_services()
    patch_main()
    patch_routes()
    write_tests()

    info("Week 4 applied. Next steps:")
    info("  1) pip install -r requirements.txt")
    info("  2) uvicorn app.main:app --reload  (check /api/v1/history)")
    info("  3) pytest -q")

if __name__ == "__main__":
    main()
