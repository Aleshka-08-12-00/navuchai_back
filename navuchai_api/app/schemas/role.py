from pydantic import BaseModel
from datetime import datetime


class RoleBase(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
