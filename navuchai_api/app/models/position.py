from sqlalchemy import Column, Integer, String
from app.models.base import Base

class Position(Base):
    __tablename__ = 'position'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False) 