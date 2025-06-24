from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.module import ModuleBase
from .module import ModuleRead
from .file import FileInDB

class CourseBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    author_id: int
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    created_at: datetime
    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None

class CourseResponse(CourseBase):
    pass

class CourseWithDetails(CourseBase):
    modules: List['ModuleBase'] = []
    class Config:
        from_attributes = True

class CourseRead(BaseModel):
    id: int
    title: str
    description: str
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    modules: List[ModuleRead]

    model_config = {
        "from_attributes": True
    }

CourseWithDetails.model_rebuild()
