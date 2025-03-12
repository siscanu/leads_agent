from typing import Optional

from agno.tools import Toolkit
from agno.utils.log import logger


class ZohoEmailTools(Toolkit):
    def __init__(
        self,
        receiver_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        sender_email: Optional[str] = None,
        sender_passkey: Optional[str] = None,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 465,
        use_ssl: bool = True,
    ):
        super().__init__(name="email_tools")
        self.receiver_email: Optional[str] = receiver_email
        self.sender_name: Optional[str] = sender_name
        self.sender_email: Optional[str] = sender_email
        self.sender_passkey: Optional[str] = sender_passkey
        self.smtp_server: str = smtp_server
        self.smtp_port: int = smtp_port
        self.use_ssl: bool = use_ssl
        self.register(self.email_user)

    def email_user(self, subject: str, body: str) -> str:
        """Emails the user with the given subject and body.

        :param subject: The subject of the email.
        :param body: The body of the email.
        :return: "success" if the email was sent successfully, "error: [error message]" otherwise.
        """
        try:
            import smtplib
            from email.message import EmailMessage
        except ImportError:
            logger.error("`smtplib` not installed")
            raise

        if not self.receiver_email:
            return "error: No receiver email provided"
        if not self.sender_name:
            return "error: No sender name provided"
        if not self.sender_email:
            return "error: No sender email provided"
        if not self.sender_passkey:
            return "error: No sender passkey provided"

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = self.receiver_email
        msg.set_content(body)

        logger.info(f"Sending Email to {self.receiver_email}")
        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as smtp:
                    smtp.login(self.sender_email, self.sender_passkey)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp:
                    smtp.starttls()
                    smtp.login(self.sender_email, self.sender_passkey)
                    smtp.send_message(msg)
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return f"error: {e}"
        return "email sent successfully"