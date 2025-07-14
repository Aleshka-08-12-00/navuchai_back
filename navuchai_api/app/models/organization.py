from sqlalchemy import Column, Integer, String
from app.models.base import Base

class Organization(Base):
    __tablename__ = 'organization'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False) 