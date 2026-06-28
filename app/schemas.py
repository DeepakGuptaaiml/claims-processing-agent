from pydantic import BaseModel, Field


class AgentProcessRequest(BaseModel):
    claim_id: str = Field(..., min_length=1, description="claim_uid from claims system")
    question: str = Field(
        default="Should this claim be reported to Medicare and what reserve should I set?",
        min_length=1,
    )


class MedicareToolResult(BaseModel):
    is_medicare_reportable: int | None = None
    probability: float | None = None
    label: str | None = None
    model_name: str | None = None
    error: str | None = None


class ReserveToolResult(BaseModel):
    total_reserve: float | None = None
    model_name: str | None = None
    target: str | None = None
    error: str | None = None


class PolicyToolResult(BaseModel):
    answer: str | None = None
    sources: list[str] = Field(default_factory=list)
    error: str | None = None


class AgentProcessResponse(BaseModel):
    claim_id: str
    question: str
    recommendation: str
    medicare: MedicareToolResult
    reserve: ReserveToolResult
    policy: PolicyToolResult
    reasoning_steps: list[str]
    processing_time_ms: float
