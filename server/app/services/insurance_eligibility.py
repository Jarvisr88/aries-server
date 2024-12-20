"""
Insurance Eligibility Service
Version: 2024-12-19_16-55

This service handles insurance eligibility checks and coverage verification.
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.insurance import (
    InsurancePolicy,
    InsuranceType,
    InsurancePayer,
    InsuranceCoverage
)
from app.schemas.insurance import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    CoverageVerificationRequest,
    CoverageVerificationResponse,
    BenefitInformation
)
from app.core.logging import logger

class InsuranceEligibilityService:
    """Service for checking insurance eligibility and coverage"""

    @staticmethod
    async def check_eligibility(
        db: Session,
        request: EligibilityCheckRequest,
        current_user: str
    ) -> EligibilityCheckResponse:
        """
        Check eligibility for a patient's insurance policy.

        Args:
            db: Database session
            request: Eligibility check request containing policy and service details
            current_user: Username of the current user

        Returns:
            EligibilityCheckResponse containing eligibility status and details

        Raises:
            HTTPException: If policy not found or eligibility check fails
        """
        try:
            # Get the insurance policy
            policy = db.query(InsurancePolicy).filter(
                InsurancePolicy.id == request.policy_id,
                InsurancePolicy.is_active == True
            ).first()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance policy not found"
                )

            # Check if policy is active for the service date
            service_date = request.service_date or datetime.now().date()
            if not (policy.start_date <= service_date <= (policy.end_date or date.max)):
                return EligibilityCheckResponse(
                    is_eligible=False,
                    status="INACTIVE",
                    message="Policy is not active for the requested service date",
                    details={
                        "policy_start": policy.start_date,
                        "policy_end": policy.end_date,
                        "service_date": service_date
                    }
                )

            # Get coverage information
            coverage = db.query(InsuranceCoverage).filter(
                InsuranceCoverage.policy_id == policy.id,
                InsuranceCoverage.service_type == request.service_type,
                InsuranceCoverage.is_active == True
            ).first()

            if not coverage:
                return EligibilityCheckResponse(
                    is_eligible=False,
                    status="NO_COVERAGE",
                    message=f"No coverage found for service type: {request.service_type}",
                    details={"service_type": request.service_type}
                )

            # Build benefit information
            benefits = BenefitInformation(
                deductible=coverage.deductible,
                deductible_met=coverage.deductible_met,
                out_of_pocket_max=coverage.out_of_pocket_max,
                out_of_pocket_met=coverage.out_of_pocket_met,
                copay=coverage.copay,
                coinsurance=coverage.coinsurance
            )

            # Return eligibility response
            return EligibilityCheckResponse(
                is_eligible=True,
                status="ACTIVE",
                message="Coverage verified",
                details={
                    "policy_number": policy.policy_number,
                    "payer_id": policy.payer_id,
                    "service_type": request.service_type,
                    "service_date": service_date,
                    "benefits": benefits.model_dump()
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking eligibility: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error checking eligibility"
            )

    @staticmethod
    async def verify_coverage(
        db: Session,
        request: CoverageVerificationRequest,
        current_user: str
    ) -> CoverageVerificationResponse:
        """
        Verify coverage details for specific services.

        Args:
            db: Database session
            request: Coverage verification request containing policy and service details
            current_user: Username of the current user

        Returns:
            CoverageVerificationResponse containing coverage details

        Raises:
            HTTPException: If policy not found or verification fails
        """
        try:
            # Get the insurance policy
            policy = db.query(InsurancePolicy).filter(
                InsurancePolicy.id == request.policy_id,
                InsurancePolicy.is_active == True
            ).first()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance policy not found"
                )

            # Check if policy is active
            service_date = request.service_date or datetime.now().date()
            if not (policy.start_date <= service_date <= (policy.end_date or date.max)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Policy is not active for the requested service date"
                )

            # Get coverage information for each service type
            coverage_details = {}
            for service_type in request.service_types:
                coverage = db.query(InsuranceCoverage).filter(
                    InsuranceCoverage.policy_id == policy.id,
                    InsuranceCoverage.service_type == service_type,
                    InsuranceCoverage.is_active == True
                ).first()

                if coverage:
                    coverage_details[service_type] = {
                        "is_covered": True,
                        "requires_authorization": coverage.requires_authorization,
                        "network_restrictions": coverage.network_restrictions,
                        "benefit_details": {
                            "deductible": coverage.deductible,
                            "deductible_met": coverage.deductible_met,
                            "out_of_pocket_max": coverage.out_of_pocket_max,
                            "out_of_pocket_met": coverage.out_of_pocket_met,
                            "copay": coverage.copay,
                            "coinsurance": coverage.coinsurance,
                            "limitations": coverage.limitations
                        }
                    }
                else:
                    coverage_details[service_type] = {
                        "is_covered": False,
                        "message": "Service type not covered under policy"
                    }

            return CoverageVerificationResponse(
                policy_number=policy.policy_number,
                payer_id=policy.payer_id,
                verification_date=service_date,
                coverage_details=coverage_details
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying coverage: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying coverage"
            )
