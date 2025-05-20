from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class UserAnswerCreate(BaseModel):
    question_id: int
    answer: Dict[str, Any]


class ResultCreate(BaseModel):
    test_id: int
    user_id: int
    score: Optional[int] = None
    answers: List[UserAnswerCreate]

    model_config = ConfigDict(from_attributes=True)


class UserAnswerResponse(BaseModel):
    id: int
    result_id: int
    question_id: int
    user_id: int
    answer: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResultResponse(BaseModel):
    id: int
    user_id: int
    test_id: int
    score: Optional[int] = None
    completed_at: datetime
    created_at: datetime
    updated_at: datetime
    answers: List[UserAnswerResponse]

    model_config = ConfigDict(from_attributes=True) 