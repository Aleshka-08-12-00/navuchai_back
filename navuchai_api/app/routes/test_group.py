from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.test_group import TestGroup, TestGroupCreate, TestGroupUpdate, TestGroupList, TestGroupEnriched
from app.schemas.test_group_test import TestGroupTest, TestGroupTestCreate
from app.crud import test_group as crud
from app.dependencies import get_db
from app.schemas.test import TestWithDetails
from app.crud import root_admin_moderator_required, authorized_required, get_test_groups_with_categories
from sqlalchemy.exc import SQLAlchemyError
from app.exceptions import NotFoundException, DatabaseException
from pydantic import BaseModel
from app.schemas.test_group import TestGroupWithCategories

router = APIRouter(prefix="/api/test-groups", tags=["Test groups"])


class RemoveTestFromGroupBody(BaseModel):
    test_id: int
    test_group_id: int


@router.delete("/remove-test/")
async def remove_test_from_group(
        data: RemoveTestFromGroupBody,
        db: AsyncSession = Depends(get_db),
        user=Depends(root_admin_moderator_required)
):
    from app.crud import test_group as crud
    return await crud.remove_test_from_group(db, data.test_id, data.test_group_id)


@router.get("/", response_model=List[TestGroupEnriched])
async def list_test_groups(db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        # Получаем роль пользователя
        user_role_code = user.role.code if user.role else None
        return await crud.get_test_groups_by_user_access(db, user.id, user_role_code)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка групп")


@router.get("/with-categories/", response_model=List[TestGroupWithCategories])
async def get_test_groups_with_categories_route(
        db: AsyncSession = Depends(get_db),
        user=Depends(authorized_required)
):
    """
    Получение всех доступных групп тестов с группировкой тестов по категориям.
    Для админа и модератора - все группы, для пользователя - только доступные.
    """
    try:
        user_role_code = user.role.code if user.role else None
        return await get_test_groups_with_categories(db, user.id, user_role_code)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении групп с категориями")


@router.get("/{group_id}/", response_model=TestGroupEnriched)
async def get_test_group(group_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        # Получаем роль пользователя
        user_role_code = user.role.code if user.role else None
        group = await crud.get_test_group_with_access_check(db, group_id, user.id, user_role_code)
        # enrich
        group_dict = {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                      for k, v in group.__dict__.items()
                      if not k.startswith('_')
                      and k not in {'status', 'img', 'thumbnail'}
                      and not isinstance(v, (dict, list, set, tuple))}
        if hasattr(group, 'status') and group.status:
            group_dict['status_name'] = group.status.name
            group_dict['status_name_ru'] = group.status.name_ru
            group_dict['status_color'] = group.status.color
        else:
            group_dict['status_name'] = None
            group_dict['status_name_ru'] = None
            group_dict['status_color'] = None
        group_dict['image'] = group.img.path if hasattr(group, 'img') and group.img else None
        group_dict['thumbnail'] = group.thumbnail.path if hasattr(group, 'thumbnail') and group.thumbnail else None
        return group_dict
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении группы")


@router.post("/", response_model=TestGroup)
async def create_test_group(data: TestGroupCreate, db: AsyncSession = Depends(get_db),
                            user=Depends(root_admin_moderator_required)):
    try:
        return await crud.create_test_group(db, data, creator_user_id=user.id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании группы")


@router.put("/{group_id}/", response_model=TestGroup)
async def update_test_group(group_id: int, data: TestGroupUpdate, db: AsyncSession = Depends(get_db),
                            user=Depends(root_admin_moderator_required)):
    try:
        return await crud.update_test_group(db, group_id, data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении группы")


@router.delete("/{group_id}/", response_model=TestGroup)
async def delete_test_group(group_id: int, db: AsyncSession = Depends(get_db), user=Depends(root_admin_moderator_required)):
    try:
        return await crud.delete_test_group(db, group_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении группы")


@router.post("/add-test/", response_model=TestGroupTest)
async def add_test_to_group(data: TestGroupTestCreate, db: AsyncSession = Depends(get_db),
                            user=Depends(root_admin_moderator_required)):
    try:
        return await crud.add_test_to_group(db, data)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при добавлении теста в группу")


@router.get("/{group_id}/tests/", response_model=List[TestWithDetails])
async def get_tests_by_group_id(
        group_id: int,
        db: AsyncSession = Depends(get_db),
        user=Depends(authorized_required)
):
    try:
        # Сначала проверяем доступ к группе
        user_role_code = user.role.code if user.role else None
        await crud.get_test_group_with_access_check(db, group_id, user.id, user_role_code)
        # Если доступ есть, возвращаем тесты с учетом роли пользователя
        return await crud.get_tests_by_group_id(db, group_id, user.id, user_role_code)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении тестов группы")


class CheckTestAvailabilityBody(BaseModel):
    user_id: int
    test_id: int
    test_group_id: int


class CheckTestAvailabilityResponse(BaseModel):
    is_available: bool
    message: str
    attempts_left: int | None = None
    attempts_used: int | None = None
    attempts_total: int | None = None


@router.post("/check-availability/", response_model=CheckTestAvailabilityResponse)
async def check_test_availability(
        data: CheckTestAvailabilityBody,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(authorized_required)
):
    """Проверяет доступность теста в рамках группы по датам и количеству попыток."""
    from app.crud.result import count_user_attempts_in_group
    from app.crud.test_group import get_test_group
    from datetime import datetime, timezone

    # 1) Получаем группу
    group = await get_test_group(db, data.test_group_id)

    # 2) Проверяем, что test_id есть в options и извлекаем настройки
    options_list = group.options or []
    matched = None
    for item in options_list:
        try:
            if int(item.get("test_id")) == int(data.test_id):
                matched = item
                break
        except Exception:
            continue

    if not matched:
        return CheckTestAvailabilityResponse(
            is_available=False,
            message="Тест не входит в данную группу",
            attempts_left=None,
            attempts_used=None,
            attempts_total=None
        )

    # 3) Проверка дат (берём date_start/date_end из элемента options; если их нет, используем даты группы)
    def parse_iso(dt_str: str | None):
        if not dt_str:
            return None
        # Поддержка суффикса 'Z'
        if isinstance(dt_str, str) and dt_str.endswith('Z'):
            try:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except Exception:
                pass
        try:
            return datetime.fromisoformat(dt_str)
        except Exception:
            return None

    now = datetime.now(timezone.utc)
    start_str = matched.get("date_start") or (group.date_start.isoformat() if group.date_start else None)
    end_str = matched.get("date_end") or (group.date_end.isoformat() if group.date_end else None)

    start_dt = parse_iso(start_str)
    end_dt = parse_iso(end_str)

    if start_dt and now < start_dt:
        start_dt_str = start_dt.strftime("%d.%m.%Y %H:%M")
        end_dt_str = end_dt.strftime("%d.%m.%Y %H:%M") if end_dt else None
        msg = (
            f"Тест недоступен: доступ откроется {start_dt_str}."
            if not end_dt_str
            else f"Тест недоступен: доступ откроется {start_dt_str} и будет доступен до {end_dt_str}."
        )
        return CheckTestAvailabilityResponse(
            is_available=False,
            message=msg,
            attempts_left=None,
            attempts_used=None,
            attempts_total=None
        )

    if end_dt and now > end_dt:
        end_dt_str = end_dt.strftime("%d.%m.%Y %H:%M")
        return CheckTestAvailabilityResponse(
            is_available=False,
            message=f"Тест недоступен: период доступа завершился {end_dt_str}.",
            attempts_left=None,
            attempts_used=None,
            attempts_total=None
        )

    # 4) Подсчёт попыток
    attempts_total = None
    try:
        attempts_total = int(matched.get("attempts_count")) if matched.get("attempts_count") is not None else None
    except Exception:
        attempts_total = None

    attempts_used = await count_user_attempts_in_group(db, data.user_id, data.test_id, data.test_group_id)

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

    # Если attempts_total не задан — считаем попытки неограниченными
    return CheckTestAvailabilityResponse(
        is_available=True,
        message="Тест доступен",
        attempts_left=None,
        attempts_used=attempts_used,
        attempts_total=None
    )


class GetAvailableTestsBody(BaseModel):
    user_id: int
    test_group_id: int


class AvailableTestResponse(BaseModel):
    test_id: int
    test_title: str
    time_limit: int | None = None
    date_start: str | None = None
    date_end: str | None = None
    attempts_total: int | None = None
    attempts_used: int
    attempts_left: int | None = None
    is_available: bool


@router.post("/available-tests/", response_model=List[AvailableTestResponse])
async def get_available_tests_in_group(
    data: GetAvailableTestsBody,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(authorized_required)
):
    """Возвращает все доступные тесты в группе для пользователя с учётом попыток и дат."""
    from app.crud.test_group import get_available_tests_in_group_for_user
    
    try:
        available_tests = await get_available_tests_in_group_for_user(db, data.user_id, data.test_group_id)
        return available_tests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
