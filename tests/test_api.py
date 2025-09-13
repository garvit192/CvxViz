import math
import os
import pytest

from starlette.testclient import TestClient

# --- App + settings ---
from app.main import app
from app.core.config import settings

# --- Service-level imports (avoid rate-limit for many edge cases) ---
from app.services.solver_interface import solve_problem
from app.models.schema import ProblemInput
from app.core.errors import BadInput


# ----------------------
# API-LEVEL TESTS
# ----------------------

def test_health_ok():
    client = TestClient(app)
    r = client.get(f"{settings.API_V1_STR}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_missing_api_key_unauthorized():
    client = TestClient(app)
    r = client.post(f"{settings.API_V1_STR}/solve", json={"c": [1]})
    assert r.status_code in (401, 403)


def test_wrong_api_key_unauthorized():
    client = TestClient(app)
    r = client.post(
        f"{settings.API_V1_STR}/solve",
        headers={"X-API-Key": "not-the-token"},
        json={"c": [1, 2], "A": [[1, 1]], "b": [5], "sense": "minimize"},
    )
    assert r.status_code in (401, 403)


def test_valid_solve_minimize_simple():
    client = TestClient(app)
    r = client.post(
        f"{settings.API_V1_STR}/solve",
        headers={"X-API-Key": settings.API_TOKEN},
        json={"c": [1, 2], "A": [[1, 1]], "b": [5], "bounds": [[0, None], [0, None]], "sense": "minimize"},
    )
    assert r.status_code < 400, r.text
    body = r.json()
    assert "status" in body
    assert "objective_value" in body
    assert "solution" in body


def test_timeout_504(monkeypatch):
    client = TestClient(app)
    # Force extremely small timeout at runtime
    orig = settings.TIMEOUT_SECONDS
    try:
        settings.TIMEOUT_SECONDS = 0
        r = client.post(
            f"{settings.API_V1_STR}/solve",
            headers={"X-API-Key": settings.API_TOKEN},
            json={"c": [1, 2], "A": [[1, 1]], "b": [5], "sense": "minimize"},
        )
        assert r.status_code == 504, r.text
        assert "detail" in r.json()
    finally:
        settings.TIMEOUT_SECONDS = orig


def test_zz_rate_limit_429():
    client = TestClient(app)
    ok = 0
    hit_429 = 0
    # Call 12 times; limit is 10/minute
    for _ in range(12):
        r = client.post(
            f"{settings.API_V1_STR}/solve",
            headers={"X-API-Key": settings.API_TOKEN},
            json={"c": [1, 2], "A": [[1, 1]], "b": [5], "sense": "minimize"},
        )
        if r.status_code == 429:
            hit_429 += 1
        elif r.status_code < 400:
            ok += 1
    assert hit_429 >= 1, f"Expected at least one 429; got ok={ok}, 429={hit_429}"


# ----------------------
# SERVICE-LEVEL TESTS (edge cases without hitting rate limits)
# ----------------------

def test_service_missing_c_raises_badinput():
    with pytest.raises(BadInput):
        solve_problem(ProblemInput(c=[], sense="minimize"))


def test_service_mismatched_A_columns():
    p = ProblemInput(c=[1, 2, 3], A=[[1, 1]], b=[1], sense="minimize")
    with pytest.raises(BadInput):
        solve_problem(p)


def test_service_b_length_mismatch():
    p = ProblemInput(c=[1, 2], A=[[1, 1], [1, 0]], b=[1], sense="minimize")
    with pytest.raises(BadInput):
        solve_problem(p)


def test_service_bounds_length_mismatch():
    p = ProblemInput(c=[1, 2, 3], bounds=[(0, None), (0, None)], sense="minimize")
    with pytest.raises(BadInput):
        solve_problem(p)


def test_service_Q_not_square():
    p = ProblemInput(c=[1, 2], Q=[[1, 0, 0], [0, 1, 0]], sense="minimize")
    with pytest.raises(BadInput):
        solve_problem(p)


def test_service_none_in_c():
    p = ProblemInput(c=[1, None], sense="minimize")
    with pytest.raises(BadInput):
        solve_problem(p)


def test_service_none_in_b():
    p = ProblemInput(c=[1, 2], A=[[1, 1]], b=[None], sense="minimize")
    with pytest.raises(BadInput):
        solve_problem(p)


@pytest.mark.xfail(reason="Invalid 'sense' currently propagates from solver; ideal mapping to 422 not implemented yet.")
def test_service_invalid_sense_future_behavior():
    p = ProblemInput(c=[1, 2], A=[[1, 1]], b=[5], sense="not-a-sense")
    with pytest.raises(BadInput):
        solve_problem(p)