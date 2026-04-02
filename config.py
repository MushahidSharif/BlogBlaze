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

    db_connection_string : str = "sqlite+aiosqlite:///./blog.db"
    
    app_url: str   

    # SMTP configuration
    email_enable: bool = False  # if email sending is enabled or not.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_security_type : Literal["ssl", "tls"] = "tls"
    smtp_from_email: EmailStr | None = None

    max_upload_size_bytes: int = 5 * 1024 * 1024  # 5 MB
    posts_per_page: int = 10
    
    #comma separated list of urls for cors origins
    cors_origins: str = "http://127.0.0.1:8080"


settings = Settings()  # type: ignore[call-arg] # Loaded from .env file