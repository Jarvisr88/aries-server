"""
Enhanced authorization service implementation
Version: 2024-12-20_00-03
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import asyncio
import uuid
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.insurance import (
    InsuranceAuthorization,
    InsurancePolicy,
    AuthorizationStatusHistory,
    InsuranceCoverage,
    AuthorizationDocument
)
from app.schemas.authorization import (
    AuthorizationRequest,
    AuthorizationResponse,
    AuthorizationStatusUpdate,
    BatchAuthorizationRequest,
    BatchAuthorizationResponse
)
from app.core.logging import logger
from .base import (
    BaseAuthorizationService,
    AuthorizationStatus,
    InvalidStatusTransitionError,
    BatchSizeExceededError,
    RetryableAuthorizationError,
    NonRetryableAuthorizationError
)
from .cache import AuthorizationCache, BatchOperationCache
from .retry import retry_with_backoff, RetryContext

class InsuranceAuthorizationService(BaseAuthorizationService):
    """Enhanced service for managing insurance authorizations"""

    def __init__(self):
        """Initialize service dependencies"""
        self.auth_cache = AuthorizationCache[AuthorizationResponse](AuthorizationResponse)
        self.batch_cache = BatchOperationCache()

    @retry_with_backoff()
    async def request_authorization(
        self,
        db: Session,
        auth_request: AuthorizationRequest,
        current_user: str
    ) -> AuthorizationResponse:
        """
        Submit a new authorization request with retry capability.
        
        Args:
            db: Database session
            auth_request: Authorization request data
            current_user: Username of the current user
            
        Returns:
            Created authorization request
            
        Raises:
            HTTPException: If request submission fails
        """
        try:
            # Verify policy exists and is active
            policy = await self._verify_policy(db, auth_request.policy_id)
            
            # Verify service requires authorization
            coverage = await self._verify_coverage(
                db,
                policy.id,
                auth_request.service_type
            )

            # Create authorization request
            authorization = InsuranceAuthorization(
                **auth_request.model_dump(exclude={'documents'}),
                status=AuthorizationStatus.DRAFT,
                created_by=current_user,
                updated_by=current_user
            )
            db.add(authorization)

            # Create initial status history
            await self._add_status_history(
                db,
                authorization.id,
                AuthorizationStatus.DRAFT,
                "Authorization request created",
                current_user
            )

            # Add documents if any
            if auth_request.documents:
                await self._add_documents(
                    db,
                    authorization.id,
                    auth_request.documents,
                    current_user
                )

            await db.commit()
            await db.refresh(authorization)

            # Cache the new authorization
            response = AuthorizationResponse.model_validate(authorization)
            await self.auth_cache.set(
                self.cache_key(authorization.id),
                response
            )

            return response

        except HTTPException as e:
            await db.rollback()
            raise NonRetryableAuthorizationError(str(e))
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Database integrity error: {str(e)}")
            raise RetryableAuthorizationError("Database constraint violation")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating authorization: {str(e)}")
            raise RetryableAuthorizationError(str(e))

    async def request_authorizations_batch(
        self,
        db: Session,
        batch_request: BatchAuthorizationRequest,
        current_user: str
    ) -> BatchAuthorizationResponse:
        """
        Submit multiple authorization requests as a batch.
        
        Args:
            db: Database session
            batch_request: Batch request data
            current_user: Username of the current user
            
        Returns:
            Batch operation response
        """
        if len(batch_request.requests) > self.MAX_BATCH_SIZE:
            raise BatchSizeExceededError(
                len(batch_request.requests),
                self.MAX_BATCH_SIZE
            )

        # Initialize batch status
        batch_response = BatchAuthorizationResponse(
            batch_id=batch_request.batch_id,
            total=len(batch_request.requests),
            completed=0,
            failed=0,
            status="IN_PROGRESS"
        )
        await self.batch_cache.set_batch_status(
            batch_response.batch_id,
            batch_response.total
        )

        # Process requests in parallel with limited concurrency
        semaphore = asyncio.Semaphore(self.PARALLEL_WORKERS)
        tasks = []

        async def process_request(request: AuthorizationRequest, index: int):
            async with semaphore:
                try:
                    result = await self.request_authorization(
                        db,
                        request,
                        current_user
                    )
                    batch_response.results[str(index)] = result
                    batch_response.completed += 1
                except Exception as e:
                    batch_response.errors[str(index)] = str(e)
                    batch_response.failed += 1
                finally:
                    await self.batch_cache.update_batch_progress(
                        batch_response.batch_id,
                        completed=batch_response.completed,
                        failed=batch_response.failed,
                        errors=batch_response.errors
                    )

        for i, request in enumerate(batch_request.requests):
            task = asyncio.create_task(process_request(request, i))
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Update final status
        batch_response.status = "COMPLETED"
        batch_response.updated_at = datetime.utcnow()
        await self.batch_cache.set_batch_status(
            batch_response.batch_id,
            batch_response.total,
            batch_response.completed,
            batch_response.failed,
            batch_response.errors
        )

        return batch_response

    @retry_with_backoff()
    async def update_authorization_status(
        self,
        db: Session,
        authorization_id: int,
        status_update: AuthorizationStatusUpdate,
        current_user: str
    ) -> AuthorizationResponse:
        """
        Update authorization status with validation and retry capability.
        
        Args:
            db: Database session
            authorization_id: Authorization ID
            status_update: Status update data
            current_user: Username of the current user
            
        Returns:
            Updated authorization
            
        Raises:
            HTTPException: If update fails
        """
        try:
            # Get current authorization
            authorization = await self._get_authorization(db, authorization_id)
            
            # Validate status transition
            if not self.validate_status_transition(
                authorization.status,
                status_update.status
            ):
                raise InvalidStatusTransitionError(
                    authorization.status,
                    status_update.status
                )

            # Update authorization
            authorization.status = status_update.status
            if status_update.approved_units is not None:
                authorization.approved_units = status_update.approved_units
            if status_update.expiration_date is not None:
                authorization.expiration_date = status_update.expiration_date
            authorization.updated_by = current_user
            authorization.updated_at = datetime.utcnow()

            # Add status history
            await self._add_status_history(
                db,
                authorization_id,
                status_update.status,
                status_update.notes,
                current_user
            )

            await db.commit()
            await db.refresh(authorization)

            # Update cache
            response = AuthorizationResponse.model_validate(authorization)
            await self.auth_cache.set(
                self.cache_key(authorization_id),
                response
            )

            return response

        except InvalidStatusTransitionError as e:
            await db.rollback()
            raise NonRetryableAuthorizationError(str(e))
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Database integrity error: {str(e)}")
            raise RetryableAuthorizationError("Database constraint violation")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating authorization: {str(e)}")
            raise RetryableAuthorizationError(str(e))

    async def get_authorization(
        self,
        db: Session,
        authorization_id: int,
        include_history: bool = False
    ) -> AuthorizationResponse:
        """
        Get authorization with caching.
        
        Args:
            db: Database session
            authorization_id: Authorization ID
            include_history: Whether to include status history
            
        Returns:
            Authorization details
        """
        # Try cache first
        cache_key = self.cache_key(authorization_id)
        cached = await self.auth_cache.get(cache_key)
        
        if cached and not include_history:
            return cached

        try:
            # Get from database
            query = db.query(InsuranceAuthorization)
            if include_history:
                query = query.options(
                    joinedload(InsuranceAuthorization.status_history)
                )
            
            authorization = query.filter(
                InsuranceAuthorization.id == authorization_id
            ).first()
            
            if not authorization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Authorization not found"
                )

            response = AuthorizationResponse.model_validate(authorization)
            
            # Cache the response
            if not include_history:
                await self.auth_cache.set(cache_key, response)

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving authorization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving authorization"
            )

    async def get_authorizations(
        self,
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
        Get authorizations with filtering and pagination.
        
        Args:
            db: Database session
            policy_id: Filter by policy ID
            status: Filter by status
            service_type: Filter by service type
            start_date: Filter by start date
            end_date: Filter by end date
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of authorizations
        """
        try:
            query = db.query(InsuranceAuthorization)

            # Apply filters
            if policy_id:
                query = query.filter(
                    InsuranceAuthorization.policy_id == policy_id
                )
            if status:
                query = query.filter(InsuranceAuthorization.status == status)
            if service_type:
                query = query.filter(
                    InsuranceAuthorization.service_type == service_type
                )
            if start_date:
                query = query.filter(
                    InsuranceAuthorization.start_date >= start_date
                )
            if end_date:
                query = query.filter(
                    InsuranceAuthorization.end_date <= end_date
                )

            # Add pagination
            authorizations = query.offset(skip).limit(limit).all()
            
            return [
                AuthorizationResponse.model_validate(auth)
                for auth in authorizations
            ]

        except Exception as e:
            logger.error(f"Error retrieving authorizations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving authorizations"
            )

    @retry_with_backoff()
    async def check_authorization(
        self,
        db: Session,
        policy_id: int,
        service_type: str,
        service_date: Optional[date] = None
    ) -> Optional[AuthorizationResponse]:
        """
        Check if service is authorized with caching and retry capability.
        
        Args:
            db: Database session
            policy_id: Insurance policy ID
            service_type: Type of service
            service_date: Date of service
            
        Returns:
            Active authorization if found
        """
        try:
            check_date = service_date or datetime.now().date()
            
            # Generate cache key for this check
            cache_key = f"{self.CACHE_PREFIX}check:{policy_id}:{service_type}:{check_date}"
            cached = await self.auth_cache.get(cache_key)
            
            if cached:
                return cached

            # Query database
            authorization = db.query(InsuranceAuthorization).filter(
                InsuranceAuthorization.policy_id == policy_id,
                InsuranceAuthorization.service_type == service_type,
                InsuranceAuthorization.status == AuthorizationStatus.APPROVED,
                InsuranceAuthorization.start_date <= check_date,
                InsuranceAuthorization.end_date >= check_date
            ).first()

            if authorization:
                response = AuthorizationResponse.model_validate(authorization)
                await self.auth_cache.set(cache_key, response)
                return response

            return None

        except Exception as e:
            logger.error(f"Error checking authorization: {str(e)}")
            raise RetryableAuthorizationError(str(e))

    # Private helper methods
    async def _verify_policy(
        self,
        db: Session,
        policy_id: int
    ) -> InsurancePolicy:
        """Verify policy exists and is active"""
        policy = db.query(InsurancePolicy).filter(
            InsurancePolicy.id == policy_id,
            InsurancePolicy.is_active == True
        ).first()
        
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Insurance policy not found or inactive"
            )
        
        return policy

    async def _verify_coverage(
        self,
        db: Session,
        policy_id: int,
        service_type: str
    ) -> InsuranceCoverage:
        """Verify service requires authorization"""
        coverage = db.query(InsuranceCoverage).filter(
            InsuranceCoverage.policy_id == policy_id,
            InsuranceCoverage.service_type == service_type,
            InsuranceCoverage.is_active == True
        ).first()

        if not coverage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No coverage found for service type: {service_type}"
            )

        if not coverage.requires_authorization:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service type {service_type} does not require authorization"
            )

        return coverage

    async def _get_authorization(
        self,
        db: Session,
        authorization_id: int
    ) -> InsuranceAuthorization:
        """Get authorization by ID"""
        authorization = db.query(InsuranceAuthorization).filter(
            InsuranceAuthorization.id == authorization_id
        ).first()
        
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authorization not found"
            )
            
        return authorization

    async def _add_status_history(
        self,
        db: Session,
        authorization_id: int,
        status: str,
        notes: Optional[str],
        current_user: str
    ):
        """Add status history entry"""
        history = AuthorizationStatusHistory(
            authorization_id=authorization_id,
            status=status,
            notes=notes,
            created_by=current_user,
            updated_by=current_user
        )
        db.add(history)

    async def _add_documents(
        self,
        db: Session,
        authorization_id: int,
        documents: List[Any],
        current_user: str
    ):
        """Add authorization documents"""
        for doc in documents:
            auth_document = AuthorizationDocument(
                authorization_id=authorization_id,
                **doc.model_dump(),
                created_by=current_user,
                updated_by=current_user
            )
            db.add(auth_document)
