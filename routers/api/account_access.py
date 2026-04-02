from typing import Annotated

from fastapi import APIRouter, Depends,  HTTPException, Request, status, Form
from sqlalchemy.ext.asyncio import AsyncSession

from access_manager import AccessManager
from auth import hash_password
from data_services import users_service
from database import get_db
from schemas import ForgotPasswordRequest, ResetPasswordRequest, AccountVerificationRequest
from config import settings

router = APIRouter()

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(db: Annotated[AsyncSession, Depends(get_db)], forgot_pw_request_data: ForgotPasswordRequest):

    email= forgot_pw_request_data.email
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
        AccessManager.send_password_reset_email(user.id, email)

    return {
        "message":"If an account exists with this email, you will receive an email with password reset instructions shortly."
    }

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(db: Annotated[AsyncSession, Depends(get_db)], reset_pw_data: ResetPasswordRequest):

    # Verify the reset token
    user_id = AccessManager.verify_password_reset_token(reset_pw_data.token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect or expired password reset link",
        )

    # Find user
    user = await users_service.get_user_or_404(db, int(user_id))

    # Update password
    user.password_hash = hash_password(reset_pw_data.new_password)
    await db.commit()
    await db.refresh(user)

    return {
        "message": "Password reset successful. Please login with your new password.",
    }


@router.post("/account_verification_request", status_code=status.HTTP_200_OK)
async def account_verification_request(request_data: AccountVerificationRequest, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    
    user_email = request_data.user_email

    user = await users_service.get_user_from_email(db, user_email=user_email)
    
    if user:
        if user.account_status != 0 and settings.email_verification:
            AccessManager.send_account_verification_email(user.id, user.email, request)
            
            return {
                "message": "Account Verification email has been send. Please check your email." 
            }

        return {
            "message": "User Account is already active. Please login with your User/Password"
        }

    return {
        "message": "Account Verification email has been send. Please check your email."
    }

@router.get("/verify_account", status_code=status.HTTP_200_OK)
async def verify_account(token:str, db: Annotated[AsyncSession, Depends(get_db)]):
    user_id = AccessManager.verify_email_verification_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect or expired verification link",
        )

    user = await users_service.get_user_or_404(db, int(user_id))
    if user.account_status != 0:
        user.account_status = 0
        await db.commit()
    
    return {
        "message" : "Email account is successfully verified. Please login with your user/password." 
    }
