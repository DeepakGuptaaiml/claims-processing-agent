"""Feature engineering mirroring medicare_classifier and claims-intelligence notebooks."""

from __future__ import annotations

import hashlib

import pandas as pd

MEDICARE_FEATURES = [
    "data_set",
    "pay_cat",
    "pay_code",
    "pay_type",
    "paid_1",
    "paid_3",
    "amount",
    "proc_unit",
    "cont_num",
    "claim_open",
    "date_v1m_xmit_flag",
    "is_us_claimant",
    "orm_threshold_met",
    "tpoc_threshold_met",
    "is_wc",
    "pay_code_bucket",
    "is_excluded_coverage",
    "is_excluded_line",
    "days_open",
    "age_at_event",
]

RESERVE_FEATURES = [
    "patient_age",
    "diagnosis_code",
    "procedure_code",
    "admission_type",
    "days_in_hospital",
    "provider_type",
    "injury_severity",
    "num_previous_claims",
    "avg_previous_reserve",
    "initial_estimate",
    "reported_delay_days",
    "state",
]


def pay_code_bucket(code) -> str:
    try:
        code = int(code)
    except (TypeError, ValueError):
        return "OTHER"
    if code in (113, 120, 135, 137, 153):
        return "SETTLEMENT"
    if 100 <= code <= 199 or code == 390:
        return "TPOC"
    if 300 <= code <= 399:
        return "ORM"
    return "OTHER"


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["date_event", "date_open", "date_close", "clmnt_dob", "date_v1m_xmit"]:
        out[f"{col}_dt"] = pd.to_datetime(out[col], format="%m/%d/%Y", errors="coerce")
    return out


def engineer_claim_frames(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build Oracle-view-shaped frames from raw claims_data.csv."""
    df = _parse_dates(raw)
    df["claim_id"] = df["claim_uid"].astype(str)

    # Medicare-shaped fields
    med = df.copy()
    med["date_v1m_xmit_flag"] = med["date_v1m_xmit_dt"].notna().astype(int)
    med["is_us_claimant"] = (med["clmnt_country"].astype(str) == "USA").astype(int)
    med["orm_threshold_met"] = (pd.to_numeric(med["paid_3"], errors="coerce").fillna(0) > 750).astype(int)
    med["tpoc_threshold_met"] = (pd.to_numeric(med["paid_1"], errors="coerce").fillna(0) > 0).astype(int)
    med["is_wc"] = (med["data_set"].astype(str) == "WC").astype(int)
    med["pay_code_bucket"] = med["pay_code"].apply(pay_code_bucket)
    med["is_excluded_coverage"] = med["coverage_code"].isin(["ZE", "WA", "LT"]).astype(int)
    med["is_excluded_line"] = med["line_code"].isin(["ZE", "GR"]).astype(int)
    med["days_open"] = (med["date_close_dt"] - med["date_open_dt"]).dt.days
    med.loc[med["claim_open"].astype(bool), "days_open"] = 0
    med["days_open"] = med["days_open"].fillna(0)
    med["age_at_event"] = ((med["date_event_dt"] - med["clmnt_dob_dt"]).dt.days / 365.25).round(1)
    med["claim_open"] = med["claim_open"].astype(int)

    claim_summary = med[["claim_id", *MEDICARE_FEATURES]].copy()
    for col in MEDICARE_FEATURES:
        if col not in {"data_set", "pay_cat", "pay_type", "pay_code_bucket"}:
            claim_summary[col] = pd.to_numeric(claim_summary[col], errors="coerce")

    payment_summary = med[["claim_id", "paid_1", "paid_3", "amount", "pay_code", "pay_cat"]].copy()

    # Reserve-shaped fields + claimant history
    res = df.sort_values(["clmnt_ssn", "date_open_dt"]).reset_index(drop=True)
    res["patient_age"] = ((res["date_event_dt"] - res["clmnt_dob_dt"]).dt.days / 365.25).round(1)
    res["days_in_hospital"] = (res["date_close_dt"] - res["date_open_dt"]).dt.days
    res["diagnosis_code"] = res["our_cause_3"]
    res["procedure_code"] = res["our_cause_4"]
    res["admission_type"] = res["claim_type"]
    res["provider_type"] = res["proc_unit"].astype(str)
    res["injury_severity"] = res["our_cause_2"]
    res["initial_estimate"] = pd.to_numeric(res["amount"], errors="coerce")
    res["reported_delay_days"] = pd.to_numeric(res["days_to_cms"], errors="coerce")
    res["state"] = res["clmnt_state"].astype(str)
    res["num_previous_claims"] = res.groupby("clmnt_ssn").cumcount()
    res["avg_previous_reserve"] = (
        res.groupby("clmnt_ssn")["reserve_6"]
        .apply(lambda s: s.shift(1).expanding().mean())
        .reset_index(level=0, drop=True)
        .fillna(0)
    )

    reserve_context = res[["claim_id", *RESERVE_FEATURES]].copy()

    claimant = res[["claim_id", "clmnt_ssn", "num_previous_claims", "avg_previous_reserve"]].copy()
    claimant["claimant_key"] = claimant["clmnt_ssn"].astype(str).apply(
        lambda s: hashlib.sha256(s.encode()).hexdigest()[:12]
    )
    claimant = claimant.drop(columns=["clmnt_ssn"])

    return claim_summary, payment_summary, reserve_context, claimant
