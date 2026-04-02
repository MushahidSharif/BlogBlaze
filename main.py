"""
Main module for initializing and starting FAST Api application
"""
from contextlib import asynccontextmanager
from logging_config import log_config

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers.api import users, posts, account_access
from routers.pages import users_pages, posts_pages, account_access_pages
from utils import html_utils
from pathlib import Path
import  appinfo
from config import settings

# Logger is none here because it will be initialized in the lifespan function after the log manager is configured.
logger = None

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    global logger
    logmanager = log_config.get_log_manager()
    logmanager.configure()
    logger = log_config.get_logger(__name__)
    logger.info("Application is starting")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()
    logmanager.shutdown()  # if running with QueueLoggingManager, ensure all logs are flushed before shutdown


app = FastAPI(lifespan=lifespan)

#Handle general exceptions
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
):
    logger.error("Invalid Http request. %s", str(exception))
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    return html_utils.get_html_message_response(
        request=request, message_type="error", title=exception.status_code,
        message=message, status_code=exception.status_code
    )

#Handle Data Validation error
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
):
    logger.error("Invalid Data in request. %s",  str(exception))
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)

    return html_utils.get_html_message_response(
        request=request, message_type="error", title=status.HTTP_422_UNPROCESSABLE_CONTENT,
        message="Invalid request. Please check your input and try again.",
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )


def create_required_folders():
    log_folder = Path(appinfo.APP_BASE_DIR +"/logs")
    log_folder.mkdir(parents=True, exist_ok=True)

def initialize_application():
    create_required_folders()

    cors_origins = settings.cors_origins.split(",")

    # # Define the list of origins that should be permitted
    # origins = [
    #     "http://localhost:3000",  # Example frontend development URL
    #     "http://127.0.0.1:3000",
    #     #"https://yourproductionapp.com",
    #     # You can also use "http://127.0.0.1:3000" if necessary
    # ]

    origins = cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # List of allowed origins
        allow_credentials=True,  # Allow cookies/authorization headers (requires specific origins, not "*")
        allow_methods=["*"],  # Allow all standard HTTP methods (GET, POST, PUT, etc.)
        allow_headers=["*"],  # Allow all standard headers
    )

    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/media", StaticFiles(directory="media"), name="media")

    # Adding REST API Routers
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
    app.include_router(account_access.router, prefix="/api/account_access", tags=["account_access"])

    # Adding HTML Page Routers
    app.include_router(account_access_pages.router)
    app.include_router(users_pages.router)
    app.include_router(posts_pages.router)


initialize_application()

