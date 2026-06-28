"""SQLite implementation of Oracle-shaped claim views (dev)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mcp_server.stores.base import ClaimHistoryStore


class SqliteClaimStore(ClaimHistoryStore):
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        if not db_path.exists():
            raise FileNotFoundError(
                f"SQLite DB not found: {db_path}. Run: python mcp_server/seed/seed_from_csv.py"
            )

    def _fetch_one(self, table: str, claim_id: str) -> dict:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                f"SELECT * FROM {table} WHERE claim_id = ?",
                (claim_id,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            raise KeyError(f"claim_id not found: {claim_id}")
        return dict(row)

    def get_claim_summary(self, claim_id: str) -> dict:
        return self._fetch_one("v_claim_summary_for_ai", claim_id)

    def get_payment_summary(self, claim_id: str) -> dict:
        return self._fetch_one("v_payment_summary_for_ai", claim_id)

    def get_reserve_context(self, claim_id: str) -> dict:
        return self._fetch_one("v_reserve_context_for_ai", claim_id)

    def get_claimant_context(self, claim_id: str) -> dict:
        return self._fetch_one("v_claimant_context_for_ai", claim_id)
