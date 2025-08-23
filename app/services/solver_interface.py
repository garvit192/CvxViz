from app.models.schema import ProblemInput, ProblemResult
from solver.solve import solve_lp

def solve_problem(p: ProblemInput) -> ProblemResult:
    res = solve_lp(
        c=p.c,
        Q=p.Q,
        A=p.A,
        b=p.b,
        bounds=p.bounds,
        sense=p.sense,
    )
    return ProblemResult(
        status=res.get("status", "unknown"),
        objective_value=res.get("objective_value"),
        solution=res.get("solution"),
        message=res.get("message"),
    )
