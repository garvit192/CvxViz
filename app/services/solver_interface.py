from app.models.schema import ProblemInput, ProblemResult
from solver.solve import solve_lp

import math

def solve_problem(problem_input: ProblemInput) -> ProblemResult:
    result = solve_lp(
        c=problem_input.c,
        Q=problem_input.Q,
        A=problem_input.A,
        b=problem_input.b,
        sense=problem_input.sense
    )

    # Safely handle inf/nan for JSON compliance
    obj_val = result.get("objective_value", None)
    if obj_val is not None and (math.isinf(obj_val) or math.isnan(obj_val)):
        obj_val = None  # or use a string like "Infinity"

    return ProblemResult(
        status=result.get("status", "unknown"),
        objective_value=obj_val,
        solution=result.get("solution", [])
    )