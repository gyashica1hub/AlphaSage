"""Local authentication primitives for Phase 2."""

import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select

from src.db.models import EmailVerificationOTP, PasswordResetOTP, User
from src.db.session import get_session

password_hasher = PasswordHasher()


def _serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("SESSION_SECRET")
    if not secret:
        raise RuntimeError("SESSION_SECRET must be configured before authentication is enabled")
    return URLSafeTimedSerializer(secret, salt="alphasage-session")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except Exception:
        return False


def create_session_token(user_id: str) -> str:
    return _serializer().dumps({"user_id": user_id, "session_id": str(uuid.uuid4())})


def read_session_token(token: str, max_age: int = 60 * 60 * 24 * 7) -> str | None:
    try:
        return _serializer().loads(token, max_age=max_age).get("user_id")
    except (BadSignature, SignatureExpired, RuntimeError):
        return None


def find_user_by_email(email: str) -> User | None:
    with get_session() as session:
        return session.scalar(select(User).where(User.email == email.lower().strip()))


def create_user(email: str, password: str, display_name: str | None) -> User:
    now = datetime.now(UTC)
    user = User(id=str(uuid.uuid4()), email=email.lower().strip(), display_name=display_name,
                password_hash=hash_password(password), created_at=now, updated_at=now)
    with get_session() as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def create_email_verification_otp(user_id: str) -> str:
    otp = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(UTC)
    row = EmailVerificationOTP(id=str(uuid.uuid4()), user_id=user_id, otp_hash=hash_password(otp), expires_at=now + timedelta(minutes=10), created_at=now)
    with get_session() as session:
        session.add(row)
        session.commit()
    return otp


def verify_email_verification_otp(email: str, otp: str) -> str | None:
    user = find_user_by_email(email)
    if not user or user.email_verified:
        return None
    now = datetime.now(UTC)
    with get_session() as session:
        row = session.scalar(select(EmailVerificationOTP).where(EmailVerificationOTP.user_id == user.id, EmailVerificationOTP.used.is_(False), EmailVerificationOTP.expires_at > now).order_by(EmailVerificationOTP.created_at.desc()))
        if not row or row.attempts >= 5:
            return None
        row.attempts += 1
        valid = verify_password(otp, row.otp_hash)
        if valid:
            row.used = True
            session.get(User, user.id).email_verified = True
            session.commit()
            return user.id
        session.commit()
    return None


def create_password_reset_otp(user_id: str) -> str:
    otp = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(UTC)
    row = PasswordResetOTP(id=str(uuid.uuid4()), user_id=user_id, otp_hash=hash_password(otp), expires_at=now + timedelta(minutes=10), created_at=now)
    with get_session() as session:
        session.add(row)
        session.commit()
    return otp


def verify_password_reset_otp(email: str, otp: str) -> str | None:
    user = find_user_by_email(email)
    if not user:
        return None
    now = datetime.now(UTC)
    with get_session() as session:
        row = session.scalar(select(PasswordResetOTP).where(PasswordResetOTP.user_id == user.id, PasswordResetOTP.used.is_(False), PasswordResetOTP.expires_at > now).order_by(PasswordResetOTP.created_at.desc()))
        if not row or row.attempts >= 5:
            return None
        row.attempts += 1
        valid = verify_password(otp, row.otp_hash)
        if valid:
            row.used = True
            session.commit()
            return user.id
        session.commit()
    return None
