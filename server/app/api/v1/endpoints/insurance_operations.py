"""
Insurance Operations API Endpoints
Version: 2024-12-19_17-45

This module contains endpoints for insurance operations such as:
- Eligibility checks
- Claims management
- Prior authorizations
- Insurance verification
"""
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.insurance_eligibility import InsuranceEligibilityService
from app.services.insurance_claim import InsuranceClaimService
from app.services.insurance_authorization import InsuranceAuthorizationService
from app.services.insurance_verification import InsuranceVerificationService
from app.schemas.insurance_eligibility import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    CoverageVerificationRequest,
    CoverageVerificationResponse
)
from app.schemas.insurance_claim import (
    InsuranceClaimCreate,
    InsuranceClaimUpdate,
    InsuranceClaimResponse,
    ClaimStatusUpdate,
    ClaimDocumentCreate
)
from app.schemas.insurance_authorization import (
    AuthorizationRequest,
    AuthorizationResponse,
    AuthorizationStatusUpdate
)
from app.schemas.insurance_verification import (
    VerificationRequest,
    VerificationResponse
)

router = APIRouter(prefix="/insurance/operations", tags=["insurance-operations"])

# Eligibility Endpoints

@router.post(
    "/eligibility/check",
    response_model=EligibilityCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check insurance eligibility"
)
async def check_eligibility(
    request: EligibilityCheckRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Check eligibility for a patient's insurance policy."""
    return await InsuranceEligibilityService.check_eligibility(db, request, current_user)

@router.post(
    "/eligibility/verify-coverage",
    response_model=CoverageVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify coverage details"
)
async def verify_coverage(
    request: CoverageVerificationRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Verify coverage details for specific services."""
    return await InsuranceEligibilityService.verify_coverage(db, request, current_user)

# Claims Endpoints

@router.post(
    "/claims",
    response_model=InsuranceClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new insurance claim"
)
async def submit_claim(
    claim_data: InsuranceClaimCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Submit a new insurance claim."""
    return await InsuranceClaimService.submit_claim(db, claim_data, current_user)

@router.get(
    "/claims/{claim_id}",
    response_model=InsuranceClaimResponse,
    summary="Get claim details"
)
async def get_claim(
    claim_id: int,
    include_history: bool = Query(False, description="Include status history"),
    db: Session = Depends(get_db)
):
    """Get details of a specific claim."""
    return await InsuranceClaimService.get_claim(db, claim_id, include_history)

@router.get(
    "/claims",
    response_model=List[InsuranceClaimResponse],
    summary="List insurance claims"
)
async def list_claims(
    policy_id: Optional[int] = None,
    status: Optional[str] = None,
    service_date_from: Optional[datetime] = None,
    service_date_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get a list of insurance claims with optional filtering."""
    return await InsuranceClaimService.get_claims(
        db, policy_id, status, service_date_from, service_date_to, skip, limit
    )

@router.patch(
    "/claims/{claim_id}/status",
    response_model=InsuranceClaimResponse,
    summary="Update claim status"
)
async def update_claim_status(
    claim_id: int,
    status_update: ClaimStatusUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update the status of an insurance claim."""
    return await InsuranceClaimService.update_claim_status(
        db, claim_id, status_update, current_user
    )

@router.post(
    "/claims/{claim_id}/documents",
    response_model=InsuranceClaimResponse,
    summary="Add document to claim"
)
async def add_claim_document(
    claim_id: int,
    document: ClaimDocumentCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Add a document to an existing claim."""
    return await InsuranceClaimService.add_claim_document(
        db, claim_id, document, current_user
    )

# Authorization Endpoints

@router.post(
    "/authorizations",
    response_model=AuthorizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit authorization request"
)
async def request_authorization(
    auth_request: AuthorizationRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Submit a new authorization request."""
    return await InsuranceAuthorizationService.request_authorization(
        db, auth_request, current_user
    )

@router.get(
    "/authorizations/{authorization_id}",
    response_model=AuthorizationResponse,
    summary="Get authorization details"
)
async def get_authorization(
    authorization_id: int,
    include_history: bool = Query(False, description="Include status history"),
    db: Session = Depends(get_db)
):
    """Get details of a specific authorization request."""
    return await InsuranceAuthorizationService.get_authorization(
        db, authorization_id, include_history
    )

@router.get(
    "/authorizations",
    response_model=List[AuthorizationResponse],
    summary="List authorization requests"
)
async def list_authorizations(
    policy_id: Optional[int] = None,
    status: Optional[str] = None,
    service_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get a list of authorization requests with optional filtering."""
    return await InsuranceAuthorizationService.get_authorizations(
        db, policy_id, status, service_type, start_date, end_date, skip, limit
    )

@router.patch(
    "/authorizations/{authorization_id}/status",
    response_model=AuthorizationResponse,
    summary="Update authorization status"
)
async def update_authorization_status(
    authorization_id: int,
    status_update: AuthorizationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Update the status of an authorization request."""
    return await InsuranceAuthorizationService.update_authorization_status(
        db, authorization_id, status_update, current_user
    )

@router.get(
    "/authorizations/check",
    response_model=Optional[AuthorizationResponse],
    summary="Check service authorization"
)
async def check_authorization(
    policy_id: int = Query(..., description="ID of the insurance policy"),
    service_type: str = Query(..., description="Type of service to check"),
    service_date: Optional[date] = Query(None, description="Date of service"),
    db: Session = Depends(get_db)
):
    """Check if a service is authorized for a given policy and date."""
    return await InsuranceAuthorizationService.check_authorization(
        db, policy_id, service_type, service_date
    )

# Verification Endpoints

@router.post(
    "/verify",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify insurance"
)
async def verify_insurance(
    verification_request: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Perform a comprehensive insurance verification."""
    return await InsuranceVerificationService.verify_insurance(
        db, verification_request, current_user
    )

@router.get(
    "/verify/history",
    response_model=List[VerificationResponse],
    summary="Get verification history"
)
async def get_verification_history(
    policy_id: int = Query(..., description="ID of the insurance policy"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get verification history for a policy."""
    return await InsuranceVerificationService.get_verification_history(
        db, policy_id, skip, limit
    )
