"""
Endpoints related to account access management, such as password reset and email verification.
"""
from typing import Annotated
from fastapi import APIRouter, Depends,  HTTPException, Request, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

from auth import hash_password
from access_manager import AccessManager

from config import settings
from appinfo import templates
from utils import html_utils
from data_services import users_service


router = APIRouter(include_in_schema=False)

# account access related endpoints (e.g. forgot password, account verification)
@router.get("/forgot-password", include_in_schema=False, name="forgot_password_page")
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {"title": "Forgot Password"},
    )

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(db: Annotated[AsyncSession, Depends(get_db)], request: Request, email: str=Form()):

    if email == '':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address.",
        )

    # Find user by email
    user = await users_service.get_user_from_email(db=db, user_email=email)

    # For security, don't reveal if email exists or not
    if user:
        # Send password reset email
        AccessManager.send_password_reset_email(user.id, email, request)


    return html_utils.get_html_message_response(
        request,message_type="success", title="Success",
        message='If an account exists with this email, you will receive an email with password reset instructions shortly.',
        status_code=status.HTTP_200_OK,
    )

@router.get("/reset-password", include_in_schema=False, name="reset_password_page")
async def reset_password_page(token: str, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Render the password reset page if the token provided in query string  is valid.
    Otherwise, show an error message.
    """

    user_id = AccessManager.verify_password_reset_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect or expired password reset link",
        )

    user = await users_service.get_user_or_404(db, int(user_id))

    return templates.TemplateResponse(
        request,
        "reset_password.html",
        {"title": "Reset Password"},
    )

@router.post("/reset-password", include_in_schema=False, status_code=status.HTTP_200_OK)
async def reset_password(token:str, db: Annotated[AsyncSession, Depends(get_db)], request: Request, password:str = Form()):

    # Verify the reset token
    user_id = AccessManager.verify_password_reset_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect or expired password reset link",
        )

    # Find user
    user = await users_service.get_user_or_404(db, int(user_id))

    # Update password
    user.password_hash = hash_password(password)
    await db.commit()
    await db.refresh(user)

    return html_utils.get_html_message_response(
        request, message_type="success", title="Success",
        message="Password reset successful. Please login with your new password.",
        status_code=status.HTTP_200_OK,
    )

@router.get("/resend_email_verification")
async def resend_email_verification(uid:int, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):

    user = await users_service.get_user_or_404(db, uid)

    if user.account_status != 0 and settings.email_verification:
        AccessManager.send_account_verification_email(uid, user.email, request)
        return html_utils.get_html_message_response(
            request, message_type="success", title="Success",
            message="Account Verification email has been send. Please check your email.",
            status_code=status.HTTP_200_OK,
        )

    return html_utils.get_html_message_response(
        request, message_type="success", title="Success",
        message="User Account is already active. Please login with your User/Password",
        status_code=status.HTTP_200_OK,
    )

@router.get("/verifyEmail")
async def verify_email(token:str, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    user_id = AccessManager.verify_email_verification_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect or expired verification link",
        )

    user = await users_service.get_user_or_404(db, int(user_id))

    if user.account_status ==0:
        return html_utils.get_html_message_response(
            request, message_type="success", title="Success",
            message="Email account is already verified. Please login with your user/password",
            status_code=status.HTTP_200_OK,
        )

    user.account_status =0
    await db.commit()

    return html_utils.get_html_message_response(
            request, message_type="success", title="Success",
            message="Email account is successfully verified. Please login with your user/password",
            status_code=status.HTTP_200_OK,
    )