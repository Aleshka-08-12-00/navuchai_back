from typing import Optional, List
from pydantic import BaseModel, Field


class AdaptationElementBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    text_content: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_title: Optional[str] = None
    order_index: int
    parent_id: Optional[int] = None
    level: int = Field(ge=1, le=3)


class AdaptationElement(AdaptationElementBase):
    id: int
    is_completed: bool

    class Config:
        from_attributes = True


class AdaptationElementCreate(AdaptationElementBase):
    section_id: int


class AdaptationElementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    text_content: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_title: Optional[str] = None
    order_index: Optional[int] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None


class AdaptationSectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    order_index: int


class AdaptationSection(AdaptationSectionBase):
    id: int
    is_completed: bool
    completion_percentage: int
    elements: List[AdaptationElement] = []

    class Config:
        from_attributes = True


class AdaptationSectionCreate(AdaptationSectionBase):
    template_id: int


class AdaptationSectionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    order_index: Optional[int] = None


class AdaptationTemplateBase(BaseModel):
    title: str
    description: Optional[str] = None
    welcome_message: Optional[str] = None
    is_active: Optional[bool] = True


class AdaptationTemplateCreate(AdaptationTemplateBase):
    pass


class AdaptationTemplate(AdaptationTemplateBase):
    id: int
    sections: List[AdaptationSection] = []

    class Config:
        from_attributes = True


class EmployeeAdaptationBase(BaseModel):
    template_id: int
    employee_id: int


class EmployeeAdaptationCreate(EmployeeAdaptationBase):
    assigned_by: int


class EmployeeAdaptation(EmployeeAdaptationBase):
    id: int
    is_completed: bool
    completion_percentage: int

    class Config:
        from_attributes = True


class UpdateElementStatusRequest(BaseModel):
    is_completed: bool


class CopyAdaptationRequest(BaseModel):
    source_adaptation_id: int
    target_employee_id: int


