"""
Insurance API Endpoints
Version: 2024-12-19_13-31
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.insurance import (
    InsuranceCompanyService, 
    InsuranceCompanyGroupService, 
    InsurancePayerService,
    InsuranceTypeService,
    InsurancePolicyService
)
from app.schemas.insurance import (
    InsuranceCompanyCreate,
    InsuranceCompanyUpdate,
    InsuranceCompanyInDB,
    InsuranceCompanyGroupCreate,
    InsuranceCompanyGroupUpdate,
    InsuranceCompanyGroupInDB,
    InsurancePayerCreate,
    InsurancePayerUpdate,
    InsurancePayerInDB,
    InsuranceTypeCreate,
    InsuranceTypeUpdate,
    InsuranceTypeInDB,
    InsurancePolicyCreate,
    InsurancePolicyUpdate,
    InsurancePolicyInDB
)

router = APIRouter(prefix="/insurance", tags=["insurance"])

# Insurance Company Endpoints

@router.post(
    "/companies",
    response_model=InsuranceCompanyInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new insurance company"
)
async def create_insurance_company(
    company_data: InsuranceCompanyCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new insurance company with the provided data.

    Args:
        company_data: Insurance company data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created insurance company
    """
    return await InsuranceCompanyService.create_company(
        db=db,
        company_data=company_data,
        current_user=current_user
    )

@router.get(
    "/companies/{company_id}",
    response_model=InsuranceCompanyInDB,
    summary="Get an insurance company by ID"
)
async def get_insurance_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an insurance company by its ID.

    Args:
        company_id: ID of the insurance company
        db: Database session

    Returns:
        Insurance company if found

    Raises:
        HTTPException: If company not found
    """
    company = await InsuranceCompanyService.get_company(db=db, company_id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance company with ID {company_id} not found"
        )
    return company

@router.get(
    "/companies",
    response_model=List[InsuranceCompanyInDB],
    summary="Get a list of insurance companies"
)
async def list_insurance_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of insurance companies with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status if provided
        db: Database session

    Returns:
        List of insurance companies
    """
    return await InsuranceCompanyService.get_companies(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active
    )

@router.put(
    "/companies/{company_id}",
    response_model=InsuranceCompanyInDB,
    summary="Update an insurance company"
)
async def update_insurance_company(
    company_id: int,
    company_data: InsuranceCompanyUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing insurance company.

    Args:
        company_id: ID of the insurance company to update
        company_data: Updated insurance company data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated insurance company

    Raises:
        HTTPException: If company not found
    """
    company = await InsuranceCompanyService.update_company(
        db=db,
        company_id=company_id,
        company_data=company_data,
        current_user=current_user
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance company with ID {company_id} not found"
        )
    return company

@router.delete(
    "/companies/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an insurance company"
)
async def delete_insurance_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete (soft delete) an insurance company.

    Args:
        company_id: ID of the insurance company to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If company not found
    """
    deleted = await InsuranceCompanyService.delete_company(
        db=db,
        company_id=company_id,
        current_user=current_user
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance company with ID {company_id} not found"
        )

@router.get(
    "/companies/search",
    response_model=List[InsuranceCompanyInDB],
    summary="Search insurance companies"
)
async def search_insurance_companies(
    query: str = Query(..., min_length=2),
    is_active: Optional[bool] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search insurance companies by name or payer_id.

    Args:
        query: Search term
        is_active: Filter by active status if provided
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of matching insurance companies
    """
    return await InsuranceCompanyService.search_companies(
        db=db,
        search_term=query,
        is_active=is_active,
        limit=limit
    )

# Insurance Company Group Endpoints

@router.post(
    "/company-groups",
    response_model=InsuranceCompanyGroupInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new insurance company group"
)
async def create_insurance_company_group(
    group_data: InsuranceCompanyGroupCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new insurance company group with the provided data.

    Args:
        group_data: Insurance company group data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created insurance company group
    """
    return await InsuranceCompanyGroupService.create_group(
        db=db,
        group_data=group_data,
        current_user=current_user
    )

@router.get(
    "/company-groups/{group_id}",
    response_model=InsuranceCompanyGroupInDB,
    summary="Get an insurance company group by ID"
)
async def get_insurance_company_group(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an insurance company group by its ID.

    Args:
        group_id: ID of the insurance company group
        db: Database session

    Returns:
        Insurance company group if found

    Raises:
        HTTPException: If group not found
    """
    group = await InsuranceCompanyGroupService.get_group(db=db, group_id=group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance company group with ID {group_id} not found"
        )
    return group

@router.get(
    "/company-groups",
    response_model=List[InsuranceCompanyGroupInDB],
    summary="Get a list of insurance company groups"
)
async def list_insurance_company_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    parent_group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of insurance company groups with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status if provided
        parent_group_id: Filter by parent group ID if provided
        db: Database session

    Returns:
        List of insurance company groups
    """
    return await InsuranceCompanyGroupService.get_groups(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        parent_group_id=parent_group_id
    )

@router.put(
    "/company-groups/{group_id}",
    response_model=InsuranceCompanyGroupInDB,
    summary="Update an insurance company group"
)
async def update_insurance_company_group(
    group_id: int,
    group_data: InsuranceCompanyGroupUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing insurance company group.

    Args:
        group_id: ID of the insurance company group to update
        group_data: Updated insurance company group data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated insurance company group

    Raises:
        HTTPException: If group not found
    """
    group = await InsuranceCompanyGroupService.update_group(
        db=db,
        group_id=group_id,
        group_data=group_data,
        current_user=current_user
    )
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance company group with ID {group_id} not found"
        )
    return group

@router.delete(
    "/company-groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an insurance company group"
)
async def delete_insurance_company_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete (soft delete) an insurance company group.
    This will also deactivate all child groups.

    Args:
        group_id: ID of the insurance company group to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If group not found
    """
    deleted = await InsuranceCompanyGroupService.delete_group(
        db=db,
        group_id=group_id,
        current_user=current_user
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance company group with ID {group_id} not found"
        )

@router.get(
    "/company-groups/{group_id}/hierarchy",
    response_model=Dict[str, Any],
    summary="Get group hierarchy"
)
async def get_insurance_company_group_hierarchy(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the complete hierarchy for a group, including its parents and children.

    Args:
        group_id: ID of the insurance company group
        db: Database session

    Returns:
        Dictionary containing the group hierarchy

    Raises:
        HTTPException: If group not found
    """
    hierarchy = await InsuranceCompanyGroupService.get_group_hierarchy(
        db=db,
        group_id=group_id
    )
    if not hierarchy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance company group with ID {group_id} not found"
        )
    return hierarchy

# Insurance Payer Endpoints

@router.post(
    "/payers",
    response_model=InsurancePayerInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new insurance payer"
)
async def create_insurance_payer(
    payer_data: InsurancePayerCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new insurance payer with the provided data.

    Args:
        payer_data: Insurance payer data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created insurance payer
    """
    return await InsurancePayerService.create_payer(
        db=db,
        payer_data=payer_data,
        current_user=current_user
    )

@router.get(
    "/payers/{payer_id}",
    response_model=InsurancePayerInDB,
    summary="Get an insurance payer by ID"
)
async def get_insurance_payer(
    payer_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an insurance payer by its ID.

    Args:
        payer_id: ID of the insurance payer
        db: Database session

    Returns:
        Insurance payer if found

    Raises:
        HTTPException: If payer not found
    """
    payer = await InsurancePayerService.get_payer(db=db, payer_id=payer_id)
    if not payer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance payer with ID {payer_id} not found"
        )
    return payer

@router.get(
    "/payers/code/{payer_code}",
    response_model=InsurancePayerInDB,
    summary="Get an insurance payer by code"
)
async def get_insurance_payer_by_code(
    payer_code: str,
    db: Session = Depends(get_db)
):
    """
    Get an insurance payer by its payer code.

    Args:
        payer_code: Code of the insurance payer
        db: Database session

    Returns:
        Insurance payer if found

    Raises:
        HTTPException: If payer not found
    """
    payer = await InsurancePayerService.get_payer_by_code(db=db, payer_code=payer_code)
    if not payer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance payer with code '{payer_code}' not found"
        )
    return payer

@router.get(
    "/payers",
    response_model=List[InsurancePayerInDB],
    summary="Get a list of insurance payers"
)
async def list_insurance_payers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    payer_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of insurance payers with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status if provided
        payer_type: Filter by payer type if provided
        db: Database session

    Returns:
        List of insurance payers
    """
    return await InsurancePayerService.get_payers(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        payer_type=payer_type
    )

@router.put(
    "/payers/{payer_id}",
    response_model=InsurancePayerInDB,
    summary="Update an insurance payer"
)
async def update_insurance_payer(
    payer_id: int,
    payer_data: InsurancePayerUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing insurance payer.

    Args:
        payer_id: ID of the insurance payer to update
        payer_data: Updated insurance payer data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated insurance payer

    Raises:
        HTTPException: If payer not found
    """
    payer = await InsurancePayerService.update_payer(
        db=db,
        payer_id=payer_id,
        payer_data=payer_data,
        current_user=current_user
    )
    if not payer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance payer with ID {payer_id} not found"
        )
    return payer

@router.delete(
    "/payers/{payer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an insurance payer"
)
async def delete_insurance_payer(
    payer_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete (soft delete) an insurance payer.
    This will also check for active policies before deletion.

    Args:
        payer_id: ID of the insurance payer to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If payer not found or has active policies
    """
    deleted = await InsurancePayerService.delete_payer(
        db=db,
        payer_id=payer_id,
        current_user=current_user
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance payer with ID {payer_id} not found"
        )

@router.get(
    "/payers/search",
    response_model=List[InsurancePayerInDB],
    summary="Search insurance payers"
)
async def search_insurance_payers(
    search_term: str = Query(..., min_length=1),
    is_active: Optional[bool] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search insurance payers by name, code, or type.

    Args:
        search_term: Term to search for in payer name, code, or type
        is_active: Filter by active status if provided
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of matching insurance payers
    """
    return await InsurancePayerService.search_payers(
        db=db,
        search_term=search_term,
        is_active=is_active,
        limit=limit
    )

@router.get(
    "/payers/{payer_id}/policies",
    response_model=List[Dict[str, Any]],
    summary="Get payer policies"
)
async def get_insurance_payer_policies(
    payer_id: int,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all policies associated with a payer.

    Args:
        payer_id: ID of the insurance payer
        status: Filter by policy status if provided
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of policies with basic patient information

    Raises:
        HTTPException: If payer not found
    """
    return await InsurancePayerService.get_payer_policies(
        db=db,
        payer_id=payer_id,
        status=status,
        skip=skip,
        limit=limit
    )

# Insurance Type Endpoints

@router.post(
    "/types",
    response_model=InsuranceTypeInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new insurance type"
)
async def create_insurance_type(
    type_data: InsuranceTypeCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new insurance type with the provided data.

    Args:
        type_data: Insurance type data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created insurance type
    """
    return await InsuranceTypeService.create_type(
        db=db,
        type_data=type_data,
        current_user=current_user
    )

@router.get(
    "/types/{type_id}",
    response_model=InsuranceTypeInDB,
    summary="Get an insurance type by ID"
)
async def get_insurance_type(
    type_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an insurance type by its ID.

    Args:
        type_id: ID of the insurance type
        db: Database session

    Returns:
        Insurance type if found

    Raises:
        HTTPException: If type not found
    """
    type_obj = await InsuranceTypeService.get_type(db=db, type_id=type_id)
    if not type_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance type with ID {type_id} not found"
        )
    return type_obj

@router.get(
    "/types/code/{type_code}",
    response_model=InsuranceTypeInDB,
    summary="Get an insurance type by code"
)
async def get_insurance_type_by_code(
    type_code: str,
    db: Session = Depends(get_db)
):
    """
    Get an insurance type by its type code.

    Args:
        type_code: Code of the insurance type
        db: Database session

    Returns:
        Insurance type if found

    Raises:
        HTTPException: If type not found
    """
    type_obj = await InsuranceTypeService.get_type_by_code(db=db, type_code=type_code)
    if not type_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance type with code '{type_code}' not found"
        )
    return type_obj

@router.get(
    "/types",
    response_model=List[InsuranceTypeInDB],
    summary="Get a list of insurance types"
)
async def list_insurance_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of insurance types with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status if provided
        category: Filter by category if provided
        db: Database session

    Returns:
        List of insurance types
    """
    return await InsuranceTypeService.get_types(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        category=category
    )

@router.put(
    "/types/{type_id}",
    response_model=InsuranceTypeInDB,
    summary="Update an insurance type"
)
async def update_insurance_type(
    type_id: int,
    type_data: InsuranceTypeUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing insurance type.

    Args:
        type_id: ID of the insurance type to update
        type_data: Updated insurance type data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated insurance type

    Raises:
        HTTPException: If type not found
    """
    type_obj = await InsuranceTypeService.update_type(
        db=db,
        type_id=type_id,
        type_data=type_data,
        current_user=current_user
    )
    if not type_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance type with ID {type_id} not found"
        )
    return type_obj

@router.delete(
    "/types/{type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an insurance type"
)
async def delete_insurance_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete (soft delete) an insurance type.
    This will also check for active policies before deletion.

    Args:
        type_id: ID of the insurance type to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If type not found or has active policies
    """
    deleted = await InsuranceTypeService.delete_type(
        db=db,
        type_id=type_id,
        current_user=current_user
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance type with ID {type_id} not found"
        )

@router.get(
    "/types/search",
    response_model=List[InsuranceTypeInDB],
    summary="Search insurance types"
)
async def search_insurance_types(
    search_term: str = Query(..., min_length=1),
    is_active: Optional[bool] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search insurance types by name, code, or category.

    Args:
        search_term: Term to search for in type name, code, or category
        is_active: Filter by active status if provided
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of matching insurance types
    """
    return await InsuranceTypeService.search_types(
        db=db,
        search_term=search_term,
        is_active=is_active,
        limit=limit
    )

@router.get(
    "/types/{type_id}/policies",
    response_model=List[Dict[str, Any]],
    summary="Get type policies"
)
async def get_insurance_type_policies(
    type_id: int,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all policies associated with a type.

    Args:
        type_id: ID of the insurance type
        status: Filter by policy status if provided
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of policies with basic patient and payer information

    Raises:
        HTTPException: If type not found
    """
    return await InsuranceTypeService.get_type_policies(
        db=db,
        type_id=type_id,
        status=status,
        skip=skip,
        limit=limit
    )

# Insurance Policy Endpoints

@router.post(
    "/policies",
    response_model=InsurancePolicyInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new insurance policy"
)
async def create_insurance_policy(
    policy_data: InsurancePolicyCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new insurance policy with the provided data.

    Args:
        policy_data: Insurance policy data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created insurance policy
    """
    return await InsurancePolicyService.create_policy(
        db=db,
        policy_data=policy_data,
        current_user=current_user
    )

@router.get(
    "/policies/{policy_id}",
    response_model=InsurancePolicyInDB,
    summary="Get an insurance policy by ID"
)
async def get_insurance_policy(
    policy_id: int,
    include_relations: bool = Query(False, description="Include related entities"),
    db: Session = Depends(get_db)
):
    """
    Get an insurance policy by its ID.

    Args:
        policy_id: ID of the insurance policy
        include_relations: If True, include related entities
        db: Database session

    Returns:
        Insurance policy if found

    Raises:
        HTTPException: If policy not found
    """
    policy = await InsurancePolicyService.get_policy(
        db=db,
        policy_id=policy_id,
        include_relations=include_relations
    )
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance policy with ID {policy_id} not found"
        )
    return policy

@router.get(
    "/policies/number/{policy_number}",
    response_model=InsurancePolicyInDB,
    summary="Get an insurance policy by number"
)
async def get_insurance_policy_by_number(
    policy_number: str,
    include_relations: bool = Query(False, description="Include related entities"),
    db: Session = Depends(get_db)
):
    """
    Get an insurance policy by its policy number.

    Args:
        policy_number: Number of the insurance policy
        include_relations: If True, include related entities
        db: Database session

    Returns:
        Insurance policy if found

    Raises:
        HTTPException: If policy not found
    """
    policy = await InsurancePolicyService.get_policy_by_number(
        db=db,
        policy_number=policy_number,
        include_relations=include_relations
    )
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance policy with number '{policy_number}' not found"
        )
    return policy

@router.get(
    "/policies",
    response_model=List[InsurancePolicyInDB],
    summary="Get a list of insurance policies"
)
async def list_insurance_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    payer_id: Optional[int] = None,
    type_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    include_relations: bool = Query(False, description="Include related entities"),
    db: Session = Depends(get_db)
):
    """
    Get a list of insurance policies with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by policy status if provided
        payer_id: Filter by payer ID if provided
        type_id: Filter by type ID if provided
        patient_id: Filter by patient ID if provided
        include_relations: If True, include related entities
        db: Database session

    Returns:
        List of insurance policies
    """
    return await InsurancePolicyService.get_policies(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        payer_id=payer_id,
        type_id=type_id,
        patient_id=patient_id,
        include_relations=include_relations
    )

@router.put(
    "/policies/{policy_id}",
    response_model=InsurancePolicyInDB,
    summary="Update an insurance policy"
)
async def update_insurance_policy(
    policy_id: int,
    policy_data: InsurancePolicyUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing insurance policy.

    Args:
        policy_id: ID of the insurance policy to update
        policy_data: Updated insurance policy data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated insurance policy

    Raises:
        HTTPException: If policy not found
    """
    policy = await InsurancePolicyService.update_policy(
        db=db,
        policy_id=policy_id,
        policy_data=policy_data,
        current_user=current_user
    )
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance policy with ID {policy_id} not found"
        )
    return policy

@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an insurance policy"
)
async def delete_insurance_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete (cancel) an insurance policy.

    Args:
        policy_id: ID of the insurance policy to delete
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: If policy not found or already cancelled
    """
    deleted = await InsurancePolicyService.delete_policy(
        db=db,
        policy_id=policy_id,
        current_user=current_user
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance policy with ID {policy_id} not found"
        )

@router.get(
    "/policies/search",
    response_model=List[InsurancePolicyInDB],
    summary="Search insurance policies"
)
async def search_insurance_policies(
    search_term: str = Query(..., min_length=1),
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    include_relations: bool = Query(True, description="Include related entities"),
    db: Session = Depends(get_db)
):
    """
    Search insurance policies by policy number or patient name.

    Args:
        search_term: Term to search for in policy number or patient name
        status: Filter by policy status if provided
        limit: Maximum number of records to return
        include_relations: If True, include related entities
        db: Database session

    Returns:
        List of matching insurance policies
    """
    return await InsurancePolicyService.search_policies(
        db=db,
        search_term=search_term,
        status=status,
        limit=limit,
        include_relations=include_relations
    )

@router.get(
    "/policies/active",
    response_model=Optional[InsurancePolicyInDB],
    summary="Get active policy"
)
async def get_active_insurance_policy(
    patient_id: int = Query(..., description="ID of the patient"),
    type_id: int = Query(..., description="ID of the insurance type"),
    reference_date: Optional[datetime] = Query(None, description="Date to check policy status"),
    db: Session = Depends(get_db)
):
    """
    Get the active policy for a patient and insurance type at a specific date.

    Args:
        patient_id: ID of the patient
        type_id: ID of the insurance type
        reference_date: Date to check policy status (defaults to current date)
        db: Database session

    Returns:
        Active insurance policy if found, None otherwise
    """
    return await InsurancePolicyService.get_active_policy(
        db=db,
        patient_id=patient_id,
        type_id=type_id,
        reference_date=reference_date
    )

@router.get(
    "/policies/history/{patient_id}",
    response_model=List[InsurancePolicyInDB],
    summary="Get policy history"
)
async def get_insurance_policy_history(
    patient_id: int,
    type_id: Optional[int] = None,
    include_relations: bool = Query(True, description="Include related entities"),
    db: Session = Depends(get_db)
):
    """
    Get the policy history for a patient, optionally filtered by type.

    Args:
        patient_id: ID of the patient
        type_id: ID of the insurance type to filter by
        include_relations: If True, include related entities
        db: Database session

    Returns:
        List of insurance policies ordered by start date
    """
    return await InsurancePolicyService.get_policy_history(
        db=db,
        patient_id=patient_id,
        type_id=type_id,
        include_relations=include_relations
    )
