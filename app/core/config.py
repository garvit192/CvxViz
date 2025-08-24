from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json

class Settings(BaseSettings):
    API_TOKEN: str
    PROJECT_NAME: str = "CvxViz"
    API_V1_STR: str = "/api/v1"
    ENV: str = "dev"
    # Keep env as a plain string to avoid pydantic trying to JSON-decode a List[str]
    ALLOWED_ORIGINS_RAW: str = "http://localhost:3000"
    TIMEOUT_SECONDS: int = 8
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        raw = (self.ALLOWED_ORIGINS_RAW or "").strip()
        # If user provides JSON, accept it; otherwise split by comma
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed]
            except Exception:
                pass
        return [s.strip() for s in raw.split(",") if s.strip()]

settings = Settings()
