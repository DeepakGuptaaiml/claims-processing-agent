"""Claim history store adapters — swap SQLite (dev) for Oracle views (prod)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ClaimHistoryStore(ABC):
    """Read-only claim history — mirrors MCP tool contracts."""

    @abstractmethod
    def get_claim_summary(self, claim_id: str) -> dict:
        """Medicare classifier features (V_CLAIM_SUMMARY_FOR_AI)."""

    @abstractmethod
    def get_payment_summary(self, claim_id: str) -> dict:
        """Payment amounts (V_PAYMENT_SUMMARY_FOR_AI)."""

    @abstractmethod
    def get_reserve_context(self, claim_id: str) -> dict:
        """Reserve model features (V_RESERVE_CONTEXT_FOR_AI)."""

    @abstractmethod
    def get_claimant_context(self, claim_id: str) -> dict:
        """Aggregated claimant history — no raw PHI (V_CLAIMANT_CONTEXT_FOR_AI)."""

    def get_full_claim_context(self, claim_id: str) -> dict:
        return {
            "claim_id": claim_id,
            "claim_summary": self.get_claim_summary(claim_id),
            "payment_summary": self.get_payment_summary(claim_id),
            "reserve_context": self.get_reserve_context(claim_id),
            "claimant_context": self.get_claimant_context(claim_id),
        }
