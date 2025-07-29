from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TestGroupAccessBase(BaseModel):
    test_group_id: int
    user_id: int
    user_group_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: Optional[int] = None


class TestGroupAccessCreate(TestGroupAccessBase):
    pass


class TestGroupAccessUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: Optional[int] = None


class TestGroupAccessResponse(TestGroupAccessBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 