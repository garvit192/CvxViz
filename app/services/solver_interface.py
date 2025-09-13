import math
from app.models.schema import ProblemInput, ProblemResult
from solver.solve import solve_lp
from app.services.validators import validate_problem
from app.core.errors import BadInput

def _finite(x) -> bool:
    try:
        return math.isfinite(float(x))
    except Exception:
        return True

def _sanitize_solution(sol):
    if not isinstance(sol, list):
        return sol
    out = []
    for x in sol:
        if isinstance(x, float) and not _finite(x):
            out.append(None)
        else:
            out.append(x)
    return out

def solve_problem(p: ProblemInput) -> ProblemResult:
    try:
        validate_problem(p)
    except ValueError as e:
        raise BadInput(str(e))

    res = solve_lp(
        c=p.c,
        Q=p.Q,
        A=p.A,
        b=p.b,
        bounds=p.bounds,
        sense=p.sense,
    )

    status = res.get("status", "unknown")
    obj = res.get("objective_value")
    if isinstance(obj, float) and not _finite(obj):
        obj = None

    sol = _sanitize_solution(res.get("solution"))

    return ProblemResult(
        status=status,
        objective_value=obj,
        solution=sol,
        message=res.get("message"),
    )
