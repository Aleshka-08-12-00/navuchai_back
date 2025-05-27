from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class UserAnswerCreate(BaseModel):
    question_id: int
    answer: Dict[str, Any]


class ResultCreate(BaseModel):
    test_id: int
    user_id: int
    answers: List[UserAnswerCreate]


class UserAnswerResponse(BaseModel):
    id: int
    question_id: int
    user_id: int
    answer: Dict[str, Any]
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


class TestResult(BaseModel):
    total_score: int
    max_possible_score: int
    percentage: float
    checked_answers: List[CheckedAnswer]


class ResultResponse(BaseModel):
    id: int
    test_id: int
    user_id: int
    score: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    completed_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 