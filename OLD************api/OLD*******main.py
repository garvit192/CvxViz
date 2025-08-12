from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Tuple
from solver.solve import solve_lp

app = FastAPI()

class SolveRequest(BaseModel):
    c: List[float]
    A: Optional[List[List[float]]] = None
    b: Optional[List[float]] = None
    Q: Optional[List[List[float]]] = None
    bounds: Optional[List[Tuple[Optional[float], Optional[float]]]] = None
    sense: Optional[str] = "minimize"

class SolveResponse(BaseModel):
    status: str
    objective_value: Optional[float]
    solution: Optional[List[float]]
    error: Optional[str] = None

@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest):
    result = solve_lp(
        c=request.c,
        A=request.A,
        b=request.b,
        Q=request.Q,
        bounds=request.bounds,
        sense=request.sense
    )
    return result