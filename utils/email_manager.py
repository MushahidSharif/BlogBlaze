from pathlib import Path
import appinfo
from appinfo import EMAIL_TEMPLATES_DIR
from config import settings
from .email_sender_smtp import EmailSenderSMTP
import  datetime

class EmailManager():
    """
    This class is responsible for managing email sending in the application. It provides methods to send different
    types of emails such as account verification and password reset emails.
    """

    def __init__(self):
        self.__email_sender: EmailSenderSMTP = EmailSenderSMTP()

    def __send_html_email(self, template_path: Path, place_holder_replacement_dict,
                          to_email: str, subject: str
                          ):

        if not template_path.is_file():
            raise FileNotFoundError(
                f"Password reset email template not found at {template_path}"
            )

        html_body = template_path.read_text(encoding="utf-8")

        for item in place_holder_replacement_dict.items():
            place_holder_name = item[0]
            replacement_value = item[1]
            html_body = html_body.replace(place_holder_name, replacement_value)

        print(html_body)
        #return
        # TODO Remove it

        self.__email_sender.send_email(
            subject=subject,
            body=html_body,
            to=to_email,
            html=True,
        )


    def send_verification_email(self, to_email: str, verification_link: str,*,
                                subject: str = f"Verify your {appinfo.APP_NAME} account",
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
            place_holder_replacement_dict = {
                "{{VERIFICATION_LINK}}": verification_link,
                "{{APP_NAME}}": appinfo.APP_NAME,
                "{{CURRENT_YEAR}}": str(datetime.datetime.now(datetime.UTC).year)
            }
            self.__send_html_email(template_path, place_holder_replacement_dict, to_email, subject)

        except Exception as ex:
            print('Error in sending emails.', ex)


    def send_password_reset_email(self, to_email: str, reset_link: str, *,
                                  subject: str = f"Reset your {appinfo.APP_NAME} password",
    ) -> None:
        """
        Load the HTML password reset template, inject the reset link,
        and send it to the given email address.

        The template name is expected to be reset_password_email.html and exist in EMAIL_TEMPLATES_DIR

        Placeholders:
            {{RESET_LINK}} - replaced with the provided reset_link
            {{CURRENT_YEAR}}   - replaced with the current year
        """
        if not settings.email_enable:
            return
        try:
            template_path = Path(EMAIL_TEMPLATES_DIR + "/reset_password_email.html")
            place_holder_replacement_dict = {
                "{{RESET_LINK}}": reset_link,
                "{{APP_NAME}}": appinfo.APP_NAME,
                "{{CURRENT_YEAR}}": str(datetime.datetime.now(datetime.UTC).year)
            }
            self.__send_html_email(template_path,place_holder_replacement_dict, to_email, subject)

        except Exception as ex:
            print('Error in sending emails.', ex)


