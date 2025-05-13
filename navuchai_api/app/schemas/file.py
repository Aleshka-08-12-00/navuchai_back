from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileUploadResponse(BaseModel):
    """Схема ответа при успешной загрузке файла"""
    success: bool = True
    filename: str
    content_type: str
    size: int
    url: str
    uploaded_at: datetime = datetime.now()
    message: Optional[str] = None
