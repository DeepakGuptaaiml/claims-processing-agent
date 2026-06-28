from typing import TypedDict


class AgentState(TypedDict, total=False):
    claim_id: str
    question: str
    claim_context: dict
    medicare_payload: dict
    reserve_payload: dict
    medicare_result: dict
    reserve_result: dict
    policy_result: dict
    recommendation: str
    reasoning_steps: list[str]
    error: str | None
