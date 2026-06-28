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
    bundled = ROOT / "data" / "claims_data.csv"
    if bundled.exists():
        return bundled
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


def _timeout_seconds(env_key: str, default: float) -> float:
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return default
    return float(raw)


def get_http_timeouts() -> dict[str, float]:
    """HTTP client timeouts — reserve needs extra headroom for Container App cold starts."""
    return {
        "medicare": _timeout_seconds("HTTP_TIMEOUT_MEDICARE", 60.0),
        "reserve": _timeout_seconds("HTTP_TIMEOUT_RESERVE", 90.0),
        "policy": _timeout_seconds("HTTP_TIMEOUT_POLICY", 90.0),
    }

