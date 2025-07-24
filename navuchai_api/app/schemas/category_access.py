from datetime import datetime
from pydantic import BaseModel


class CategoryAccessBase(BaseModel):
    id: int
    category_id: int
    user_id: int
    granted_at: datetime

    class Config:
        from_attributes = True
