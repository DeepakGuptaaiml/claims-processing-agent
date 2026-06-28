"""Run LangGraph claims processing agent."""

from __future__ import annotations

import time

from agent.graph.workflow import run_claims_agent
from app.schemas import (
    AgentProcessResponse,
    MedicareToolResult,
    PolicyToolResult,
    ReserveToolResult,
)


def process_claim(claim_id: str, question: str) -> AgentProcessResponse:
    start = time.time()
    state = run_claims_agent(claim_id=claim_id, question=question)
    elapsed_ms = (time.time() - start) * 1000

    med = state.get("medicare_result") or {}
    res = state.get("reserve_result") or {}
    pol = state.get("policy_result") or {}

    return AgentProcessResponse(
        claim_id=claim_id,
        question=question,
        recommendation=state.get("recommendation") or "",
        medicare=MedicareToolResult(
            is_medicare_reportable=med.get("is_medicare_reportable"),
            probability=med.get("probability"),
            label=med.get("label"),
            model_name=med.get("model_name"),
            error=med.get("error"),
        ),
        reserve=ReserveToolResult(
            total_reserve=res.get("total_reserve"),
            model_name=res.get("model_name"),
            target=res.get("target"),
            error=res.get("error"),
        ),
        policy=PolicyToolResult(
            answer=pol.get("answer"),
            sources=pol.get("sources") or [],
            error=pol.get("error"),
        ),
        reasoning_steps=state.get("reasoning_steps") or [],
        processing_time_ms=round(elapsed_ms, 2),
    )
