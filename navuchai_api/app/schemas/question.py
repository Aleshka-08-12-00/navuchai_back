from datetime import datetime
from typing import Dict, Optional, Any

from pydantic import BaseModel


# Схема для создания нового вопроса
class QuestionCreate(BaseModel):
    text: str
    type: str
    options: Dict[str, Any]

    class Config:
        from_attributes = True


# Схема для отображения информации о вопросе (ответ API)
class QuestionResponse(BaseModel):
    id: int
    text: str
    type: str
    options: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Схема для обновления вопроса
class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    type: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
