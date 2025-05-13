from pydantic import BaseModel
from datetime import datetime


class RoleBase(BaseModel):
    name: str
    code: str


class RoleInDB(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
