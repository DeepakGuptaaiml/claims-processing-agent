"""LangGraph workflow: fetch claim → ML tools → policy → synthesize."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.graph.state import AgentState
from agent.tools.claim_store_tool import fetch_claim_context
from agent.tools.http_tools import ask_policy, predict_medicare, predict_reserve
from agent.tools.payloads import medicare_payload_from_summary, reserve_payload_from_context


def _step(name: str, steps: list[str]) -> list[str]:
    return steps + [name]


def fetch_claim_node(state: AgentState) -> AgentState:
    steps = state.get("reasoning_steps") or []
    try:
        context = fetch_claim_context(state["claim_id"])
        summary = context["claim_summary"]
        reserve_ctx = context["reserve_context"]
        return {
            **state,
            "claim_context": context,
            "medicare_payload": medicare_payload_from_summary(summary),
            "reserve_payload": reserve_payload_from_context(reserve_ctx),
            "reasoning_steps": _step("fetch_claim_context", steps),
            "error": None,
        }
    except Exception as exc:
        return {**state, "error": str(exc), "reasoning_steps": _step("fetch_claim_context_failed", steps)}


def medicare_node(state: AgentState) -> AgentState:
    steps = state.get("reasoning_steps") or []
    if state.get("error"):
        return state
    try:
        result = predict_medicare(state["medicare_payload"])
        return {
            **state,
            "medicare_result": result,
            "reasoning_steps": _step("check_medicare_reportability", steps),
        }
    except Exception as exc:
        return {
            **state,
            "medicare_result": {"error": str(exc)},
            "reasoning_steps": _step("check_medicare_failed", steps),
        }


def reserve_node(state: AgentState) -> AgentState:
    steps = state.get("reasoning_steps") or []
    if state.get("error"):
        return state
    try:
        result = predict_reserve(state["reserve_payload"])
        return {
            **state,
            "reserve_result": result,
            "reasoning_steps": _step("predict_reserve", steps),
        }
    except Exception as exc:
        return {
            **state,
            "reserve_result": {"error": str(exc)},
            "reasoning_steps": _step("predict_reserve_failed", steps),
        }


def policy_node(state: AgentState) -> AgentState:
    steps = state.get("reasoning_steps") or []
    if state.get("error"):
        return state
    policy_question = (
        f"{state['question']} "
        f"Context: WC claim, ORM threshold met={state['medicare_payload'].get('orm_threshold_met')}."
    )
    try:
        result = ask_policy(policy_question)
        return {
            **state,
            "policy_result": result,
            "reasoning_steps": _step("search_policy_context", steps),
        }
    except Exception as exc:
        return {
            **state,
            "policy_result": {"error": str(exc), "answer": None, "sources": []},
            "reasoning_steps": _step("search_policy_failed", steps),
        }


def synthesize_node(state: AgentState) -> AgentState:
    steps = state.get("reasoning_steps") or []
    if state.get("error"):
        recommendation = f"Unable to process claim: {state['error']}"
        return {**state, "recommendation": recommendation, "reasoning_steps": _step("synthesize", steps)}

    med = state.get("medicare_result") or {}
    res = state.get("reserve_result") or {}
    pol = state.get("policy_result") or {}

    med_label = med.get("label", "unknown")
    med_prob = med.get("probability", "N/A")
    reserve_amt = res.get("total_reserve", "N/A")
    policy_snippet = (pol.get("answer") or "No policy context available.")[:500]
    sources = pol.get("sources") or []

    recommendation = (
        f"Claim {state['claim_id']}: Medicare assessment is **{med_label}** "
        f"(probability {med_prob}). Recommended reserve: **{reserve_amt}**. "
        f"Policy context: {policy_snippet}"
    )
    if sources:
        recommendation += f" Sources: {', '.join(sources)}."

    return {
        **state,
        "recommendation": recommendation,
        "reasoning_steps": _step("synthesize_recommendation", steps),
    }


def build_workflow():
    graph = StateGraph(AgentState)
    graph.add_node("fetch_claim", fetch_claim_node)
    graph.add_node("check_medicare", medicare_node)
    graph.add_node("predict_reserve", reserve_node)
    graph.add_node("search_policy", policy_node)
    graph.add_node("synthesize", synthesize_node)

    graph.add_edge(START, "fetch_claim")
    graph.add_edge("fetch_claim", "check_medicare")
    graph.add_edge("check_medicare", "predict_reserve")
    graph.add_edge("predict_reserve", "search_policy")
    graph.add_edge("search_policy", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_workflow()
    return _compiled_graph


def run_claims_agent(claim_id: str, question: str) -> AgentState:
    graph = get_graph()
    initial: AgentState = {
        "claim_id": claim_id,
        "question": question,
        "reasoning_steps": [],
    }
    return graph.invoke(initial)
