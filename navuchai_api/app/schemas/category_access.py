from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CategoryAccessBase(BaseModel):
    category_id: int
    user_group_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: Optional[int] = None


class CategoryAccessCreate(CategoryAccessBase):
    class Config:
        from_attributes = True


class CategoryAccessUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: Optional[int] = None

    class Config:
        from_attributes = True


class CategoryAccessInDB(BaseModel):
    id: int
    category_id: int
    user_group_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


