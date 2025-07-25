from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.test_group import TestGroup, TestGroupCreate, TestGroupUpdate, TestGroupList, TestGroupEnriched
from app.schemas.test_group_test import TestGroupTest, TestGroupTestCreate
from app.crud import test_group as crud
from app.dependencies import get_db
from app.schemas.test import TestWithDetails
from app.crud import admin_moderator_required, authorized_required
from sqlalchemy.exc import SQLAlchemyError
from app.exceptions import NotFoundException, DatabaseException

router = APIRouter(prefix="/api/test-groups", tags=["Test groups"])


@router.get("/", response_model=List[TestGroupEnriched])
async def list_test_groups(db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        return await crud.get_test_groups(db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка групп")


@router.get("/{group_id}/", response_model=TestGroupEnriched)
async def get_test_group(group_id: int, db: AsyncSession = Depends(get_db), user=Depends(authorized_required)):
    try:
        group = await crud.get_test_group(db, group_id)
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
                            user=Depends(admin_moderator_required)):
    try:
        return await crud.create_test_group(db, data)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании группы")


@router.put("/{group_id}/", response_model=TestGroup)
async def update_test_group(group_id: int, data: TestGroupUpdate, db: AsyncSession = Depends(get_db),
                            user=Depends(admin_moderator_required)):
    try:
        return await crud.update_test_group(db, group_id, data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении группы")


@router.delete("/{group_id}/", response_model=TestGroup)
async def delete_test_group(group_id: int, db: AsyncSession = Depends(get_db), user=Depends(admin_moderator_required)):
    try:
        return await crud.delete_test_group(db, group_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении группы")


@router.post("/add-test/", response_model=TestGroupTest)
async def add_test_to_group(data: TestGroupTestCreate, db: AsyncSession = Depends(get_db),
                            user=Depends(admin_moderator_required)):
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
        return await crud.get_tests_by_group_id(db, group_id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении тестов группы")
