from fastapi import APIRouter, Depends
from app.models.schema import ProblemInput, ProblemResult
from app.services.solver_interface import solve_problem
from app.core.security import verify_api_key

router = APIRouter()

@router.post("/solve", response_model=ProblemResult, dependencies=[Depends(verify_api_key)])
def solve_optimization_problem(input_data: ProblemInput):
    return solve_problem(input_data)

@router.get("/health")
def health_check():
    return {"status": "ok"}