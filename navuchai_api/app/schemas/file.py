from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileBase(BaseModel):
    """Базовая схема файла"""
    type: Optional[str] = None
    name: str
    size: int
    path: str
    provider: Optional[str] = None
    creator_id: int


class FileCreate(FileBase):
    """Схема для создания файла"""
    pass


class FileInDB(FileBase):
    """Схема файла в БД"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """Схема ответа при успешной загрузке файла"""
    success: bool = True
    id: int
    filename: str
    content_type: str
    size: int
    url: str
    uploaded_at: datetime = datetime.now()
    message: Optional[str] = None


class FileUploadWithMobileResponse(BaseModel):
    original: FileUploadResponse
    mobile: FileUploadResponse
