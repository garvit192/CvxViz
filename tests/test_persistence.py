from starlette.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.persistence import spec_hash
from app.models.schema import ProblemInput

client = TestClient(app)

def _hdr(ip='11.0.0.1'):
    return {'X-API-Key': settings.API_TOKEN, 'X-Forwarded-For': ip, 'Content-Type': 'application/json'}

def _payload():
    return {'c':[1,2], 'A':[[1,1]], 'b':[5], 'bounds':[[0,None],[0,None]], 'sense':'minimize'}

def _count_for_hash(spec_h):
    r = client.get(f"{settings.API_V1_STR}/history?limit=500", headers=_hdr('11.0.0.2'))
    assert r.status_code == 200
    items = r.json().get('items', [])
    return sum(1 for it in items if it.get('spec_hash') == spec_h)

def test_persist_and_history_smoke():
    p = ProblemInput(**_payload())
    h = spec_hash(p)
    before = _count_for_hash(h)

    r = client.post(f"{settings.API_V1_STR}/solve", json=_payload(), headers=_hdr('11.0.0.3'))
    assert r.status_code < 400

    after = _count_for_hash(h)
    assert after == before + 1

def test_cache_hit_does_not_create_new_row():
    p = ProblemInput(**_payload())
    h = spec_hash(p)
    before = _count_for_hash(h)

    # first call
    r1 = client.post(f"{settings.API_V1_STR}/solve", json=_payload(), headers=_hdr('11.0.0.4'))
    assert r1.status_code < 400

    # second call (same payload) should be served from cache
    r2 = client.post(f"{settings.API_V1_STR}/solve?use_cache=true", json=_payload(), headers=_hdr('11.0.0.5'))
    assert r2.status_code < 400

    after = _count_for_hash(h)
    # only the first call should have persisted a new row
    assert after == before + 1

def test_bypass_cache_creates_new_solution():
    p = ProblemInput(**_payload())
    h = spec_hash(p)
    before = _count_for_hash(h)

    # force bypass
    r = client.post(f"{settings.API_V1_STR}/solve?use_cache=false", json=_payload(), headers=_hdr('11.0.0.6'))
    assert r.status_code < 400

    after = _count_for_hash(h)
    assert after == before + 1
