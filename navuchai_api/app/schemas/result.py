from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from app.schemas.test import TestResponse
from app.schemas.user import UserResponse


class UserAnswerCreate(BaseModel):
    question_id: int
    time_start: datetime
    time_end: datetime
    answer: Dict[str, Any]


class ResultCreate(BaseModel):
    test_id: int
    user_id: int
    time_start: datetime
    time_end: datetime
    answers: List[UserAnswerCreate]


class UserAnswerResponse(BaseModel):
    id: int
    question_id: int
    user_id: int
    answer: Dict[str, Any]
    time_start: datetime
    time_end: datetime
    created_at: datetime
    updated_at: datetime


class CheckedAnswer(BaseModel):
    question_id: int
    question_text: str
    question_type: str
    max_score: int
    score: int
    is_correct: bool
    check_details: Dict[str, Any]
    time_start: datetime
    time_end: datetime


class TestResult(BaseModel):
    total_score: int
    max_possible_score: int
    percentage: float
    time_start: datetime
    time_end: datetime
    total_time_seconds: int
    checked_answers: List[CheckedAnswer]


class ResultResponse(BaseModel):
    id: int
    test_id: int
    user_id: int
    score: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    time_start: datetime
    time_end: datetime
    completed_at: datetime
    created_at: datetime
    updated_at: datetime
    test: Optional[TestResponse] = None
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True) 