"""
Authorization API endpoints
Version: 2024-12-20_00-24
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import logger
from app.schemas.authorization import (
    AuthorizationRequest,
    AuthorizationResponse,
    AuthorizationStatusUpdate,
    BatchAuthorizationRequest,
    BatchAuthorizationResponse,
    AuthorizationHistoryResponse
)
from app.services.authorization.service import InsuranceAuthorizationService
from app.services.authorization.base import (
    InvalidStatusTransitionError,
    BatchSizeExceededError
)

router = APIRouter(prefix="/v1/authorizations", tags=["authorizations"])
auth_service = InsuranceAuthorizationService()

@router.post("", response_model=AuthorizationResponse)
async def create_authorization(
    request: AuthorizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
) -> AuthorizationResponse:
    """
    Create a new authorization request.
    
    Args:
        request: Authorization request data
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current user
        
    Returns:
        Created authorization
    """
    try:
        return await auth_service.request_authorization(db, request, current_user)
    except Exception as e:
        logger.error(f"Error creating authorization: {str(e)}")
        raise

@router.post("/batch", response_model=BatchAuthorizationResponse)
async def create_authorizations_batch(
    request: BatchAuthorizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
) -> BatchAuthorizationResponse:
    """
    Submit multiple authorization requests as a batch.
    
    Args:
        request: Batch request data
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current user
        
    Returns:
        Batch operation response
    """
    try:
        # Start batch processing in background
        background_tasks.add_task(
            auth_service.request_authorizations_batch,
            db,
            request,
            current_user
        )
        
        # Return initial response
        return BatchAuthorizationResponse(
            batch_id=request.batch_id,
            total=len(request.requests),
            completed=0,
            failed=0,
            status="PROCESSING"
        )
    except BatchSizeExceededError as e:
        logger.error(f"Batch size exceeded: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error processing batch request: {str(e)}")
        raise

@router.get("/batch/{batch_id}", response_model=BatchAuthorizationResponse)
async def get_batch_status(
    batch_id: str = Path(..., description="Batch operation ID"),
    db: Session = Depends(get_db)
) -> BatchAuthorizationResponse:
    """
    Get status of a batch operation.
    
    Args:
        batch_id: Batch operation ID
        db: Database session
        
    Returns:
        Batch operation status
    """
    try:
        status = await auth_service.batch_cache.get_batch_status(batch_id)
        if not status:
            raise ValueError(f"Batch operation {batch_id} not found")
        return BatchAuthorizationResponse(**status)
    except Exception as e:
        logger.error(f"Error retrieving batch status: {str(e)}")
        raise

@router.put("/{authorization_id}/status", response_model=AuthorizationResponse)
async def update_authorization_status(
    status_update: AuthorizationStatusUpdate,
    authorization_id: int = Path(..., description="Authorization ID"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
) -> AuthorizationResponse:
    """
    Update authorization status.
    
    Args:
        status_update: Status update data
        authorization_id: Authorization ID
        db: Database session
        current_user: Current user
        
    Returns:
        Updated authorization
    """
    try:
        return await auth_service.update_authorization_status(
            db,
            authorization_id,
            status_update,
            current_user
        )
    except InvalidStatusTransitionError as e:
        logger.error(f"Invalid status transition: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating authorization status: {str(e)}")
        raise

@router.get("/{authorization_id}", response_model=AuthorizationResponse)
async def get_authorization(
    authorization_id: int = Path(..., description="Authorization ID"),
    include_history: bool = Query(False, description="Include status history"),
    db: Session = Depends(get_db)
) -> AuthorizationResponse:
    """
    Get authorization by ID.
    
    Args:
        authorization_id: Authorization ID
        include_history: Whether to include status history
        db: Database session
        
    Returns:
        Authorization details
    """
    try:
        return await auth_service.get_authorization(
            db,
            authorization_id,
            include_history
        )
    except Exception as e:
        logger.error(f"Error retrieving authorization: {str(e)}")
        raise

@router.get("/{authorization_id}/history", response_model=List[AuthorizationHistoryResponse])
async def get_authorization_history(
    authorization_id: int = Path(..., description="Authorization ID"),
    db: Session = Depends(get_db)
) -> List[AuthorizationHistoryResponse]:
    """
    Get authorization status history.
    
    Args:
        authorization_id: Authorization ID
        db: Database session
        
    Returns:
        Status history
    """
    try:
        auth = await auth_service.get_authorization(
            db,
            authorization_id,
            include_history=True
        )
        return auth.status_history or []
    except Exception as e:
        logger.error(f"Error retrieving authorization history: {str(e)}")
        raise

@router.get("", response_model=List[AuthorizationResponse])
async def get_authorizations(
    policy_id: Optional[int] = Query(None, description="Filter by policy ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
) -> List[AuthorizationResponse]:
    """
    Get authorizations with filtering.
    
    Args:
        policy_id: Filter by policy ID
        status: Filter by status
        service_type: Filter by service type
        start_date: Filter by start date
        end_date: Filter by end date
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of authorizations
    """
    try:
        return await auth_service.get_authorizations(
            db,
            policy_id=policy_id,
            status=status,
            service_type=service_type,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error retrieving authorizations: {str(e)}")
        raise

@router.get("/check", response_model=Optional[AuthorizationResponse])
async def check_authorization(
    policy_id: int = Query(..., description="Insurance policy ID"),
    service_type: str = Query(..., description="Type of service"),
    service_date: Optional[date] = Query(None, description="Date of service"),
    db: Session = Depends(get_db)
) -> Optional[AuthorizationResponse]:
    """
    Check if service is authorized.
    
    Args:
        policy_id: Insurance policy ID
        service_type: Type of service
        service_date: Date of service
        db: Database session
        
    Returns:
        Active authorization if found
    """
    try:
        return await auth_service.check_authorization(
            db,
            policy_id,
            service_type,
            service_date
        )
    except Exception as e:
        logger.error(f"Error checking authorization: {str(e)}")
        raise
