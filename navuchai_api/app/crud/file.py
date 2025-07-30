from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from app.models import File
from app.schemas.file import FileCreate
from app.exceptions import DatabaseException, NotFoundException


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


async def get_file(db: AsyncSession, file_id: int) -> File:
    """
    Получение файла по ID
    
    Args:
        db: Сессия базы данных
        file_id: ID файла
        
    Returns:
        File: Найденный файл
        
    Raises:
        NotFoundException: Если файл не найден
        DatabaseException: При ошибке получения файла
    """
    try:
        result = await db.execute(select(File).where(File.id == file_id))
        file = result.scalar_one_or_none()
        if not file:
            raise NotFoundException(f"Файл с ID {file_id} не найден")
        return file
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении файла: {str(e)}") 