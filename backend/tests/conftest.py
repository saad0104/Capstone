import os
import tempfile

import pytest

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ.setdefault("LLM_PROVIDER", "gemini")  # value irrelevant, provider is mocked in tests

from backend.app import create_app  # noqa: E402
from backend.db import engine  # noqa: E402
from backend.models import Base  # noqa: E402


@pytest.fixture
def app():
    Base.metadata.create_all(bind=engine)
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    yield flask_app
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app):
    return app.test_client()


class FakeLLM:
    def summarize(self, text):
        return {
            "summary": "Fake summary",
            "threat_type": "ransomware",
            "severity": "High",
            "recommended_action": "Patch now",
            "processing_ms": 5,
        }


@pytest.fixture
def mock_llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr("backend.app.get_llm_service", lambda: fake)
    return fake


@pytest.fixture(scope="session", autouse=True)
def _cleanup_temp_db():
    yield
    if os.path.exists(_db_path):
        os.remove(_db_path)
