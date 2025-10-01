from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class UserActivityBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    context: Optional[Dict[str, Any]] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


class UserActivityCreate(UserActivityBase):
    pass


class UserActivityRead(UserActivityBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


