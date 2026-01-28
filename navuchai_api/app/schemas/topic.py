from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.schemas.file import FileInDB


class TopicTagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TopicResponse(BaseModel):
    id: int
    name: str
    tags: List[TopicTagResponse] = []
    files: List[FileInDB] = []
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class TopicSplitRequest(BaseModel):
    page_topic_map: dict = Field(alias="pageTopicMap")

    class Config:
        populate_by_name = True


class TopicSplitBodyRequest(BaseModel):
    page_topic_map: dict = Field(alias="pageTopicMap")
    lesson_id: int = Field(alias="lessonId")
    file_id: int | None = Field(default=None, alias="fileId")

    class Config:
        populate_by_name = True


class TopicTagsUpdateRequest(BaseModel):
    tags: List[str]


class TopicSearchRequest(BaseModel):
    tags: List[str]


class TopicContentsItem(BaseModel):
    name: str
    page_from: int = Field(alias="pageFrom")
    page_to: int = Field(alias="pageTo")

    class Config:
        populate_by_name = True
