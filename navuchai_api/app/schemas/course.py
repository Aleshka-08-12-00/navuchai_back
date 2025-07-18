from datetime import datetime
from typing import List, Optional

from app.schemas.module import ModuleBase
from pydantic import BaseModel, Field

from .file import FileInDB
from .module import ModuleRead


class CourseBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    author_id: int
    img_id: Optional[int] = Field(default=None, alias="imgId")
    thumbnail_id: Optional[int] = Field(default=None, alias="thumbnailId")
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    created_at: datetime
    enrolled: Optional[bool] = None
    progress: Optional[float] = None
    done: Optional[bool] = None
    rating: Optional[float] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    img_id: Optional[int] = Field(default=None, alias="imgId")
    thumbnail_id: Optional[int] = Field(default=None, alias="thumbnailId")

    class Config:
        populate_by_name = True


class CourseResponse(CourseBase):
    pass


class CourseWithDetails(CourseBase):
    modules: List["ModuleBase"] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class CourseRead(BaseModel):
    id: int
    title: str
    description: str
    img_id: Optional[int] = Field(default=None, alias="imgId")
    thumbnail_id: Optional[int] = Field(default=None, alias="thumbnailId")
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    lessons_count: Optional[int] = Field(default=None, alias="lessonsCount")
    students_count: Optional[int] = Field(default=None, alias="studentsCount")
    rating: Optional[float] = None
    
    enrolled: Optional[bool] = None
    progress: Optional[float] = None
    done: Optional[bool] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ListCoursesResponse(BaseModel):
    current: Optional[CourseRead]
    courses: List[CourseRead]


CourseWithDetails.model_rebuild()
