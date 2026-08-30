from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories import user_repo


class AuthError(Exception):
    pass


async def register_user(session: AsyncSession, username: str, email: str, password: str):
    existing = await user_repo.get_by_username(session, username)
    if existing:
        raise AuthError("Username already taken")
    hashed = hash_password(password)
    return await user_repo.create_user(session, username, email, hashed)


async def login_user(session: AsyncSession, username: str, password: str) -> str:
    user = await user_repo.get_by_username(session, username)
    if not user or not verify_password(password, user.password):
        raise AuthError("Invalid username or password")
    return create_access_token(user.userid)