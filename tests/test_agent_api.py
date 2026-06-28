"""Tests for claims-processing-agent."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from mcp_server.stores.factory import reset_claim_store


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


@patch("agent.graph.workflow.predict_medicare")
@patch("agent.graph.workflow.predict_reserve")
@patch("agent.graph.workflow.ask_policy")
def test_agent_process(mock_policy, mock_reserve, mock_medicare, client):
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


def test_agent_process_unknown_claim(client):
    response = client.post(
        "/agent/process",
        json={"claim_id": "does-not-exist", "question": "test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "Unable to process claim" in body["recommendation"]
