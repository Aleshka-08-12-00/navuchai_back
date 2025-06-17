from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.crud import admin_moderator_required
from app.crud import test_access_status as crud
from app.models.user import User
from app.schemas.test_access_status import TestAccessStatusCreate, TestAccessStatusResponse
from app.exceptions import DatabaseException, NotFoundException

router = APIRouter(prefix="/api/test-access-status", tags=["Test Access Status"])


@router.get("/", response_model=List[TestAccessStatusResponse])
async def get_test_access_statuses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    """Получение всех статусов доступа к тесту"""
    try:
        return await crud.get_test_access_statuses(db)
    except DatabaseException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{status_id}", response_model=TestAccessStatusResponse)
async def get_test_access_status(
    status_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    """Получение статуса доступа к тесту по ID"""
    try:
        return await crud.get_test_access_status(db, status_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/", response_model=TestAccessStatusResponse)
async def create_test_access_status(
    status: TestAccessStatusCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    """Создание нового статуса доступа к тесту"""
    try:
        return await crud.create_test_access_status(db, status)
    except DatabaseException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{status_id}", response_model=TestAccessStatusResponse)
async def update_test_access_status(
    status_id: int,
    status: TestAccessStatusCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    """Обновление статуса доступа к тесту"""
    try:
        return await crud.update_test_access_status(db, status_id, status)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{status_id}", response_model=TestAccessStatusResponse)
async def delete_test_access_status(
    status_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    """Удаление статуса доступа к тесту"""
    try:
        return await crud.delete_test_access_status(db, status_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e)) 