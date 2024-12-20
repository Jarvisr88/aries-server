"""
Insurance Authorization Service
Version: 2024-12-19_17-25

This service handles prior authorizations and approval workflows for insurance services.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.insurance import (
    InsuranceAuthorization,
    InsurancePolicy,
    AuthorizationStatusHistory,
    InsuranceCoverage
)
from app.schemas.insurance import (
    AuthorizationRequest,
    AuthorizationResponse,
    AuthorizationStatusUpdate,
    AuthorizationDocumentCreate
)
from app.core.logging import logger

class InsuranceAuthorizationService:
    """Service for managing insurance authorizations"""

    @staticmethod
    async def request_authorization(
        db: Session,
        auth_request: AuthorizationRequest,
        current_user: str
    ) -> AuthorizationResponse:
        """
        Submit a new authorization request.

        Args:
            db: Database session
            auth_request: Authorization request data
            current_user: Username of the current user

        Returns:
            Created authorization request

        Raises:
            HTTPException: If request submission fails or validation errors occur
        """
        try:
            # Verify policy exists and is active
            policy = db.query(InsurancePolicy).filter(
                InsurancePolicy.id == auth_request.policy_id,
                InsurancePolicy.is_active == True
            ).first()
            
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance policy not found or inactive"
                )

            # Verify service requires authorization
            coverage = db.query(InsuranceCoverage).filter(
                InsuranceCoverage.policy_id == policy.id,
                InsuranceCoverage.service_type == auth_request.service_type,
                InsuranceCoverage.is_active == True
            ).first()

            if not coverage:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No coverage found for service type: {auth_request.service_type}"
                )

            if not coverage.requires_authorization:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service type {auth_request.service_type} does not require authorization"
                )

            # Create authorization request
            authorization = InsuranceAuthorization(
                **auth_request.model_dump(exclude={'documents'}),
                status="PENDING",
                created_by=current_user,
                updated_by=current_user
            )
            db.add(authorization)

            # Create initial status history entry
            status_history = AuthorizationStatusHistory(
                authorization_id=authorization.id,
                status="PENDING",
                notes="Authorization request submitted",
                created_by=current_user,
                updated_by=current_user
            )
            db.add(status_history)

            # Add any submitted documents
            if auth_request.documents:
                for doc in auth_request.documents:
                    auth_document = AuthorizationDocument(
                        authorization_id=authorization.id,
                        **doc.model_dump(),
                        created_by=current_user,
                        updated_by=current_user
                    )
                    db.add(auth_document)

            db.commit()
            db.refresh(authorization)

            return AuthorizationResponse.model_validate(authorization)

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error submitting authorization request: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error submitting authorization request"
            )

    @staticmethod
    async def update_authorization_status(
        db: Session,
        authorization_id: int,
        status_update: AuthorizationStatusUpdate,
        current_user: str
    ) -> AuthorizationResponse:
        """
        Update the status of an authorization request.

        Args:
            db: Database session
            authorization_id: ID of the authorization to update
            status_update: New status and notes
            current_user: Username of the current user

        Returns:
            Updated authorization request

        Raises:
            HTTPException: If authorization not found or status update fails
        """
        try:
            # Get the authorization
            authorization = db.query(InsuranceAuthorization).filter(
                InsuranceAuthorization.id == authorization_id
            ).first()
            
            if not authorization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Authorization not found"
                )

            # Update authorization status
            authorization.status = status_update.status
            if status_update.approved_units:
                authorization.approved_units = status_update.approved_units
            if status_update.expiration_date:
                authorization.expiration_date = status_update.expiration_date
            authorization.updated_by = current_user
            authorization.updated_at = datetime.utcnow()

            # Add status history entry
            status_history = AuthorizationStatusHistory(
                authorization_id=authorization_id,
                status=status_update.status,
                notes=status_update.notes,
                created_by=current_user,
                updated_by=current_user
            )
            db.add(status_history)

            db.commit()
            db.refresh(authorization)

            return AuthorizationResponse.model_validate(authorization)

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating authorization status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating authorization status"
            )

    @staticmethod
    async def get_authorization(
        db: Session,
        authorization_id: int,
        include_history: bool = False
    ) -> AuthorizationResponse:
        """
        Get an authorization request by ID.

        Args:
            db: Database session
            authorization_id: ID of the authorization to retrieve
            include_history: Whether to include status history

        Returns:
            Authorization request details

        Raises:
            HTTPException: If authorization not found
        """
        try:
            query = db.query(InsuranceAuthorization)
            if include_history:
                query = query.options(joinedload(InsuranceAuthorization.status_history))
            
            authorization = query.filter(InsuranceAuthorization.id == authorization_id).first()
            
            if not authorization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Authorization not found"
                )

            return AuthorizationResponse.model_validate(authorization)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving authorization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving authorization"
            )

    @staticmethod
    async def get_authorizations(
        db: Session,
        policy_id: Optional[int] = None,
        status: Optional[str] = None,
        service_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuthorizationResponse]:
        """
        Get a list of authorization requests with optional filtering.

        Args:
            db: Database session
            policy_id: Filter by policy ID
            status: Filter by authorization status
            service_type: Filter by service type
            start_date: Filter by start date range
            end_date: Filter by end date range
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of authorization requests
        """
        try:
            query = db.query(InsuranceAuthorization)

            if policy_id:
                query = query.filter(InsuranceAuthorization.policy_id == policy_id)
            if status:
                query = query.filter(InsuranceAuthorization.status == status)
            if service_type:
                query = query.filter(InsuranceAuthorization.service_type == service_type)
            if start_date:
                query = query.filter(InsuranceAuthorization.start_date >= start_date)
            if end_date:
                query = query.filter(InsuranceAuthorization.end_date <= end_date)

            authorizations = query.offset(skip).limit(limit).all()
            return [AuthorizationResponse.model_validate(auth) for auth in authorizations]

        except Exception as e:
            logger.error(f"Error retrieving authorizations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving authorizations"
            )

    @staticmethod
    async def check_authorization(
        db: Session,
        policy_id: int,
        service_type: str,
        service_date: Optional[date] = None
    ) -> Optional[AuthorizationResponse]:
        """
        Check if a service is authorized for a given policy and date.

        Args:
            db: Database session
            policy_id: ID of the insurance policy
            service_type: Type of service to check
            service_date: Date of service (defaults to current date)

        Returns:
            Active authorization if found, None otherwise
        """
        try:
            check_date = service_date or datetime.now().date()
            
            authorization = db.query(InsuranceAuthorization).filter(
                InsuranceAuthorization.policy_id == policy_id,
                InsuranceAuthorization.service_type == service_type,
                InsuranceAuthorization.status == "APPROVED",
                InsuranceAuthorization.start_date <= check_date,
                InsuranceAuthorization.end_date >= check_date
            ).first()

            return AuthorizationResponse.model_validate(authorization) if authorization else None

        except Exception as e:
            logger.error(f"Error checking authorization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error checking authorization"
            )
