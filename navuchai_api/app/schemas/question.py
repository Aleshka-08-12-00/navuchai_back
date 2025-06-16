from datetime import datetime
from typing import Dict, Optional, Any

from pydantic import BaseModel
from .question_type import QuestionTypeResponse


class QuestionBase(BaseModel):
    id: int
    text: str
    text_abstract: str
    type_id: int
    reviewable: bool
    answers: dict
    time_limit: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class QuestionCreate(BaseModel):
    text: str
    text_abstract: str
    type_id: int
    reviewable: bool
    answers: Dict[str, Any]
    time_limit: Optional[int] = 0

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    text: str
    text_abstract: str
    type_id: int
    reviewable: bool
    answers: Dict[str, Any]
    time_limit: Optional[int] = 0
    type: QuestionTypeResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestionWithDetails(BaseModel):
    question: QuestionResponse
    position: int
    required: bool
    max_score: Optional[int] = None


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    text_abstract: Optional[str] = None
    type_id: Optional[int] = None
    reviewable: Optional[bool] = None
    answers: Optional[Dict[str, Any]] = None
    time_limit: Optional[int] = None

    class Config:
        from_attributes = True
