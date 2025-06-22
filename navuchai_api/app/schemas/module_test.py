from pydantic import BaseModel


class ModuleTestBase(BaseModel):
    id: int
    module_id: int
    test_id: int
    required: bool

    class Config:
        from_attributes = True


class ModuleTestCreate(BaseModel):
    module_id: int
    test_id: int
    required: bool = True
