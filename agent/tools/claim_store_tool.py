"""Fetch claim context from MCP-backed store (SQLite dev / Oracle prod)."""

from __future__ import annotations

from mcp_server.stores.factory import get_claim_store


def fetch_claim_context(claim_id: str) -> dict:
    store = get_claim_store()
    return store.get_full_claim_context(claim_id)
