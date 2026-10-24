"""SMTP email delivery for authentication messages."""

import os
import smtplib
from email.message import EmailMessage


def send_password_reset_email(recipient: str, reset_url: str) -> None:
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    sender = os.getenv("MAIL_FROM", username or "")
    if not username or not password or not sender:
        raise RuntimeError("Mail settings are not configured")

    message = EmailMessage()
    message["Subject"] = "Reset your AlphaSage password"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "We received a request to reset your AlphaSage password.\n\n"
        f"Reset your password here: {reset_url}\n\n"
        "This link expires in 30 minutes. If you did not request this, ignore this email."
    )
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


def send_password_reset_otp(recipient: str, otp: str) -> None:
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    sender = os.getenv("MAIL_FROM", username or "")
    if not username or not password or not sender:
        raise RuntimeError("Mail settings are not configured")
    message = EmailMessage()
    message["Subject"] = "Your AlphaSage password reset code"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(f"Your AlphaSage password reset OTP is: {otp}\n\nThis code expires in 10 minutes.")
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)
