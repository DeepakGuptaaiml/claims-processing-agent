import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get_medicare_api_url() -> str:
    return os.getenv("MEDICARE_API_URL", "http://127.0.0.1:8000").rstrip("/")


def get_reserve_api_url() -> str:
    return os.getenv("RESERVE_API_URL", "http://127.0.0.1:8001").rstrip("/")


def get_claims_csv_path() -> Path:
    env = os.getenv("CLAIMS_CSV_PATH")
    if env:
        return Path(env)
    return ROOT.parent / "medicare_classifier" / "data" / "claims_data.csv"


def get_sqlite_path() -> Path:
    env = os.getenv("SQLITE_DB_PATH")
    if env:
        return Path(env)
    return ROOT / "mcp_server" / "data" / "claims_ai.db"


def get_oracle_config() -> dict[str, str]:
    return {
        "dsn": os.getenv("ORACLE_DSN", ""),
        "user": os.getenv("ORACLE_USER", ""),
        "password": os.getenv("ORACLE_PASSWORD", ""),
    }
