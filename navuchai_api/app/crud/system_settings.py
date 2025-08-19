from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
from app.models.system_settings import SystemSettings
from app.schemas.system_settings import SystemSettingsCreate, SystemSettingsUpdate
from app.exceptions import NotFoundException, DatabaseException

async def get_system_settings(db: AsyncSession):
    try:
        result = await db.execute(select(SystemSettings).order_by(SystemSettings.id))
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка системных настроек")


async def get_system_setting(db: AsyncSession, setting_id: int):
    try:
        result = await db.execute(select(SystemSettings).filter(SystemSettings.id == setting_id))
        setting = result.scalar_one_or_none()
        if not setting:
            raise NotFoundException("Системная настройка не найдена")
        return setting
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении системной настройки")


async def get_system_setting_by_code(db: AsyncSession, code: str):
    try:
        result = await db.execute(select(SystemSettings).filter(SystemSettings.code == code))
        setting = result.scalar_one_or_none()
        if not setting:
            raise NotFoundException("Системная настройка не найдена")
        return setting
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении системной настройки")


async def create_system_setting_crud(db: AsyncSession, setting_data: SystemSettingsCreate):
    try:
        db_obj = SystemSettings(
            name=setting_data.name,
            code=setting_data.code,
            settings=setting_data.settings
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при создании системной настройки")


async def update_system_setting(db: AsyncSession, setting_id: int, setting_data: SystemSettingsUpdate):
    try:
        existing_setting = await get_system_setting(db, setting_id)
        update_data = setting_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_setting, field, value)
        db.add(existing_setting)
        await db.commit()
        await db.refresh(existing_setting)
        return existing_setting
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении системной настройки")


async def delete_system_setting(db: AsyncSession, setting_id: int):
    try:
        setting = await get_system_setting(db, setting_id)
        await db.delete(setting)
        await db.commit()
        return setting
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при удалении системной настройки")


async def get_settings_by_codes(db: AsyncSession, codes: List[str]) -> Dict[str, Any]:
    """Получить настройки по кодам и вернуть как словарь"""
    try:
        result = await db.execute(select(SystemSettings).filter(SystemSettings.code.in_(codes)))
        settings = result.scalars().all()
        return {setting.code: setting.settings for setting in settings}
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении настроек по кодам")


async def update_settings_by_code(db: AsyncSession, code: str, settings: Dict[str, Any]):
    """Обновить только настройки по коду"""
    try:
        setting = await get_system_setting_by_code(db, code)
        setting.settings = settings
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
        return setting
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении настроек") 