from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class File(Base):
    """Модель файла"""
    __tablename__ = "file"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=True)
    name = Column(String(120), nullable=False)
    size = Column(Integer, nullable=False)
    path = Column(String, nullable=False)
    provider = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    creator_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False) 