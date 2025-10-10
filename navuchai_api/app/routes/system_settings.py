from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any

from app.crud.system_settings import (
    get_system_settings, get_system_setting, get_system_setting_by_code,
    create_system_setting_crud, update_system_setting, delete_system_setting,
    get_settings_by_codes, update_settings_by_code
)
from app.dependencies import get_db
from app.crud import authorized_required, root_admin_required
from app.exceptions import NotFoundException, DatabaseException, BadRequestException
from app.schemas.system_settings import (
    SystemSettingsResponse, SystemSettingsCreate, SystemSettingsUpdate,
    SettingsUpdateRequest, SettingsByCodesRequest
)
from app.models.user import User

router = APIRouter(prefix="/api/system-settings", tags=["System Settings"])


@router.get("/", response_model=List[SystemSettingsResponse], dependencies=[Depends(root_admin_required)])
async def list_system_settings(
        db: AsyncSession = Depends(get_db)
):
    """
    Получить список всех системных настроек
    """
    return await get_system_settings(db)


@router.post("/", response_model=SystemSettingsResponse, dependencies=[Depends(root_admin_required)])
async def create_system_setting(
        setting_data: SystemSettingsCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Создать новую системную настройку
    """
    try:
        # Проверяем, что код уникален
        try:
            existing_setting = await get_system_setting_by_code(db, setting_data.code)
        except NotFoundException:
            existing_setting = None
        if existing_setting:
            raise BadRequestException("Настройка с таким кодом уже существует")

        return await create_system_setting_crud(db, setting_data)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании системной настройки")


@router.get("/{setting_id}/", response_model=SystemSettingsResponse)
async def get_system_setting_by_id(
        setting_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    """
    Получить системную настройку по ID
    """
    try:
        return await get_system_setting(db, setting_id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении системной настройки")


# @router.get("/by-code/{code}/", response_model=SystemSettingsResponse)
# async def get_system_setting_by_code_route(
#         code: str,
#         db: AsyncSession = Depends(get_db),
#         current_user: User = Depends(authorized_required)
# ):
#     """
#     Получить системную настройку по коду
#     """
#     try:
#         return await get_system_setting_by_code(db, code)
#     except SQLAlchemyError:
#         raise DatabaseException("Ошибка при получении системной настройки")


@router.put("/{setting_id}/", response_model=SystemSettingsResponse, dependencies=[Depends(root_admin_required)])
async def update_system_setting_by_id(
        setting_id: int,
        setting_data: SystemSettingsUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    Обновить системную настройку
    """
    try:
        # Если обновляется код, проверяем уникальность
        if setting_data.code:
            existing_setting = await get_system_setting_by_code(db, setting_data.code)
            if existing_setting and existing_setting.id != setting_id:
                raise BadRequestException("Настройка с таким кодом уже существует")

        return await update_system_setting(db, setting_id, setting_data)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении системной настройки")


# @router.patch("/by-code/{code}/settings/", response_model=SystemSettingsResponse)
# async def update_settings_by_code_route(
#         code: str,
#         settings_data: SettingsUpdateRequest,
#         db: AsyncSession = Depends(get_db),
#         current_user: User = Depends(authorized_required)
# ):
#     """
#     Обновить только настройки по коду
#     """
#     try:
#         return await update_settings_by_code(db, code, settings_data.settings)
#     except SQLAlchemyError:
#         raise DatabaseException("Ошибка при обновлении настроек")


# @router.post("/by-codes/", response_model=Dict[str, Any])
# async def get_settings_by_codes_route(
#         request_data: SettingsByCodesRequest,
#         db: AsyncSession = Depends(get_db),
#         current_user: User = Depends(authorized_required)
# ):
#     """
#     Получить настройки по списку кодов
#     """
#     try:
#         return await get_settings_by_codes(db, request_data.codes)
#     except SQLAlchemyError:
#         raise DatabaseException("Ошибка при получении настроек по кодам")


@router.delete("/{setting_id}/", response_model=SystemSettingsResponse, dependencies=[Depends(root_admin_required)])
async def delete_system_setting_by_id(
        setting_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Удалить системную настройку
    """
    try:
        return await delete_system_setting(db, setting_id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении системной настройки")
