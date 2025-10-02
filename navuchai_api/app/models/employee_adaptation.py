from sqlalchemy import Column, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class EmployeeAdaptation(Base):
    __tablename__ = 'employee_adaptation'

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('adaptation_template.id', ondelete='CASCADE'), nullable=False)
    employee_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    assigned_by = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    completed_to = Column(TIMESTAMP, nullable=True)  # Дата до которой нужно выполнить адаптацию
    is_completed = Column(Boolean, nullable=False, server_default='false', default=False)
    is_failed = Column(Boolean, nullable=False, server_default='false', default=False)  # Статус провала по сроку
    completion_percentage = Column(Integer, nullable=False, server_default='0')
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    template = relationship('AdaptationTemplate', back_populates='employee_adaptations')
    employee = relationship('User', foreign_keys=[employee_id])
    assigner = relationship('User', foreign_keys=[assigned_by])


