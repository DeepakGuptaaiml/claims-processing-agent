"""Store and payload unit tests."""

from __future__ import annotations

from pathlib import Path

from agent.tools.payloads import medicare_payload_from_summary, reserve_payload_from_context
from mcp_server.stores.factory import get_claim_store, reset_claim_store
from mcp_server.stores.sqlite_store import SqliteClaimStore

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "mcp_server" / "data" / "claims_ai.db"


def setup_function():
    reset_claim_store()


def teardown_function():
    reset_claim_store()


def test_sqlite_store_fetch():
    store = SqliteClaimStore(DB_PATH)
    summary = store.get_claim_summary("1000000.639")
    assert summary["data_set"] == "WC"
    assert summary["orm_threshold_met"] == 1


def test_medicare_payload_types():
    store = get_claim_store()
    summary = store.get_claim_summary("1000000.639")
    payload = medicare_payload_from_summary(summary)
    assert isinstance(payload["pay_code"], int)
    assert isinstance(payload["amount"], float)
    assert payload["pay_code_bucket"] in {"ORM", "TPOC", "SETTLEMENT", "OTHER"}


def test_reserve_payload_state():
    store = get_claim_store()
    ctx = store.get_reserve_context("1000000.639")
    payload = reserve_payload_from_context(ctx)
    assert len(payload["state"]) == 2
