from pathlib import Path
from typing import Optional

import os
from dotenv import load_dotenv
from pydantic import BaseModel


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = BACKEND_DIR / "aegis.sqlite"

load_dotenv(BACKEND_DIR / ".env")


def _stable_sqlite_url(raw_url: Optional[str]) -> str:
    if not raw_url:
        return f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

    url = raw_url.strip()
    if not url.startswith("sqlite:///"):
        return url

    path_text = url.replace("sqlite:///", "", 1)
    if path_text in {"", ".", "./aegis.sqlite", "aegis.sqlite"}:
        return f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

    candidate = Path(path_text)
    if not candidate.is_absolute():
        candidate = BACKEND_DIR / candidate

    return f"sqlite:///{candidate.resolve().as_posix()}"


class Settings(BaseModel):
    database_url: str = _stable_sqlite_url(os.getenv("DATABASE_URL"))
    jwt_secret: str = os.getenv("JWT_SECRET", "aegis_demo_secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    fraud_ml_enabled: bool = os.getenv("FRAUD_ML_ENABLED", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    fraud_ml_fail_open: bool = os.getenv("FRAUD_ML_FAIL_OPEN", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    fraud_model_path: str = os.getenv(
        "FRAUD_MODEL_PATH",
        str(BACKEND_DIR / "app" / "ml" / "outputs" / "fibank_fraud_model.ubj"),
    )
    brand_protection_enabled: bool = os.getenv(
        "BRAND_PROTECTION_ENABLED", "true"
    ).lower() in {"1", "true", "yes", "on"}
    brand_target_domain: str = os.getenv("BRAND_TARGET_DOMAIN", "fibank.al")
    brand_target_name: str = os.getenv("BRAND_TARGET_NAME", "fibank")
    brand_target_url: str = os.getenv("BRAND_TARGET_URL", "https://www.fibank.al")
    brand_scan_quick_default: bool = os.getenv(
        "BRAND_SCAN_QUICK_DEFAULT", "true"
    ).lower() in {"1", "true", "yes", "on"}
    brand_scan_max_candidates: int = int(os.getenv("BRAND_SCAN_MAX_CANDIDATES", "300"))
    brand_scan_request_timeout: float = float(os.getenv("BRAND_SCAN_REQUEST_TIMEOUT", "8"))
    brand_scan_request_delay: float = float(os.getenv("BRAND_SCAN_REQUEST_DELAY", "0.5"))

    @property
    def resolved_fraud_model_path(self) -> Path:
        candidate = Path(self.fraud_model_path)
        if candidate.is_absolute():
            return candidate
        return BACKEND_DIR / candidate

    @property
    def cors_origins(self) -> list[str]:
        origins = {
            self.frontend_url,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        }
        return sorted(origin for origin in origins if origin)


settings = Settings()

