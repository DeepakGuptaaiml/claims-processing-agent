"""Oracle read-replica store (prod) — stub with documented view queries."""

from __future__ import annotations

from mcp_server.stores.base import ClaimHistoryStore

# Prod queries (parameterized only — never LLM-generated SQL):
# SELECT * FROM CLAIMS_AI_RO.V_CLAIM_SUMMARY_FOR_AI WHERE claim_id = :claim_id


class OracleClaimStore(ClaimHistoryStore):
    """Connect to Oracle via oracledb in production."""

    def __init__(self, dsn: str, user: str, password: str) -> None:
        self.dsn = dsn
        self.user = user
        self.password = password
        self._connection = None

    def _connect(self):
        try:
            import oracledb
        except ImportError as exc:
            raise RuntimeError(
                "Install oracledb for Oracle backend: pip install oracledb"
            ) from exc
        if self._connection is None:
            self._connection = oracledb.connect(
                user=self.user, password=self.password, dsn=self.dsn
            )
        return self._connection

    def _fetch_view(self, view_name: str, claim_id: str) -> dict:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM CLAIMS_AI_RO.{view_name} WHERE claim_id = :claim_id",
            {"claim_id": claim_id},
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"claim_id not found: {claim_id}")
        columns = [d[0].lower() for d in cursor.description]
        return dict(zip(columns, row))

    def get_claim_summary(self, claim_id: str) -> dict:
        return self._fetch_view("V_CLAIM_SUMMARY_FOR_AI", claim_id)

    def get_payment_summary(self, claim_id: str) -> dict:
        return self._fetch_view("V_PAYMENT_SUMMARY_FOR_AI", claim_id)

    def get_reserve_context(self, claim_id: str) -> dict:
        return self._fetch_view("V_RESERVE_CONTEXT_FOR_AI", claim_id)

    def get_claimant_context(self, claim_id: str) -> dict:
        return self._fetch_view("V_CLAIMANT_CONTEXT_FOR_AI", claim_id)
