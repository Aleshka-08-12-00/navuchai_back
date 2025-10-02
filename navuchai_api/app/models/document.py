from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Document(Base):
    __tablename__ = 'document'
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(120), nullable=True)
    name = Column(String(120), nullable=False)
    size = Column(Integer, nullable=False)
    path = Column(String, nullable=False)
    provider = Column(String(120), nullable=True)
    folder_id = Column(Integer, ForeignKey('folder.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    folder = relationship('Folder', back_populates='documents', lazy='selectin')
    creator = relationship('User')
