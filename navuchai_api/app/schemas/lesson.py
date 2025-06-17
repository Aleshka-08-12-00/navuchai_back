from typing import Optional, List
from app.schemas.lesson_test import LessonTestBase
from pydantic import BaseModel
from app.models.test import TestAccessEnum

class LessonBase(BaseModel):
    id: int
    module_id: int
    title: str
    content: Optional[str] = None
    video: Optional[str] = None
    order: Optional[int] = None
    access: TestAccessEnum
    class Config:
        from_attributes = True

class LessonCreate(BaseModel):
    # module_id: int
    title: str
    content: Optional[str] = None
    video: Optional[str] = None
    order: Optional[int] = None
    access: TestAccessEnum = TestAccessEnum.PRIVATE

class LessonResponse(LessonBase):
    pass

class LessonWithTests(LessonBase):
    tests: List['LessonTestBase'] = []
    class Config:
        from_attributes = True

from pydantic import BaseModel

class LessonRead(BaseModel):
    id: int
    title: str
    content: str
    video: Optional[str] = None
    order: int
    access: TestAccessEnum

    model_config = {
        "from_attributes": True
    }

LessonWithTests.model_rebuild()