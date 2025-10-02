from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.file import FileUploadResponse

class DocumentCreate(BaseModel):
    type: Optional[str] = None
    name: str
    size: int
    path: str
    provider: Optional[str] = None
    folder_id: Optional[int] = Field(default=None, alias="folderId")

    class Config:
        populate_by_name = True

class DocumentUpdate(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    size: Optional[int] = None
    path: Optional[str] = None
    provider: Optional[str] = None
    folder_id: Optional[int] = Field(default=None, alias="folderId")

    class Config:
        populate_by_name = True

class DocumentResponse(BaseModel):
    id: int
    type: Optional[str] = None
    name: str
    size: int
    path: str
    provider: Optional[str] = None
    folder_id: Optional[int] = Field(default=None, alias="folderId")
    creator_id: int = Field(alias="creatorId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True

class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    file: FileUploadResponse
