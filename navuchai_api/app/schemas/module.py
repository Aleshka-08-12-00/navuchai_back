from typing import Optional, List
from pydantic import BaseModel
from app.schemas.lesson import LessonBase
from .lesson import LessonRead

class ModuleBase(BaseModel):
    id: int
    course_id: int
    title: str
    order: Optional[int] = None
    class Config:
        from_attributes = True

class ModuleCreate(BaseModel):
    title: str

class ModuleWithLessons(ModuleBase):
    lessons: List['LessonBase'] = []
    class Config:
        from_attributes = True

class ModuleRead(BaseModel):
    id: int
    title: str
    order: int
    lessons: List[LessonRead]

    model_config = {
        "from_attributes": True
    }

class ModuleResponse(BaseModel):
    title: str
    order: Optional[int] = None

    class Config:
        orm_mode = True

ModuleWithLessons.model_rebuild()
