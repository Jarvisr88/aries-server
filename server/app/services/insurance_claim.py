"""
Insurance Claim Service
Version: 2024-12-19_19-54

This service handles insurance claim submission, tracking, and processing workflows.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from functools import wraps
import asyncio
import json

from app.models.insurance import (
    InsuranceClaim,
    InsurancePolicy,
    ClaimStatusHistory,
    InsuranceCoverage,
    ClaimDocument
)
from app.schemas.insurance import (
    InsuranceClaimCreate,
    InsuranceClaimUpdate,
    InsuranceClaimResponse,
    ClaimStatusUpdate,
    ClaimDocumentCreate,
    BatchClaimSubmission,
    BatchClaimResponse
)
from app.core.logging import logger
from app.core.cache import cache
from app.core.config import settings
from app.utils.retry import retry_with_backoff

class InsuranceClaimService:
    """Service for managing insurance claims"""

    CACHE_TTL = 3600  # 1 hour cache TTL
    MAX_BATCH_SIZE = 100
    ALLOWED_STATUS_TRANSITIONS = {
        "DRAFT": ["SUBMITTED"],
        "SUBMITTED": ["IN_PROCESS", "REJECTED"],
        "IN_PROCESS": ["ADJUDICATED", "REJECTED", "PENDING_INFO"],
        "PENDING_INFO": ["IN_PROCESS", "REJECTED"],
        "ADJUDICATED": ["FINALIZED", "REJECTED"],
        "FINALIZED": [],
        "REJECTED": []
    }

    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> bool:
        """Validate if the status transition is allowed."""
        allowed_transitions = InsuranceClaimService.ALLOWED_STATUS_TRANSITIONS.get(current_status, [])
        return new_status in allowed_transitions

    @staticmethod
    def cache_key(claim_id: int) -> str:
        """Generate cache key for a claim."""
        return f"claim:{claim_id}"

    @staticmethod
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    async def submit_claim(
        db: Session,
        claim_data: InsuranceClaimCreate,
        current_user: str
    ) -> InsuranceClaimResponse:
        """
        Submit a new insurance claim.

        Args:
            db: Database session
            claim_data: Insurance claim data
            current_user: Username of the current user

        Returns:
            Created insurance claim

        Raises:
            HTTPException: If claim submission fails or validation errors occur
        """
        try:
            # Verify policy exists and is active
            policy = db.query(InsurancePolicy).filter(
                InsurancePolicy.id == claim_data.policy_id,
                InsurancePolicy.is_active == True
            ).first()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance policy not found or inactive"
                )

            # Verify service date falls within policy period
            if not (policy.start_date <= claim_data.service_date <= (policy.end_date or datetime.max.date())):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Service date is outside policy coverage period"
                )

            # Create new claim
            claim = InsuranceClaim(
                **claim_data.model_dump(exclude={'documents'}),
                status="SUBMITTED",
                created_by=current_user,
                updated_by=current_user
            )
            db.add(claim)

            # Create initial status history entry
            status_history = ClaimStatusHistory(
                claim_id=claim.id,
                status="SUBMITTED",
                notes="Claim initially submitted",
                created_by=current_user,
                updated_by=current_user
            )
            db.add(status_history)

            # Add any submitted documents
            if claim_data.documents:
                for doc in claim_data.documents:
                    claim_document = ClaimDocument(
                        claim_id=claim.id,
                        **doc.model_dump(),
                        created_by=current_user,
                        updated_by=current_user
                    )
                    db.add(claim_document)

            db.commit()
            db.refresh(claim)

            # Cache the claim
            await cache.set(
                InsuranceClaimService.cache_key(claim.id),
                json.dumps(InsuranceClaimResponse.model_validate(claim).model_dump()),
                expire=InsuranceClaimService.CACHE_TTL
            )

            return InsuranceClaimResponse.model_validate(claim)

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error submitting claim: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error submitting claim"
            )

    @staticmethod
    async def submit_claims_batch(
        db: Session,
        claims_data: BatchClaimSubmission,
        current_user: str
    ) -> BatchClaimResponse:
        """
        Submit multiple claims in a batch.

        Args:
            db: Database session
            claims_data: Batch of claims to submit
            current_user: Username of the current user

        Returns:
            Batch submission results

        Raises:
            HTTPException: If batch size exceeds limit
        """
        if len(claims_data.claims) > InsuranceClaimService.MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size exceeds maximum limit of {InsuranceClaimService.MAX_BATCH_SIZE}"
            )

        results = []
        errors = []

        for claim_data in claims_data.claims:
            try:
                claim = await InsuranceClaimService.submit_claim(db, claim_data, current_user)
                results.append(claim)
            except Exception as e:
                errors.append({
                    "claim_data": claim_data.model_dump(),
                    "error": str(e)
                })

        return BatchClaimResponse(
            successful_claims=results,
            failed_claims=errors,
            total_submitted=len(claims_data.claims),
            total_successful=len(results),
            total_failed=len(errors)
        )

    @staticmethod
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    async def update_claim_status(
        db: Session,
        claim_id: int,
        status_update: ClaimStatusUpdate,
        current_user: str
    ) -> InsuranceClaimResponse:
        """
        Update the status of an insurance claim.

        Args:
            db: Database session
            claim_id: ID of the claim to update
            status_update: New status and notes
            current_user: Username of the current user

        Returns:
            Updated insurance claim

        Raises:
            HTTPException: If claim not found or status update fails
        """
        try:
            # Get the claim
            claim = db.query(InsuranceClaim).filter(
                InsuranceClaim.id == claim_id
            ).first()
            
            if not claim:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Claim not found"
                )

            # Validate status transition
            if not InsuranceClaimService.validate_status_transition(claim.status, status_update.status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status transition from {claim.status} to {status_update.status}"
                )

            # Update claim status
            claim.status = status_update.status
            claim.updated_by = current_user
            claim.updated_at = datetime.utcnow()

            # Add status history entry
            status_history = ClaimStatusHistory(
                claim_id=claim_id,
                status=status_update.status,
                notes=status_update.notes,
                created_by=current_user,
                updated_by=current_user
            )
            db.add(status_history)

            db.commit()
            db.refresh(claim)

            # Update cache
            await cache.set(
                InsuranceClaimService.cache_key(claim.id),
                json.dumps(InsuranceClaimResponse.model_validate(claim).model_dump()),
                expire=InsuranceClaimService.CACHE_TTL
            )

            return InsuranceClaimResponse.model_validate(claim)

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating claim status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating claim status"
            )

    @staticmethod
    async def get_claim(
        db: Session,
        claim_id: int,
        include_history: bool = False
    ) -> InsuranceClaimResponse:
        """
        Get an insurance claim by ID.

        Args:
            db: Database session
            claim_id: ID of the claim to retrieve
            include_history: Whether to include status history

        Returns:
            Insurance claim details

        Raises:
            HTTPException: If claim not found
        """
        try:
            # Try to get from cache first
            cached_claim = await cache.get(InsuranceClaimService.cache_key(claim_id))
            if cached_claim and not include_history:
                return InsuranceClaimResponse.model_validate(json.loads(cached_claim))

            query = db.query(InsuranceClaim)
            if include_history:
                query = query.options(joinedload(InsuranceClaim.status_history))
            
            claim = query.filter(InsuranceClaim.id == claim_id).first()
            
            if not claim:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Claim not found"
                )

            response = InsuranceClaimResponse.model_validate(claim)
            
            # Cache the response if not including history
            if not include_history:
                await cache.set(
                    InsuranceClaimService.cache_key(claim_id),
                    json.dumps(response.model_dump()),
                    expire=InsuranceClaimService.CACHE_TTL
                )

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving claim: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving claim"
            )

    @staticmethod
    async def get_claims(
        db: Session,
        policy_id: Optional[int] = None,
        status: Optional[str] = None,
        service_date_from: Optional[datetime] = None,
        service_date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InsuranceClaimResponse]:
        """
        Get a list of insurance claims with optional filtering.

        Args:
            db: Database session
            policy_id: Filter by policy ID
            status: Filter by claim status
            service_date_from: Filter by service date range start
            service_date_to: Filter by service date range end
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of insurance claims
        """
        try:
            query = db.query(InsuranceClaim)

            if policy_id:
                query = query.filter(InsuranceClaim.policy_id == policy_id)
            if status:
                query = query.filter(InsuranceClaim.status == status)
            if service_date_from:
                query = query.filter(InsuranceClaim.service_date >= service_date_from)
            if service_date_to:
                query = query.filter(InsuranceClaim.service_date <= service_date_to)

            # Add index hints for performance
            if policy_id:
                query = query.with_hint(InsuranceClaim, 'USE INDEX (ix_insurance_claims_policy_id)')
            elif status:
                query = query.with_hint(InsuranceClaim, 'USE INDEX (ix_insurance_claims_status)')
            elif service_date_from or service_date_to:
                query = query.with_hint(InsuranceClaim, 'USE INDEX (ix_insurance_claims_dates)')

            claims = query.offset(skip).limit(limit).all()
            return [InsuranceClaimResponse.model_validate(claim) for claim in claims]

        except Exception as e:
            logger.error(f"Error retrieving claims: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving claims"
            )

    @staticmethod
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    async def add_claim_document(
        db: Session,
        claim_id: int,
        document: ClaimDocumentCreate,
        current_user: str
    ) -> InsuranceClaimResponse:
        """
        Add a document to an existing claim.

        Args:
            db: Database session
            claim_id: ID of the claim
            document: Document to add
            current_user: Username of the current user

        Returns:
            Updated insurance claim

        Raises:
            HTTPException: If claim not found or document addition fails
        """
        try:
            # Verify claim exists
            claim = db.query(InsuranceClaim).filter(
                InsuranceClaim.id == claim_id
            ).first()
            
            if not claim:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Claim not found"
                )

            # Add document
            claim_document = ClaimDocument(
                claim_id=claim_id,
                **document.model_dump(),
                created_by=current_user,
                updated_by=current_user
            )
            db.add(claim_document)

            # Update claim
            claim.updated_by = current_user
            claim.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(claim)

            # Update cache
            await cache.set(
                InsuranceClaimService.cache_key(claim.id),
                json.dumps(InsuranceClaimResponse.model_validate(claim).model_dump()),
                expire=InsuranceClaimService.CACHE_TTL
            )

            return InsuranceClaimResponse.model_validate(claim)

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding claim document: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error adding claim document"
            )
