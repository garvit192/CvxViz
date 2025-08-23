from pydantic import BaseModel, Field
from typing import List, Optional, Tuple

class ProblemInput(BaseModel):
    c: List[float] = Field(..., description="Objective vector")
    A: Optional[List[List[float]]] = None
    b: Optional[List[float]] = None
    Q: Optional[List[List[float]]] = None
    bounds: Optional[List[Tuple[Optional[float], Optional[float]]]] = None
    sense: str = "minimize"  # or "maximize"

class ProblemResult(BaseModel):
    status: str
    objective_value: Optional[float] = None
    solution: Optional[List[float]] = None
    message: Optional[str] = None
