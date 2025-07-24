from datetime import datetime
from pydantic import BaseModel


class FaqCategoryBase(BaseModel):
    title: str
    user_group_id: int | None = None
    express: bool | None = False


class FaqCategoryCreate(FaqCategoryBase):
    pass


class FaqCategoryUpdate(BaseModel):
    title: str | None = None
    user_group_id: int | None = None
    express: bool | None = None


class FaqCategoryInDB(FaqCategoryBase):
    id: int
    class Config:
        from_attributes = True
