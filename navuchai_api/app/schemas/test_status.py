from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TestStatusBase(BaseModel):
    name: str
    code: str
    name_ru: str
    color: str


class TestStatusCreate(TestStatusBase):
    pass


class TestStatusUpdate(TestStatusBase):
    name: Optional[str] = None
    code: Optional[str] = None
    name_ru: Optional[str] = None
    color: Optional[str] = None


class TestStatusResponse(TestStatusBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
