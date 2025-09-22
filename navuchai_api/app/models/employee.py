from sqlalchemy import Integer, String, Column, TIMESTAMP
from sqlalchemy.sql import func
from app.models.base import Base


class Employee(Base):
    __tablename__ = 'employee'

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, nullable=False, default=0)
    bitrix_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    position = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


