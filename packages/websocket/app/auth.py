import logging

import jwt

from .config import Settings

logger = logging.getLogger(__name__)


def decode_user_id(token: str | None, settings: Settings) -> str | None:
    """Best-effort JWT verification. Never raises — a missing or invalid
    token simply resolves to a guest (None), matching the Node service's
    guest-viewing behavior. Callers that need to gate an action on auth
    (e.g. placing a pixel) must check the returned value themselves."""
    if not token:
        return None
    try:
        decoded = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as err:
        logger.info("JWT verification failed: %s", err)
        return None
    return decoded.get("userId")
