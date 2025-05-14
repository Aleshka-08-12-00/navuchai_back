from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class UserGroupBase(BaseModel):
    """Базовая схема группы пользователей"""
    name: str
    description: Optional[str] = None


class UserGroupCreate(UserGroupBase):
    """Схема создания группы пользователей"""
    pass


class UserGroupUpdate(UserGroupBase):
    """Схема обновления группы пользователей"""
    pass


class UserGroupInDB(UserGroupBase):
    """Схема группы пользователей в БД"""
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserGroupMemberBase(BaseModel):
    """Базовая схема участника группы"""
    user_id: int
    group_id: int


class UserGroupMemberCreate(UserGroupMemberBase):
    """Схема создания участника группы"""
    pass


class UserGroupMemberInDB(UserGroupMemberBase):
    """Схема участника группы в БД"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserGroupResponse(UserGroupInDB):
    """Схема ответа с группой пользователей"""
    members: List[UserGroupMemberInDB] = [] 