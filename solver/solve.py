import cvxpy as cp
import numpy as np

def solve_lp(c, A=None, b=None, Q=None, bounds=None, A_eq=None, b_eq=None, sense="minimize"):
    """
    Solve a convex optimization problem:
    
        minimize or maximize: (1/2)xᵀQx + cᵀx
        subject to:
            Ax ≤ b
            A_eq x = b_eq
            bounds on variables
    
    Parameters:
        c      : Linear cost vector
        A, b   : Inequality constraints (Ax ≤ b)
        Q      : Quadratic matrix for QP
        bounds : List of (lb, ub) tuples for each variable
        A_eq, b_eq : Equality constraints (A_eq x = b_eq)
        sense  : "minimize" or "maximize"
    
    Returns:
        Dict with status, objective_value, and solution
    """
    c = np.array(c)
    n = len(c)
    x = cp.Variable(n)

    # Objective
    objective_expr = c @ x
    if Q is not None:
        Q = np.array(Q)
        objective_expr = 0.5 * cp.quad_form(x, Q) + objective_expr

    objective = cp.Minimize(objective_expr) if sense == "minimize" else cp.Maximize(objective_expr)

    constraints = []

    # Inequality
    if A is not None and b is not None:
        A = np.array(A)
        b = np.array(b)
        constraints.append(A @ x <= b)

    # Equality
    if A_eq is not None and b_eq is not None:
        A_eq = np.array(A_eq)
        b_eq = np.array(b_eq)
        constraints.append(A_eq @ x == b_eq)

    # Bounds
    if bounds is not None:
        for i, (lb, ub) in enumerate(bounds):
            if lb is not None:
                constraints.append(x[i] >= lb)
            if ub is not None:
                constraints.append(x[i] <= ub)

    prob = cp.Problem(objective, constraints)

    try:
        prob.solve()
    except cp.SolverError as e:
        return {
            "status": "solver_error",
            "objective_value": None,
            "solution": None,
            "error": str(e)
        }
    

    return {
        "status": prob.status,
        "objective_value": prob.value,
        "solution": x.value.tolist() if x.value is not None else None
    }