"""
Billing & Insurance Domain Schemas
Version: 2024-12-14_17-58
"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from app.models.billing import ClaimStatus, PaymentStatus, PaymentType, AdjustmentType

class ClaimBase(BaseModel):
    order_id: int
    insurance_id: int
    claim_number: str
    status: ClaimStatus = ClaimStatus.DRAFT
    filing_date: Optional[date] = None
    service_from_date: date
    service_to_date: Optional[date] = None
    billed_amount: Decimal
    allowed_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    patient_responsibility: Optional[Decimal] = None
    diagnosis_codes: str
    authorization_number: Optional[str] = None
    notes: Optional[str] = None

class ClaimCreate(ClaimBase):
    pass

class ClaimUpdate(ClaimBase):
    pass

class ClaimInDB(ClaimBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ClaimLineItemBase(BaseModel):
    claim_id: int
    order_detail_id: int
    sequence_number: int
    service_date: date
    hcpcs_code: str
    modifier1: Optional[str] = None
    modifier2: Optional[str] = None
    modifier3: Optional[str] = None
    modifier4: Optional[str] = None
    units: int
    billed_amount: Decimal
    allowed_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    notes: Optional[str] = None

class ClaimLineItemCreate(ClaimLineItemBase):
    pass

class ClaimLineItemUpdate(ClaimLineItemBase):
    pass

class ClaimLineItemInDB(ClaimLineItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ClaimStatusHistoryBase(BaseModel):
    claim_id: int
    status: ClaimStatus
    notes: Optional[str] = None

class ClaimStatusHistoryCreate(ClaimStatusHistoryBase):
    pass

class ClaimStatusHistoryUpdate(ClaimStatusHistoryBase):
    pass

class ClaimStatusHistoryInDB(ClaimStatusHistoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaymentBase(BaseModel):
    claim_id: Optional[int] = None
    order_id: int
    payment_number: str
    payment_date: datetime
    payment_type: PaymentType
    status: PaymentStatus = PaymentStatus.PENDING
    amount: Decimal
    reference_number: Optional[str] = None
    payment_method: Optional[str] = None
    payment_source: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(PaymentBase):
    pass

class PaymentInDB(PaymentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaymentAdjustmentBase(BaseModel):
    payment_id: int
    adjustment_type: AdjustmentType
    amount: Decimal
    reason_code: Optional[str] = None
    notes: Optional[str] = None

class PaymentAdjustmentCreate(PaymentAdjustmentBase):
    pass

class PaymentAdjustmentUpdate(PaymentAdjustmentBase):
    pass

class PaymentAdjustmentInDB(PaymentAdjustmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BillingCodeBase(BaseModel):
    code: str
    description: str
    code_type: str
    effective_date: date
    end_date: Optional[date] = None
    default_price: Optional[Decimal] = None
    unit_type: str
    is_active: bool = True
    notes: Optional[str] = None

class BillingCodeCreate(BillingCodeBase):
    pass

class BillingCodeUpdate(BillingCodeBase):
    pass

class BillingCodeInDB(BillingCodeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InsurancePlanBase(BaseModel):
    insurance_company_id: int
    plan_name: str
    plan_type: str
    plan_number: Optional[str] = None
    claims_address: Optional[str] = None
    claims_phone: Optional[str] = None
    claims_email: Optional[str] = None
    payer_id: Optional[str] = None
    supports_electronic_filing: bool = True
    notes: Optional[str] = None
    is_active: bool = True

class InsurancePlanCreate(InsurancePlanBase):
    pass

class InsurancePlanUpdate(InsurancePlanBase):
    pass

class InsurancePlanInDB(InsurancePlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InsuranceFeeScheduleBase(BaseModel):
    insurance_plan_id: int
    billing_code_id: int
    allowed_amount: Decimal
    effective_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: bool = True

class InsuranceFeeScheduleCreate(InsuranceFeeScheduleBase):
    pass

class InsuranceFeeScheduleUpdate(InsuranceFeeScheduleBase):
    pass

class InsuranceFeeScheduleInDB(InsuranceFeeScheduleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
