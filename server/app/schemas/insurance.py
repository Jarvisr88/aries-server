"""
Insurance Domain Schemas
Version: 2024-12-19_13-18
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, constr, conint, validator

# Base schemas for shared attributes
class AuditMixin(BaseModel):
    """Mixin for audit fields."""
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

class ContactInfo(BaseModel):
    """Schema for contact information."""
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None

# Insurance Company Schemas
class InsuranceCompanyBase(BaseModel):
    """Base schema for insurance company."""
    name: constr(min_length=1, max_length=100)
    code: constr(min_length=1, max_length=50)
    tax_id: Optional[constr(max_length=20)] = None
    npi: Optional[constr(min_length=10, max_length=10)] = None
    contact_info: Optional[ContactInfo] = None
    is_active: bool = True
    group_id: Optional[int] = None

class InsuranceCompanyCreate(InsuranceCompanyBase):
    """Schema for creating an insurance company."""
    pass

class InsuranceCompanyUpdate(BaseModel):
    """Schema for updating an insurance company."""
    name: Optional[constr(min_length=1, max_length=100)] = None
    code: Optional[constr(min_length=1, max_length=50)] = None
    tax_id: Optional[constr(max_length=20)] = None
    npi: Optional[constr(min_length=10, max_length=10)] = None
    contact_info: Optional[ContactInfo] = None
    is_active: Optional[bool] = None
    group_id: Optional[int] = None

class InsuranceCompanyInDB(InsuranceCompanyBase, AuditMixin):
    """Schema for insurance company in database."""
    id: int

    class Config:
        from_attributes = True

# Insurance Company Group Schemas
class InsuranceCompanyGroupBase(BaseModel):
    """Base schema for insurance company group."""
    name: constr(min_length=1, max_length=100)
    code: constr(min_length=1, max_length=50)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True

class InsuranceCompanyGroupCreate(InsuranceCompanyGroupBase):
    """Schema for creating an insurance company group."""
    pass

class InsuranceCompanyGroupUpdate(BaseModel):
    """Schema for updating an insurance company group."""
    name: Optional[constr(min_length=1, max_length=100)] = None
    code: Optional[constr(min_length=1, max_length=50)] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None

class InsuranceCompanyGroupInDB(InsuranceCompanyGroupBase, AuditMixin):
    """Schema for insurance company group in database."""
    id: int
    children: Optional[List['InsuranceCompanyGroupInDB']] = None
    companies: Optional[List[InsuranceCompanyInDB]] = None

    class Config:
        from_attributes = True

# Insurance Payer Schemas
class SubmissionConfig(BaseModel):
    """Schema for payer submission configuration."""
    allows_electronic: bool = True
    requires_auth: bool = False
    auth_endpoint: Optional[str] = None
    submission_format: Optional[str] = None
    additional_settings: Optional[Dict[str, Any]] = None

class InsurancePayerBase(BaseModel):
    """Base schema for insurance payer."""
    name: constr(min_length=1, max_length=100)
    code: constr(min_length=1, max_length=50)
    payer_id: Optional[constr(max_length=50)] = None
    company_id: int
    type_id: int
    contact_info: Optional[ContactInfo] = None
    submission_config: Optional[SubmissionConfig] = None
    is_active: bool = True

class InsurancePayerCreate(InsurancePayerBase):
    """Schema for creating an insurance payer."""
    pass

class InsurancePayerUpdate(BaseModel):
    """Schema for updating an insurance payer."""
    name: Optional[constr(min_length=1, max_length=100)] = None
    code: Optional[constr(min_length=1, max_length=50)] = None
    payer_id: Optional[constr(max_length=50)] = None
    company_id: Optional[int] = None
    type_id: Optional[int] = None
    contact_info: Optional[ContactInfo] = None
    submission_config: Optional[SubmissionConfig] = None
    is_active: Optional[bool] = None

class InsurancePayerInDB(InsurancePayerBase, AuditMixin):
    """Schema for insurance payer in database."""
    id: int
    company: Optional[InsuranceCompanyInDB] = None

    class Config:
        from_attributes = True

# Insurance Type Schemas
class InsuranceTypeSettings(BaseModel):
    """Schema for insurance type settings."""
    requires_auth: bool = False
    auth_validity_days: Optional[int] = None
    coverage_rules: Optional[Dict[str, Any]] = None
    additional_settings: Optional[Dict[str, Any]] = None

class InsuranceTypeBase(BaseModel):
    """Base schema for insurance type."""
    name: constr(min_length=1, max_length=100)
    code: constr(min_length=1, max_length=50)
    description: Optional[str] = None
    category: constr(min_length=1, max_length=50)
    priority: conint(ge=0) = 0
    settings: Optional[InsuranceTypeSettings] = None
    is_active: bool = True

class InsuranceTypeCreate(InsuranceTypeBase):
    """Schema for creating an insurance type."""
    pass

class InsuranceTypeUpdate(BaseModel):
    """Schema for updating an insurance type."""
    name: Optional[constr(min_length=1, max_length=100)] = None
    code: Optional[constr(min_length=1, max_length=50)] = None
    description: Optional[str] = None
    category: Optional[constr(min_length=1, max_length=50)] = None
    priority: Optional[conint(ge=0)] = None
    settings: Optional[InsuranceTypeSettings] = None
    is_active: Optional[bool] = None

class InsuranceTypeInDB(InsuranceTypeBase, AuditMixin):
    """Schema for insurance type in database."""
    id: int
    payers: Optional[List[InsurancePayerInDB]] = None

    class Config:
        from_attributes = True

# Insurance Policy Schemas
class InsuranceBenefits(BaseModel):
    """Schema for insurance policy benefits."""
    copay: Optional[float] = None
    coinsurance: Optional[float] = None
    deductible: Optional[float] = None
    out_of_pocket_max: Optional[float] = None
    coverage_details: Optional[Dict[str, Any]] = None

class VerificationInfo(BaseModel):
    """Schema for insurance verification information."""
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verification_method: Optional[str] = None
    verification_details: Optional[Dict[str, Any]] = None
    is_verified: bool = False

class InsurancePolicyBase(BaseModel):
    """Base schema for insurance policy."""
    policy_number: constr(min_length=1, max_length=50)
    group_number: Optional[constr(max_length=50)] = None
    patient_id: int
    payer_id: int
    type_id: int
    coverage_start_date: date
    coverage_end_date: Optional[date] = None
    status: constr(regex='^(active|inactive|cancelled|expired)$') = 'active'
    priority: conint(ge=0) = 0
    benefits: Optional[InsuranceBenefits] = None
    verification_info: Optional[VerificationInfo] = None

    @validator('coverage_end_date')
    def end_date_after_start_date(cls, v, values):
        """Validate that end date is after start date."""
        if v and values.get('coverage_start_date') and v <= values['coverage_start_date']:
            raise ValueError('Coverage end date must be after start date')
        return v

class InsurancePolicyCreate(InsurancePolicyBase):
    """Schema for creating an insurance policy."""
    pass

class InsurancePolicyUpdate(BaseModel):
    """Schema for updating an insurance policy."""
    policy_number: Optional[constr(min_length=1, max_length=50)] = None
    group_number: Optional[constr(max_length=50)] = None
    payer_id: Optional[int] = None
    type_id: Optional[int] = None
    coverage_start_date: Optional[date] = None
    coverage_end_date: Optional[date] = None
    status: Optional[constr(regex='^(active|inactive|cancelled|expired)$')] = None
    priority: Optional[conint(ge=0)] = None
    benefits: Optional[InsuranceBenefits] = None
    verification_info: Optional[VerificationInfo] = None

class InsurancePolicyInDB(InsurancePolicyBase, AuditMixin):
    """Schema for insurance policy in database."""
    id: int
    payer: Optional[InsurancePayerInDB] = None
    type: Optional[InsuranceTypeInDB] = None

    class Config:
        from_attributes = True

# Batch Operation Schemas
class ClaimDocumentCreate(BaseModel):
    """Schema for creating a claim document"""
    document_type: str = Field(..., description="Type of document")
    document_url: str = Field(..., description="URL to the document")
    description: Optional[str] = Field(None, description="Document description")

class InsuranceClaimCreate(BaseModel):
    """Schema for creating an insurance claim"""
    policy_id: int = Field(..., description="ID of the insurance policy")
    service_date: datetime = Field(..., description="Date of service")
    service_provider: str = Field(..., description="Name of service provider")
    diagnosis_codes: List[str] = Field(..., description="List of diagnosis codes")
    procedure_codes: List[str] = Field(..., description="List of procedure codes")
    claim_amount: float = Field(..., description="Total claim amount")
    documents: Optional[List[ClaimDocumentCreate]] = Field(None, description="Supporting documents")

    @validator('claim_amount')
    def validate_claim_amount(cls, v):
        """Validate claim amount is positive"""
        if v <= 0:
            raise ValueError("Claim amount must be positive")
        return v

class InsuranceClaimUpdate(BaseModel):
    """Schema for updating an insurance claim"""
    service_provider: Optional[str] = None
    diagnosis_codes: Optional[List[str]] = None
    procedure_codes: Optional[List[str]] = None
    claim_amount: Optional[float] = None

    @validator('claim_amount')
    def validate_claim_amount(cls, v):
        """Validate claim amount is positive"""
        if v is not None and v <= 0:
            raise ValueError("Claim amount must be positive")
        return v

class ClaimStatusUpdate(BaseModel):
    """Schema for updating claim status"""
    status: str = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Notes about the status change")

class InsuranceClaimResponse(BaseModel):
    """Schema for insurance claim response"""
    id: int
    policy_id: int
    service_date: datetime
    service_provider: str
    diagnosis_codes: List[str]
    procedure_codes: List[str]
    claim_amount: float
    status: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str

    class Config:
        """Pydantic config"""
        from_attributes = True

class BatchClaimSubmission(BaseModel):
    """Schema for batch claim submission"""
    claims: List[InsuranceClaimCreate] = Field(
        ...,
        description="List of claims to submit",
        max_items=100
    )

class BatchClaimResponse(BaseModel):
    """Schema for batch claim submission response"""
    successful_claims: List[InsuranceClaimResponse] = Field(
        ...,
        description="Successfully submitted claims"
    )
    failed_claims: List[Dict[str, Any]] = Field(
        ...,
        description="Failed claim submissions with errors"
    )
    total_submitted: int = Field(..., description="Total number of claims submitted")
    total_successful: int = Field(..., description="Number of successful submissions")
    total_failed: int = Field(..., description="Number of failed submissions")

# Update forward references
InsuranceCompanyGroupInDB.update_forward_refs()
