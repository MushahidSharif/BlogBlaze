"""
This module defines the routes for rendering HTML pages related to posts, including the home page,
individual post pages, and user-specific post pages. It uses FastAPI's templating system to render the
appropriate HTML templates with the necessary data retrieved from the database.

The page handlers delegate to data_services modules for business logic (listing posts, fetching users,
retrieving specific posts) to reduce code duplication and maintain separation of concerns.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from appinfo import templates
from database import get_db
from data_services import posts_service, users_service

router = APIRouter()

@router.get("/", include_in_schema=False, name="home")
@router.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    """Render the home page displaying all posts ordered by date (newest first)."""
    posts = await posts_service.list_posts(db=db)
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


@router.get("/posts/{post_id}", include_in_schema=False)
async def post_page(
    request: Request,
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Render a single post page. Returns 404 if the post does not exist."""
    post = await posts_service.get_post_or_404(db=db, post_id=post_id)
    title = post.title[:50]
    return templates.TemplateResponse(
        request,
        "post.html",
        {"post": post, "title": title},
    )


@router.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Render the user posts page displaying all posts for a specific user. Returns 404 if user does not exist."""
    user = await users_service.get_user_or_404(db=db, user_id=user_id)
    posts = await posts_service.get_posts_by_user(db=db, user_id=user_id)

    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )