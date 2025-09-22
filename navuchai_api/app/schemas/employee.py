from typing import List, Optional
from pydantic import BaseModel, Field


class EmployeeNode(BaseModel):
    id: str
    name: str
    position: Optional[str] = None
    department: Optional[str] = None
    email: str
    phone: Optional[str] = None
    level: int
    children: List["EmployeeNode"] = Field(default_factory=list)

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_schema_extra = {
            "examples": []
        }

EmployeeNode.model_rebuild()


