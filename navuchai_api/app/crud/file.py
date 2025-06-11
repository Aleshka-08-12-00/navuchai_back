from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models import File
from app.schemas.file import FileCreate
from app.exceptions import DatabaseException


async def create_file(db: AsyncSession, file_data: FileCreate) -> File:
    """
    Создание записи о файле в БД
    
    Args:
        db: Сессия базы данных
        file_data: Данные файла
        
    Returns:
        File: Созданная запись о файле
        
    Raises:
        DatabaseException: При ошибке создания записи
    """
    try:
        db_file = File(**file_data.dict())
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
        return db_file
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании записи о файле: {str(e)}") 