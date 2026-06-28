"""Pytest configuration — ensure repo root is on PYTHONPATH and claim DB exists."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "mcp_server" / "data" / "claims_ai.db"
CSV_PATH = ROOT / "data" / "claims_data.csv"


@pytest.fixture(scope="session", autouse=True)
def seed_claim_store():
    """Seed claim store for store integration tests (CI has no pre-built .db)."""
    if DB_PATH.exists():
        return
    if not CSV_PATH.exists():
        pytest.fail(f"Missing seed data: {CSV_PATH}")
    subprocess.run(
        [sys.executable, str(ROOT / "mcp_server" / "seed" / "seed_from_csv.py")],
        check=True,
        cwd=str(ROOT),
    )
