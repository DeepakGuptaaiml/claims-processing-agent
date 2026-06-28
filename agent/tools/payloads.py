"""Normalize SQLite view rows into downstream API payloads."""

from __future__ import annotations

import math


def _int(value, default: int = 0) -> int:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    return int(value)


def _float(value, default: float = 0.0) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    return float(value)


def _optional_float(value) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return float(value)


def _str(value, default: str = "") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    return str(value)


def medicare_payload_from_summary(summary: dict) -> dict:
    return {
        "data_set": _str(summary.get("data_set")),
        "pay_cat": _str(summary.get("pay_cat")),
        "pay_code": _int(summary.get("pay_code")),
        "pay_type": _str(summary.get("pay_type")),
        "paid_1": _float(summary.get("paid_1")),
        "paid_3": _float(summary.get("paid_3")),
        "amount": max(_float(summary.get("amount"), 1.0), 0.01),
        "proc_unit": _int(summary.get("proc_unit")),
        "cont_num": _int(summary.get("cont_num")),
        "claim_open": _int(summary.get("claim_open")),
        "date_v1m_xmit_flag": _int(summary.get("date_v1m_xmit_flag")),
        "is_us_claimant": _int(summary.get("is_us_claimant"), 1),
        "orm_threshold_met": _int(summary.get("orm_threshold_met")),
        "tpoc_threshold_met": _int(summary.get("tpoc_threshold_met")),
        "is_wc": _int(summary.get("is_wc")),
        "pay_code_bucket": _str(summary.get("pay_code_bucket"), "OTHER"),
        "is_excluded_coverage": _int(summary.get("is_excluded_coverage")),
        "is_excluded_line": _int(summary.get("is_excluded_line")),
        "days_open": _float(summary.get("days_open")),
        "age_at_event": _float(summary.get("age_at_event")),
    }


def reserve_payload_from_context(context: dict) -> dict:
    state = _str(context.get("state"), "PA")[:2].upper()
    return {
        "patient_age": _float(context.get("patient_age")),
        "diagnosis_code": _str(context.get("diagnosis_code"), "UNKNOWN"),
        "procedure_code": _str(context.get("procedure_code"), "UNKNOWN"),
        "admission_type": _str(context.get("admission_type"), "MO"),
        "days_in_hospital": _optional_float(context.get("days_in_hospital")),
        "provider_type": _str(context.get("provider_type"), "0"),
        "injury_severity": _str(context.get("injury_severity"), "UNKNOWN"),
        "num_previous_claims": _int(context.get("num_previous_claims")),
        "avg_previous_reserve": _float(context.get("avg_previous_reserve")),
        "initial_estimate": _float(context.get("initial_estimate")),
        "reported_delay_days": _optional_float(context.get("reported_delay_days")),
        "state": state if len(state) == 2 else "PA",
    }
