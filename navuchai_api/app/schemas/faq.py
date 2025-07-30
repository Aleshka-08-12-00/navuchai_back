from datetime import datetime
from pydantic import BaseModel, computed_field


class FaqBase(BaseModel):
    id: int
    category_id: int
    username: str | None = None
    question: str | None = None
    date: datetime
    answer: str | None = None
    answered_at: datetime | None = None
    answer_author_id: int | None = None
    has_new_answer: bool
    hits: int
    active: bool
    owner_id: int

    @computed_field(return_type=bool)
    @property
    def answered(self) -> bool:
        return bool(self.answer)

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
