"""Tests for claims-processing-agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from mcp_server.stores.factory import reset_claim_store

SAMPLE_CLAIM_CONTEXT = {
    "claim_id": "1000000.639",
    "claim_summary": {
        "claim_id": "1000000.639",
        "data_set": "WC",
        "pay_cat": "CL",
        "pay_code": 100,
        "pay_type": "HIS",
        "paid_1": 40290.96,
        "paid_3": 69813.94,
        "amount": 3468.48,
        "proc_unit": 29,
        "cont_num": 5013,
        "claim_open": 1,
        "date_v1m_xmit_flag": 1,
        "is_us_claimant": 1,
        "orm_threshold_met": 1,
        "tpoc_threshold_met": 1,
        "is_wc": 1,
        "pay_code_bucket": "TPOC",
        "is_excluded_coverage": 1,
        "is_excluded_line": 0,
        "days_open": 0.0,
        "age_at_event": 68.0,
    },
    "payment_summary": {
        "claim_id": "1000000.639",
        "paid_1": 40290.96,
        "paid_3": 69813.94,
        "amount": 3468.48,
        "pay_code": 100,
        "pay_cat": "CL",
    },
    "reserve_context": {
        "claim_id": "1000000.639",
        "patient_age": 68.0,
        "diagnosis_code": "SPRAIN",
        "procedure_code": "KNEE",
        "admission_type": "IO",
        "days_in_hospital": 120.0,
        "provider_type": "29",
        "injury_severity": "STRAIN",
        "num_previous_claims": 0,
        "avg_previous_reserve": 0.0,
        "initial_estimate": 3468.48,
        "reported_delay_days": 53.0,
        "state": "PA",
    },
    "claimant_context": {
        "claim_id": "1000000.639",
        "claimant_key": "abc123",
        "num_previous_claims": 0,
        "avg_previous_reserve": 0.0,
    },
}


@pytest.fixture(autouse=True)
def reset_store():
    reset_claim_store()
    yield
    reset_claim_store()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("agent.graph.workflow.fetch_claim_context")
@patch("agent.graph.workflow.predict_medicare")
@patch("agent.graph.workflow.predict_reserve")
@patch("agent.graph.workflow.ask_policy")
def test_agent_process(mock_policy, mock_reserve, mock_medicare, mock_fetch, client):
    mock_fetch.return_value = SAMPLE_CLAIM_CONTEXT
    mock_medicare.return_value = {
        "is_medicare_reportable": 1,
        "probability": 0.91,
        "label": "Reportable",
        "model_name": "AdaBoost Undersampled",
        "target": "is_medicare_reportable",
    }
    mock_reserve.return_value = {
        "total_reserve": 12500.0,
        "model_name": "GradientBoosting",
        "target": "total_reserve",
    }
    mock_policy.return_value = {
        "answer": "ORM reporting applies when medical payments exceed threshold.",
        "sources": ["CMS Section 111 Guide"],
    }

    response = client.post(
        "/agent/process",
        json={"claim_id": "1000000.639", "question": "Should I report this claim?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["claim_id"] == "1000000.639"
    assert body["medicare"]["label"] == "Reportable"
    assert body["reserve"]["total_reserve"] == 12500.0
    assert "fetch_claim_context" in body["reasoning_steps"]
    assert body["processing_time_ms"] >= 0
    mock_fetch.assert_called_once_with("1000000.639")


@patch("agent.graph.workflow.fetch_claim_context")
def test_agent_process_unknown_claim(mock_fetch, client):
    mock_fetch.side_effect = KeyError("claim_id not found: does-not-exist")

    response = client.post(
        "/agent/process",
        json={"claim_id": "does-not-exist", "question": "test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "Unable to process claim" in body["recommendation"]
