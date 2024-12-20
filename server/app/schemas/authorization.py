"""
Authorization schemas
Version: 2024-12-20_00-03
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import uuid

from app.services.authorization.base import AuthorizationStatus

class AuthorizationDocumentCreate(BaseModel):
    """Schema for creating authorization documents"""
    document_type: str = Field(..., description="Type of document")
    document_url: str = Field(..., description="URL to the document")
    notes: Optional[str] = Field(None, description="Additional notes")

class AuthorizationRequest(BaseModel):
    """Schema for authorization request"""
    policy_id: int = Field(..., description="Insurance policy ID")
    service_type: str = Field(..., description="Type of service requiring authorization")
    start_date: date = Field(..., description="Start date for authorization")
    end_date: date = Field(..., description="End date for authorization")
    requested_units: Optional[int] = Field(None, description="Number of service units requested")
    diagnosis_codes: List[str] = Field(default_factory=list, description="List of diagnosis codes")
    procedure_codes: List[str] = Field(default_factory=list, description="List of procedure codes")
    provider_id: Optional[int] = Field(None, description="Healthcare provider ID")
    facility_id: Optional[int] = Field(None, description="Healthcare facility ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    documents: List[AuthorizationDocumentCreate] = Field(
        default_factory=list,
        description="Supporting documents"
    )

    @validator("end_date")
    def validate_dates(cls, v, values):
        """Validate end date is after start date"""
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v

class AuthorizationStatusUpdate(BaseModel):
    """Schema for authorization status update"""
    status: AuthorizationStatus = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Status update notes")
    approved_units: Optional[int] = Field(None, description="Number of units approved")
    expiration_date: Optional[date] = Field(None, description="Updated expiration date")

class AuthorizationHistoryResponse(BaseModel):
    """Schema for authorization status history"""
    status: str = Field(..., description="Status")
    notes: Optional[str] = Field(None, description="Status notes")
    created_at: datetime = Field(..., description="Status creation timestamp")
    created_by: str = Field(..., description="User who created the status")

class AuthorizationResponse(BaseModel):
    """Schema for authorization response"""
    id: int = Field(..., description="Authorization ID")
    policy_id: int = Field(..., description="Insurance policy ID")
    service_type: str = Field(..., description="Type of service")
    status: AuthorizationStatus = Field(..., description="Current status")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    requested_units: Optional[int] = Field(None, description="Requested units")
    approved_units: Optional[int] = Field(None, description="Approved units")
    diagnosis_codes: List[str] = Field(..., description="Diagnosis codes")
    procedure_codes: List[str] = Field(..., description="Procedure codes")
    provider_id: Optional[int] = Field(None, description="Provider ID")
    facility_id: Optional[int] = Field(None, description="Facility ID")
    notes: Optional[str] = Field(None, description="Notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str = Field(..., description="User who created the authorization")
    updated_by: str = Field(..., description="User who last updated the authorization")
    status_history: Optional[List[AuthorizationHistoryResponse]] = Field(
        None,
        description="Status history"
    )

class BatchAuthorizationRequest(BaseModel):
    """Schema for batch authorization request"""
    requests: List[AuthorizationRequest] = Field(
        ...,
        description="List of authorization requests",
        max_items=100
    )
    batch_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique batch ID"
    )

    @validator("requests")
    def validate_batch_size(cls, v):
        """Validate batch size"""
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 requests")
        return v

class BatchAuthorizationResponse(BaseModel):
    """Schema for batch authorization response"""
    batch_id: str = Field(..., description="Batch operation ID")
    total: int = Field(..., description="Total number of requests")
    completed: int = Field(..., description="Number of completed requests")
    failed: int = Field(..., description="Number of failed requests")
    status: str = Field(..., description="Batch operation status")
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results for completed requests"
    )
    errors: Dict[str, str] = Field(
        default_factory=dict,
        description="Errors for failed requests"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Batch creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )
