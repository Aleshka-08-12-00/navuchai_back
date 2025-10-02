from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = Field(default=None, alias="parentId")

    class Config:
        populate_by_name = True

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = Field(default=None, alias="parentId")

    class Config:
        populate_by_name = True

class FolderResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = Field(default=None, alias="parentId")
    creator_id: int = Field(alias="creatorId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True

class FolderWithChildren(FolderResponse):
    children: List["FolderResponse"] = []

FolderWithChildren.model_rebuild()
