from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Role


async def get_roles(db: AsyncSession) -> list[Role]:
    """
    Получение списка всех ролей
    
    Args:
        db: Сессия базы данных
        
    Returns:
        list[Role]: Список ролей
    """
    result = await db.execute(select(Role).order_by(Role.id))
    return result.scalars().all() 