"""
Authentication helpers: password hashing and session tokens.

Passwords  — hashlib.scrypt (no extra dependencies)
Tokens     — secrets.token_hex(32), stored as sha256 hash
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone


# ── passwords ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return 'salt_hex:hash_hex' suitable for storing in the database."""
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Return True if password matches the stored hash."""
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


# ── session tokens ─────────────────────────────────────────────────────────────

SESSION_TTL_DAYS = 30


def generate_token() -> tuple[str, str]:
    """Return (raw_token, token_hash). Send raw to client, store hash in DB."""
    raw = secrets.token_hex(32)
    hashed = _hash_token(raw)
    return raw, hashed


def hash_token(raw: str) -> str:
    return _hash_token(raw)


def token_expires_at() -> str:
    """Return ISO-8601 expiry timestamp (UTC)."""
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)
    return expires.isoformat()


def token_is_expired(expires_at: str) -> bool:
    expires = datetime.fromisoformat(expires_at)
    return datetime.now(timezone.utc) > expires


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
