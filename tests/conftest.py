# tests/conftest.py
import os
import sys
import pytest

# Force SQLite for tests
os.environ["DATABASE_URL"] = ""
os.environ["JWT_SECRET"]   = "test-secret-key-for-testing-only"
os.environ["ENV"]          = "test"

# Add both root AND backend to path so 'routers' is found
ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, ROOT)
sys.path.insert(0, BACKEND)

from fastapi.testclient import TestClient
from database.connection import engine, init_db
from database.models import Base


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user():
    from auth.auth import signup, login
    signup("testuser", "test@analytiq.com", "testpass123")
    _, _, user = login("testuser", "testpass123")
    return user


@pytest.fixture
def sample_csv_path():
    import pandas as pd
    import numpy as np
    import tempfile

    df = pd.DataFrame({
        "tenure":           np.random.randint(1, 72, 200),
        "monthly_charges":  np.random.uniform(20, 100, 200).round(2),
        "contract":         np.random.choice(["Month-to-month", "One year", "Two year"], 200),
        "internet_service": np.random.choice(["DSL", "Fiber optic", "No"], 200),
        "churn":            np.random.choice(["Yes", "No"], 200, p=[0.27, 0.73]),
    })
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f, index=False)
        return f.name
