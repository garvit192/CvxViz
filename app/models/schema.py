from pydantic import BaseModel, Field
from typing import List, Optional, Tuple

class ProblemInput(BaseModel):
    c: List[Optional[float]] = Field(..., description="Objective vector")
    A: Optional[List[List[float]]] = None
    b: Optional[List[Optional[float]]] = None
    Q: Optional[List[List[float]]] = None
    bounds: Optional[List[Tuple[Optional[float], Optional[float]]]] = None
    sense: str = "minimize"

class ProblemResult(BaseModel):
    status: str
    objective_value: Optional[float] = None
    solution: Optional[List[float]] = None
    message: Optional[str] = None
