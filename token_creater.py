"""
This module defines the TokenCreator class, which is responsible for creating and verifying JWT tokens for different
 contexts such as access tokens, email verification tokens, and password reset tokens.
 The class uses the PyJWT library to handle token encoding and decoding, and it manages secret keys and expiration
 times based on the token type.
"""
from datetime import UTC, datetime, timedelta
import enum
import jwt
from config import settings


class TokenType(enum.StrEnum):
    """Enumeration of different token types used in the application."""
    ACCESS_TOKEN = "access"
    EMAIL_VERIFICATION_TOKEN = "email_verification"
    PASSWORD_RESET_TOKEN = "password_reset"

class TokenCreator:
    """Manages JWT token creation and verification for different token types."""

    ALGORITHM = settings.algorithm

    #These will be used to create unique secret key for each context by appending with <general_secret_key> value.
    EMAIL_VERIFICATION_CONTEXT: str = "email-verify"
    PASSWORD_RESET_CONTEXT: str = "password-reset"


    @staticmethod
    def _get_secret_key(token_type: TokenType) -> str:
        """Get the appropriate secret key based on token type."""
        if token_type == TokenType.ACCESS_TOKEN:
            return settings.secret_key.get_secret_value()
        elif token_type == TokenType.EMAIL_VERIFICATION_TOKEN:
            return settings.general_secret_key.get_secret_value() + TokenCreator.EMAIL_VERIFICATION_CONTEXT
        elif token_type == TokenType.PASSWORD_RESET_TOKEN:
            return settings.general_secret_key.get_secret_value() + TokenCreator.PASSWORD_RESET_CONTEXT
        else:
            raise ValueError(f"Unknown token type: {token_type}")

    @staticmethod
    def _get_default_expiration(token_type: TokenType) -> timedelta | None:
        """Get the default expiration time based on token type."""
        if token_type == TokenType.ACCESS_TOKEN:
            return timedelta(minutes=settings.access_token_expire_minutes)
        elif token_type == TokenType.EMAIL_VERIFICATION_TOKEN:
            return timedelta(minutes=120)
        elif token_type == TokenType.PASSWORD_RESET_TOKEN:
            return timedelta(minutes=settings.password_reset_token_expire_minutes)
        return None

    @staticmethod
    def create_token(
        data: dict,
        token_type: TokenType,
        expire_in_minutes: int | None = None,
    ) -> str:
        """Create a JWT token with the specified type and expiration."""
        to_encode = data.copy()

        # Use provided expiration or fall back to default
        if expire_in_minutes:
            expires_delta = timedelta(minutes=expire_in_minutes)
        else:
            expires_delta = TokenCreator._get_default_expiration(token_type)

        expire = datetime.now(UTC) + expires_delta

        to_encode.update({"exp": expire})
        secret_key = TokenCreator._get_secret_key(token_type)

        encoded_jwt = jwt.encode(
            to_encode,
            secret_key,
            algorithm=TokenCreator.ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def verify_token(
        token: str,
        token_type: TokenType,
    ) -> str | None:
        """Verify a JWT token and return the subject (user id) if valid."""
        try:
            secret_key = TokenCreator._get_secret_key(token_type)
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[TokenCreator.ALGORITHM],
                options={"require": ["exp", "sub"]},
            )
        except jwt.InvalidTokenError:
            return None
        else:
            return payload.get("sub")
