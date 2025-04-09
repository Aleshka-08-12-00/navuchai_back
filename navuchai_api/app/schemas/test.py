from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TestBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: int
    access_timestamp: datetime
    status: str
    frozen: bool
    locale: str
    time_limit: Optional[int] = None

    class Config:
        orm_mode = True


class TestWithDetails(TestBase):
    category_name: str
    creator_name: str

# Схема для создания нового теста
class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: int
    access_timestamp: datetime
    status: str
    frozen: bool
    locale: str
    time_limit: Optional[int] = None

    class Config:
        from_attributes = True


# Схема для отображения информации о тесте (отвечает за вывод данных)
class TestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: int
    access_timestamp: datetime
    status: str
    frozen: bool
    locale: str
    time_limit: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Схема для списка всех тестов (когда выводим только ключевые данные)
class TestListResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: int
    access_timestamp: datetime
    status: str
    frozen: bool
    locale: str
    time_limit: Optional[int] = None

    class Config:
        from_attributes = True
