"""
Insurance Verification Schemas
Version: 2024-12-19_17-41
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

class VerificationRequest(BaseModel):
    """Schema for insurance verification request"""
    policy_id: int = Field(..., description="ID of the insurance policy to verify")
    verification_type: str = Field(..., description="Type of verification (INITIAL, PERIODIC, PRE_SERVICE)")
    service_types: List[str] = Field(..., description="List of service types to verify")
    reference_date: Optional[date] = Field(None, description="Date for which to verify coverage")

    @validator('verification_type')
    def validate_verification_type(cls, v):
        valid_types = {"INITIAL", "PERIODIC", "PRE_SERVICE"}
        if v not in valid_types:
            raise ValueError(f"Verification type must be one of: {', '.join(valid_types)}")
        return v

class PolicyVerificationResponse(BaseModel):
    """Schema for policy verification response"""
    policy_number: str = Field(..., description="Insurance policy number")
    payer_id: str = Field(..., description="ID of the insurance payer")
    payer_name: Optional[str] = Field(None, description="Name of the insurance payer")
    is_active: bool = Field(..., description="Whether the policy is currently active")
    start_date: date = Field(..., description="Policy start date")
    end_date: Optional[date] = Field(None, description="Policy end date")
    verification_date: date = Field(..., description="Date for which policy was verified")
    policy_type: str = Field(..., description="Type of insurance policy")
    group_number: Optional[str] = Field(None, description="Group number if applicable")
    subscriber_id: str = Field(..., description="Subscriber ID")
    subscriber_name: str = Field(..., description="Name of the subscriber")

class BenefitDetails(BaseModel):
    """Schema for benefit details"""
    deductible: float = Field(..., description="Annual deductible amount")
    deductible_met: float = Field(..., description="Amount of deductible met")
    out_of_pocket_max: float = Field(..., description="Annual out-of-pocket maximum")
    out_of_pocket_met: float = Field(..., description="Amount of out-of-pocket maximum met")
    copay: Optional[float] = Field(None, description="Copay amount if applicable")
    coinsurance: Optional[float] = Field(None, description="Coinsurance percentage if applicable")
    limitations: Optional[Dict[str, Any]] = Field(None, description="Coverage limitations and restrictions")

class ServiceBenefits(BaseModel):
    """Schema for service-specific benefits"""
    is_covered: bool = Field(..., description="Whether the service is covered")
    requires_authorization: Optional[bool] = Field(None, description="Whether prior authorization is required")
    network_restrictions: Optional[Dict[str, Any]] = Field(None, description="Network-specific restrictions")
    benefit_details: Optional[BenefitDetails] = Field(None, description="Detailed benefit information")
    message: Optional[str] = Field(None, description="Additional information or explanation")

class BenefitVerificationResponse(BaseModel):
    """Schema for benefit verification response"""
    verification_date: date = Field(..., description="Date benefits were verified")
    benefits_by_service: Dict[str, ServiceBenefits] = Field(
        ..., 
        description="Benefits information for each service type"
    )

class VerificationStatusHistoryResponse(BaseModel):
    """Schema for verification status history"""
    id: int = Field(..., description="Status history entry ID")
    verification_id: int = Field(..., description="ID of the associated verification")
    status: str = Field(..., description="Status value")
    notes: Optional[str] = Field(None, description="Notes about the status")
    created_at: datetime
    created_by: str

class VerificationResponse(BaseModel):
    """Schema for verification response"""
    id: int = Field(..., description="Verification ID")
    status: str = Field(..., description="Current verification status")
    policy_verification: PolicyVerificationResponse = Field(
        ..., 
        description="Policy verification results"
    )
    benefits_verification: Optional[BenefitVerificationResponse] = Field(
        None, 
        description="Benefits verification results"
    )
    failure_reason: Optional[str] = Field(None, description="Reason for verification failure if applicable")
    verification_date: datetime = Field(..., description="Date and time of verification")
    status_history: Optional[List[VerificationStatusHistoryResponse]] = Field(
        None, 
        description="Verification status history"
    )
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True
