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
