"""
User-related API endpoints for registration, authentication, and profile management.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import PostResponse, Token, UserCreate, UserPrivate, UserPublic, UserUpdate, PasswordUpdate

from data_services import users_service

router = APIRouter()

@router.post(
    "",
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Create a new user account. Usernames and emails must be unique (case-insensitive). Passwords are hashed before storing.
    """
    return await users_service.create_user(db=db, user=user, request=request)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    return await users_service.login_user(db=db, email=form_data.username, password=form_data.password, request=request)


@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    """
    Get the currently authenticated user's information. Requires a valid access token.
    :param current_user: populated by the get_current_user dependency, which verifies the access token
           and retrieves the user from the database
    :return: Current user's information, excluding password hash. If the token is invalid or expired, a 401 error is
            returned by the dependency.
    """
    return current_user

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await users_service.get_user_or_404(db=db, user_id=user_id)


@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await users_service.get_user_posts(db=db, user_id=user_id)


@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await users_service.update_user(db=db, user_id=user_id, user_update=user_update, current_user=current_user)


@router.post("/{user_id}/update-password", response_model=UserPrivate)
async def update_password(
    user_id: int,
    password_update: PasswordUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Update user password. Only the authenticated user can update their own password.
    """
    return await users_service.update_password(db=db, user_id=user_id, password_update=password_update, current_user=current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await users_service.delete_user(db=db, user_id=user_id, current_user=current_user)
