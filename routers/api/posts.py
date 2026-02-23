"""
This module defines the API endpoints for managing blog posts. It includes routes for creating, retrieving, updating,
 and deleting posts. Each post is associated with a user (the author), and the endpoints enforce authorization to
 ensure that only the author can modify or delete their posts.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate
from data_services import posts_service

router = APIRouter()

@router.get("", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    return await posts_service.list_posts(db=db)


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: PostCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await posts_service.create_post(db=db, post=post, current_user=current_user)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await posts_service.get_post_or_404(db=db, post_id=post_id)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int,
    post_data: PostCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await posts_service.update_post_full(db=db, post_id=post_id, post_data=post_data, current_user=current_user)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await posts_service.update_post_partial(db=db, post_id=post_id, post_data=post_data, current_user=current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await posts_service.delete_post(db=db, post_id=post_id, current_user=current_user)
