from typing import Optional, List
from app.schemas.lesson_test import LessonTestBase
from pydantic import BaseModel
from .file import FileInDB

class LessonBase(BaseModel):
    id: int
    module_id: int
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    video: Optional[str] = None
    order: Optional[int] = None
    files: List[FileInDB] = []
    class Config:
        from_attributes = True

class LessonCreate(BaseModel):
    # module_id: int
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    video: Optional[str] = None
    order: Optional[int] = None
    file_ids: List[int] = []

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
    description: Optional[str] = None
    content: str
    video: Optional[str] = None
    order: int

    model_config = {
        "from_attributes": True
    }

LessonWithTests.model_rebuild()