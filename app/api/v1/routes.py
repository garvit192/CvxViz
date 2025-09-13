from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import text
from app.core.security import RequireAPIKey
from app.core.config import settings
from app.core.limiting import get_limit_decorator
from app.models.schema import ProblemInput
from app.services.solver_interface import solve_problem
from app.services.persistence import (
    find_cached_solution_by_hash,
    persist_problem_and_solution,
    spec_hash,
    get_session,
)
import time
import json
from typing import Optional

router = APIRouter()
limit = get_limit_decorator("10/minute")


def _to_plain_dict(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):   # Pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):         # Pydantic v1
        return obj.dict()
    return obj

@router.post("/solve", dependencies=[RequireAPIKey])
@limit
async def solve_endpoint(
    request: Request,
    payload: ProblemInput,
    use_cache: Optional[bool] = Query(default=None),
):
    if getattr(settings, "TIMEOUT_SECONDS", 8) <= 0:
        raise HTTPException(status_code=504, detail="Timeout")

    bypass_hdr = request.headers.get("X-Force-Recompute") or request.headers.get("X-Bypass-Cache")
    effective_use_cache = bool(use_cache) and not bool(bypass_hdr)

    shash = spec_hash(payload)

    with get_session() as db:
        if effective_use_cache:
            cached = find_cached_solution_by_hash(db, shash)
            if cached:
                try:
                    cached_payload = json.loads(cached.get("solution_json") or "{}")
                except Exception:
                    cached_payload = {}
                return {
                    "status": cached.get("status") or cached_payload.get("status"),
                    "objective_value": (
                        cached.get("objective_value")
                        if cached.get("objective_value") is not None
                        else cached_payload.get("objective_value")
                    ),
                    "solution": cached_payload.get("solution"),
                    "cached": True,
                    "solution_id": cached.get("id"),
                    "problem_id": cached.get("problem_id"),
                }

        # fresh solve
        t0 = time.perf_counter()
        res_model = solve_problem(payload)         
        dt_ms = int((time.perf_counter() - t0) * 1000)

        res = _to_plain_dict(res_model)
        persist_problem_and_solution(db, payload, res, dt_ms, cached=False)

        res = dict(res)
        res["cached"] = False
        return res

@router.get("/history", dependencies=[RequireAPIKey])
def history(limit: int = 50, offset: int = 0):
    from app.services.persistence import get_session
    with get_session() as db:
        rows = db.execute(
            text("""
                SELECT p.id as problem_id, p.spec_hash, p.created_at,
                       s.id as solution_id, s.status, s.objective_value, s.duration_ms, s.cached, s.created_at as solved_at
                FROM problems p
                JOIN solutions s ON s.problem_id = p.id
                ORDER BY p.created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset}
        ).mappings().all()
    return {"items": rows, "limit": limit, "offset": offset}


@router.get("/problems/{problem_id}", dependencies=[RequireAPIKey])
def get_problem(problem_id: str):
    from app.services.persistence import get_session
    with get_session() as db:
        row = db.execute(
            text("SELECT id, spec_hash, payload_json, created_at FROM problems WHERE id=:id"),
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
            text("SELECT id, problem_id, status, objective_value, solution_json, duration_ms, cached, created_at FROM solutions WHERE id=:id"),
            {"id": solution_id}
        ).mappings().first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    return row

@router.get("/health")
def health():
    return {"status": "ok"}