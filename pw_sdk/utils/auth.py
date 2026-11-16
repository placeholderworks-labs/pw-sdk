import hashlib
import hmac
import secrets


def bearer(header: str | None) -> str:
    value = (header or "").strip()
    return value[7:].strip() if value.lower().startswith("bearer ") else value


def authorization_value(token: str) -> str:
    token = (token or "").strip()
    return token if " " in token else f"Bearer {token}"


def same_secret(expected: str | None, given: str | None) -> bool:
    if not expected or not given:
        return False
    return hmac.compare_digest(expected.encode(), given.encode())


def token_hash(token: str, salt: str = "") -> str:
    return hashlib.sha256(f"{salt}{token}".encode()).hexdigest()


def new_token(nbytes: int = 24) -> str:
    return secrets.token_urlsafe(nbytes)
