"""Examiner-facing Streamlit UI for the Claims Processing Agent."""

from __future__ import annotations

import os
import re

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8002").rstrip("/")

SAMPLE_CLAIM_IDS = [
    "1000000.639",
    "1000001.38",
    "1000054.19",
]

SAMPLE_QUESTIONS = [
    "Should this claim be reported to Medicare?",
    "What reserve should I set for this claim?",
    "Does ORM reporting apply to this claim?",
]

st.set_page_config(
    page_title="Claims Processing Agent",
    page_icon="🧭",
    layout="wide",
)

st.title("Claims Processing Agent")
st.caption(
    "LangGraph orchestration: claim context → Medicare ML → reserve forecast → policy guidance"
)


def check_health() -> tuple[bool, str]:
    try:
        response = requests.get(f"{API_URL}/health", timeout=15)
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        body = response.json()
        if body.get("status") != "ok":
            return False, str(body)
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


def _strip_policy_prefix(text: str) -> str:
    cleaned = re.sub(r"^Based on policy documents:\s*", "", text or "", flags=re.IGNORECASE)
    return cleaned.strip()


def _policy_summary(text: str, max_chars: int = 480) -> str:
    cleaned = _strip_policy_prefix(text)
    if not cleaned:
        return "No policy guidance retrieved."
    paragraph = cleaned.split("\n\n")[0].strip()
    if len(paragraph) > max_chars:
        return paragraph[: max_chars - 3].rstrip() + "..."
    return paragraph


def _recommended_action(medicare: dict, reserve: dict) -> str:
    label = (medicare.get("label") or "").lower()
    reserve_err = reserve.get("error")
    reserve_amt = reserve.get("total_reserve")

    if "reportable" in label and "not" not in label:
        action = "Initiate Medicare Section 111 reporting workflow and validate ORM/TPOC thresholds."
    elif reserve_err:
        action = "Review Medicare determination first; reserve forecast unavailable — retry or set manual reserve."
    else:
        action = "No Medicare reporting required based on model assessment; confirm with policy rules below."

    if reserve_amt is not None and not reserve_err:
        action += f" Set case reserve to ${reserve_amt:,.0f}."
    return action


def _format_reserve(reserve: dict) -> str:
    if reserve.get("error"):
        return "Unavailable (downstream timeout — retry in a moment)"
    amount = reserve.get("total_reserve")
    if amount is None:
        return "Not available"
    return f"${amount:,.0f}"


def set_sample_claim(claim_id: str) -> None:
    st.session_state["claim_id"] = claim_id


def set_sample_question(question: str) -> None:
    st.session_state["examiner_question"] = question


with st.sidebar:
    st.header("Agent API")
    st.caption(f"**API_URL:** `{API_URL}`")
    healthy, detail = check_health()
    if healthy:
        st.success("Connected to agent API")
    else:
        st.error("Agent API unavailable")
        if detail:
            st.caption(detail)

    st.divider()
    st.markdown("**Sample claim IDs**")
    for claim_id in SAMPLE_CLAIM_IDS:
        st.button(
            claim_id,
            key=f"sample_claim_{claim_id}",
            use_container_width=True,
            on_click=set_sample_claim,
            args=(claim_id,),
        )


if "claim_id" not in st.session_state:
    st.session_state["claim_id"] = SAMPLE_CLAIM_IDS[0]
if "examiner_question" not in st.session_state:
    st.session_state["examiner_question"] = SAMPLE_QUESTIONS[0]

col_input, col_samples = st.columns([2, 1])

with col_input:
    claim_id = st.text_input("Claim ID", key="claim_id")
    question = st.text_area(
        "Examiner question",
        key="examiner_question",
        height=80,
        placeholder="e.g. Should this claim be reported to Medicare?",
    )

with col_samples:
    st.markdown("**Quick questions**")
    for idx, sample_q in enumerate(SAMPLE_QUESTIONS):
        st.button(
            sample_q,
            key=f"sample_q_{idx}",
            use_container_width=True,
            on_click=set_sample_question,
            args=(sample_q,),
        )

process = st.button("Process claim", type="primary", use_container_width=True)

if process:
    if not claim_id.strip():
        st.warning("Enter a claim ID.")
    elif not question.strip():
        st.warning("Enter a question for the agent.")
    elif not healthy:
        st.error("Agent API is not reachable. Check API_URL and deployment status.")
    else:
        with st.spinner("Running LangGraph workflow (claim context → ML → policy)..."):
            try:
                response = requests.post(
                    f"{API_URL}/agent/process",
                    json={"claim_id": claim_id.strip(), "question": question.strip()},
                    timeout=120,
                )
                if response.status_code != 200:
                    st.error(f"Agent returned HTTP {response.status_code}")
                    st.code(response.text)
                else:
                    st.session_state["agent_result"] = response.json()
            except requests.RequestException as exc:
                st.error(f"Request failed: {exc}")

result = st.session_state.get("agent_result")

if result and result.get("claim_id") == claim_id.strip():
    med = result.get("medicare") or {}
    res = result.get("reserve") or {}
    pol = result.get("policy") or {}

    st.divider()
    st.subheader("Examiner summary")

    dec_col, res_col, time_col = st.columns(3)
    label = med.get("label") or "Unknown"
    is_reportable = med.get("is_medicare_reportable") == 1

    with dec_col:
        st.metric("Medicare determination", label)
        prob = med.get("probability")
        if prob is not None:
            st.caption(f"Model confidence: {prob:.0%}")

    with res_col:
        st.metric("Recommended reserve", _format_reserve(res))

    with time_col:
        ms = result.get("processing_time_ms", 0)
        st.metric("Processing time", f"{ms / 1000:.1f}s")

    if is_reportable:
        st.error("Action required: Medicare reportable — verify CMS reporting rules.")
    elif med.get("error"):
        st.warning(f"Medicare check issue: {med['error']}")
    else:
        st.success("No Medicare reporting indicated by the classifier.")

    st.markdown("**Recommended action**")
    st.info(_recommended_action(med, res))

    st.markdown("**Policy guidance**")
    policy_text = pol.get("answer") or ""
    st.write(_policy_summary(policy_text))
    if pol.get("sources"):
        st.caption(f"Sources: {', '.join(pol['sources'])}")

    if pol.get("error"):
        st.warning(f"Policy retrieval note: {pol['error']}")

    with st.expander("Audit trail (LangGraph reasoning steps)"):
        for step in result.get("reasoning_steps") or []:
            st.markdown(f"- `{step}`")

    with st.expander("Technical details (for engineering / compliance)"):
        st.json(result)

st.markdown("---")
st.caption(
    "Examiner UI → FastAPI `/agent/process` → LangGraph agent orchestrating Medicare, reserve, and policy RAG"
)
