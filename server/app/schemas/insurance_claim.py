"""
Insurance Claim Schemas
Version: 2024-12-19_17-20
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator

class ClaimDocumentCreate(BaseModel):
    """Schema for creating a claim document"""
    document_type: str = Field(..., description="Type of document (e.g., INVOICE, RECEIPT)")
    file_path: str = Field(..., description="Path to the stored document")
    description: Optional[str] = Field(None, description="Description of the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the document")

class ClaimDocumentResponse(ClaimDocumentCreate):
    """Schema for claim document response"""
    id: int = Field(..., description="Document ID")
    claim_id: int = Field(..., description="ID of the associated claim")
    created_at: datetime = Field(..., description="Timestamp when document was created")
    updated_at: datetime = Field(..., description="Timestamp when document was last updated")
    created_by: str = Field(..., description="Username who created the document")
    updated_by: str = Field(..., description="Username who last updated the document")

class ClaimServiceLineCreate(BaseModel):
    """Schema for creating a claim service line"""
    service_code: str = Field(..., description="Service code (e.g., CPT, HCPCS)")
    quantity: int = Field(..., description="Quantity of service provided")
    unit_price: Decimal = Field(..., description="Price per unit of service")
    diagnosis_codes: List[str] = Field(..., description="List of diagnosis codes")
    service_date: date = Field(..., description="Date service was provided")
    provider_id: str = Field(..., description="ID of the service provider")
    modifiers: Optional[List[str]] = Field(None, description="Service code modifiers")
    notes: Optional[str] = Field(None, description="Additional notes about the service")

class ClaimServiceLineResponse(ClaimServiceLineCreate):
    """Schema for claim service line response"""
    id: int = Field(..., description="Service line ID")
    claim_id: int = Field(..., description="ID of the associated claim")
    total_amount: Decimal = Field(..., description="Total amount for this service line")
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

class InsuranceClaimCreate(BaseModel):
    """Schema for creating an insurance claim"""
    policy_id: int = Field(..., description="ID of the insurance policy")
    service_date: date = Field(..., description="Date service was provided")
    provider_id: str = Field(..., description="ID of the service provider")
    facility_id: Optional[str] = Field(None, description="ID of the service facility")
    diagnosis_codes: List[str] = Field(..., description="List of diagnosis codes")
    service_lines: List[ClaimServiceLineCreate] = Field(..., description="List of service lines")
    documents: Optional[List[ClaimDocumentCreate]] = Field(None, description="Supporting documents")
    notes: Optional[str] = Field(None, description="Additional notes about the claim")

    @validator('service_lines')
    def validate_service_lines(cls, v):
        if not v:
            raise ValueError("At least one service line is required")
        return v

class InsuranceClaimUpdate(BaseModel):
    """Schema for updating an insurance claim"""
    diagnosis_codes: Optional[List[str]] = Field(None, description="Updated diagnosis codes")
    notes: Optional[str] = Field(None, description="Updated notes")

class ClaimStatusUpdate(BaseModel):
    """Schema for updating claim status"""
    status: str = Field(..., description="New status for the claim")
    notes: str = Field(..., description="Notes about the status change")

class ClaimStatusHistoryResponse(BaseModel):
    """Schema for claim status history"""
    id: int = Field(..., description="Status history entry ID")
    claim_id: int = Field(..., description="ID of the associated claim")
    status: str = Field(..., description="Status value")
    notes: Optional[str] = Field(None, description="Notes about the status")
    created_at: datetime
    created_by: str

class InsuranceClaimResponse(BaseModel):
    """Schema for insurance claim response"""
    id: int = Field(..., description="Claim ID")
    policy_id: int = Field(..., description="ID of the insurance policy")
    claim_number: str = Field(..., description="Unique claim number")
    status: str = Field(..., description="Current claim status")
    service_date: date = Field(..., description="Date service was provided")
    provider_id: str = Field(..., description="ID of the service provider")
    facility_id: Optional[str] = Field(None, description="ID of the service facility")
    diagnosis_codes: List[str] = Field(..., description="List of diagnosis codes")
    total_amount: Decimal = Field(..., description="Total claim amount")
    notes: Optional[str] = Field(None, description="Additional notes about the claim")
    service_lines: List[ClaimServiceLineResponse] = Field(..., description="List of service lines")
    documents: List[ClaimDocumentResponse] = Field(..., description="Supporting documents")
    status_history: Optional[List[ClaimStatusHistoryResponse]] = Field(
        None, 
        description="Claim status history"
    )
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True
