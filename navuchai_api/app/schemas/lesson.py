from typing import List, Optional

from app.schemas.lesson_test import LessonTestBase
from pydantic import BaseModel, Field

from .file import FileInDB


class LessonBase(BaseModel):
    id: int
    module_id: int
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    video: Optional[str] = None
    order: Optional[int] = None
    img_id: Optional[int] = Field(default=None, alias="imgId")
    thumbnail_id: Optional[int] = Field(default=None, alias="thumbnailId")
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    files: List[FileInDB] = []
    completed: Optional[bool] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class LessonCreate(BaseModel):
    module_id: Optional[int] = Field(default=None, alias="moduleId")
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    video: Optional[str] = None
    order: Optional[int] = None
    img_id: Optional[int] = Field(default=None, alias="imgId")
    thumbnail_id: Optional[int] = Field(default=None, alias="thumbnailId")
    file_ids: List[int] = []

    class Config:
        populate_by_name = True


class LessonResponse(LessonBase):
    pass


class LessonWithTests(LessonBase):
    tests: List["LessonTestBase"] = []

    class Config:
        from_attributes = True
        populate_by_name = True


from pydantic import BaseModel


class LessonRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content: str
    video: Optional[str] = None
    order: int
    img_id: Optional[int] = Field(default=None, alias="imgId")
    thumbnail_id: Optional[int] = Field(default=None, alias="thumbnailId")
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    completed: Optional[bool] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


LessonWithTests.model_rebuild()
