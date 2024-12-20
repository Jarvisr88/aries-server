"""
Insurance Eligibility Schemas
Version: 2024-12-19_16-55
"""
from datetime import date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class BenefitInformation(BaseModel):
    """Schema for insurance benefit information"""
    deductible: float = Field(..., description="Annual deductible amount")
    deductible_met: float = Field(..., description="Amount of deductible met")
    out_of_pocket_max: float = Field(..., description="Annual out-of-pocket maximum")
    out_of_pocket_met: float = Field(..., description="Amount of out-of-pocket maximum met")
    copay: Optional[float] = Field(None, description="Copay amount if applicable")
    coinsurance: Optional[float] = Field(None, description="Coinsurance percentage if applicable")

class EligibilityCheckRequest(BaseModel):
    """Schema for eligibility check request"""
    policy_id: int = Field(..., description="ID of the insurance policy to check")
    service_type: str = Field(..., description="Type of service to check eligibility for")
    service_date: Optional[date] = Field(None, description="Date of service (defaults to current date)")

class EligibilityCheckResponse(BaseModel):
    """Schema for eligibility check response"""
    is_eligible: bool = Field(..., description="Whether the patient is eligible for the service")
    status: str = Field(..., description="Status of eligibility (e.g., ACTIVE, INACTIVE)")
    message: str = Field(..., description="Human-readable message about eligibility status")
    details: Dict[str, Any] = Field(..., description="Additional details about eligibility")

class CoverageVerificationRequest(BaseModel):
    """Schema for coverage verification request"""
    policy_id: int = Field(..., description="ID of the insurance policy to verify")
    service_types: List[str] = Field(..., description="List of service types to verify coverage for")
    service_date: Optional[date] = Field(None, description="Date of service (defaults to current date)")

class CoverageVerificationResponse(BaseModel):
    """Schema for coverage verification response"""
    policy_number: str = Field(..., description="Insurance policy number")
    payer_id: str = Field(..., description="ID of the insurance payer")
    verification_date: date = Field(..., description="Date for which coverage was verified")
    coverage_details: Dict[str, Dict[str, Any]] = Field(
        ..., 
        description="Coverage details for each service type"
    )
