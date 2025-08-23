from fastapi import APIRouter, Depends
from app.core.security import RequireAPIKey
from app.models.schema import ProblemInput, ProblemResult
from app.services.solver_interface import solve_problem

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/solve", response_model=ProblemResult, dependencies=[RequireAPIKey])
def solve_endpoint(payload: ProblemInput):
    return solve_problem(payload)
