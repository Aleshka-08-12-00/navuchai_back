from pydantic import BaseModel
from datetime import datetime


class TestQuestionResponse(BaseModel):
    id: int
    test_id: int
    question_id: int
    position: int
    required: bool
    max_score: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
