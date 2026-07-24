from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models import User, UserCreate, UserLogin

RANDOM_HASH = "$argon2i$v=19$m=16,t=2,p=1$YXNkYXNkYXM$AVBfoT4P1h879+Muu0tCxQ"


async def create_user(user: UserCreate, db: AsyncSession):
    try:
        new_user = User(name=user.name, password=user.password, role_id=1)
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user, ["role", "createdAt", "name"])
        return new_user
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )


async def login_user(form: UserLogin, db: AsyncSession):
    fetched_user = await db.scalar(select(User).where(User.name == form.username))
    if fetched_user is None:
        verify_password(form.password, RANDOM_HASH)
        return None
    result, updated_hash = verify_password(form.password, fetched_user._hash_password)
    if not result:
        return None
    if updated_hash is not None:
        fetched_user._hash_password = updated_hash
    return fetched_user
