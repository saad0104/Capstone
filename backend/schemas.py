from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class AnalyzeRequest(BaseModel):
    text: str
    provider: Optional[str] = None

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    summary: Optional[str] = None
    threat_type: Optional[str] = None
    severity: Optional[str] = None
    ioc_list: List[str] = []
    recommended_action: Optional[str] = None
    processing_ms: Optional[int] = None
    created_at: Optional[datetime] = None
