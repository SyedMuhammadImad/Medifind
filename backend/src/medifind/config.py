from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

ROOT = Path(__file__).resolve().parents[3]


def validate_database_target(value: str, *, test: bool = False) -> str:
    try:
        url = make_url(value)
        valid = (
            url.drivername == "postgresql+psycopg"
            and url.host == "127.0.0.1"
            and url.port == 55432
            and url.username == "medifind"
            and bool(url.password)
            and url.password != "REPLACE_PRIVATELY"
            and url.database == ("medifind_test" if test else "medifind")
            and not url.query
        )
    except (ValueError, TypeError, ArgumentError):
        valid = False
    if not valid:
        raise ValueError("Invalid dedicated local PostgreSQL target; credentials are not displayed")
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", extra="ignore", hide_input_in_errors=True
    )
    database_url: SecretStr
    test_database_url: SecretStr
    browser_origin: str = "http://127.0.0.1:5173"
    cookie_secure: bool = False
    session_hours: int = Field(default=8, ge=1, le=24)
    stock_fresh_hours: int = Field(default=24, ge=1, le=168)

    @field_validator("browser_origin")
    @classmethod
    def exact_browser_origin(cls, value: str) -> str:
        origin = urlsplit(value)
        if (
            origin.scheme not in {"http", "https"}
            or not origin.hostname
            or origin.username
            or origin.password
            or origin.path
            or origin.query
            or origin.fragment
            or (origin.scheme == "http" and origin.hostname not in {"127.0.0.1", "localhost"})
        ):
            raise ValueError("Expected an exact HTTPS or loopback HTTP browser origin")
        return value

    @model_validator(mode="after")
    def https_cookie(self):
        if self.browser_origin.startswith("https://") and not self.cookie_secure:
            raise ValueError("HTTPS browser origin requires secure cookies")
        return self

    @field_validator("database_url")
    @classmethod
    def development_target(cls, value: SecretStr) -> SecretStr:
        validate_database_target(value.get_secret_value())
        return value

    @field_validator("test_database_url")
    @classmethod
    def dedicated_test_target(cls, value: SecretStr) -> SecretStr:
        validate_database_target(value.get_secret_value(), test=True)
        return value
