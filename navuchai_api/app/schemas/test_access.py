from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TestAccessBase(BaseModel):
    test_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: Optional[int] = None
    access_code: Optional[str] = None


class TestAccessCreate(BaseModel):
    test_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: Optional[int] = None
    access_code: Optional[str] = None

    class Config:
        from_attributes = True


class TestAccessResponse(BaseModel):
    id: int
    test_id: int
    user_id: int
    group_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: Optional[int] = None
    status_name: Optional[str] = None
    access_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 