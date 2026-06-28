"""Factory for claim history store — swap backend via STORE_BACKEND env."""

from __future__ import annotations

import os

from app.config import get_oracle_config, get_sqlite_path
from mcp_server.stores.base import ClaimHistoryStore
from mcp_server.stores.oracle_store import OracleClaimStore
from mcp_server.stores.sqlite_store import SqliteClaimStore

_store: ClaimHistoryStore | None = None


def get_claim_store() -> ClaimHistoryStore:
    global _store
    if _store is not None:
        return _store

    backend = os.getenv("STORE_BACKEND", "sqlite").lower()
    if backend == "sqlite":
        _store = SqliteClaimStore(get_sqlite_path())
    elif backend == "oracle":
        cfg = get_oracle_config()
        _store = OracleClaimStore(cfg["dsn"], cfg["user"], cfg["password"])
    else:
        raise ValueError(f"Unknown STORE_BACKEND: {backend}")
    return _store


def reset_claim_store() -> None:
    """Test helper."""
    global _store
    _store = None
