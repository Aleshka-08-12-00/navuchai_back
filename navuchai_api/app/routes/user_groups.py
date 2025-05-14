from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.crud import admin_teacher_required, authorized_required
from app.crud import user_group as crud
from app.schemas.user_group import (
    UserGroupCreate,
    UserGroupUpdate,
    UserGroupResponse,
    UserGroupMemberInDB
)
from app.models import User

router = APIRouter(prefix="/api/user-groups", tags=["User Groups"])


@router.post("/", response_model=UserGroupResponse, status_code=201)
async def create_user_group(
    group_data: UserGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> UserGroupResponse:
    return await crud.create_group(db, group_data, current_user.id)


@router.get("/", response_model=List[UserGroupResponse])
async def get_user_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required),
) -> List[UserGroupResponse]:
    return await crud.get_groups(db)


@router.get("/{group_id}", response_model=UserGroupResponse)
async def get_user_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
) -> UserGroupResponse:
    return await crud.get_group(db, group_id)


@router.put("/{group_id}", response_model=UserGroupResponse)
async def update_user_group(
    group_id: int,
    group_data: UserGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> UserGroupResponse:
    group = await crud.get_group(db, group_id)
    if group.creator_id != current_user.id and current_user.role.code != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения этой группы")
    return await crud.update_group(db, group_id, group_data)


@router.delete("/{group_id}", response_model=UserGroupResponse)
async def delete_user_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> UserGroupResponse:
    group = await crud.get_group(db, group_id)
    if group.creator_id != current_user.id and current_user.role.code != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав для удаления этой группы")
    return await crud.delete_group(db, group_id)


@router.post("/{group_id}/members/{user_id}", response_model=UserGroupMemberInDB)
async def add_user_to_group(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> UserGroupMemberInDB:
    group = await crud.get_group(db, group_id)
    if group.creator_id != current_user.id and current_user.role.code != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав для управления участниками группы")
    return await crud.add_group_member(db, group_id, user_id)


@router.delete("/{group_id}/members/{user_id}", response_model=UserGroupMemberInDB)
async def remove_user_from_group(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> UserGroupMemberInDB:
    group = await crud.get_group(db, group_id)
    if group.creator_id != current_user.id and current_user.role.code != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав для управления участниками группы")
    return await crud.remove_group_member(db, group_id, user_id) 