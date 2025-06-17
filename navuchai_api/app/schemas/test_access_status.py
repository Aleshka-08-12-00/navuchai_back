from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TestAccessStatusBase(BaseModel):
    name: str
    code: str
    color: str


class TestAccessStatusCreate(TestAccessStatusBase):
    pass


class TestAccessStatusResponse(TestAccessStatusBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 