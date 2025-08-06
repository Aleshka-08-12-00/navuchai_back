from datetime import datetime
from pydantic import BaseModel, computed_field


class FaqBase(BaseModel):
    id: int
    category_id: int
    username: str | None = None
    question: str | None = None
    question_file_url: str | None = None
    date: datetime
    answer: str | None = None
    answer_file_url: str | None = None
    answered_at: datetime | None = None
    has_new_answer: bool
    hits: int
    active: bool
    owner_id: int

    @computed_field(return_type=bool)
    @property
    def answered(self) -> bool:
        return bool(self.answer)

    @computed_field(return_type=str | None)
    @property
    def answer_author_name(self) -> str | None:
        author = getattr(self, "answer_author", None)
        return author.name if author else None

    class Config:
        from_attributes = True


class FaqCreate(BaseModel):
    category_id: int
    question: str
    question_file_url: str | None = None


class FaqAnswerUpdate(BaseModel):
    answer: str
    active: bool | None = True
    answer_file_url: str | None = None


class FaqInDB(FaqBase):
    pass
