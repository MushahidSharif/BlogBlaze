"""
This module defines the routes for user-related pages, including login, registration, and account management.
Each route renders the appropriate HTML template for the corresponding page. These are page-rendering endpoints
that return HTML templates rather than API responses, and they are excluded from the OpenAPI schema.
"""

from fastapi import APIRouter, Request
from appinfo import templates

router = APIRouter()

@router.get("/login", include_in_schema=False)
async def login_page(request: Request):
    """Render the login page for user authentication."""
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@router.get("/register", include_in_schema=False)
async def register_page(request: Request):
    """Render the registration page for creating a new user account."""
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )


@router.get("/account", include_in_schema=False)
async def account_page(request: Request):
    """Render the account management page for the currently authenticated user."""
    return templates.TemplateResponse(
        request,
        "account.html",
        {"title": "Account"},
    )

