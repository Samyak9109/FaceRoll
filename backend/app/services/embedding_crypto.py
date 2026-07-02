import json

from app.core.security import get_fernet


def encrypt_embedding(embedding: list[float]) -> str:
    payload = json.dumps(embedding, separators=(",", ":")).encode("utf-8")
    return get_fernet().encrypt(payload).decode("utf-8")


def decrypt_embedding(token: str) -> list[float]:
    payload = get_fernet().decrypt(token.encode("utf-8"))
    return json.loads(payload.decode("utf-8"))
