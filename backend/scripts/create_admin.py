"""Create or promote an admin: `uv run python -m scripts.create_admin email password`."""

import asyncio
import sys

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import User
from app.models.enums import UserRole


async def main(email: str, password: str) -> None:
    email = email.lower()
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, password_hash=hash_password(password), display_name="Admin")
            session.add(user)
        else:
            user.password_hash = hash_password(password)
        user.role = UserRole.ADMIN
        user.is_active = True
        await session.commit()
    print(f"admin ready: {email}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or len(sys.argv[2]) < 8:
        sys.exit("usage: python -m scripts.create_admin EMAIL PASSWORD(>=8 chars)")
    asyncio.run(main(sys.argv[1], sys.argv[2]))
