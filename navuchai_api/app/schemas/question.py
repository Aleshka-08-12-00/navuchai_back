from datetime import datetime
from typing import Dict, Optional, Any

from pydantic import BaseModel


class QuestionBase(BaseModel):
    id: int
    text: str
    text_abstract: str
    type: str
    reviewable: bool
    answers: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class QuestionWithDetails(BaseModel):
    question: QuestionBase
    position: int
    required: bool
    max_score: Optional[int] = None


# Схема для создания нового вопроса
class QuestionCreate(BaseModel):
    text: str
    text_abstract: str
    type: str
    reviewable: bool
    answers: Dict[str, Any]

    class Config:
        from_attributes = True


# Схема для отображения информации о вопросе (ответ API)
class QuestionResponse(BaseModel):
    id: int
    text: str
    text_abstract: str
    type: str
    reviewable: bool
    answers: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Схема для обновления вопроса
class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    text_abstract: Optional[str] = None
    type: Optional[str] = None
    reviewable: Optional[bool] = None
    answers: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
