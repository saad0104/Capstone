from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

def gen_uuid():
    return str(uuid.uuid4())

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(String, primary_key=True, default=gen_uuid)
    raw_input = Column(Text, nullable=False)
    summary = Column(Text)
    threat_type = Column(String(64))
    severity = Column(String(16))
    ioc_list = Column(JSON)
    recommended_action = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_ms = Column(Integer)
