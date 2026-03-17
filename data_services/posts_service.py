"""
Post-related functions. Provides async functions for listing, creating, retrieving, updating and deleting posts.
"""
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from schemas import PostCreate, PostUpdate, RatingCreate, PostWithAverageRating
from logging_config import log_config
from config import settings

logger = log_config.get_logger(__name__)


async def list_posts(db: AsyncSession, skip: int, limit: int) -> (list[models.Post], int, bool):
    """Return all posts with their authors, ordered by date posted descending."""
    count_result = await db.execute(select(func.count()).select_from(models.Post))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
        .offset(skip)
        .limit(limit),
    )
    posts = result.scalars().all()

    has_more = skip + len(posts) < total

    return posts, total, has_more

async def list_posts_with_rating(db: AsyncSession, skip: int, limit: int) -> tuple[list[PostWithAverageRating], int, bool]:
    """
    Return all posts with their authors, average ratings and total count of ratings,
    ordered by date posted descending.
    :param db:
    :param skip: offset to start fetching posts from
    :param limit: No of rows to return
    :return: tuple list[PostWithAverageRating], total count of posts, has_more flag
    """

    (posts, total, has_more) = await list_posts(db=db, skip=skip, limit=limit)
    dict_post_ratings = await get_average_ratings_of_posts(db=db)

    # PostWithAverageRating
    post_list = []
    for post in posts:

        avg_post_rating_tuple = dict_post_ratings.get(post.id, None)
        avg_rating = 0
        total_count = 0
        if avg_post_rating_tuple:
            avg_rating = avg_post_rating_tuple[1]
            total_count = avg_post_rating_tuple[2]

        p = PostWithAverageRating(id=post.id, title=post.title, content=post.content,
                                  date_posted=post.date_posted, user_id=post.user_id,
                                  author=post.author, average_rating=avg_rating, rating_count=total_count
                                  )

        post_list.append(p)

    return post_list, total, has_more


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


async def create_rating(db: AsyncSession, post_id: int, rating_data: RatingCreate, current_user: models.User) -> models.PostRating:
    """
    Create a rating for a post.

    Args:
        db: AsyncSession for database operations
        post_id: The ID of the post to rate
        rating_data: RatingCreate schema containing rating (1-5) and optional review
        current_user: The current authenticated user

    Returns:
        PostRating object created in the database

    Raises:
        HTTPException: If post not found (404) or internal server error (500)
    """
    try:
        # Check if post exists
        result = await db.execute(select(models.Post).where(models.Post.id == post_id))
        post = result.scalars().first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        result = await db.execute(select(models.PostRating)
            .where(
                and_(models.PostRating.post_id == post_id, models.PostRating.user_id == current_user.id)
            )
        )
        post_rating = result.scalars().first()
        if post_rating:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has already rated this post")

        # Create new rating
        new_rating = models.PostRating(
            post_id=post_id,
            user_id=current_user.id,
            rating=rating_data.rating,
            review=rating_data.review
        )
        db.add(new_rating)
        await db.commit()
        await db.refresh(new_rating)
        return new_rating

    except HTTPException:
        raise

    except Exception:
        logger.exception("Error creating rating for post_id:%s, user_id:%s" % (post_id, current_user.id))
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


async def get_average_ratings_of_posts(db: AsyncSession) -> dict[int, tuple[int, float, int]]:
    """
    Get average ratings and total count of ratings for all posts.
    """
    try:
        stmt = (
            select(
                models.PostRating.post_id,
                func.round(func.avg(models.PostRating.rating),1).label("average_rating"),
                func.count(models.PostRating.id).label("total_count")
            )
            .group_by(models.PostRating.post_id)
        )

        result = await db.execute(stmt)
        ratings = result.all()

        dict_ratings = {}
        for row in ratings:
            dict_ratings[row.post_id] = (row.post_id, float(row.average_rating), row.total_count)
        return dict_ratings

    except Exception:
        logger.exception("Error fetching average ratings for posts")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
