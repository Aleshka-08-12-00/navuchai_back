from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, func
from app.models.base import Base

class AnalyticsView(Base):
    __tablename__ = "analytics_views"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    background = Column(String(50))
    background_hover = Column(String(50))
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False) 