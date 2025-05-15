from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.schemas.file import FileInDB


class TestBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: Optional[int] = None
    access_timestamp: datetime
    status_id: int
    frozen: bool
    locale_id: int
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    percent: Optional[int] = None
    completed: Optional[int] = None

    class Config:
        orm_mode = True


class TestWithDetails(TestBase):
    category_name: str
    creator_name: str
    locale_code: str
    status_name: str
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    image: Optional[FileInDB] = None


class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: Optional[int] = None
    access_timestamp: datetime
    status_id: int
    status_name: str
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    frozen: bool
    locale_id: int
    time_limit: Optional[int] = None
    img_id: Optional[int] = None

    class Config:
        from_attributes = True


class TestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: Optional[int] = None
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
    image: Optional[FileInDB] = None
    created_at: datetime
    updated_at: datetime
    percent: Optional[int] = None
    completed: Optional[int] = None

    class Config:
        from_attributes = True


class TestListResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: Optional[int] = None
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
    image: Optional[FileInDB] = None
    percent: Optional[int] = None
    completed: Optional[int] = None

    class Config:
        from_attributes = True
