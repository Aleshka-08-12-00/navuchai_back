from typing import Optional, List
from pydantic import BaseModel
from app.schemas.lesson import LessonBase, LessonWithoutContent
from .lesson import LessonRead

class ModuleBase(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    order: Optional[int] = None
    class Config:
        from_attributes = True

class ModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ModuleWithLessons(ModuleBase):
    lessons: List['LessonBase'] = []
    class Config:
        from_attributes = True

class ModuleRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    order: int
    lessons: List[LessonRead]

    model_config = {
        "from_attributes": True
    }

class ModuleResponse(BaseModel):
    title: str
    description: Optional[str] = None
    order: Optional[int] = None

    class Config:
        orm_mode = True

ModuleWithLessons.model_rebuild()


class ModuleWithLessonsWithoutContent(ModuleBase):
    lessons: List['LessonWithoutContent'] = []

    class Config:
        from_attributes = True


ModuleWithLessonsWithoutContent.model_rebuild()
