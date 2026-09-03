"""
Standardized API envelope, metadata, and error models for FINRES FastAPI backend.
"""
from typing import Generic, TypeVar, Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponseMeta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "2.0.0"
    request_id: Optional[str] = None
    execution_time_ms: Optional[float] = None


class StandardAPIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation executed successfully"
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    meta: APIResponseMeta = Field(default_factory=APIResponseMeta)


class TokenData(BaseModel):
    user_id: str
    role: str  # CREDIT_OFFICER, RISK_ANALYST, AUDITOR, CUSTOMER
    permissions: List[str]
