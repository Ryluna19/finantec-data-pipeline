from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

@pytest.fixture(autouse=True)
def isolate_database_backend(monkeypatch):
    """Impede que testes utilizem o banco remoto configurado no ambiente."""
    monkeypatch.setenv(
        "FINANTEC_DATABASE_BACKEND",
        "sqlite",
    )
    monkeypatch.delenv(
        "TURSO_DATABASE_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "TURSO_AUTH_TOKEN",
        raising=False,
    )