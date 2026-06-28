import time

from fastapi import FastAPI, HTTPException

from agent.claims_agent import process_claim
from app.schemas import AgentProcessRequest, AgentProcessResponse

app = FastAPI(
    title="Claims Processing Agent",
    description=(
        "LangGraph agent orchestrating Medicare classifier, reserve forecaster, "
        "and policy RAG. Claim history via MCP store (SQLite dev / Oracle prod)."
    ),
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "claims-processing-agent"}


@app.post("/agent/process", response_model=AgentProcessResponse)
def agent_process(request: AgentProcessRequest):
    try:
        return process_claim(request.claim_id, request.question)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent failed: {exc}") from exc
