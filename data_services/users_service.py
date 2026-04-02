"""
User-related business logic extracted from routers/api/users.py.
Provides async functions for creating, authenticating, retrieving, updating and deleting users.
"""
from fastapi import HTTPException, status, Request, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool
from PIL import UnidentifiedImageError

import models
from auth import hash_password, verify_password, create_access_token
from access_manager import AccessManager
from config import settings
from schemas import Token, UserCreate, UserUpdate, PasswordUpdate
from logging_config import log_config
from utils.image_utils import process_profile_image, delete_profile_image

logger = log_config.get_logger(__name__)


async def create_user(db: AsyncSession, user: UserCreate, request: Request | None = None) -> models.User:
    """Create a new user. Usernames and emails must be unique (case-insensitive). Passwords are hashed before storing.
     Raises HTTPException on duplicate username/email.
    Returns the newly created models.User.
    """
    try:
        # Check if user with same username or email already exists (case-insensitive). If yes, raise error
        result = await db.execute(
            select(models.User).where(func.lower(models.User.username) == str(user.username).lower())
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        # Check to ensure email is not already registered (case-insensitive). If yes, raise error
        result = await db.execute(
            select(models.User).where(func.lower(models.User.email) == str(user.email).lower())
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Set account status based on whether email verification is required
        account_status = 0 if not settings.email_verification else 1

        new_user = models.User(
            username=user.username,
            email=str(user.email).lower(),
            password_hash=hash_password(user.password),
            account_status=account_status,
        )

        # add new user to database and commit
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        if settings.email_verification and request is not None:
            # send verification email but don't fail creation if email sending fails
            try:
                AccessManager.send_account_verification_email(new_user.id, new_user.email, request)
            except Exception:
                logger.exception("Failed to send account verification email for userid %s" % (new_user.id))
                # Best-effort: don't interrupt user creation for email failures
                pass

        return new_user
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error creating new")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


async def login_user(db: AsyncSession, email: str, password: str, request: Request | None = None) -> Token:
    """Authenticate user and return Token. If account not active, return Token with account_status and resend link."""
    try:
        # Look up user by email (case-insensitive)
        result = await db.execute(
            select(models.User).where(func.lower(models.User.email) == str(email).lower())
        )
        user = result.scalars().first()

        # Verify user exists and password is correct
        # Don't reveal which one failed (security best practice)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.account_status != 0:
            return Token(
                access_token="",
                token_type="",
                account_status=user.account_status
            )

        # Create access token with user id as subject
        access_token = create_access_token(user.id)
        return Token(access_token=access_token, token_type="bearer", account_status=0)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


async def get_user_or_404(db: AsyncSession, user_id: int) -> models.User:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


async def get_user_posts(db: AsyncSession, user_id: int) -> list[models.Post]:
    user  = await get_user_or_404(db, user_id)  # will raise 404 if user doesn't exist

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc()),
    )
    posts = result.scalars().all()
    return list(posts)


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate, current_user: models.User) -> models.User:
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

    try:
        user = await get_user_or_404(db, user_id)  # will raise 404 if user doesn't exist

        if (
            user_update.username is not None
            and str(user_update.username).lower() != str(user.username).lower()
        ):
            result = await db.execute(
                select(models.User).where(func.lower(models.User.username) == str(user_update.username).lower()),
            )
            existing_user = result.scalars().first()
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        if (
            user_update.email is not None
            and str(user_update.email).lower() != str(user.email).lower()
        ):
            result = await db.execute(
                select(models.User).where(func.lower(models.User.email) == str(user_update.email).lower()),
            )
            existing_email = result.scalars().first()
            if existing_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        if user_update.username is not None:
            user.username = user_update.username
        if user_update.email is not None:
            user.email = str(user_update.email).lower()

        await db.commit()
        await db.refresh(user)
        return user

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

async def delete_user(db: AsyncSession, user_id: int, current_user: models.User) -> None:
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")

    try:
        user = await get_user_or_404(db, user_id)  # will raise 404 if user doesn't exist

        old_filename = user.image_file

        await db.delete(user)
        await db.commit()

        if old_filename:
            delete_profile_image(old_filename)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error in deleting user userid:%s " % (current_user.id))
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

async def get_user_from_email(db: AsyncSession, user_email:str):
    """Get user by email (case-insensitive). Returns models.User or None if not found."""

    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == str(user_email).lower())
    )
    user = result.scalars().first()
    return user


async def update_password(db: AsyncSession, user_id: int, password_update: PasswordUpdate, current_user: models.User) -> models.User:
    """Update user password. Only the user can update their own password."""
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user's password")

    try:
        user = await get_user_or_404(db, user_id)  # will raise 404 if user doesn't exist

        if not verify_password(password_update.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Hash the new password and update it
        user.password_hash = hash_password(password_update.new_password)

        await db.commit()
        await db.refresh(user)
        return user

    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        logger.exception("Error updating password for user_id:%s" % (user_id))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

async def upload_profile_picture(db: AsyncSession, user_id: int, file: UploadFile,
                              current_user: models.User) -> models.User:

    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

    try:
        user = await get_user_or_404(db, user_id)  # will raise 404 if user doesn't exist

        content = await file.read()

        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // (1024 * 1024)}MB",
            )

        try:
            new_filename = await run_in_threadpool(process_profile_image, content)
        except UnidentifiedImageError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
            ) from err

        old_filename = current_user.image_file
        user.image_file = new_filename


        await db.commit()
        await db.refresh(user)

        if old_filename:
            delete_profile_image(old_filename)

        return user

    except HTTPException:
        raise
    except Exception:

        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

async def delete_user_picture(user_id: int, current_user: models.User, db:AsyncSession):

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's picture",
        )

    old_filename = current_user.image_file

    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture to delete",
        )

    current_user.image_file = None
    await db.commit()
    await db.refresh(current_user)

    delete_profile_image(old_filename)

    return current_user

