from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# Схема для создания нового теста
class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: int
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
    time_limit: Optional[int] = None

    class Config:
        from_attributes = True
