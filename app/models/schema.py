from typing import List, Optional
from pydantic import BaseModel

class ProblemInput(BaseModel):
    c: List[float]
    A: Optional[List[List[float]]] = None
    b: Optional[List[float]] = None
    Q: Optional[List[List[float]]] = None
    bounds: Optional[List[Optional[List[float]]]] = None
    sense: str = "minimize"

class ProblemResult(BaseModel):
    status: str
    objective_value: Optional[float] = None
    solution: Optional[List[float]] = None
