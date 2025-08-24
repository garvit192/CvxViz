from fastapi import APIRouter, Depends, Request
import asyncio
import structlog

from app.core.config import settings
from app.core.security import RequireAPIKey
from app.models.schema import ProblemInput, ProblemResult
from app.services.solver_interface import solve_problem

# Get a decorator without importing from main.py
from app.core.limiting import get_limit_decorator

router = APIRouter()
logger = structlog.get_logger()

@router.get("/health")
def health():
    return {"status": "ok"}

# Build the decorator at import time; if slowapi missing, it's a no-op.
limit_deco = get_limit_decorator("10/minute")

@router.post("/solve", response_model=ProblemResult, dependencies=[RequireAPIKey])
@limit_deco
async def solve_endpoint(request: Request, payload: ProblemInput):
    logger.info("solve_start", sense=payload.sense)
    try:
        res = await asyncio.wait_for(
            asyncio.to_thread(solve_problem, payload),
            timeout=settings.TIMEOUT_SECONDS,
        )
        logger.info("solve_done", status=res.status, obj=res.objective_value)
        return res
    except asyncio.TimeoutError:
        # handled by our 504 handler in main
        raise TimeoutError()
