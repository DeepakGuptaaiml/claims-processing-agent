"""HTTP tools calling existing ML APIs."""

from __future__ import annotations

import httpx

from app.config import get_http_timeouts, get_medicare_api_url, get_reserve_api_url

_TIMEOUTS = get_http_timeouts()


def predict_medicare(payload: dict, timeout: float | None = None) -> dict:
    url = f"{get_medicare_api_url()}/predict"
    response = httpx.post(url, json=payload, timeout=timeout or _TIMEOUTS["medicare"])
    response.raise_for_status()
    return response.json()


def predict_reserve(payload: dict, timeout: float | None = None) -> dict:
    url = f"{get_reserve_api_url()}/predict"
    response = httpx.post(url, json=payload, timeout=timeout or _TIMEOUTS["reserve"])
    response.raise_for_status()
    return response.json()


def ask_policy(question: str, timeout: float | None = None) -> dict:
    url = f"{get_medicare_api_url()}/ask"
    response = httpx.post(url, json={"question": question}, timeout=timeout or _TIMEOUTS["policy"])
    response.raise_for_status()
    return response.json()

