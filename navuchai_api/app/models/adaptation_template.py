from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class AdaptationTemplate(Base):
    __tablename__ = 'adaptation_template'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    welcome_message = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default='true', default=True)
    creator_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    creator = relationship('User', lazy='selectin')
    sections = relationship('AdaptationSection', back_populates='template', cascade='all, delete-orphan', lazy='selectin', order_by='AdaptationSection.order_index')
    employee_adaptations = relationship('EmployeeAdaptation', back_populates='template', cascade='all, delete-orphan')


