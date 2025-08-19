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
    get_test_universal,
    root_admin_moderator_required,
    authorized_required,
    get_current_user_optional
)
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException
from app.models import User
from app.schemas.test import TestCreate, TestResponse, TestWithDetails, TestUpdate, TestWithAccessDetails
from pydantic import BaseModel


class CheckTestAvailabilityNoGroupBody(BaseModel):
    user_id: int
    test_id: int


class CheckTestAvailabilityResponse(BaseModel):
    is_available: bool
    message: str
    attempts_left: int | None = None
    attempts_used: int | None = None
    attempts_total: int | None = None


router = APIRouter(prefix="/api/tests", tags=["Tests"])


@router.get("/", response_model=list[TestWithDetails])
async def get_all_tests(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(root_admin_moderator_required)
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


@router.get("/test/{identifier}/", response_model=TestWithDetails)
async def get_test_route(
    identifier: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """Получение теста по ID, публичному коду или приватному access_code"""
    try:
        return await get_test_universal(db, identifier, current_user)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении теста")


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
    current_user: User = Depends(root_admin_moderator_required)
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
    current_user: User = Depends(root_admin_moderator_required)
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
    current_user: User = Depends(root_admin_moderator_required)
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


@router.post("/check-availability/", response_model=CheckTestAvailabilityResponse)
async def check_test_availability_no_group(
    data: CheckTestAvailabilityNoGroupBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    from datetime import datetime, timezone
    from app.crud.test import get_test_by_id
    from app.crud.result import count_user_attempts_without_group

    # Получаем тест (SQLAlchemy модель)
    test = await get_test_by_id(db, data.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    # Даты доступа берём из теста (если есть)
    test_date_start = getattr(test, 'date_start', None)
    test_date_end = getattr(test, 'date_end', None)

    def now_for(dt: datetime | None) -> datetime:
        if dt is None:
            return datetime.utcnow()
        return datetime.now(timezone.utc) if dt.tzinfo else datetime.utcnow()

    def fmt(dt: datetime | None) -> str | None:
        if not dt:
            return None
        return dt.strftime("%d.%m.%Y %H:%M")

    # Проверка доступности по датам
    if test_date_start is not None and now_for(test_date_start) < test_date_start:
        start_str = fmt(test_date_start)
        end_str = fmt(test_date_end)
        msg = (
            f"Тест недоступен: доступ откроется {start_str}."
            if not end_str
            else f"Тест недоступен: доступ откроется {start_str} и будет доступен до {end_str}."
        )
        return CheckTestAvailabilityResponse(
            is_available=False,
            message=msg,
            attempts_left=None,
            attempts_used=None,
            attempts_total=None
        )

    if test_date_end is not None and now_for(test_date_end) > test_date_end:
        end_str = fmt(test_date_end)
        return CheckTestAvailabilityResponse(
            is_available=False,
            message=f"Тест недоступен: период доступа завершился {end_str}.",
            attempts_left=None,
            attempts_used=None,
            attempts_total=None
        )

    # Подсчёт попыток без группы
    attempts_total = getattr(test, 'attempts', None)
    try:
        attempts_total = int(attempts_total) if attempts_total is not None else None
    except Exception:
        attempts_total = None

    attempts_used = await count_user_attempts_without_group(db, data.user_id, data.test_id)

    if attempts_total is not None:
        attempts_left = max(attempts_total - attempts_used, 0)
        if attempts_left <= 0:
            return CheckTestAvailabilityResponse(
                is_available=False,
                message="Все попытки израсходованы",
                attempts_left=0,
                attempts_used=attempts_used,
                attempts_total=attempts_total
            )
        return CheckTestAvailabilityResponse(
            is_available=True,
            message=f"Тест доступен. Осталось попыток: {attempts_left}",
            attempts_left=attempts_left,
            attempts_used=attempts_used,
            attempts_total=attempts_total
        )

    # attempts не задан — считаем попытки неограниченными
    return CheckTestAvailabilityResponse(
        is_available=True,
        message="Тест доступен",
        attempts_left=None,
        attempts_used=attempts_used,
        attempts_total=None
    )


@router.get("/debug/{test_id}/")
async def debug_test_structure(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """Временный эндпоинт для отладки структуры теста"""
    from app.crud.test import get_test_by_id
    
    test = await get_test_by_id(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Получаем все атрибуты модели
    test_dict = {}
    for column in test.__table__.columns:
        test_dict[column.name] = getattr(test, column.name)
    
    return {
        "test_id": test_id,
        "all_columns": test_dict,
        "has_attempts": hasattr(test, 'attempts'),
        "has_date_start": hasattr(test, 'date_start'),
        "has_date_end": hasattr(test, 'date_end'),
        "attempts_value": getattr(test, 'attempts', 'NOT_FOUND'),
        "date_start_value": getattr(test, 'date_start', 'NOT_FOUND'),
        "date_end_value": getattr(test, 'date_end', 'NOT_FOUND'),
    }
