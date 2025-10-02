from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models import UserActivity
from app.schemas.user_activity import UserActivityCreate
from app.exceptions import DatabaseException


async def create_user_activity(db: AsyncSession, data: UserActivityCreate) -> UserActivity:
    try:
        record = UserActivity(
            user_id=data.user_id,
            action=data.action,
            action_ru=data.action_ru,
            context=data.context,
            ip=data.ip,
            user_agent=data.user_agent,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании записи активности: {str(e)}")


async def get_user_activities(
    db: AsyncSession,
    user_id: int,
    limit: int = 100,
    offset: int = 0,
    action: Optional[str] = None,
) -> List[UserActivity]:
    try:
        stmt = select(UserActivity).where(UserActivity.user_id == user_id)
        if action:
            stmt = stmt.where(UserActivity.action == action)
        stmt = stmt.order_by(UserActivity.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении активности пользователя")


