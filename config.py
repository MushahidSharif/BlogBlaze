from typing import Literal
from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email / SMTP configuration
    email_verification: bool = False
    general_secret_key: SecretStr = ""

    password_reset_token_expire_minutes: int = 30

    # SMTP configuration
    email_enable: bool = False  # if email sending is enabled or not.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_security_type : Literal["ssl", "tls"] = "tls"
    smtp_from_email: EmailStr | None = None


settings = Settings()  # type: ignore[call-arg] # Loaded from .env file