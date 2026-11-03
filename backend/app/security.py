"""Password hashing (Argon2id), JWT, and RFC 6238 TOTP (no fixed demo OTP)."""
import base64
import hashlib
import hmac
import struct
import time
import uuid
from datetime import datetime, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from .config import settings

_ph = PasswordHasher()
ALG = "HS256"
STAGE_FULL, STAGE_OTP = "full", "otp"


def hash_password(pw: str) -> str:
    return _ph.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, pw)
    except (VerifyMismatchError, InvalidHashError):
        return False


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def issue_token(emp_no: str, stage: str, ttl: int, log_id: int | None = None, now: float | None = None) -> str:
    iat = int(now if now is not None else time.time())
    claims = {"sub": emp_no, "stage": stage, "iat": iat, "exp": iat + ttl, "jti": uuid.uuid4().hex}
    if log_id is not None:
        claims["lid"] = log_id
    return jwt.encode(claims, settings.app_secret, algorithm=ALG)


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError on invalid/expired tokens."""
    return jwt.decode(token, settings.app_secret, algorithms=[ALG], options={"require": ["sub", "exp", "stage"]})


def totp_at(secret_b32: str, counter: int, digits: int = 6) -> str:
    key = base64.b32decode(secret_b32.upper() + "=" * (-len(secret_b32) % 8))
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    off = mac[-1] & 0x0F
    code = (struct.unpack(">I", mac[off:off + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)


def verify_totp(secret_b32: str, code: str, now: float | None = None, window: int = 1) -> int | None:
    """Return matched time-step counter (±window) or None."""
    if not code or not code.isdigit() or len(code) != 6:
        return None
    ctr = int((now if now is not None else time.time()) // 30)
    for d in range(-window, window + 1):
        if hmac.compare_digest(totp_at(secret_b32, ctr + d), code):
            return ctr + d
    return None
