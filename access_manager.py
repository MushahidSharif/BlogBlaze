from utils.email_manager import EmailManager
from token_creater import TokenCreator, TokenType
from logging_config import log_config
from config import settings

logger = log_config.get_logger(__name__)


class AccessManager:

    @staticmethod
    def create_access_token(data: dict, expire_in_minutes: int | None = None) -> str:
        """Create a JWT access token."""
        return TokenCreator.create_token(data, TokenType.ACCESS_TOKEN, expire_in_minutes)

    @staticmethod
    def verify_access_token(token: str) -> str | None:
        """Verify a JWT access token and return the subject (user id) if valid."""
        return TokenCreator.verify_token(token, TokenType.ACCESS_TOKEN)

    # -------------------------------------------
    # Email verification related functions

    @staticmethod
    def verify_email_verification_token(token: str) -> str | None:
        """Verify a JWT email verification token and return the subject (user id) if valid."""
        return TokenCreator.verify_token(token, TokenType.EMAIL_VERIFICATION_TOKEN)


    @staticmethod
    def send_account_verification_email(user_id, user_email, request):
        """Generate a email account verification token and send an email account verification email to the user."""
        logger.info("Sending password reset email for userid %s", user_id)
        data = {"sub": str(user_id)}
        email_ver_token = TokenCreator.create_token(data, TokenType.EMAIL_VERIFICATION_TOKEN)
        email_verification_url = settings.app_url + '/verify_email?token=' + email_ver_token

        email_manager = EmailManager()
        email_manager.send_verification_email(user_email, email_verification_url)

    # -------------------------------------------
    # Password reset related functions

    @staticmethod
    def verify_password_reset_token(token: str) -> str | None:
        """Verify a JWT password reset token and return the subject (user id) if valid."""
        return TokenCreator.verify_token(token, TokenType.PASSWORD_RESET_TOKEN)

    @staticmethod
    def send_password_reset_email(user_id, user_email):
        """Generate a token for password reset and send a password reset email to the user."""
        logger.info("Sending password reset email for userid %s",  user_id )
        data = {"sub": str(user_id)}
        reset_token = TokenCreator.create_token(data, TokenType.PASSWORD_RESET_TOKEN)
        password_reset_url = settings.app_url + '/reset-password?token=' + reset_token

        email_manager = EmailManager()
        email_manager.send_password_reset_email(user_email, password_reset_url)
