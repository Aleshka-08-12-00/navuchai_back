from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnalyticsViewSchema(BaseModel):
    id: int
    type: str
    name: str
    background: Optional[str]
    background_hover: Optional[str]
    description: Optional[str]
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 