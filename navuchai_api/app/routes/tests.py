from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_tests,
    get_test,
    create_test,
    delete_test,
    update_test,
    get_user_tests,
    get_test_by_code,
    get_test_by_access_code,
    admin_moderator_required,
    authorized_required
)
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException
from app.models import User
from app.schemas.test import TestCreate, TestResponse, TestWithDetails, TestUpdate, TestWithAccessDetails

router = APIRouter(prefix="/api/tests", tags=["Tests"])


@router.get("/", response_model=list[TestWithDetails])
async def get_all_tests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_moderator_required)
):
    try:
        return await get_tests(db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка тестов")


@router.get("/my/", response_model=list[TestWithAccessDetails])
async def get_my_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        return await get_user_tests(db, current_user.id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка тестов пользователя")


@router.get("/{test_id}/", response_model=TestWithDetails)
async def get_test_by_id(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        return await get_test(db, test_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении теста")


@router.post("/", response_model=TestResponse)
async def create_new_test(
    test: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    try:
        return await create_test(db, test)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании теста")


@router.put("/{test_id}/", response_model=TestResponse)
async def update_test_by_id(
    test_id: int,
    test: TestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    try:
        return await update_test(db, test_id, test)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении теста")


@router.delete("/{test_id}/", response_model=TestResponse)
async def delete_test_by_id(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    try:
        return await delete_test(db, test_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении теста")


@router.get("/public/{code}/", response_model=TestWithDetails)
async def get_public_test_by_code(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Получение публичного теста по коду (без авторизации)"""
    try:
        return await get_test_by_code(db, code)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении теста")


@router.get("/private/{access_code}/", response_model=TestWithDetails)
async def get_private_test_by_access_code(
    access_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """Получение приватного теста по access_code (требует авторизации и проверки доступа)"""
    try:
        return await get_test_by_access_code(db, access_code, current_user.id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении теста")
