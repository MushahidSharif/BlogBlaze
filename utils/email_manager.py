from pathlib import Path
from appinfo import EMAIL_TEMPLATES_DIR
from config import settings
from .email_sender_smtp import EmailSenderSMTP
import  datetime

class EmailManager():
    def __init__(self):
        self.__email_sender: EmailSenderSMTP = EmailSenderSMTP()

    def send_verification_email(self, to_email: str, verification_link: str,*,
                                subject: str = "Verify your DishTalk account",
    ) -> None:
        """
        Load the HTML email verification template, inject the verification link,
        and send it to the given email address.

        The template name is expected to be verification_email.html and exist in EMAIL_TEMPLATES_DIR

        Placeholders:
            {{VERIFICATION_LINK}} - replaced with the provided verification_link
            {{CURRENT_YEAR}}      - replaced with the current year
        """
        if not settings.email_enable:
            return
        try:

            template_path = Path(EMAIL_TEMPLATES_DIR + "/verification_email.html")
            if not template_path.is_file():
                raise FileNotFoundError(
                    f"Verification email template not found at {template_path}"
                )

            html_body = template_path.read_text(encoding="utf-8")



            html_body = (
                html_body.replace("{{VERIFICATION_LINK}}", verification_link)
                .replace("{{CURRENT_YEAR}}", str(datetime.datetime.now(datetime.UTC).year))
            )

            self.__email_sender.send_email(
                subject=subject,
                body=html_body,
                to=to_email,
                html=True,
            )
        except Exception as ex:
            print('Error in sending emails.', ex)

