from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.auth import decode_token
from app.dependencies import get_db
from app.exceptions import UnauthorizedException, NotFoundException, DatabaseException
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            raise UnauthorizedException("Неверный токен")

        user_id = int(payload["sub"])

        result = await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("Пользователь не найден")

        return user
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных пользователя")
