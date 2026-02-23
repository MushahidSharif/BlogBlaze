"""
Post-related functions. Provides async functions for listing, creating, retrieving, updating and deleting posts.
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from schemas import PostCreate, PostUpdate
from logging_config import log_config

logger = log_config.get_logger(__name__)


async def list_posts(db: AsyncSession) -> list[models.Post]:
    """Return all posts with their authors, ordered by date posted descending."""
    result = await db.execute(
        select(models.Post).options(selectinload(models.Post.author)).order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return list(posts)


async def get_posts_by_user(db: AsyncSession, user_id: int) -> list[models.Post]:
    """
    Get all posts for a specific user, ordered by date posted descending.

    Args:
        db: AsyncSession for database operations
        user_id: The ID of the user whose posts to fetch

    Returns:
        List of Post objects for the user, with author relationships loaded

    """

    # Fetch posts filtered by user_id at database level
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return list(posts)


async def create_post(db: AsyncSession, post: PostCreate, current_user: models.User) -> models.Post:
    try:
        new_post = models.Post(title=post.title, content=post.content, user_id=current_user.id)
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post, attribute_names=["author"])
        return new_post
    except Exception:
        logger.exception("Error creating post userid:%s, post data:%s " % (current_user.id, str(post)))
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


async def get_post_or_404(db: AsyncSession, post_id: int) -> models.Post:
    result = await db.execute(
        select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


async def update_post_full(db: AsyncSession, post_id: int, post_data: PostCreate, current_user: models.User) -> models.Post:
    try:
        result = await db.execute(select(models.Post).where(models.Post.id == post_id))
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

        post.title = post_data.title
        post.content = post_data.content

        await db.commit()
        await db.refresh(post, attribute_names=["author"])
        return post

    except HTTPException:
        raise

    except Exception:
        logger.exception("Error updating post userid:%s, post id:%s " % (current_user.id, post_id))
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


async def update_post_partial(db: AsyncSession, post_id: int, post_data: PostUpdate, current_user: models.User) -> models.Post:
    try:
        result = await db.execute(select(models.Post).where(models.Post.id == post_id))
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)

        await db.commit()
        await db.refresh(post, attribute_names=["author"])
        return post
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error updating partial post userid:%s, post id:%s " % (current_user.id, post_id))
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


async def delete_post(db: AsyncSession, post_id: int, current_user: models.User) -> None:
    try:
        result = await db.execute(select(models.Post).where(models.Post.id == post_id))
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

        await db.delete(post)
        await db.commit()

    except HTTPException:
        raise

    except Exception:
        logger.exception("Error in deleting post userid:%s, post id:%s " % (current_user.id, post_id))
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
