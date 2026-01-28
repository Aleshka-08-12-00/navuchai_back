from typing import List, Optional

from app.schemas.lesson_test import LessonTestBase
from pydantic import BaseModel, Field

from .file import FileInDB


class LessonTopicContentItem(BaseModel):
    name: str
    page_from: int = Field(alias="pageFrom")
    page_to: int = Field(alias="pageTo")

    class Config:
        populate_by_name = True


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
    topic_contents: Optional[List[LessonTopicContentItem]] = Field(default=None, alias="topicContents")
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
    topic_contents: Optional[List[LessonTopicContentItem]] = Field(default=None, alias="topicContents")

    class Config:
        populate_by_name = True


class LessonResponse(LessonBase):
    pass


class LessonWithoutContent(BaseModel):
    id: int
    module_id: int
    title: str
    description: Optional[str] = None
    video: Optional[str] = None
    order: Optional[int] = None
    img_id: Optional[int] = Field(default=None, alias="imgId")
    thumbnail_id: Optional[int] = Field(default=None, alias="thumbnailId")
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    files: List[FileInDB] = []
    topic_contents: Optional[List[LessonTopicContentItem]] = Field(default=None, alias="topicContents")
    completed: Optional[bool] = None

    class Config:
        from_attributes = True
        populate_by_name = True


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
    topic_contents: Optional[List[LessonTopicContentItem]] = Field(default=None, alias="topicContents")
    completed: Optional[bool] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


LessonWithTests.model_rebuild()
