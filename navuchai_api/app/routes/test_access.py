from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from pydantic import BaseModel

from app.dependencies import get_db
from app.crud import admin_moderator_required
from app.crud import test_access as crud
from app.models.user import User
from app.schemas.test_access import TestAccessCreate, TestAccessResponse, TestAccessGroupCreate
from app.schemas.test import TestResponse
from app.exceptions import DatabaseException, NotFoundException

router = APIRouter(prefix="/api/test-access", tags=["Test Access"])


@router.post("/user/", response_model=TestAccessResponse)
async def create_user_test_access(
        test_access: TestAccessCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
) -> TestAccessResponse:
    try:
        # Проверяем, нет ли уже доступа у пользователя к этому тесту
        existing_access = await crud.get_test_access(db, test_access.test_id, test_access.user_id)
        if existing_access:
            raise HTTPException(
                status_code=400,
                detail="У пользователя уже есть доступ к этому тесту"
            )
        if test_access.status_id is None:
            test_access.status_id = 1
        return await crud.create_test_access(db, test_access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/group/", response_model=List[TestAccessResponse])
async def create_group_test_access(
        data: TestAccessGroupCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
) -> List[TestAccessResponse]:
    try:
        return await crud.create_group_test_access(
            db=db,
            test_id=data.test_id,
            group_id=data.group_id,
            status_id=data.status_id
        )
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{test_id}/access/", response_model=TestResponse)
async def update_test_access_type(
        test_id: int,
        access: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
) -> TestResponse:
    """
    Изменение типа доступа к тесту (public/private)
    """
    try:
        return await crud.update_test_access(db, test_id, access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{test_id}/code/", response_model=dict)
async def get_test_access_code(
        test_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
) -> dict:
    """
    Получение кода доступа к тесту:
    - Если тест публичный, возвращает code из таблицы tests
    - Если тест приватный, возвращает access_code из таблицы test_access
    """
    try:
        return await crud.get_test_access_code(db, test_id, current_user.id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[TestAccessResponse])
async def get_all_test_accesses(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
) -> List[TestAccessResponse]:
    """Получить все доступы пользователей к тестам"""
    try:
        accesses = await crud.get_all_test_accesses(db)
        return [TestAccessResponse.from_orm(a) for a in accesses]
    except DatabaseException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/user/{test_id}/{user_id}/")
async def delete_user_test_access(
        test_id: int,
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
):
    """Удалить доступ пользователя к тесту"""
    try:
        return await crud.delete_test_access(db, test_id, user_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/group/{test_id}/{group_id}/", response_model=dict)
async def delete_group_test_access_route(
        test_id: int,
        group_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
) -> dict:
    """Удаление доступа к тесту для всей группы"""
    try:
        return await crud.delete_group_test_access(db, test_id, group_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{test_id}/users/", response_model=List[Dict])
async def get_test_users_route(
        test_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
):
    """Получить список пользователей, назначенных на тест"""
    try:
        return await crud.get_test_users(db, test_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{test_id}/all-users/", response_model=List[Dict])
async def get_all_test_users_route(
        test_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
):
    """Получить список всех пользователей, назначенных на тест (включая пользователей в группах)"""
    try:
        return await crud.get_all_test_users(db, test_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{test_id}/groups/", response_model=List[Dict])
async def get_test_groups_route(
        test_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
):
    """Получить список групп, назначенных на тест"""
    try:
        return await crud.get_test_groups(db, test_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


class UpdateTestAccessStatusRequest(BaseModel):
    status_id: int


@router.put("/user/{test_id}/{user_id}/status/", response_model=TestAccessResponse)
async def update_test_access_status_by_user_route(
        test_id: int,
        user_id: int,
        body: UpdateTestAccessStatusRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
):
    """Обновить статус доступа к тесту по test_id и user_id"""
    try:
        return await crud.update_test_access_status_by_user(db, test_id, user_id, body.status_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))
