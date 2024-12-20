"""
Insurance Verification Service
Version: 2024-12-19_17-41

This service handles insurance verification processes including policy validation,
coverage checks, and benefit verification.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.insurance import (
    InsurancePolicy,
    InsurancePayer,
    InsuranceCoverage,
    InsuranceVerification,
    VerificationStatusHistory
)
from app.schemas.insurance import (
    VerificationRequest,
    VerificationResponse,
    BenefitVerificationResponse,
    PolicyVerificationResponse,
    VerificationStatusUpdate
)
from app.core.logging import logger

class InsuranceVerificationService:
    """Service for managing insurance verifications"""

    @staticmethod
    async def verify_insurance(
        db: Session,
        verification_request: VerificationRequest,
        current_user: str
    ) -> VerificationResponse:
        """
        Perform a comprehensive insurance verification.

        Args:
            db: Database session
            verification_request: Verification request data
            current_user: Username of the current user

        Returns:
            Verification results

        Raises:
            HTTPException: If verification fails or validation errors occur
        """
        try:
            # Get the insurance policy
            policy = db.query(InsurancePolicy).filter(
                InsurancePolicy.id == verification_request.policy_id,
                InsurancePolicy.is_active == True
            ).first()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance policy not found or inactive"
                )

            # Create verification record
            verification = InsuranceVerification(
                policy_id=policy.id,
                verification_type=verification_request.verification_type,
                service_types=verification_request.service_types,
                status="IN_PROGRESS",
                created_by=current_user,
                updated_by=current_user
            )
            db.add(verification)

            # Create initial status history
            status_history = VerificationStatusHistory(
                verification_id=verification.id,
                status="IN_PROGRESS",
                notes="Verification process initiated",
                created_by=current_user,
                updated_by=current_user
            )
            db.add(status_history)

            # Verify policy details
            policy_verification = await cls.verify_policy_details(
                db, 
                policy, 
                verification_request.reference_date or datetime.now().date()
            )

            # If policy is not active, mark verification as failed
            if not policy_verification.is_active:
                verification.status = "FAILED"
                verification.failure_reason = "Policy inactive or expired"
                status_history = VerificationStatusHistory(
                    verification_id=verification.id,
                    status="FAILED",
                    notes="Policy inactive or expired",
                    created_by=current_user,
                    updated_by=current_user
                )
                db.add(status_history)
                db.commit()
                return VerificationResponse(
                    id=verification.id,
                    status="FAILED",
                    policy_verification=policy_verification,
                    failure_reason="Policy inactive or expired"
                )

            # Verify benefits for requested service types
            benefits_verification = await cls.verify_benefits(
                db,
                policy,
                verification_request.service_types,
                verification_request.reference_date
            )

            # Update verification status
            verification.status = "COMPLETED"
            verification.results = {
                "policy_verification": policy_verification.model_dump(),
                "benefits_verification": benefits_verification.model_dump()
            }

            status_history = VerificationStatusHistory(
                verification_id=verification.id,
                status="COMPLETED",
                notes="Verification completed successfully",
                created_by=current_user,
                updated_by=current_user
            )
            db.add(status_history)

            db.commit()
            db.refresh(verification)

            return VerificationResponse(
                id=verification.id,
                status="COMPLETED",
                policy_verification=policy_verification,
                benefits_verification=benefits_verification
            )

        except HTTPException:
            if 'verification' in locals():
                verification.status = "FAILED"
                verification.failure_reason = str(e)
                db.commit()
            raise
        except Exception as e:
            logger.error(f"Error performing insurance verification: {str(e)}")
            if 'verification' in locals():
                verification.status = "FAILED"
                verification.failure_reason = str(e)
                db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error performing insurance verification"
            )

    @staticmethod
    async def verify_policy_details(
        db: Session,
        policy: InsurancePolicy,
        reference_date: date
    ) -> PolicyVerificationResponse:
        """
        Verify policy details and status.

        Args:
            db: Database session
            policy: Insurance policy to verify
            reference_date: Date for which to verify policy status

        Returns:
            Policy verification results
        """
        try:
            # Get payer details
            payer = db.query(InsurancePayer).filter(
                InsurancePayer.id == policy.payer_id
            ).first()

            # Check policy status
            is_active = (
                policy.is_active and
                policy.start_date <= reference_date <= (policy.end_date or date.max)
            )

            return PolicyVerificationResponse(
                policy_number=policy.policy_number,
                payer_id=policy.payer_id,
                payer_name=payer.name if payer else None,
                is_active=is_active,
                start_date=policy.start_date,
                end_date=policy.end_date,
                verification_date=reference_date,
                policy_type=policy.policy_type,
                group_number=policy.group_number,
                subscriber_id=policy.subscriber_id,
                subscriber_name=policy.subscriber_name
            )

        except Exception as e:
            logger.error(f"Error verifying policy details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying policy details"
            )

    @staticmethod
    async def verify_benefits(
        db: Session,
        policy: InsurancePolicy,
        service_types: List[str],
        reference_date: Optional[date] = None
    ) -> BenefitVerificationResponse:
        """
        Verify benefits for specified service types.

        Args:
            db: Database session
            policy: Insurance policy to verify
            service_types: List of service types to verify
            reference_date: Date for which to verify benefits

        Returns:
            Benefit verification results
        """
        try:
            check_date = reference_date or datetime.now().date()
            benefits_by_service = {}

            for service_type in service_types:
                coverage = db.query(InsuranceCoverage).filter(
                    InsuranceCoverage.policy_id == policy.id,
                    InsuranceCoverage.service_type == service_type,
                    InsuranceCoverage.is_active == True
                ).first()

                if coverage:
                    benefits_by_service[service_type] = {
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
                    benefits_by_service[service_type] = {
                        "is_covered": False,
                        "message": "Service type not covered under policy"
                    }

            return BenefitVerificationResponse(
                verification_date=check_date,
                benefits_by_service=benefits_by_service
            )

        except Exception as e:
            logger.error(f"Error verifying benefits: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying benefits"
            )

    @staticmethod
    async def get_verification_history(
        db: Session,
        policy_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[VerificationResponse]:
        """
        Get verification history for a policy.

        Args:
            db: Database session
            policy_id: ID of the insurance policy
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of verification records
        """
        try:
            verifications = db.query(InsuranceVerification).filter(
                InsuranceVerification.policy_id == policy_id
            ).order_by(
                InsuranceVerification.created_at.desc()
            ).offset(skip).limit(limit).all()

            return [VerificationResponse.model_validate(v) for v in verifications]

        except Exception as e:
            logger.error(f"Error retrieving verification history: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving verification history"
            )
