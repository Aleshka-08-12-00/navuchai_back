from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.schemas.file import FileInDB
from app.models.test import TestAccessEnum


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
    thumbnail_id: Optional[int] = None
    percent: Optional[int] = None
    completed: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    access: TestAccessEnum
    code: Optional[str] = None

    class Config:
        from_attributes = True


class TestWithDetails(TestBase):
    category_name: str
    creator_name: str
    locale_code: str
    status_name: str
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    code: Optional[str] = None


class TestWithAccessDetails(TestWithDetails):
    access_status_name: Optional[str] = None
    access_status_code: Optional[str] = None
    access_status_color: Optional[str] = None
    user_percent: Optional[float] = None
    user_completed: Optional[int] = None
    access_code: Optional[str] = None


class TestCreate(BaseModel):
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
    thumbnail_id: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    access: TestAccessEnum = TestAccessEnum.PRIVATE

    class Config:
        from_attributes = True


class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    access_timestamp: Optional[datetime] = None
    status_id: Optional[int] = None
    frozen: Optional[bool] = None
    locale_id: Optional[int] = None
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None

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
    frozen: bool
    locale_id: int
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    percent: Optional[int] = None
    completed: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    access: TestAccessEnum
    created_at: datetime
    updated_at: datetime
    code: Optional[str] = None

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
    thumbnail_id: Optional[int] = None
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    percent: Optional[int] = None
    completed: Optional[int] = None
    access: TestAccessEnum

    class Config:
        from_attributes = True
