from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TestGroupTestBase(BaseModel):
    test_group_id: int
    test_id: int

class TestGroupTestCreate(TestGroupTestBase):
    pass

class TestGroupTestInDBBase(TestGroupTestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TestGroupTest(TestGroupTestInDBBase):
    pass 