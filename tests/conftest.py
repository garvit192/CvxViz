# tests/conftest.py
import pytest
from app.services.persistence import create_tables

@pytest.fixture(scope="session", autouse=True)
def _db_schema():
    create_tables()
    yield
