-- Dev SQLite tables mirror prod Oracle views in CLAIMS_AI_RO schema.

CREATE TABLE IF NOT EXISTS v_claim_summary_for_ai (
    claim_id TEXT PRIMARY KEY,
    data_set TEXT,
    pay_cat TEXT,
    pay_code REAL,
    pay_type TEXT,
    paid_1 REAL,
    paid_3 REAL,
    amount REAL,
    proc_unit REAL,
    cont_num REAL,
    claim_open INTEGER,
    date_v1m_xmit_flag INTEGER,
    is_us_claimant INTEGER,
    orm_threshold_met INTEGER,
    tpoc_threshold_met INTEGER,
    is_wc INTEGER,
    pay_code_bucket TEXT,
    is_excluded_coverage INTEGER,
    is_excluded_line INTEGER,
    days_open REAL,
    age_at_event REAL
);

CREATE TABLE IF NOT EXISTS v_payment_summary_for_ai (
    claim_id TEXT PRIMARY KEY,
    paid_1 REAL,
    paid_3 REAL,
    amount REAL,
    pay_code REAL,
    pay_cat TEXT
);

CREATE TABLE IF NOT EXISTS v_reserve_context_for_ai (
    claim_id TEXT PRIMARY KEY,
    patient_age REAL,
    diagnosis_code TEXT,
    procedure_code TEXT,
    admission_type TEXT,
    days_in_hospital REAL,
    provider_type TEXT,
    injury_severity TEXT,
    num_previous_claims INTEGER,
    avg_previous_reserve REAL,
    initial_estimate REAL,
    reported_delay_days REAL,
    state TEXT
);

CREATE TABLE IF NOT EXISTS v_claimant_context_for_ai (
    claim_id TEXT PRIMARY KEY,
    claimant_key TEXT,
    num_previous_claims INTEGER,
    avg_previous_reserve REAL
);
