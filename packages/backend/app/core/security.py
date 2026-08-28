
from pwdlib import PasswordHash

from datetime import datetime, timedelta, timezone
import jwt
from app.config import settings


password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """Turn a plain-text password into a hash, safe to store in the DB."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login attempt's password against the stored hash."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT. Pass data={"sub": username}.
    If expires_delta isn't given, falls back to settings.jwt_expires_in_minutes.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_in_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Verify and decode a token. Raises jwt.InvalidTokenError if invalid, tampered, or expired."""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])