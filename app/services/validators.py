import math
from app.models.schema import ProblemInput

def _has_nan_inf(arr):
    for v in arr:
        if v is None:
            return True
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return True
    return False

def validate_problem(p: ProblemInput):
    if not p.c or len(p.c) == 0:
        raise ValueError("c (objective) is required")
    n = len(p.c)
    if p.A:
        for row in p.A:
            if len(row) != n:
                raise ValueError("Each row of A must have len(c) columns")
    if p.b and p.A and len(p.b) != len(p.A):
        raise ValueError("len(b) must equal number of rows in A")
    if p.bounds and len(p.bounds) != n:
        raise ValueError("len(bounds) must equal len(c)")
    if _has_nan_inf(p.c):
        raise ValueError("c contains NaN/Inf")
    if p.b and _has_nan_inf(p.b):
        raise ValueError("b contains NaN/Inf")
    if p.Q:
        if len(p.Q) != n or any(len(row) != n for row in p.Q):
            raise ValueError("Q must be square with size len(c)")
