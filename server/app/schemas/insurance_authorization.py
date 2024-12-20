"""
Insurance Authorization Schemas
Version: 2024-12-19_17-25
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

class AuthorizationDocumentCreate(BaseModel):
    """Schema for creating an authorization document"""
    document_type: str = Field(..., description="Type of document (e.g., CLINICAL_NOTES, PRESCRIPTION)")
    file_path: str = Field(..., description="Path to the stored document")
    description: Optional[str] = Field(None, description="Description of the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the document")

class AuthorizationDocumentResponse(AuthorizationDocumentCreate):
    """Schema for authorization document response"""
    id: int = Field(..., description="Document ID")
    authorization_id: int = Field(..., description="ID of the associated authorization")
    created_at: datetime = Field(..., description="Timestamp when document was created")
    updated_at: datetime = Field(..., description="Timestamp when document was last updated")
    created_by: str = Field(..., description="Username who created the document")
    updated_by: str = Field(..., description="Username who last updated the document")

class AuthorizationRequest(BaseModel):
    """Schema for creating an authorization request"""
    policy_id: int = Field(..., description="ID of the insurance policy")
    service_type: str = Field(..., description="Type of service requiring authorization")
    start_date: date = Field(..., description="Requested start date for authorization")
    end_date: date = Field(..., description="Requested end date for authorization")
    requested_units: int = Field(..., description="Number of service units requested")
    diagnosis_codes: List[str] = Field(..., description="List of diagnosis codes")
    provider_id: str = Field(..., description="ID of the service provider")
    facility_id: Optional[str] = Field(None, description="ID of the service facility")
    clinical_info: Optional[Dict[str, Any]] = Field(None, description="Clinical information supporting the request")
    documents: Optional[List[AuthorizationDocumentCreate]] = Field(None, description="Supporting documents")
    urgency: Optional[str] = Field("ROUTINE", description="Request urgency (ROUTINE, URGENT, EMERGENCY)")
    notes: Optional[str] = Field(None, description="Additional notes about the request")

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError("End date must be after start date")
        return v

    @validator('urgency')
    def validate_urgency(cls, v):
        valid_urgencies = {"ROUTINE", "URGENT", "EMERGENCY"}
        if v and v not in valid_urgencies:
            raise ValueError(f"Urgency must be one of: {', '.join(valid_urgencies)}")
        return v

class AuthorizationStatusUpdate(BaseModel):
    """Schema for updating authorization status"""
    status: str = Field(..., description="New status for the authorization")
    notes: str = Field(..., description="Notes about the status change")
    approved_units: Optional[int] = Field(None, description="Number of units approved")
    expiration_date: Optional[date] = Field(None, description="Updated expiration date")
    denial_reason: Optional[str] = Field(None, description="Reason for denial if applicable")

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = {
            "PENDING", "APPROVED", "DENIED", "CANCELLED",
            "PENDING_INFORMATION", "EXPIRED", "REVOKED"
        }
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

class AuthorizationStatusHistoryResponse(BaseModel):
    """Schema for authorization status history"""
    id: int = Field(..., description="Status history entry ID")
    authorization_id: int = Field(..., description="ID of the associated authorization")
    status: str = Field(..., description="Status value")
    notes: Optional[str] = Field(None, description="Notes about the status")
    created_at: datetime
    created_by: str

class AuthorizationResponse(BaseModel):
    """Schema for authorization response"""
    id: int = Field(..., description="Authorization ID")
    policy_id: int = Field(..., description="ID of the insurance policy")
    authorization_number: str = Field(..., description="Unique authorization number")
    status: str = Field(..., description="Current authorization status")
    service_type: str = Field(..., description="Type of service")
    start_date: date = Field(..., description="Start date of authorization")
    end_date: date = Field(..., description="End date of authorization")
    requested_units: int = Field(..., description="Number of service units requested")
    approved_units: Optional[int] = Field(None, description="Number of service units approved")
    diagnosis_codes: List[str] = Field(..., description="List of diagnosis codes")
    provider_id: str = Field(..., description="ID of the service provider")
    facility_id: Optional[str] = Field(None, description="ID of the service facility")
    clinical_info: Optional[Dict[str, Any]] = Field(None, description="Clinical information")
    urgency: str = Field(..., description="Request urgency level")
    notes: Optional[str] = Field(None, description="Additional notes")
    documents: List[AuthorizationDocumentResponse] = Field(..., description="Supporting documents")
    status_history: Optional[List[AuthorizationStatusHistoryResponse]] = Field(
        None, 
        description="Authorization status history"
    )
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True
