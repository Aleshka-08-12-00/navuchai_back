from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class TestGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    status_id: Optional[int] = None
    options: Optional[List[Any]] = None


class TestGroupCreate(TestGroupBase):
    pass


class TestGroupUpdate(TestGroupBase):
    pass


class TestGroupInDBBase(TestGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    status_id: Optional[int] = None

    class Config:
        from_attributes = True


class TestGroup(TestGroupInDBBase):
    pass


class TestGroupList(BaseModel):
    items: List[TestGroup]
    total: int


class TestGroupEnriched(TestGroup):
    status_name: Optional[str] = None
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    image: Optional[str] = None
    thumbnail: Optional[str] = None


# Новые схемы для древовидной структуры
class TestInCategory(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    time_limit: Optional[int] = None
    avg_percent: Optional[int] = None
    completed_number: Optional[int] = None
    access_timestamp: datetime
    frozen: bool
    created_at: datetime
    updated_at: datetime
    image: Optional[str] = None
    thumbnail: Optional[str] = None
    status_name: Optional[str] = None
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    is_completed: Optional[bool] = None

    class Config:
        from_attributes = True


class CategoryWithTests(BaseModel):
    id: int
    name: str
    tests: List[TestInCategory]
    tests_count: int

    class Config:
        from_attributes = True


class TestGroupWithCategories(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    time_limit: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    status_name: Optional[str] = None
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    image: Optional[str] = None
    thumbnail: Optional[str] = None
    options: Optional[List[Any]] = None
    categories: List[CategoryWithTests]
    total_tests_count: int

    class Config:
        from_attributes = True
