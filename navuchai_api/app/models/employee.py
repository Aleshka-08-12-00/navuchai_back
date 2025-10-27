from sqlalchemy import Integer, String, Column, TIMESTAMP, Boolean, text
from sqlalchemy.sql import func
from app.models.base import Base


class Employee(Base):
    __tablename__ = 'employee'

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, nullable=True, default=0)
    bitrix_id = Column(Integer, nullable=True)
    name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    position = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    is_group_worker = Column(Boolean, nullable=False, server_default=text('true'))
    is_in_system = Column(Boolean, nullable=False, server_default=text('true'))
    system_id = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    is_owner = Column(Boolean, nullable=False, server_default=text('false'))


