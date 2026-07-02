from datetime import datetime, timedelta, timezone
from typing import Any

from functools import lru_cache

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import get_settings


@lru_cache
def get_fernet() -> Fernet:
    settings = get_settings()
    key = settings.embedding_encryption_key or Fernet.generate_key().decode("utf-8")
    return Fernet(key.encode("utf-8"))


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None


def verify_teacher(username: str, password: str) -> bool:
    settings = get_settings()
    return username == settings.teacher_username and password == settings.teacher_password
