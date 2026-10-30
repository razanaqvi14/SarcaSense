from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str = "sqlite:///./dev.db"
    # Signs the session JWT. There is deliberately no usable default.
    secret_key: str = Field(min_length=32)

    access_token_minutes: int = 60
    # Set to false only for plain-http local development.
    cookie_secure: bool = True

    # Argon2id cost. Defaults are argon2-cffi's (RFC 9106 low-memory profile, ~64 MiB per hash).
    # Small hosts can lower the memory, e.g. 19456 KiB / time 2 / parallelism 1 (OWASP minimum).
    argon2_time_cost: int = 3
    argon2_memory_kib: int = 65536
    argon2_parallelism: int = 4
    # Each hash briefly allocates argon2_memory_kib. Capping simultaneous hashes bounds peak
    # memory (and CPU) on small hosts; extra requests wait their turn.
    argon2_max_concurrent: int = 2

    max_text_length: int = 500
    enable_docs: bool = False

    rate_limit_enabled: bool = True
    rate_limit_login: str = "10/minute"
    rate_limit_register: str = "5/minute"
    rate_limit_predict: str = "30/minute"

    model_path: Path = ARTIFACTS_DIR / "best_model.pt"
    vocab_path: Path = ARTIFACTS_DIR / "word_to_index.json"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, v: str) -> str:
        # Hosts hand out postgres:// or postgresql:// URLs; SQLAlchemy needs the driver named.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
