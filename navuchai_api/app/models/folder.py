from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Folder(Base):
    __tablename__ = 'folder'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    parent_id = Column(Integer, ForeignKey('folder.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    parent = relationship('Folder', remote_side=[id], back_populates='children', lazy='selectin')
    children = relationship('Folder', back_populates='parent', cascade='all, delete-orphan', lazy='selectin')
    documents = relationship('Document', back_populates='folder', cascade='all, delete-orphan', lazy='selectin')
    creator = relationship('User')
