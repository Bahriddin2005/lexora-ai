from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import ACCESS_COOKIE, REFRESH_COOKIE, get_current_user
from app.core.errors import AppError, conflict, unauthorized
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    verify_password,
)
from app.models import RefreshToken, User
from app.schemas.auth import AuthOut, LoginIn, RegisterIn, UserOut, UserUpdateIn

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_tokens(session: AsyncSession, user: User, request: Request, response: Response) -> str:
    access = create_access_token(str(user.id), user.role)
    raw, token_hash = new_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
            user_agent=(request.headers.get("user-agent") or "")[:300],
        )
    )
    common = {"httponly": True, "samesite": "lax", "secure": settings.cookie_secure, "path": "/"}
    response.set_cookie(ACCESS_COOKIE, access, max_age=settings.access_token_minutes * 60, **common)
    response.set_cookie(REFRESH_COOKIE, raw, max_age=settings.refresh_token_days * 86400, **common)
    return access


def _clear_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


@router.post("/register", response_model=AuthOut, status_code=201)
async def register(
    data: RegisterIn, request: Request, response: Response, session: AsyncSession = Depends(get_db)
):
    email = data.email.lower()
    if await session.scalar(select(User.id).where(User.email == email)):
        raise conflict("Bu email bilan hisob allaqachon mavjud")
    user = User(
        email=email,
        password_hash=hash_password(data.password),
        display_name=data.display_name or email.split("@")[0],
        last_login_at=func.now(),
    )
    session.add(user)
    await session.flush()
    access = await _issue_tokens(session, user, request, response)
    await session.commit()
    await session.refresh(user)
    return AuthOut(user=UserOut.model_validate(user), access_token=access)


@router.post("/login", response_model=AuthOut)
async def login(data: LoginIn, request: Request, response: Response, session: AsyncSession = Depends(get_db)):
    user = await session.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        raise AppError(401, "invalid_credentials", "Email yoki parol noto‘g‘ri")
    if not user.is_active:
        raise AppError(403, "forbidden", "Hisob bloklangan")
    user.last_login_at = datetime.now(UTC)
    access = await _issue_tokens(session, user, request, response)
    await session.commit()
    await session.refresh(user)
    return AuthOut(user=UserOut.model_validate(user), access_token=access)


@router.post("/refresh", response_model=AuthOut)
async def refresh(request: Request, response: Response, session: AsyncSession = Depends(get_db)):
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise unauthorized()
    token = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw)))
    now = datetime.now(UTC)
    if not token or token.revoked_at or token.expires_at <= now:
        _clear_cookies(response)
        raise unauthorized("Sessiya muddati tugagan")
    user = await session.get(User, token.user_id)
    if not user or not user.is_active:
        raise unauthorized()
    token.revoked_at = now
    access = await _issue_tokens(session, user, request, response)
    await session.commit()
    await session.refresh(user)
    return AuthOut(user=UserOut.model_validate(user), access_token=access)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, session: AsyncSession = Depends(get_db)):
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == hash_token(raw), RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await session.commit()
    _clear_cookies(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdateIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    if data.display_name is not None:
        user.display_name = data.display_name.strip() or user.display_name
    if data.ui_language is not None:
        user.ui_language = data.ui_language
    await session.commit()
    await session.refresh(user)
    return user
