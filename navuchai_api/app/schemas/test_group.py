from pydantic import BaseModel
from typing import Optional, List
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

class TestGroupCreate(TestGroupBase):
    pass

class TestGroupUpdate(TestGroupBase):
    pass

class TestGroupInDBBase(TestGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TestGroup(TestGroupInDBBase):
    pass

class TestGroupList(BaseModel):
    items: List[TestGroup]
    total: int 