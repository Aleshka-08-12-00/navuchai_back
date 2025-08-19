from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class SystemSettingsBase(BaseModel):
    name: str
    code: str
    settings: Dict[str, Any] = {}


class SystemSettingsCreate(SystemSettingsBase):
    pass


class SystemSettingsUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class SystemSettingsResponse(SystemSettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]


class SettingsByCodesRequest(BaseModel):
    codes: list[str] 