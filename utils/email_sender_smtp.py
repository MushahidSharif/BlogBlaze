import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import settings

class EmailSenderSMTP():
    def __init__(self):
        pass

    def __get_smtp_connection(self) -> smtplib.SMTP:
        """
        Create and return a configured SMTP connection using values from settings.
        """
        if not settings.smtp_host:
            raise RuntimeError("SMTP host is not configured (SMTP_HOST).")

        host = settings.smtp_host
        port = settings.smtp_port

        if settings.smtp_security_type == "ssl":
            server: smtplib.SMTP = smtplib.SMTP_SSL(host=host, port=port)
            server.ehlo()
        else: # using tls
            server = smtplib.SMTP(host=host, port=port)
            server.starttls()
            server.ehlo()


        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password.get_secret_value())

        return server


    def send_email(self,
        subject: str,
        body: str,
        to: str | list[str],
        *,
        from_email: str | None = None,
        html: bool = False,
    ) -> None:
        """
        Send an email using SMTP settings defined in config.Settings.

        Environment variables (via Settings) expected:
        - SMTP_HOST
        - SMTP_PORT (optional, default 587)
        - SMTP_USERNAME (optional)
        - SMTP_PASSWORD (optional)
        - smtp_security_type (optional, default 'tls')
        - SMTP_FROM_EMAIL (optional, default sender)
        """
        sender_email = (
            from_email
            or (settings.smtp_from_email and str(settings.smtp_from_email))
            or (settings.smtp_username or "")
        )
        if not sender_email:
            raise RuntimeError(
                "No sender email configured. Set SMTP_FROM_EMAIL or pass from_email."
            )

        recipients: list[str]
        if isinstance(to, str):
            recipients = [to]
        else:
            recipients = list(to)

        if not recipients:
            raise ValueError("At least one recipient must be provided.")


        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = ", ".join(recipients)

        if html:
            content = MIMEText(body, "html")
        else:
            content = MIMEText(body, "plain")

        msg.attach(content)

        with self.__get_smtp_connection() as server:
            server.sendmail(sender_email, recipients, msg.as_string())
