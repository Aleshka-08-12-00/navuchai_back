from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Faq(Base):
    __tablename__ = 'faq'

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('faq_categories.id', ondelete='CASCADE'), nullable=False)
    username = Column(Text)
    question = Column(Text)
    date = Column(TIMESTAMP, nullable=False, server_default=func.now())
    answer = Column(Text)
    answered_at = Column(TIMESTAMP, nullable=True)
    answer_author_id = Column(Integer, ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    has_new_answer = Column(Boolean, nullable=False, default=False)
    hits = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    category = relationship('FaqCategory', back_populates='faqs')
    owner = relationship('User', foreign_keys=[owner_id])
    answer_author = relationship('User', foreign_keys=[answer_author_id])
