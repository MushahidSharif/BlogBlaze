from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db
from token_manager import TokenManager
from utils.email_manager import EmailManager

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")


def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


# Access token creation and verification
def create_access_token(userid) -> str:
    """Create a JWT access token."""
    return TokenManager.create_access_token(data={"sub": str(userid)})

def verify_access_token(token: str) -> str | None:
    """Verify a JWT access token and return the subject (user id) if valid."""
    return TokenManager.verify_access_token(token)


# Email verify token creation and verification
def get_email_verification_token(userid: int) -> str:
    """Generate an email verification token for a user."""
    return TokenManager.create_email_verification_token(data={"sub": str(userid)},)

def verify_email_verification_token(token: str) -> str | None:
    """Verify a JWT email verification token and return the subject (user id) if valid."""
    return TokenManager.verify_email_verification_token(token)

def send_account_verification_email(user_id, user_email, request):
    """Send an email account verification email to the user."""
    email_ver_token = get_email_verification_token(user_id)
    email_verification_url = str(request.url_for('verify_email')) + '?token=' + email_ver_token

    email_manager = EmailManager()
    email_manager.send_verification_email(user_email, email_verification_url)


# Password reset token creation and verification
def get_password_reset_token(userid: int) -> str:
    """Generate a password reset token for a user."""
    return TokenManager.create_password_reset_token( data={"sub": str(userid)}, )

def verify_password_reset_token(token: str) -> str | None:
    """Verify a JWT password reset token and return the subject (user id) if valid."""
    return TokenManager.verify_password_reset_token(token)

def send_password_reset_email(user_id, user_email, request):
    """Send a password reset email to the user."""
    reset_token = get_password_reset_token(user_id)
    password_reset_url = str(request.url_for('reset_password_page')) + '?token=' + reset_token

    email_manager = EmailManager()
    email_manager.send_password_reset_email(user_email, password_reset_url)



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