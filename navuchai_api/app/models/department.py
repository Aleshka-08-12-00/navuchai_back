from sqlalchemy import Column, Integer, String
from app.models.base import Base

class Department(Base):
    __tablename__ = 'department'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False) 