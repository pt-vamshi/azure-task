from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class BillingStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class BillingRecord(BaseModel):
    id: str = Field(..., description="Unique identifier for the billing record")
    customer_id: str = Field(..., description="Customer identifier")
    amount: float = Field(..., description="Billing amount")
    currency: str = Field(default="USD", description="Currency code")
    status: BillingStatus = Field(..., description="Billing status")
    description: Optional[str] = Field(None, description="Billing description")
    created_at: datetime = Field(..., description="Record creation timestamp")
    due_date: datetime = Field(..., description="Payment due date")
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ArchiveIndex(BaseModel):
    id: str = Field(..., description="Billing record ID")
    blob_path: str = Field(..., description="Path to the archived blob")
    archived_at: datetime = Field(..., description="When the record was archived")
    original_created_at: datetime = Field(..., description="Original creation date")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BillingResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    data: Optional[BillingRecord] = Field(None, description="Billing record data")
    message: Optional[str] = Field(None, description="Response message")
    source: str = Field(..., description="Data source (cosmos_db or blob_storage)")

class ArchiveResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    archived_count: int = Field(..., description="Number of records archived")
    message: str = Field(..., description="Response message") 