from pydantic import BaseModel
from datetime import datetime


class QuestionTypeBase(BaseModel):
    name: str
    code: str


class QuestionTypeCreate(QuestionTypeBase):
    pass


class QuestionTypeUpdate(QuestionTypeBase):
    pass


class QuestionTypeResponse(QuestionTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 