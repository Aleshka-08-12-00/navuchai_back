from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any

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
from app.schemas.question import QuestionPositionsUpdateRequest, QuestionPositionsUpdateResponse
from pydantic import BaseModel
from datetime import datetime, timezone
from app.models.test import TestAccessEnum, AnswerViewModeEnum


class CheckTestAvailabilityNoGroupBody(BaseModel):
    user_id: int
    test_id: int


class CheckTestAvailabilityResponse(BaseModel):
    is_available: bool
    message: str
    attempts_left: int | None = None
    attempts_used: int | None = None
    attempts_total: int | None = None


class TestGroupInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    time_limit: Optional[int] = None
    status_name: Optional[str] = None
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    image: Optional[str] = None
    thumbnail: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TestWithGroupsInfo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    category_name: str
    creator_id: Optional[int] = None
    creator_name: str
    access_timestamp: datetime
    status_id: int
    status_name: str
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    frozen: bool
    locale_id: int
    locale_code: str
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    image: Optional[str] = None
    thumbnail: Optional[str] = None
    percent: Optional[float] = None
    completed: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    access: TestAccessEnum
    answer_view_mode: AnswerViewModeEnum
    attempts: Optional[int] = None
    required_score: int = 0
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    code: Optional[str] = None
    grade_options: Optional[Dict[str, Any]] = None
    groups: List[TestGroupInfo] = []


router = APIRouter(prefix="/api/tests", tags=["Tests"])





@router.get("/with-groups/", response_model=List[TestWithGroupsInfo])
async def get_tests_with_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """Возвращает тесты с информацией о группах, в которых они состоят."""
    from app.crud.test_group import get_test_group
    from app.models.test_group_test import TestGroupTest
    
    try:
        # Получаем тесты в зависимости от роли пользователя
        if current_user.role and current_user.role.code in ('admin', 'root'):
            tests = await get_tests(db)
        else:
            tests = await get_user_tests(db, current_user.id)
        
        # Для каждого теста получаем группы
        tests_with_groups = []
        for test in tests:
            # Получаем группы для теста
            stmt = (
                select(TestGroupTest.test_group_id)
                .where(TestGroupTest.test_id == test["id"])
                .order_by(TestGroupTest.test_group_id)
            )
            result = await db.execute(stmt)
            group_ids = result.scalars().all()
            
            # Получаем информацию о группах
            groups_info = []
            for group_id in group_ids:
                try:
                    group = await get_test_group(db, group_id)
                    
                    group_info = {
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                        "date_start": group.date_start,
                        "date_end": group.date_end,
                        "time_limit": group.time_limit,
                        "status_name": group.status.name if group.status else None,
                        "status_name_ru": group.status.name_ru if group.status else None,
                        "status_color": group.status.color if group.status else None,
                        "image": group.img.path if group.img else None,
                        "thumbnail": group.thumbnail.path if group.thumbnail else None,
                        "created_at": group.created_at,
                        "updated_at": group.updated_at,
                    }
                    groups_info.append(group_info)
                except Exception as e:
                    # Пропускаем группы, к которым нет доступа
                    print(f"Ошибка при получении группы {group_id}: {str(e)}")
                    continue
            
            # Добавляем группы к тесту
            test_with_groups = test.copy()
            # Приводим image/thumbnail теста к строковым путям, если это объекты File
            img_val = test.get("image")
            thumb_val = test.get("thumbnail")
            test_with_groups["image"] = getattr(img_val, "path", img_val)
            test_with_groups["thumbnail"] = getattr(thumb_val, "path", thumb_val)
            test_with_groups["groups"] = groups_info
            tests_with_groups.append(test_with_groups)
        
        return tests_with_groups
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении тестов с группами: {str(e)}")


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


@router.put("/{test_id}/questions/positions/", response_model=QuestionPositionsUpdateResponse)
async def update_question_positions(
    test_id: int,
    data: QuestionPositionsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(root_admin_moderator_required)
):
    """
    Обновляет позиции вопросов в тесте.
    Требует права администратора или модератора.
    """
    from app.crud.question import update_question_positions
    
    try:
        # Преобразуем данные в нужный формат для CRUD функции
        positions_data = [{"questionId": item.questionId, "position": item.position} for item in data]
        
        result = await update_question_positions(db, test_id, positions_data)
        return QuestionPositionsUpdateResponse(message=result["message"])
        
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {str(e)}")



