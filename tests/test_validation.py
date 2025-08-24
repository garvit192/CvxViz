from starlette.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_bad_shapes_422():
    payload = {"c":[1,2,3], "A":[[1,1]], "b":[1], "sense":"minimize"}
    # unique IP so we don't share the 'testclient' limiter bucket
    headers = {"X-API-Key": settings.API_TOKEN, "X-Forwarded-For": "9.9.9.9"}
    r = client.post(f"{settings.API_V1_STR}/solve", json=payload, headers=headers)
    assert r.status_code == 422
    assert "detail" in r.json()
