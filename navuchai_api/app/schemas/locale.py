from datetime import datetime
from pydantic import BaseModel


class LocaleBase(BaseModel):
    code: str
    name: str


class LocaleCreate(LocaleBase):
    pass


class LocaleUpdate(LocaleBase):
    pass


class LocaleInDB(LocaleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
