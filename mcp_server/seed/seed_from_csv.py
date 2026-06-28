#!/usr/bin/env python3
"""Seed SQLite claim-history DB from claims_data.csv (Oracle view contract)."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.config import get_claims_csv_path, get_sqlite_path  # noqa: E402
from mcp_server.seed.features import engineer_claim_frames  # noqa: E402


def _load_schema(conn: sqlite3.Connection) -> None:
    schema_path = ROOT / "mcp_server" / "schema" / "sqlite_views.sql"
    conn.executescript(schema_path.read_text(encoding="utf-8"))


def _insert_df(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> None:
    df.to_sql(table, conn, if_exists="replace", index=False)


def main() -> None:
    csv_path = get_claims_csv_path()
    db_path = get_sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"claims_data.csv not found at {csv_path}. "
            "Set CLAIMS_CSV_PATH or place file in ../medicare_classifier/data/"
        )

    raw = pd.read_csv(csv_path)
    claim_summary, payment_summary, reserve_context, claimant = engineer_claim_frames(raw)

    conn = sqlite3.connect(db_path)
    try:
        _load_schema(conn)
        _insert_df(conn, "v_claim_summary_for_ai", claim_summary)
        _insert_df(conn, "v_payment_summary_for_ai", payment_summary)
        _insert_df(conn, "v_reserve_context_for_ai", reserve_context)
        _insert_df(conn, "v_claimant_context_for_ai", claimant)
        conn.commit()
    finally:
        conn.close()

    print(f"Seeded {len(claim_summary)} claims → {db_path}")


if __name__ == "__main__":
    main()
