from pydantic import BaseModel
from typing import List, Optional

class AnalyzeRequest(BaseModel):
    text: str

class AlertOut(BaseModel):
    id: Optional[str]
    summary: Optional[str]
    threat_type: Optional[str]
    severity: Optional[str]
    ioc_list: List[str] = []
    recommended_action: Optional[str]
    processing_ms: Optional[int]
