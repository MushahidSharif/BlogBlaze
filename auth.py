from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from config import settings
from database import get_db
from utils.email_manager import EmailManager

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def _create_jwt_token(data: dict, security_key: str, expires_delta: timedelta | None = None) -> str:

    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes,
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        security_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt

def get_email_verification_token(userid: int):
    access_token_expires = timedelta(minutes=120)
    email_token = create_email_verification_link_token(
        data={"sub": str(userid)},
        expires_delta=access_token_expires,
    )
    return email_token

def send_account_verification_email(user_id, user_email, request):
    email_ver_token = get_email_verification_token(user_id)
    print(email_ver_token)
    email_verification_url = str(request.url_for('verify_email')) + '?token=' + email_ver_token
    print(email_verification_url)
    from utils.email_manager import EmailManager
    email_manager = EmailManager()
    email_manager.send_verification_email(user_email, email_verification_url)

def create_email_verification_link_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""

    secret_key = settings.email_verification_token_key.get_secret_value()
    return _create_jwt_token(data, secret_key, expires_delta)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""

    secret_key = settings.secret_key.get_secret_value()
    return _create_jwt_token(data, secret_key, expires_delta)

def _verify_access_token(token: str, secret_key: str) -> str | None:
    """Verify a JWT access token and return the subject (user id) if valid."""
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")


def verify_access_token(token: str) -> str | None:
    """Verify a JWT access token and return the subject (user id) if valid."""
    return _verify_access_token(token, settings.secret_key.get_secret_value())

def verify_email_verification_token(token: str) -> str | None:
    return _verify_access_token(token, settings.email_verification_token_key.get_secret_value())



async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.User:
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(models.User).where(models.User.id == user_id_int),
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]