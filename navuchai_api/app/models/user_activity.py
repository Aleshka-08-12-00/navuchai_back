from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


class UserActivity(Base):
    __tablename__ = 'user_activity'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='SET NULL'), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    action_ru = Column(String(200), nullable=True)
    context = Column(JSONB, nullable=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)


