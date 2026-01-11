"""Encryption utilities for storing API keys securely."""

import base64
import hashlib
import platform
import uuid

from cryptography.fernet import Fernet, InvalidToken


def _machine_id() -> str:
    node = uuid.getnode()
    host = platform.node()
    return f"{node}-{host}"


def _derive_key(machine_id: str) -> bytes:
    seed = f"VCat:{machine_id}".encode("utf-8")
    digest = hashlib.sha256(seed).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_derive_key(_machine_id()))


def encrypt_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    token = _fernet().encrypt(api_key.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_api_key(token: str) -> str:
    if not token:
        return ""
    try:
        value = _fernet().decrypt(token.encode("utf-8"))
        return value.decode("utf-8")
    except InvalidToken:
        return ""
