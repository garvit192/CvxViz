from solver.solve import solve_lp

def test_simple_lp_max():
    result = solve_lp(c=[3, 4], A=[[1, 1], [-1, 0], [0, -1]], b=[5, 0, 0], sense="maximize")
    assert result["status"] == "optimal"
    assert abs(result["objective_value"] - 20) < 1e-3

def test_simple_lp_min():
    result = solve_lp(c=[1, 2], A=[[1, 1]], b=[5], bounds=[(0, None), (0, None)], sense="minimize")
    assert result["status"] == "optimal"
    assert abs(result["objective_value"]) < 1e-3

def test_qp_min():
    result = solve_lp(
        c=[0, 0],
        Q=[[2, 0], [0, 2]],
        A=[[1, 1], [-1, 0], [0, -1]],
        b=[5, 0, 0],
        sense="minimize"
    )
    assert result["status"] == "optimal"
    assert abs(result["objective_value"] - 0) < 1e-3

def test_equality_constraint():
    result = solve_lp(
        c=[1, 1],
        A_eq=[[1, -1]],
        b_eq=[0],
        bounds=[(0, 2), (0, 2)],
        sense="minimize"
    )
    assert result["status"] == "optimal"
    assert abs(result["objective_value"]) < 1e-3

def test_unbounded():
    result = solve_lp(c=[1], sense="maximize")
    assert result["status"] == "unbounded"

def test_infeasible():
    result = solve_lp(c=[1], A=[[1]], b=[-1], bounds=[(0, None)], sense="minimize")
    assert result["status"] == "infeasible"

def test_tight_bounds():
    result = solve_lp(c=[5, 5], bounds=[(1, 1), (2, 2)], sense="minimize")
    assert result["status"] == "optimal"
    assert abs(result["objective_value"] - 15) < 1e-3

def test_redundant_constraints():
    result = solve_lp(c=[1, 1], A=[[1, 1], [2, 2]], b=[5, 10], sense="minimize", bounds=[(0, None), (0, None)])
    assert result["status"] == "optimal"
    assert abs(result["objective_value"]) < 1e-3

def test_degenerate_lp():
    result = solve_lp(c=[1, 1, 1], A=[[1, 1, 1], [2, 2, 2]], b=[5, 10], sense="minimize", bounds=[(0, None), (0, None), (0, None)])
    assert result["status"] == "optimal"
    assert abs(result["objective_value"]) < 1e-3

def test_qp_with_linear_term():
    result = solve_lp(
        c=[1, 2],
        Q=[[1, 0], [0, 1]],
        A=[[1, 1]],
        b=[3],
        bounds=[(0, 2), (0, 2)],
        sense="minimize"
    )
    assert result["status"] == "optimal"
    assert result["solution"] is not None
