# app/services/persistence.py
from __future__ import annotations

import json, hashlib, re
from contextlib import contextmanager
from typing import Optional, Tuple, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine, Base
from app.db.models import Problem, Solution
from app.models.schema import ProblemInput


@contextmanager
def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def create_tables() -> None:
    Base.metadata.create_all(bind=engine)

def _canonical_problem_dict(p: ProblemInput) -> dict:
    return {
        "c": p.c,
        "A": getattr(p, "A", None),
        "b": getattr(p, "b", None),
        "A_eq": getattr(p, "A_eq", None),
        "b_eq": getattr(p, "b_eq", None),
        "Q": getattr(p, "Q", None),
        "bounds": getattr(p, "bounds", None),
        "sense": getattr(p, "sense", None),
    }

def spec_hash(p: ProblemInput) -> str:
    js = json.dumps(_canonical_problem_dict(p), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(js.encode("utf-8")).hexdigest()

# ---------- Cache lookup (flexible) ----------
def find_cached_solution_by_hash(*args: Any, **kwargs: Any) -> Optional[dict]:
    db: Optional[Session] = kwargs.get("db")
    h: Optional[str] = kwargs.get("h")

    if h is None and args:
        if isinstance(args[0], Session):
            db = args[0]
            h = args[1] if len(args) > 1 else None
        else:
            h = args[0]

    if not h:
        raise TypeError("find_cached_solution_by_hash() missing required 'h'")

    sql = """
    SELECT s.id, s.problem_id, s.status, s.objective_value, s.solution_json,
           s.duration_ms, s.cached, s.created_at
    FROM solutions s
    JOIN problems p ON p.id = s.problem_id
    WHERE p.spec_hash = :h
    ORDER BY s.created_at DESC
    LIMIT 1
    """

    if db is None:
        with get_session() as _db:
            row = _db.execute(text(sql), {"h": h}).mappings().first()
            return dict(row) if row else None
    else:
        row = db.execute(text(sql), {"h": h}).mappings().first()
        return dict(row) if row else None

# ---------- Persist (flexible, backward-compatible) ----------
_HEX = re.compile(r"^[0-9a-fA-F]{16,64}$")

def persist_problem_and_solution(*args: Any, **kwargs: Any) -> Tuple[str, str]:
    """
    Supported forms:
      - (problem, result, duration_ms, cached)
      - (problem, result, spec_hash, duration_ms, cached)
      - (db, problem, result, duration_ms, cached)
      - (db, problem, result, spec_hash, duration_ms, cached)
      - or use keywords: db=..., problem=..., result=..., duration_ms=..., cached=...
    The spec hash param is optional and ignored if present (we recompute to be safe).
    """
    db: Optional[Session] = kwargs.pop("db", None)

    pos = list(args)
    if pos and isinstance(pos[0], Session):
        db = pos.pop(0)

    problem = kwargs.pop("problem", None) or (pos.pop(0) if pos else None)
    result  = kwargs.pop("result",  None) or (pos.pop(0) if pos else None)

    duration_ms = kwargs.pop("duration_ms", None)
    if duration_ms is None and pos:
        maybe = pos.pop(0)
        if isinstance(maybe, str) and _HEX.match(maybe):
            duration_ms = pos.pop(0) if pos else None
        else:
            duration_ms = maybe

    cached = kwargs.pop("cached", None)
    if cached is None and pos:
        cached = pos.pop(0)

    missing = [n for n, v in [
        ("problem", problem), ("result", result),
        ("duration_ms", duration_ms), ("cached", cached),
    ] if v is None]
    if missing:
        raise TypeError(f"persist_problem_and_solution() missing required args: {', '.join(missing)}")


    h = spec_hash(problem)
    payload_json = json.dumps(_canonical_problem_dict(problem), separators=(",", ":"))
    res_json = json.dumps(result, separators=(",", ":"))
    dur = int(duration_ms)
    cached_i = 1 if cached else 0

    def _insert(_db: Session) -> Tuple[str, str]:
        pr = Problem(spec_hash=h, payload_json=payload_json)
        _db.add(pr)
        _db.flush()

        sol = Solution(
            problem_id=pr.id,
            status=result.get("status"),
            objective_value=result.get("objective_value"),
            solution_json=res_json,
            duration_ms=dur,
            cached=cached_i,
        )
        _db.add(sol)
        _db.flush()
        return str(pr.id), str(sol.id)

    if db is None:
        with get_session() as _db:
            return _insert(_db)
    else:
        return _insert(db)
