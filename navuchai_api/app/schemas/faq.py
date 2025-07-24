from datetime import datetime
from pydantic import BaseModel


class FaqBase(BaseModel):
    id: int
    category_id: int
    username: str | None = None
    question: str | None = None
    date: datetime
    answer: str | None = None
    answered: bool
    hits: int
    active: bool
    owner_id: int

    class Config:
        from_attributes = True


class FaqCreate(BaseModel):
    category_id: int
    question: str


class FaqAnswerUpdate(BaseModel):
    answer: str
    active: bool | None = True


class FaqInDB(FaqBase):
    pass
