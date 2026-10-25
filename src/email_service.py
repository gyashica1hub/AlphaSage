"""SMTP email delivery for authentication messages."""

import os
import smtplib
from email.message import EmailMessage

import requests


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
    send_otp_email(recipient, otp, "Your AlphaSage password reset code", "Your AlphaSage password reset OTP is")


def send_email_verification_otp(recipient: str, otp: str) -> None:
    send_otp_email(recipient, otp, "Verify your AlphaSage email", "Your AlphaSage email verification code is")


def send_alert_email(recipient: str, symbol: str, body: str) -> None:
    subject = f"AlphaSage alert: {symbol}"
    if os.getenv("EMAIL_PROVIDER", "gmail").lower() == "resend":
        api_key = os.getenv("RESEND_API_KEY")
        sender = os.getenv("MAIL_FROM", "onboarding@resend.dev")
        if not api_key:
            raise RuntimeError("RESEND_API_KEY is not configured")
        response = requests.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"from": sender, "to": [recipient], "subject": subject, "text": body}, timeout=15)
        response.raise_for_status()
        return
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    sender = os.getenv("MAIL_FROM", username or "")
    if not username or not password or not sender:
        raise RuntimeError("Mail settings are not configured")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


def send_otp_email(recipient: str, otp: str, subject: str, message_prefix: str) -> None:
    if os.getenv("EMAIL_PROVIDER", "gmail").lower() == "resend":
        send_otp_email_resend(recipient, otp, subject, message_prefix)
        return
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    sender = os.getenv("MAIL_FROM", username or "")
    if not username or not password or not sender:
        raise RuntimeError("Mail settings are not configured")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(f"{message_prefix}: {otp}\n\nThis code expires in 10 minutes.")
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


def send_password_reset_otp_resend(recipient: str, otp: str) -> None:
    send_otp_email_resend(recipient, otp, "Your AlphaSage password reset code", "Your AlphaSage password reset OTP is")


def send_otp_email_resend(recipient: str, otp: str, subject: str, message_prefix: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("MAIL_FROM", "onboarding@resend.dev")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "from": sender,
            "to": [recipient],
            "subject": subject,
            "text": f"{message_prefix}: {otp}\n\nThis code expires in 10 minutes.",
        },
        timeout=15,
    )
    response.raise_for_status()
