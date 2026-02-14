import uvicorn
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status, Form
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

import models
from database import Base, engine, get_db
from routers import posts, users
from auth import verify_email_verification_token, send_account_verification_email, send_password_reset_email
from config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc()),
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(
    request: Request,
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id),
    )
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc()),
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )


@app.get("/account", include_in_schema=False)
async def account_page(request: Request):
    return templates.TemplateResponse(
        request,
        "account.html",
        {"title": "Account"},
    )

@app.get("/forgot-password", include_in_schema=False, name="forgot_password_page")
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {"title": "Forgot Password"},
    )

@app.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(db: Annotated[AsyncSession, Depends(get_db)], request: Request, email: str=Form()):


    if email == '':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address.",
        )

    # Find user by email
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == email.lower()),
    )
    user = result.scalars().first()

    # For security, don't reveal if email exists or not
    if user:
        # Send password reset email
        send_password_reset_email(user.id, email, request)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "message_type": "success",
            "status_code": status.HTTP_200_OK,
            "title": 'Success',
            "message": "If an account with that email exists, a password reset link has been sent.",
        },
        status_code=status.HTTP_200_OK,
    )

@app.get("/reset-password", include_in_schema=False, name="reset_password_page")
async def reset_password_page(token: str, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    from auth import verify_password_reset_token

    user_id = verify_password_reset_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect or expired password reset link",
        )

    result = await db.execute(select(models.User).where(models.User.id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return templates.TemplateResponse(
        request,
        "reset_password.html",
        {"title": "Reset Password"},
    )

@app.post("/reset-password", include_in_schema=False, status_code=status.HTTP_200_OK)
async def reset_password(token:str, db: Annotated[AsyncSession, Depends(get_db)], request: Request, password:str = Form()):
    from auth import verify_password_reset_token, hash_password

    # Verify the reset token
    user_id = verify_password_reset_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect or expired password reset link",
        )

    # Find user
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update password
    user.password_hash = hash_password(password)
    await db.commit()
    await db.refresh(user)


    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "message_type": "success",
            "status_code": status.HTTP_200_OK,
            "title": 'Success',
            "message": "Password reset successful. Please login with your new password.",
        },
        status_code=status.HTTP_200_OK,
    )

@app.get("/resend_email_verification")
async def resend_email_verification(uid:int, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.User).where(models.User.id == uid))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.account_status != 0 and settings.email_verification:
        send_account_verification_email(uid, user.email, request)

        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "message_type": "success",
                "status_code": status.HTTP_200_OK,
                "title": 'Success',
                "message": 'Account Verification email has been send. Please check your email.',
            },
            status_code=status.HTTP_200_OK,
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "message_type": "success",
            "status_code": status.HTTP_200_OK,
            "title": 'Success',
            "message": 'User Account is already active. Please login with your User/Password',
        },
        status_code=status.HTTP_200_OK,
    )



@app.get("/verifyEmail")
async def verify_email(token:str, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user_id = verify_email_verification_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect or expired verification link",
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.account_status ==0:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "message_type": "success",
                "status_code": status.HTTP_200_OK,
                "title": 'Success',
                "message": 'Email account is already verified. Please login with your user/password',
            },
            status_code=status.HTTP_200_OK,
        )

    user.account_status =0
    await db.commit()

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "message_type": "success",
            "status_code": status.HTTP_200_OK,
            "title": 'Success',
            "message": 'Email account is successfully verified. Please login with your user/password',
        },
        status_code=status.HTTP_200_OK,
    )


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
):
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)