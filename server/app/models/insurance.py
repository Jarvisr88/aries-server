"""
Insurance Domain Models
Version: 2024-12-19_13-18
"""
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

class AuditMixin:
    """Mixin for audit fields."""
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(50), nullable=True)
    updated_by = Column(String(50), nullable=True)

class InsuranceCompanyGroup(Base, AuditMixin):
    """Model for insurance company groups."""
    __tablename__ = "insurance_company_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("insurance_company_groups.id"), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    parent = relationship("InsuranceCompanyGroup", remote_side=[id], backref="children")
    companies = relationship("InsuranceCompany", back_populates="group")

    __table_args__ = (
        Index("ix_insurance_company_groups_name", "name"),
        Index("ix_insurance_company_groups_code", "code"),
    )

class InsuranceCompany(Base, AuditMixin):
    """Model for insurance companies."""
    __tablename__ = "insurance_companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    tax_id = Column(String(20), nullable=True)
    npi = Column(String(10), nullable=True)
    contact_info = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True)
    group_id = Column(Integer, ForeignKey("insurance_company_groups.id"), nullable=True)

    # Relationships
    group = relationship("InsuranceCompanyGroup", back_populates="companies")
    payers = relationship("InsurancePayer", back_populates="company")

    __table_args__ = (
        Index("ix_insurance_companies_name", "name"),
        Index("ix_insurance_companies_code", "code"),
        Index("ix_insurance_companies_npi", "npi"),
    )

class InsuranceType(Base, AuditMixin):
    """Model for insurance types."""
    __tablename__ = "insurance_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(String, nullable=True)
    category = Column(String(50), nullable=False)
    priority = Column(Integer, default=0)
    settings = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    payers = relationship("InsurancePayer", back_populates="type")

    __table_args__ = (
        Index("ix_insurance_types_name", "name"),
        Index("ix_insurance_types_code", "code"),
        Index("ix_insurance_types_category", "category"),
    )

class InsurancePayer(Base, AuditMixin):
    """Model for insurance payers."""
    __tablename__ = "insurance_payers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    payer_id = Column(String(50), nullable=True)
    company_id = Column(Integer, ForeignKey("insurance_companies.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("insurance_types.id"), nullable=False)
    contact_info = Column(JSONB, nullable=True)
    submission_config = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    company = relationship("InsuranceCompany", back_populates="payers")
    type = relationship("InsuranceType", back_populates="payers")
    policies = relationship("InsurancePolicy", back_populates="payer")

    __table_args__ = (
        UniqueConstraint("code", "company_id", name="uq_payer_code_company"),
        Index("ix_insurance_payers_name", "name"),
        Index("ix_insurance_payers_code", "code"),
        Index("ix_insurance_payers_payer_id", "payer_id"),
    )

class InsurancePolicy(Base, AuditMixin):
    """Model for insurance policies."""
    __tablename__ = "insurance_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String(50), nullable=False)
    group_number = Column(String(50), nullable=True)
    patient_id = Column(Integer, nullable=False)  # Foreign key to patients table
    payer_id = Column(Integer, ForeignKey("insurance_payers.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("insurance_types.id"), nullable=False)
    coverage_start_date = Column(Date, nullable=False)
    coverage_end_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    priority = Column(Integer, default=0)
    benefits = Column(JSONB, nullable=True)
    verification_info = Column(JSONB, nullable=True)

    # Relationships
    payer = relationship("InsurancePayer", back_populates="policies")
    type = relationship("InsuranceType")

    __table_args__ = (
        Index("ix_insurance_policies_policy_number", "policy_number"),
        Index("ix_insurance_policies_patient_id", "patient_id"),
        Index("ix_insurance_policies_status", "status"),
        Index("ix_insurance_policies_coverage_dates", "coverage_start_date", "coverage_end_date"),
    )

class InsuranceAuthorization(Base, AuditMixin):
    """Model for insurance authorizations."""
    __tablename__ = "insurance_authorizations"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    auth_number = Column(String(50), nullable=False)
    service_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    authorized_units = Column(Integer, nullable=True)
    used_units = Column(Integer, default=0)
    notes = Column(String, nullable=True)
    extra_data = Column(JSONB, nullable=True)

    # Relationships
    policy = relationship("InsurancePolicy", back_populates="authorizations")

    __table_args__ = (
        Index("ix_insurance_authorizations_auth_number", "auth_number"),
        Index("ix_insurance_authorizations_status", "status"),
        Index("ix_insurance_authorizations_dates", "start_date", "end_date"),
    )

class InsuranceClaim(Base, AuditMixin):
    """Model for insurance claims."""
    __tablename__ = "insurance_claims"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    claim_number = Column(String(50), nullable=False, unique=True)
    service_date = Column(Date, nullable=False)
    filing_date = Column(Date, nullable=False)
    diagnosis_codes = Column(JSONB, nullable=True)
    procedure_codes = Column(JSONB, nullable=True)
    claim_amount = Column(Integer, nullable=False)  # Stored in cents
    approved_amount = Column(Integer, nullable=True)  # Stored in cents
    paid_amount = Column(Integer, nullable=True)  # Stored in cents
    status = Column(String(20), nullable=False, default="submitted")
    adjudication_date = Column(Date, nullable=True)
    extra_data = Column(JSONB, nullable=True)

    # Relationships
    policy = relationship("InsurancePolicy", back_populates="claims")

    __table_args__ = (
        Index("ix_insurance_claims_claim_number", "claim_number"),
        Index("ix_insurance_claims_status", "status"),
        Index("ix_insurance_claims_dates", "service_date", "filing_date"),
    )

class InsuranceCoverage(Base, AuditMixin):
    """Model for insurance coverage details."""
    __tablename__ = "insurance_coverages"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    coverage_type = Column(String(50), nullable=False)
    benefit_details = Column(JSONB, nullable=True)
    copay_amount = Column(Integer, nullable=True)  # Stored in cents
    coinsurance_rate = Column(Integer, nullable=True)  # Stored as percentage * 100
    deductible_amount = Column(Integer, nullable=True)  # Stored in cents
    out_of_pocket_max = Column(Integer, nullable=True)  # Stored in cents
    prior_auth_required = Column(Boolean, default=False)
    extra_data = Column(JSONB, nullable=True)

    # Relationships
    policy = relationship("InsurancePolicy", back_populates="coverages")

    __table_args__ = (
        Index("ix_insurance_coverages_coverage_type", "coverage_type"),
        UniqueConstraint("policy_id", "coverage_type", name="uq_policy_coverage_type"),
    )

# Set up relationships
InsurancePolicy.authorizations = relationship("InsuranceAuthorization", back_populates="policy")
InsurancePolicy.claims = relationship("InsuranceClaim", back_populates="policy")
InsurancePolicy.coverages = relationship("InsuranceCoverage", back_populates="policy")
