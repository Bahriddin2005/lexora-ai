import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import forbidden, unauthorized
from app.core.security import decode_access_token
from app.models import User
from app.models.enums import UserRole

ACCESS_COOKIE = "lx_access"
REFRESH_COOKIE = "lx_refresh"


def client_ip(request: Request) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _token(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.cookies.get(ACCESS_COOKIE)


async def get_current_user_optional(request: Request, session: AsyncSession = Depends(get_db)) -> User | None:
    token = _token(request)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None
    user = await session.get(User, user_id)
    return user if user and user.is_active else None


async def get_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    if user is None:
        raise unauthorized()
    return user


async def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.EDITOR, UserRole.ADMIN):
        raise forbidden()
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise forbidden()
    return user
