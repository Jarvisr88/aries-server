"""
Insurance Test Utilities
Version: 2024-12-19_18-17
"""
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.insurance import (
    InsurancePolicy,
    InsuranceClaim,
    InsuranceAuthorization,
    InsuranceVerification
)
from app.tests.utils.utils import random_lower_string, random_email

def create_test_insurance_policy(
    db: Session,
    *,
    payer_id: Optional[int] = None,
    type_id: Optional[int] = None,
    patient_id: Optional[int] = None
) -> InsurancePolicy:
    """Create a test insurance policy."""
    if not payer_id:
        payer_id = 1  # Default test payer
    if not type_id:
        type_id = 1  # Default test type
    if not patient_id:
        patient_id = 1  # Default test patient

    policy = InsurancePolicy(
        policy_number=f"TEST-{random_lower_string()}",
        payer_id=payer_id,
        type_id=type_id,
        patient_id=patient_id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        status="ACTIVE",
        group_number=f"GRP-{random_lower_string()}",
        subscriber_id=f"SUB-{random_lower_string()}",
        subscriber_name="Test Subscriber",
        subscriber_relationship="SELF",
        created_by="test-user",
        updated_by="test-user"
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

def create_test_insurance_claim(
    db: Session,
    policy_id: int,
    *,
    status: str = "SUBMITTED"
) -> InsuranceClaim:
    """Create a test insurance claim."""
    claim = InsuranceClaim(
        policy_id=policy_id,
        claim_number=f"CLM-{random_lower_string()}",
        service_date=date.today(),
        diagnosis_codes=["A00.0"],
        service_lines=[{
            "procedure_code": "99213",
            "quantity": 1,
            "charge_amount": 150.00
        }],
        total_charge=150.00,
        status=status,
        created_by="test-user",
        updated_by="test-user"
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim

def create_test_authorization(
    db: Session,
    policy_id: int,
    *,
    status: str = "PENDING"
) -> InsuranceAuthorization:
    """Create a test insurance authorization."""
    auth = InsuranceAuthorization(
        policy_id=policy_id,
        authorization_number=f"AUTH-{random_lower_string()}",
        service_type="SURGERY",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        diagnosis_codes=["M54.5"],
        procedure_codes=["99213"],
        status=status,
        created_by="test-user",
        updated_by="test-user"
    )
    db.add(auth)
    db.commit()
    db.refresh(auth)
    return auth

def create_test_verification(
    db: Session,
    policy_id: int,
    *,
    verification_type: str = "INITIAL"
) -> InsuranceVerification:
    """Create a test insurance verification."""
    verification = InsuranceVerification(
        policy_id=policy_id,
        verification_type=verification_type,
        service_types=["OFFICE_VISIT"],
        verification_date=datetime.now(),
        policy_verification={
            "is_active": True,
            "coverage_dates": {
                "start": date.today().isoformat(),
                "end": (date.today() + timedelta(days=365)).isoformat()
            }
        },
        benefits_verification={
            "deductible": 1000.00,
            "deductible_met": 500.00,
            "out_of_pocket_max": 5000.00,
            "out_of_pocket_met": 1000.00
        },
        created_by="test-user",
        updated_by="test-user"
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification
