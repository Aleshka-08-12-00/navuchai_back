from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class FaqCategory(Base):
    __tablename__ = 'faq_categories'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    user_group_id = Column(Integer, ForeignKey('user_group.id'), nullable=True)
    express = Column(Boolean, nullable=True, default=False)

    faqs = relationship('Faq', back_populates='category', cascade='all, delete-orphan')
    user_group = relationship('UserGroup')
