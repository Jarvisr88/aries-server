"""
Billing & Insurance Domain Models
Version: 2024-12-14_17-58
"""
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.system import TimestampMixin
from app.core.database import Base

class ClaimStatus(str, Enum):
    DRAFT = 'draft'
    READY = 'ready'
    SUBMITTED = 'submitted'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    PAID = 'paid'
    DENIED = 'denied'
    APPEALED = 'appealed'

class PaymentStatus(str, Enum):
    PENDING = 'pending'
    PROCESSED = 'processed'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    VOIDED = 'voided'

class PaymentType(str, Enum):
    CASH = 'cash'
    CHECK = 'check'
    CREDIT_CARD = 'credit_card'
    INSURANCE = 'insurance'
    MEDICARE = 'medicare'
    MEDICAID = 'medicaid'

class AdjustmentType(str, Enum):
    WRITE_OFF = 'write_off'
    DISCOUNT = 'discount'
    INSURANCE_ADJUSTMENT = 'insurance_adjustment'
    CONTRACTUAL = 'contractual'
    BAD_DEBT = 'bad_debt'

class Claim(Base, TimestampMixin):
    """Claim model - migrated from c01.tbl_claim"""
    __tablename__ = 'claims'

    id: Mapped[int] = Column(Integer, primary_key=True)
    order_id: Mapped[int] = Column(Integer, ForeignKey('orders.id'), nullable=False)
    insurance_id: Mapped[int] = Column(Integer, ForeignKey('customer_insurances.id'), nullable=False)
    
    # Claim Information
    claim_number: Mapped[str] = Column(String(50), unique=True)
    status: Mapped[ClaimStatus] = Column(SQLEnum(ClaimStatus), nullable=False, default=ClaimStatus.DRAFT)
    filing_date: Mapped[Optional[date]] = Column(Date)
    service_from_date: Mapped[date] = Column(Date, nullable=False)
    service_to_date: Mapped[Optional[date]] = Column(Date)
    
    # Amounts
    billed_amount: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    allowed_amount: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    paid_amount: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    patient_responsibility: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    
    # Additional Information
    diagnosis_codes: Mapped[str] = Column(String(500))  # Comma-separated ICD-10 codes
    authorization_number: Mapped[Optional[str]] = Column(String(50))
    notes: Mapped[Optional[str]] = Column(Text)
    
    # Relationships
    order = relationship("Order", back_populates="claims")
    insurance = relationship("CustomerInsurance")
    line_items: Mapped[List["ClaimLineItem"]] = relationship("ClaimLineItem", back_populates="claim")
    status_history: Mapped[List["ClaimStatusHistory"]] = relationship("ClaimStatusHistory", back_populates="claim")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="claim")

class ClaimLineItem(Base, TimestampMixin):
    """Claim Line Item model - migrated from c01.tbl_claim_line_item"""
    __tablename__ = 'claim_line_items'

    id: Mapped[int] = Column(Integer, primary_key=True)
    claim_id: Mapped[int] = Column(Integer, ForeignKey('claims.id'), nullable=False)
    order_detail_id: Mapped[int] = Column(Integer, ForeignKey('order_details.id'), nullable=False)
    
    # Line Item Information
    sequence_number: Mapped[int] = Column(Integer, nullable=False)
    service_date: Mapped[date] = Column(Date, nullable=False)
    
    # Billing Codes
    hcpcs_code: Mapped[str] = Column(String(20), nullable=False)
    modifier1: Mapped[Optional[str]] = Column(String(2))
    modifier2: Mapped[Optional[str]] = Column(String(2))
    modifier3: Mapped[Optional[str]] = Column(String(2))
    modifier4: Mapped[Optional[str]] = Column(String(2))
    
    # Amounts
    units: Mapped[int] = Column(Integer, nullable=False)
    billed_amount: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    allowed_amount: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    paid_amount: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    
    # Additional Information
    notes: Mapped[Optional[str]] = Column(Text)
    
    # Relationships
    claim: Mapped[Claim] = relationship("Claim", back_populates="line_items")
    order_detail = relationship("OrderDetail")

class ClaimStatusHistory(Base, TimestampMixin):
    """Claim Status History model - migrated from c01.tbl_claim_status_history"""
    __tablename__ = 'claim_status_history'

    id: Mapped[int] = Column(Integer, primary_key=True)
    claim_id: Mapped[int] = Column(Integer, ForeignKey('claims.id'), nullable=False)
    status: Mapped[ClaimStatus] = Column(SQLEnum(ClaimStatus), nullable=False)
    notes: Mapped[Optional[str]] = Column(Text)
    
    claim: Mapped[Claim] = relationship("Claim", back_populates="status_history")

class Payment(Base, TimestampMixin):
    """Payment model - migrated from c01.tbl_payment"""
    __tablename__ = 'payments'

    id: Mapped[int] = Column(Integer, primary_key=True)
    claim_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('claims.id'))
    order_id: Mapped[int] = Column(Integer, ForeignKey('orders.id'), nullable=False)
    
    # Payment Information
    payment_number: Mapped[str] = Column(String(50), unique=True)
    payment_date: Mapped[datetime] = Column(DateTime, nullable=False)
    payment_type: Mapped[PaymentType] = Column(SQLEnum(PaymentType), nullable=False)
    status: Mapped[PaymentStatus] = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Amount Information
    amount: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    
    # Payment Details
    reference_number: Mapped[Optional[str]] = Column(String(50))  # Check number, transaction ID, etc.
    payment_method: Mapped[Optional[str]] = Column(String(50))  # Visa, Mastercard, etc.
    payment_source: Mapped[Optional[str]] = Column(String(100))  # Bank name, insurance company, etc.
    
    # Additional Information
    notes: Mapped[Optional[str]] = Column(Text)
    
    # Relationships
    claim: Mapped[Optional[Claim]] = relationship("Claim", back_populates="payments")
    order = relationship("Order")
    adjustments: Mapped[List["PaymentAdjustment"]] = relationship("PaymentAdjustment", back_populates="payment")

class PaymentAdjustment(Base, TimestampMixin):
    """Payment Adjustment model - migrated from c01.tbl_payment_adjustment"""
    __tablename__ = 'payment_adjustments'

    id: Mapped[int] = Column(Integer, primary_key=True)
    payment_id: Mapped[int] = Column(Integer, ForeignKey('payments.id'), nullable=False)
    
    # Adjustment Information
    adjustment_type: Mapped[AdjustmentType] = Column(SQLEnum(AdjustmentType), nullable=False)
    amount: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    reason_code: Mapped[Optional[str]] = Column(String(20))
    notes: Mapped[Optional[str]] = Column(Text)
    
    payment: Mapped[Payment] = relationship("Payment", back_populates="adjustments")

class BillingCode(Base, TimestampMixin):
    """Billing Code model - migrated from c01.tbl_billing_code"""
    __tablename__ = 'billing_codes'

    id: Mapped[int] = Column(Integer, primary_key=True)
    code: Mapped[str] = Column(String(20), nullable=False, unique=True)
    description: Mapped[str] = Column(String(255), nullable=False)
    
    # Code Information
    code_type: Mapped[str] = Column(String(20), nullable=False)  # HCPCS, ICD-10, etc.
    effective_date: Mapped[date] = Column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = Column(Date)
    
    # Pricing Information
    default_price: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    unit_type: Mapped[str] = Column(String(20))  # Each, Day, Month, etc.
    
    # Status
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # Additional Information
    notes: Mapped[Optional[str]] = Column(Text)

class InsurancePlan(Base, TimestampMixin):
    """Insurance Plan model - migrated from c01.tbl_insurance_plan"""
    __tablename__ = 'insurance_plans'

    id: Mapped[int] = Column(Integer, primary_key=True)
    insurance_company_id: Mapped[int] = Column(Integer, ForeignKey('insurance_companies.id'), nullable=False)
    
    # Plan Information
    plan_name: Mapped[str] = Column(String(100), nullable=False)
    plan_type: Mapped[str] = Column(String(50), nullable=False)  # HMO, PPO, etc.
    plan_number: Mapped[Optional[str]] = Column(String(50))
    
    # Contact Information
    claims_address: Mapped[Optional[str]] = Column(String(255))
    claims_phone: Mapped[Optional[str]] = Column(String(20))
    claims_email: Mapped[Optional[str]] = Column(String(255))
    
    # Electronic Filing
    payer_id: Mapped[Optional[str]] = Column(String(50))
    supports_electronic_filing: Mapped[bool] = Column(Boolean, default=True)
    
    # Additional Information
    notes: Mapped[Optional[str]] = Column(Text)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    insurance_company = relationship("InsuranceCompany")

class InsuranceFeeSchedule(Base, TimestampMixin):
    """Insurance Fee Schedule model - migrated from c01.tbl_insurance_fee_schedule"""
    __tablename__ = 'insurance_fee_schedules'

    id: Mapped[int] = Column(Integer, primary_key=True)
    insurance_plan_id: Mapped[int] = Column(Integer, ForeignKey('insurance_plans.id'), nullable=False)
    billing_code_id: Mapped[int] = Column(Integer, ForeignKey('billing_codes.id'), nullable=False)
    
    # Fee Information
    allowed_amount: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    effective_date: Mapped[date] = Column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = Column(Date)
    
    # Additional Information
    notes: Mapped[Optional[str]] = Column(Text)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    insurance_plan = relationship("InsurancePlan")
    billing_code = relationship("BillingCode")
