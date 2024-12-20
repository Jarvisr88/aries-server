"""
Insurance Domain Services
Version: 2024-12-19_13-27
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.insurance import (
    InsuranceCompany,
    InsuranceCompanyGroup,
    InsurancePayer,
    InsurancePlan
)
from app.schemas.insurance import (
    InsuranceCompanyCreate,
    InsuranceCompanyUpdate,
    InsuranceCompanyInDB
)
from app.core.logging import logger

class InsuranceCompanyService:
    """Service for managing insurance companies"""

    @staticmethod
    async def create_company(
        db: Session,
        company_data: InsuranceCompanyCreate,
        current_user: str
    ) -> InsuranceCompanyInDB:
        """
        Create a new insurance company.

        Args:
            db: Database session
            company_data: Insurance company data
            current_user: Username of the current user

        Returns:
            Created insurance company

        Raises:
            HTTPException: If company with same payer_id already exists
        """
        try:
            company = InsuranceCompany(
                **company_data.model_dump(),
                created_by=current_user,
                updated_by=current_user
            )
            db.add(company)
            db.commit()
            db.refresh(company)
            logger.info(
                f"Insurance company created: {company.name} (ID: {company.id})",
                extra={"user": current_user}
            )
            return InsuranceCompanyInDB.model_validate(company)
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Failed to create insurance company: {str(e)}",
                extra={"user": current_user}
            )
            if "insurance_companies_payer_id_key" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insurance company with payer_id '{company_data.payer_id}' already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create insurance company"
            )

    @staticmethod
    async def get_company(
        db: Session,
        company_id: int
    ) -> Optional[InsuranceCompanyInDB]:
        """
        Get an insurance company by ID.

        Args:
            db: Database session
            company_id: ID of the insurance company

        Returns:
            Insurance company if found, None otherwise
        """
        company = db.query(InsuranceCompany).filter(
            InsuranceCompany.id == company_id
        ).first()
        
        if not company:
            return None
            
        return InsuranceCompanyInDB.model_validate(company)

    @staticmethod
    async def get_companies(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[InsuranceCompanyInDB]:
        """
        Get a list of insurance companies with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status if provided

        Returns:
            List of insurance companies
        """
        query = db.query(InsuranceCompany)
        
        if is_active is not None:
            query = query.filter(InsuranceCompany.is_active == is_active)
            
        companies = query.offset(skip).limit(limit).all()
        return [InsuranceCompanyInDB.model_validate(c) for c in companies]

    @staticmethod
    async def update_company(
        db: Session,
        company_id: int,
        company_data: InsuranceCompanyUpdate,
        current_user: str
    ) -> Optional[InsuranceCompanyInDB]:
        """
        Update an insurance company.

        Args:
            db: Database session
            company_id: ID of the insurance company to update
            company_data: Updated insurance company data
            current_user: Username of the current user

        Returns:
            Updated insurance company if found, None otherwise

        Raises:
            HTTPException: If update fails due to constraint violation
        """
        try:
            company = db.query(InsuranceCompany).filter(
                InsuranceCompany.id == company_id
            ).first()
            
            if not company:
                return None

            update_data = company_data.model_dump(exclude_unset=True)
            update_data["updated_by"] = current_user
            update_data["updated_at"] = datetime.utcnow()

            for field, value in update_data.items():
                setattr(company, field, value)

            db.commit()
            db.refresh(company)
            
            logger.info(
                f"Insurance company updated: {company.name} (ID: {company.id})",
                extra={"user": current_user}
            )
            return InsuranceCompanyInDB.model_validate(company)
            
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Failed to update insurance company: {str(e)}",
                extra={"user": current_user}
            )
            if "insurance_companies_payer_id_key" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insurance company with payer_id '{company_data.payer_id}' already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update insurance company"
            )

    @staticmethod
    async def delete_company(
        db: Session,
        company_id: int,
        current_user: str
    ) -> bool:
        """
        Delete an insurance company (soft delete by setting is_active=False).

        Args:
            db: Database session
            company_id: ID of the insurance company to delete
            current_user: Username of the current user

        Returns:
            True if company was deleted, False if not found
        """
        company = db.query(InsuranceCompany).filter(
            InsuranceCompany.id == company_id
        ).first()
        
        if not company:
            return False

        company.is_active = False
        company.updated_by = current_user
        company.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            f"Insurance company deactivated: {company.name} (ID: {company.id})",
            extra={"user": current_user}
        )
        return True

    @staticmethod
    async def search_companies(
        db: Session,
        search_term: str,
        is_active: Optional[bool] = None,
        limit: int = 10
    ) -> List[InsuranceCompanyInDB]:
        """
        Search insurance companies by name or payer_id.

        Args:
            db: Database session
            search_term: Term to search for in company name or payer_id
            is_active: Filter by active status if provided
            limit: Maximum number of records to return

        Returns:
            List of matching insurance companies
        """
        query = db.query(InsuranceCompany).filter(
            InsuranceCompany.name.ilike(f"%{search_term}%") |
            InsuranceCompany.payer_id.ilike(f"%{search_term}%")
        )
        
        if is_active is not None:
            query = query.filter(InsuranceCompany.is_active == is_active)
            
        companies = query.limit(limit).all()
        return [InsuranceCompanyInDB.model_validate(c) for c in companies]


"""
Insurance Services
Version: 2024-12-19_13-10

This module implements services for the Insurance domain.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.core.service import BaseService
from app.models.insurance import (
    InsuranceCompany,
    InsurancePayer,
    InsuranceType,
    InsurancePolicy,
    InsuranceCoverage
)
from app.schemas.insurance import (
    InsuranceCompanyCreate,
    InsuranceCompanyUpdate,
    InsurancePayerCreate,
    InsurancePayerUpdate,
    InsuranceTypeCreate,
    InsuranceTypeUpdate,
    InsurancePolicyCreate,
    InsurancePolicyUpdate,
    InsuranceCoverageCreate,
    InsuranceCoverageUpdate
)
from app.core.logging import logger

class InsuranceCompanyService(BaseService[InsuranceCompany, InsuranceCompanyCreate, InsuranceCompanyUpdate]):
    """Service for managing insurance companies"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InsuranceCompany, db)
    
    async def create(self, schema: InsuranceCompanyCreate, current_user_id: int, **kwargs) -> InsuranceCompany:
        """Create a new insurance company"""
        try:
            data = schema.model_dump()
            data.update(kwargs)
            
            # Check for duplicate payer_id if provided
            if data.get("payer_id"):
                existing = await self.db.execute(
                    select(self.model).where(
                        self.model.payer_id == data["payer_id"]
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insurance company with payer_id {data['payer_id']} already exists"
                    )
            
            obj = self.model(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
            
        except Exception as e:
            logger.error(f"Error creating insurance company: {str(e)}")
            await self.db.rollback()
            raise

    async def search(
        self,
        query: str,
        is_active: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[InsuranceCompany]:
        """Search insurance companies by name or payer_id"""
        try:
            stmt = select(self.model).where(
                and_(
                    self.model.is_active == is_active,
                    or_(
                        self.model.name.ilike(f"%{query}%"),
                        self.model.payer_id.ilike(f"%{query}%")
                    )
                )
            ).limit(limit).offset(offset)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching insurance companies: {str(e)}")
            raise

class InsurancePayerService:
    """Service for managing insurance payers"""

    @staticmethod
    async def create_payer(
        db: Session,
        payer_data: InsurancePayerCreate,
        current_user: str
    ) -> InsurancePayer:
        """
        Create a new insurance payer.

        Args:
            db: Database session
            payer_data: Insurance payer data
            current_user: Username of the current user

        Returns:
            Created insurance payer

        Raises:
            HTTPException: If payer with same payer_code already exists
        """
        try:
            payer = InsurancePayer(
                **payer_data.model_dump(),
                created_by=current_user,
                updated_by=current_user
            )
            db.add(payer)
            db.commit()
            db.refresh(payer)
            
            logger.info(
                f"Insurance payer created: {payer.name} (ID: {payer.id})",
                extra={"user": current_user}
            )
            return payer
            
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Failed to create insurance payer: {str(e)}",
                extra={"user": current_user}
            )
            if "uq_payer_code" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insurance payer with code '{payer_data.payer_code}' already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create insurance payer"
            )

    @staticmethod
    async def get_payer(
        db: Session,
        payer_id: int
    ) -> Optional[InsurancePayer]:
        """
        Get an insurance payer by ID.

        Args:
            db: Database session
            payer_id: ID of the insurance payer

        Returns:
            Insurance payer if found, None otherwise
        """
        payer = db.query(InsurancePayer).filter(
            InsurancePayer.id == payer_id
        ).first()
        
        if not payer:
            return None
            
        return payer

    @staticmethod
    async def get_payer_by_code(
        db: Session,
        payer_code: str
    ) -> Optional[InsurancePayer]:
        """
        Get an insurance payer by payer code.

        Args:
            db: Database session
            payer_code: Code of the insurance payer

        Returns:
            Insurance payer if found, None otherwise
        """
        payer = db.query(InsurancePayer).filter(
            InsurancePayer.payer_code == payer_code
        ).first()
        
        if not payer:
            return None
            
        return payer

    @staticmethod
    async def get_payers(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        payer_type: Optional[str] = None
    ) -> List[InsurancePayer]:
        """
        Get a list of insurance payers with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status if provided
            payer_type: Filter by payer type if provided

        Returns:
            List of insurance payers
        """
        query = db.query(InsurancePayer)
        
        if is_active is not None:
            query = query.filter(InsurancePayer.is_active == is_active)
            
        if payer_type:
            query = query.filter(InsurancePayer.type == payer_type)
            
        payers = query.offset(skip).limit(limit).all()
        return payers

    @staticmethod
    async def update_payer(
        db: Session,
        payer_id: int,
        payer_data: InsurancePayerUpdate,
        current_user: str
    ) -> Optional[InsurancePayer]:
        """
        Update an insurance payer.

        Args:
            db: Database session
            payer_id: ID of the insurance payer to update
            payer_data: Updated insurance payer data
            current_user: Username of the current user

        Returns:
            Updated insurance payer if found, None otherwise

        Raises:
            HTTPException: If update fails due to constraint violation
        """
        try:
            payer = db.query(InsurancePayer).filter(
                InsurancePayer.id == payer_id
            ).first()
            
            if not payer:
                return None

            update_data = payer_data.model_dump(exclude_unset=True)
            update_data["updated_by"] = current_user
            update_data["updated_at"] = datetime.utcnow()

            for field, value in update_data.items():
                setattr(payer, field, value)

            db.commit()
            db.refresh(payer)
            
            logger.info(
                f"Insurance payer updated: {payer.name} (ID: {payer.id})",
                extra={"user": current_user}
            )
            return payer
            
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Failed to update insurance payer: {str(e)}",
                extra={"user": current_user}
            )
            if "uq_payer_code" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insurance payer with code '{payer_data.payer_code}' already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update insurance payer"
            )

    @staticmethod
    async def delete_payer(
        db: Session,
        payer_id: int,
        current_user: str
    ) -> bool:
        """
        Delete an insurance payer (soft delete by setting is_active=False).

        Args:
            db: Database session
            payer_id: ID of the insurance payer to delete
            current_user: Username of the current user

        Returns:
            True if payer was deleted, False if not found

        Raises:
            HTTPException: If payer has active policies
        """
        payer = db.query(InsurancePayer).filter(
            InsurancePayer.id == payer_id
        ).first()
        
        if not payer:
            return False

        # Check for active policies
        active_policies = db.query(InsurancePolicy).filter(
            InsurancePolicy.payer_id == payer_id,
            InsurancePolicy.status == "active"
        ).count()

        if active_policies > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete payer with {active_policies} active policies"
            )

        payer.is_active = False
        payer.updated_by = current_user
        payer.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            f"Insurance payer deactivated: {payer.name} (ID: {payer.id})",
            extra={"user": current_user}
        )
        return True

    @staticmethod
    async def search_payers(
        db: Session,
        search_term: str,
        is_active: Optional[bool] = None,
        limit: int = 10
    ) -> List[InsurancePayer]:
        """
        Search insurance payers by name, code, or type.

        Args:
            db: Database session
            search_term: Term to search for in payer name, code, or type
            is_active: Filter by active status if provided
            limit: Maximum number of records to return

        Returns:
            List of matching insurance payers
        """
        query = db.query(InsurancePayer).filter(
            InsurancePayer.name.ilike(f"%{search_term}%") |
            InsurancePayer.payer_code.ilike(f"%{search_term}%") |
            InsurancePayer.type.ilike(f"%{search_term}%")
        )
        
        if is_active is not None:
            query = query.filter(InsurancePayer.is_active == is_active)
            
        payers = query.limit(limit).all()
        return payers

    @staticmethod
    async def get_payer_policies(
        db: Session,
        payer_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all policies associated with a payer.

        Args:
            db: Database session
            payer_id: ID of the insurance payer
            status: Filter by policy status if provided
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of policies with basic patient information

        Raises:
            HTTPException: If payer not found
        """
        payer = db.query(InsurancePayer).filter(
            InsurancePayer.id == payer_id
        ).first()
        
        if not payer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insurance payer with ID {payer_id} not found"
            )

        query = db.query(InsurancePolicy, "patients.*").join(
            "patient"
        ).filter(
            InsurancePolicy.payer_id == payer_id
        )

        if status:
            query = query.filter(InsurancePolicy.status == status)

        policies = query.offset(skip).limit(limit).all()
        
        return [{
            "policy_id": policy.id,
            "policy_number": policy.policy_number,
            "status": policy.status,
            "coverage_start_date": policy.coverage_start_date,
            "coverage_end_date": policy.coverage_end_date,
            "patient": {
                "id": patient.id,
                "first_name": patient.first_name,
                "last_name": patient.last_name
            }
        } for policy, patient in policies]

class InsuranceTypeService:
    """Service for managing insurance types"""

    @staticmethod
    async def create_type(
        db: Session,
        type_data: InsuranceTypeCreate,
        current_user: str
    ) -> InsuranceType:
        """
        Create a new insurance type.

        Args:
            db: Database session
            type_data: Insurance type data
            current_user: Username of the current user

        Returns:
            Created insurance type

        Raises:
            HTTPException: If type with same code already exists
        """
        try:
            type_obj = InsuranceType(
                **type_data.model_dump(),
                created_by=current_user,
                updated_by=current_user
            )
            db.add(type_obj)
            db.commit()
            db.refresh(type_obj)
            
            logger.info(
                f"Insurance type created: {type_obj.name} (ID: {type_obj.id})",
                extra={"user": current_user}
            )
            return type_obj
            
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Failed to create insurance type: {str(e)}",
                extra={"user": current_user}
            )
            if "uq_type_code" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insurance type with code '{type_data.type_code}' already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create insurance type"
            )

    @staticmethod
    async def get_type(
        db: Session,
        type_id: int
    ) -> Optional[InsuranceType]:
        """
        Get an insurance type by ID.

        Args:
            db: Database session
            type_id: ID of the insurance type

        Returns:
            Insurance type if found, None otherwise
        """
        return db.query(InsuranceType).filter(
            InsuranceType.id == type_id
        ).first()

    @staticmethod
    async def get_type_by_code(
        db: Session,
        type_code: str
    ) -> Optional[InsuranceType]:
        """
        Get an insurance type by type code.

        Args:
            db: Database session
            type_code: Code of the insurance type

        Returns:
            Insurance type if found, None otherwise
        """
        return db.query(InsuranceType).filter(
            InsuranceType.type_code == type_code
        ).first()

    @staticmethod
    async def get_types(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        category: Optional[str] = None
    ) -> List[InsuranceType]:
        """
        Get a list of insurance types with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status if provided
            category: Filter by category if provided

        Returns:
            List of insurance types
        """
        query = db.query(InsuranceType)
        
        if is_active is not None:
            query = query.filter(InsuranceType.is_active == is_active)
            
        if category:
            query = query.filter(InsuranceType.category == category)
            
        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def update_type(
        db: Session,
        type_id: int,
        type_data: InsuranceTypeUpdate,
        current_user: str
    ) -> Optional[InsuranceType]:
        """
        Update an insurance type.

        Args:
            db: Database session
            type_id: ID of the insurance type to update
            type_data: Updated insurance type data
            current_user: Username of the current user

        Returns:
            Updated insurance type if found, None otherwise

        Raises:
            HTTPException: If update fails due to constraint violation
        """
        try:
            type_obj = db.query(InsuranceType).filter(
                InsuranceType.id == type_id
            ).first()
            
            if not type_obj:
                return None

            update_data = type_data.model_dump(exclude_unset=True)
            update_data["updated_by"] = current_user
            update_data["updated_at"] = datetime.utcnow()

            for field, value in update_data.items():
                setattr(type_obj, field, value)

            db.commit()
            db.refresh(type_obj)
            
            logger.info(
                f"Insurance type updated: {type_obj.name} (ID: {type_obj.id})",
                extra={"user": current_user}
            )
            return type_obj
            
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Failed to update insurance type: {str(e)}",
                extra={"user": current_user}
            )
            if "uq_type_code" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insurance type with code '{type_data.type_code}' already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update insurance type"
            )

    @staticmethod
    async def delete_type(
        db: Session,
        type_id: int,
        current_user: str
    ) -> bool:
        """
        Delete an insurance type (soft delete by setting is_active=False).

        Args:
            db: Database session
            type_id: ID of the insurance type to delete
            current_user: Username of the current user

        Returns:
            True if type was deleted, False if not found

        Raises:
            HTTPException: If type has active policies
        """
        type_obj = db.query(InsuranceType).filter(
            InsuranceType.id == type_id
        ).first()
        
        if not type_obj:
            return False

        # Check for active policies
        active_policies = db.query(InsurancePolicy).filter(
            InsurancePolicy.type_id == type_id,
            InsurancePolicy.status == "active"
        ).count()

        if active_policies > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete type with {active_policies} active policies"
            )

        type_obj.is_active = False
        type_obj.updated_by = current_user
        type_obj.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            f"Insurance type deactivated: {type_obj.name} (ID: {type_obj.id})",
            extra={"user": current_user}
        )
        return True

    @staticmethod
    async def search_types(
        db: Session,
        search_term: str,
        is_active: Optional[bool] = None,
        limit: int = 10
    ) -> List[InsuranceType]:
        """
        Search insurance types by name, code, or category.

        Args:
            db: Database session
            search_term: Term to search for in type name, code, or category
            is_active: Filter by active status if provided
            limit: Maximum number of records to return

        Returns:
            List of matching insurance types
        """
        query = db.query(InsuranceType).filter(
            InsuranceType.name.ilike(f"%{search_term}%") |
            InsuranceType.type_code.ilike(f"%{search_term}%") |
            InsuranceType.category.ilike(f"%{search_term}%")
        )
        
        if is_active is not None:
            query = query.filter(InsuranceType.is_active == is_active)
            
        return query.limit(limit).all()

    @staticmethod
    async def get_type_policies(
        db: Session,
        type_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all policies associated with a type.

        Args:
            db: Database session
            type_id: ID of the insurance type
            status: Filter by policy status if provided
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of policies with basic patient and payer information

        Raises:
            HTTPException: If type not found
        """
        type_obj = db.query(InsuranceType).filter(
            InsuranceType.id == type_id
        ).first()
        
        if not type_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insurance type with ID {type_id} not found"
            )

        query = db.query(
            InsurancePolicy,
            "patients.*",
            "payers.*"
        ).join(
            "patient"
        ).join(
            "payer"
        ).filter(
            InsurancePolicy.type_id == type_id
        )

        if status:
            query = query.filter(InsurancePolicy.status == status)

        policies = query.offset(skip).limit(limit).all()
        
        return [{
            "policy_id": policy.id,
            "policy_number": policy.policy_number,
            "status": policy.status,
            "coverage_start_date": policy.coverage_start_date,
            "coverage_end_date": policy.coverage_end_date,
            "patient": {
                "id": patient.id,
                "first_name": patient.first_name,
                "last_name": patient.last_name
            },
            "payer": {
                "id": payer.id,
                "name": payer.name,
                "payer_code": payer.payer_code
            }
        } for policy, patient, payer in policies]

class InsurancePolicyService:
    """Service for managing insurance policies"""

    @staticmethod
    async def create_policy(
        db: Session,
        policy_data: InsurancePolicyCreate,
        current_user: str
    ) -> InsurancePolicy:
        """
        Create a new insurance policy.

        Args:
            db: Database session
            policy_data: Insurance policy data
            current_user: Username of the current user

        Returns:
            Created insurance policy

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Validate patient exists
            patient = db.query(Patient).filter(
                Patient.id == policy_data.patient_id
            ).first()
            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Patient with ID {policy_data.patient_id} not found"
                )

            # Validate payer exists and is active
            payer = db.query(InsurancePayer).filter(
                InsurancePayer.id == policy_data.payer_id,
                InsurancePayer.is_active == True
            ).first()
            if not payer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Active insurance payer with ID {policy_data.payer_id} not found"
                )

            # Validate type exists and is active
            type_obj = db.query(InsuranceType).filter(
                InsuranceType.id == policy_data.type_id,
                InsuranceType.is_active == True
            ).first()
            if not type_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Active insurance type with ID {policy_data.type_id} not found"
                )

            # Validate date ranges
            if policy_data.coverage_end_date and policy_data.coverage_start_date >= policy_data.coverage_end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coverage end date must be after start date"
                )

            # Check for overlapping active policies of the same type
            overlapping = db.query(InsurancePolicy).filter(
                InsurancePolicy.patient_id == policy_data.patient_id,
                InsurancePolicy.type_id == policy_data.type_id,
                InsurancePolicy.status == "active",
                InsurancePolicy.coverage_start_date <= (policy_data.coverage_end_date or datetime.max),
                or_(
                    InsurancePolicy.coverage_end_date.is_(None),
                    InsurancePolicy.coverage_end_date >= policy_data.coverage_start_date
                )
            ).first()

            if overlapping:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Patient already has an active policy of type '{type_obj.name}' during this period"
                )

            policy = InsurancePolicy(
                **policy_data.model_dump(),
                created_by=current_user,
                updated_by=current_user
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
            
            logger.info(
                f"Insurance policy created: {policy.policy_number} (ID: {policy.id})",
                extra={"user": current_user}
            )
            return policy
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to create insurance policy: {str(e)}",
                extra={"user": current_user}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create insurance policy"
            )

    @staticmethod
    async def get_policy(
        db: Session,
        policy_id: int,
        include_relations: bool = False
    ) -> Optional[InsurancePolicy]:
        """
        Get an insurance policy by ID.

        Args:
            db: Database session
            policy_id: ID of the insurance policy
            include_relations: If True, eagerly load related entities

        Returns:
            Insurance policy if found, None otherwise
        """
        query = db.query(InsurancePolicy)
        
        if include_relations:
            query = query.options(
                joinedload(InsurancePolicy.patient),
                joinedload(InsurancePolicy.payer),
                joinedload(InsurancePolicy.type)
            )
            
        return query.filter(InsurancePolicy.id == policy_id).first()

    @staticmethod
    async def get_policy_by_number(
        db: Session,
        policy_number: str,
        include_relations: bool = False
    ) -> Optional[InsurancePolicy]:
        """
        Get an insurance policy by policy number.

        Args:
            db: Database session
            policy_number: Number of the insurance policy
            include_relations: If True, eagerly load related entities

        Returns:
            Insurance policy if found, None otherwise
        """
        query = db.query(InsurancePolicy)
        
        if include_relations:
            query = query.options(
                joinedload(InsurancePolicy.patient),
                joinedload(InsurancePolicy.payer),
                joinedload(InsurancePolicy.type)
            )
            
        return query.filter(InsurancePolicy.policy_number == policy_number).first()

    @staticmethod
    async def get_policies(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        payer_id: Optional[int] = None,
        type_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        include_relations: bool = False
    ) -> List[InsurancePolicy]:
        """
        Get a list of insurance policies with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by policy status if provided
            payer_id: Filter by payer ID if provided
            type_id: Filter by type ID if provided
            patient_id: Filter by patient ID if provided
            include_relations: If True, eagerly load related entities

        Returns:
            List of insurance policies
        """
        query = db.query(InsurancePolicy)
        
        if include_relations:
            query = query.options(
                joinedload(InsurancePolicy.patient),
                joinedload(InsurancePolicy.payer),
                joinedload(InsurancePolicy.type)
            )
            
        if status:
            query = query.filter(InsurancePolicy.status == status)
            
        if payer_id:
            query = query.filter(InsurancePolicy.payer_id == payer_id)
            
        if type_id:
            query = query.filter(InsurancePolicy.type_id == type_id)
            
        if patient_id:
            query = query.filter(InsurancePolicy.patient_id == patient_id)
            
        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def update_policy(
        db: Session,
        policy_id: int,
        policy_data: InsurancePolicyUpdate,
        current_user: str
    ) -> Optional[InsurancePolicy]:
        """
        Update an insurance policy.

        Args:
            db: Database session
            policy_id: ID of the insurance policy to update
            policy_data: Updated insurance policy data
            current_user: Username of the current user

        Returns:
            Updated insurance policy if found, None otherwise

        Raises:
            HTTPException: If validation fails
        """
        try:
            policy = db.query(InsurancePolicy).filter(
                InsurancePolicy.id == policy_id
            ).first()
            
            if not policy:
                return None

            update_data = policy_data.model_dump(exclude_unset=True)

            # If updating payer, validate it exists and is active
            if "payer_id" in update_data:
                payer = db.query(InsurancePayer).filter(
                    InsurancePayer.id == update_data["payer_id"],
                    InsurancePayer.is_active == True
                ).first()
                if not payer:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Active insurance payer with ID {update_data['payer_id']} not found"
                    )

            # If updating type, validate it exists and is active
            if "type_id" in update_data:
                type_obj = db.query(InsuranceType).filter(
                    InsuranceType.id == update_data["type_id"],
                    InsuranceType.is_active == True
                ).first()
                if not type_obj:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Active insurance type with ID {update_data['type_id']} not found"
                    )

            # If updating dates, validate them
            if "coverage_end_date" in update_data or "coverage_start_date" in update_data:
                start_date = update_data.get("coverage_start_date", policy.coverage_start_date)
                end_date = update_data.get("coverage_end_date", policy.coverage_end_date)
                
                if end_date and start_date >= end_date:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Coverage end date must be after start date"
                    )

                # Check for overlapping active policies of the same type
                overlapping = db.query(InsurancePolicy).filter(
                    InsurancePolicy.patient_id == policy.patient_id,
                    InsurancePolicy.type_id == (update_data.get("type_id") or policy.type_id),
                    InsurancePolicy.status == "active",
                    InsurancePolicy.id != policy_id,
                    InsurancePolicy.coverage_start_date <= (end_date or datetime.max),
                    or_(
                        InsurancePolicy.coverage_end_date.is_(None),
                        InsurancePolicy.coverage_end_date >= start_date
                    )
                ).first()

                if overlapping:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Patient already has an active policy of this type during this period"
                    )

            update_data["updated_by"] = current_user
            update_data["updated_at"] = datetime.utcnow()

            for field, value in update_data.items():
                setattr(policy, field, value)

            db.commit()
            db.refresh(policy)
            
            logger.info(
                f"Insurance policy updated: {policy.policy_number} (ID: {policy.id})",
                extra={"user": current_user}
            )
            return policy
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to update insurance policy: {str(e)}",
                extra={"user": current_user}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update insurance policy"
            )

    @staticmethod
    async def delete_policy(
        db: Session,
        policy_id: int,
        current_user: str
    ) -> bool:
        """
        Delete an insurance policy (soft delete by setting status to 'cancelled').

        Args:
            db: Database session
            policy_id: ID of the insurance policy to delete
            current_user: Username of the current user

        Returns:
            True if policy was deleted, False if not found

        Raises:
            HTTPException: If policy cannot be deleted
        """
        try:
            policy = db.query(InsurancePolicy).filter(
                InsurancePolicy.id == policy_id
            ).first()
            
            if not policy:
                return False

            if policy.status == "cancelled":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Policy is already cancelled"
                )

            policy.status = "cancelled"
            policy.updated_by = current_user
            policy.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(
                f"Insurance policy cancelled: {policy.policy_number} (ID: {policy.id})",
                extra={"user": current_user}
            )
            return True
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to cancel insurance policy: {str(e)}",
                extra={"user": current_user}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel insurance policy"
            )

    @staticmethod
    async def search_policies(
        db: Session,
        search_term: str,
        status: Optional[str] = None,
        limit: int = 10,
        include_relations: bool = True
    ) -> List[InsurancePolicy]:
        """
        Search insurance policies by policy number or patient name.

        Args:
            db: Database session
            search_term: Term to search for in policy number or patient name
            status: Filter by policy status if provided
            limit: Maximum number of records to return
            include_relations: If True, eagerly load related entities

        Returns:
            List of matching insurance policies
        """
        query = db.query(InsurancePolicy).join(
            Patient
        ).filter(
            or_(
                InsurancePolicy.policy_number.ilike(f"%{search_term}%"),
                Patient.first_name.ilike(f"%{search_term}%"),
                Patient.last_name.ilike(f"%{search_term}%")
            )
        )
        
        if include_relations:
            query = query.options(
                joinedload(InsurancePolicy.patient),
                joinedload(InsurancePolicy.payer),
                joinedload(InsurancePolicy.type)
            )
        
        if status:
            query = query.filter(InsurancePolicy.status == status)
            
        return query.limit(limit).all()

    @staticmethod
    async def get_active_policy(
        db: Session,
        patient_id: int,
        type_id: int,
        reference_date: Optional[datetime] = None
    ) -> Optional[InsurancePolicy]:
        """
        Get the active policy for a patient and insurance type at a specific date.

        Args:
            db: Database session
            patient_id: ID of the patient
            type_id: ID of the insurance type
            reference_date: Date to check policy status (defaults to current date)

        Returns:
            Active insurance policy if found, None otherwise
        """
        if reference_date is None:
            reference_date = datetime.utcnow()

        return db.query(InsurancePolicy).filter(
            InsurancePolicy.patient_id == patient_id,
            InsurancePolicy.type_id == type_id,
            InsurancePolicy.status == "active",
            InsurancePolicy.coverage_start_date <= reference_date,
            or_(
                InsurancePolicy.coverage_end_date.is_(None),
                InsurancePolicy.coverage_end_date >= reference_date
            )
        ).first()

    @staticmethod
    async def get_policy_history(
        db: Session,
        patient_id: int,
        type_id: Optional[int] = None,
        include_relations: bool = True
    ) -> List[InsurancePolicy]:
        """
        Get the policy history for a patient, optionally filtered by type.

        Args:
            db: Database session
            patient_id: ID of the patient
            type_id: ID of the insurance type to filter by
            include_relations: If True, eagerly load related entities

        Returns:
            List of insurance policies ordered by start date
        """
        query = db.query(InsurancePolicy).filter(
            InsurancePolicy.patient_id == patient_id
        )
        
        if include_relations:
            query = query.options(
                joinedload(InsurancePolicy.payer),
                joinedload(InsurancePolicy.type)
            )
            
        if type_id:
            query = query.filter(InsurancePolicy.type_id == type_id)
            
        return query.order_by(InsurancePolicy.coverage_start_date.desc()).all()

class InsurancePolicyService(BaseService[InsurancePolicy, InsurancePolicyCreate, InsurancePolicyUpdate]):
    """Service for managing insurance policies"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InsurancePolicy, db)
    
    async def create(self, schema: InsurancePolicyCreate, current_user_id: int, **kwargs) -> InsurancePolicy:
        """Create a new insurance policy"""
        try:
            data = schema.model_dump()
            data.update(kwargs)
            
            # Validate dates
            if data["termination_date"] and data["effective_date"] >= data["termination_date"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Effective date must be before termination date"
                )
            
            # Check for active policies for same customer and plan
            active_policy = await self.db.execute(
                select(self.model).where(
                    and_(
                        self.model.customer_id == data["customer_id"],
                        self.model.insurance_plan_id == data["insurance_plan_id"],
                        self.model.is_active == True,
                        or_(
                            self.model.termination_date.is_(None),
                            self.model.termination_date >= func.current_date()
                        )
                    )
                )
            )
            if active_policy.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An active policy already exists for this customer and plan"
                )
            
            obj = self.model(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
            
        except Exception as e:
            logger.error(f"Error creating insurance policy: {str(e)}")
            await self.db.rollback()
            raise

    async def get_active_policies(self, customer_id: int) -> List[InsurancePolicy]:
        """Get all active policies for a customer"""
        try:
            stmt = select(self.model).where(
                and_(
                    self.model.customer_id == customer_id,
                    self.model.is_active == True,
                    or_(
                        self.model.termination_date.is_(None),
                        self.model.termination_date >= func.current_date()
                    )
                )
            )
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting active policies: {str(e)}")
            raise

class InsuranceCoverageService(BaseService[InsuranceCoverage, InsuranceCoverageCreate, InsuranceCoverageUpdate]):
    """Service for managing insurance coverage"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InsuranceCoverage, db)
    
    async def create(self, schema: InsuranceCoverageCreate, current_user_id: int, **kwargs) -> InsuranceCoverage:
        """Create a new insurance coverage"""
        try:
            data = schema.model_dump()
            data.update(kwargs)
            
            # Validate dates
            if data["end_date"] and data["effective_date"] >= data["end_date"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Effective date must be before end date"
                )
            
            # Check for overlapping coverage
            overlapping = await self.db.execute(
                select(self.model).where(
                    and_(
                        self.model.policy_id == data["policy_id"],
                        self.model.service_type == data["service_type"],
                        self.model.is_active == True,
                        or_(
                            and_(
                                self.model.effective_date <= data["effective_date"],
                                or_(
                                    self.model.end_date.is_(None),
                                    self.model.end_date >= data["effective_date"]
                                )
                            ),
                            and_(
                                self.model.effective_date <= data["end_date"],
                                or_(
                                    self.model.end_date.is_(None),
                                    self.model.end_date >= data["end_date"]
                                )
                            ) if data["end_date"] else True
                        )
                    )
                )
            )
            if overlapping.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Overlapping coverage exists for this policy and service type"
                )
            
            obj = self.model(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
            
        except Exception as e:
            logger.error(f"Error creating insurance coverage: {str(e)}")
            await self.db.rollback()
            raise

    async def get_active_coverage(
        self,
        policy_id: int,
        service_type: Optional[str] = None,
        as_of_date: Optional[date] = None
    ) -> List[InsuranceCoverage]:
        """Get active coverage for a policy"""
        try:
            conditions = [
                self.model.policy_id == policy_id,
                self.model.is_active == True
            ]
            
            if service_type:
                conditions.append(self.model.service_type == service_type)
            
            if as_of_date:
                conditions.extend([
                    self.model.effective_date <= as_of_date,
                    or_(
                        self.model.end_date.is_(None),
                        self.model.end_date >= as_of_date
                    )
                ])
            
            stmt = select(self.model).where(and_(*conditions))
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting active coverage: {str(e)}")
            raise

class InsuranceCompanyGroupService:
    """Service for managing insurance company groups"""

    @staticmethod
    async def create_group(
        db: Session,
        group_data: InsuranceCompanyGroupCreate,
        current_user: str
    ) -> InsuranceCompanyGroupInDB:
        """
        Create a new insurance company group.

        Args:
            db: Database session
            group_data: Insurance company group data
            current_user: Username of the current user

        Returns:
            Created insurance company group

        Raises:
            HTTPException: If parent group not found when specified
        """
        try:
            # Validate parent group if specified
            if group_data.parent_group_id:
                parent_group = db.query(InsuranceCompanyGroup).filter(
                    InsuranceCompanyGroup.id == group_data.parent_group_id
                ).first()
                if not parent_group:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Parent group with ID {group_data.parent_group_id} not found"
                    )

            group = InsuranceCompanyGroup(
                **group_data.model_dump(),
                created_by=current_user,
                updated_by=current_user
            )
            db.add(group)
            db.commit()
            db.refresh(group)
            
            logger.info(
                f"Insurance company group created: {group.name} (ID: {group.id})",
                extra={"user": current_user}
            )
            return InsuranceCompanyGroupInDB.model_validate(group)
            
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Failed to create insurance company group: {str(e)}",
                extra={"user": current_user}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create insurance company group"
            )

    @staticmethod
    async def get_group(
        db: Session,
        group_id: int
    ) -> Optional[InsuranceCompanyGroupInDB]:
        """
        Get an insurance company group by ID.

        Args:
            db: Database session
            group_id: ID of the insurance company group

        Returns:
            Insurance company group if found, None otherwise
        """
        group = db.query(InsuranceCompanyGroup).filter(
            InsuranceCompanyGroup.id == group_id
        ).first()
        
        if not group:
            return None
            
        return InsuranceCompanyGroupInDB.model_validate(group)

    @staticmethod
    async def get_groups(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        parent_group_id: Optional[int] = None
    ) -> List[InsuranceCompanyGroupInDB]:
        """
        Get a list of insurance company groups with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status if provided
            parent_group_id: Filter by parent group ID if provided

        Returns:
            List of insurance company groups
        """
        query = db.query(InsuranceCompanyGroup)
        
        if is_active is not None:
            query = query.filter(InsuranceCompanyGroup.is_active == is_active)
            
        if parent_group_id is not None:
            query = query.filter(InsuranceCompanyGroup.parent_group_id == parent_group_id)
            
        groups = query.offset(skip).limit(limit).all()
        return [InsuranceCompanyGroupInDB.model_validate(g) for g in groups]

    @staticmethod
    async def update_group(
        db: Session,
        group_id: int,
        group_data: InsuranceCompanyGroupUpdate,
        current_user: str
    ) -> Optional[InsuranceCompanyGroupInDB]:
        """
        Update an insurance company group.

        Args:
            db: Database session
            group_id: ID of the insurance company group to update
            group_data: Updated insurance company group data
            current_user: Username of the current user

        Returns:
            Updated insurance company group if found, None otherwise

        Raises:
            HTTPException: If update fails or creates circular reference
        """
        try:
            group = db.query(InsuranceCompanyGroup).filter(
                InsuranceCompanyGroup.id == group_id
            ).first()
            
            if not group:
                return None

            # Prevent circular parent-child relationships
            if group_data.parent_group_id:
                if group_data.parent_group_id == group_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Group cannot be its own parent"
                    )
                
                # Check if the new parent is actually a child of this group
                current_group = db.query(InsuranceCompanyGroup).filter(
                    InsuranceCompanyGroup.id == group_data.parent_group_id
                ).first()
                
                if current_group and current_group.parent_group_id == group_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot create circular group reference"
                    )

            update_data = group_data.model_dump(exclude_unset=True)
            update_data["updated_by"] = current_user
            update_data["updated_at"] = datetime.utcnow()

            for field, value in update_data.items():
                setattr(group, field, value)

            db.commit()
            db.refresh(group)
            
            logger.info(
                f"Insurance company group updated: {group.name} (ID: {group.id})",
                extra={"user": current_user}
            )
            return InsuranceCompanyGroupInDB.model_validate(group)
            
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Failed to update insurance company group: {str(e)}",
                extra={"user": current_user}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update insurance company group"
            )

    @staticmethod
    async def delete_group(
        db: Session,
        group_id: int,
        current_user: str
    ) -> bool:
        """
        Delete an insurance company group (soft delete by setting is_active=False).

        Args:
            db: Database session
            group_id: ID of the insurance company group to delete
            current_user: Username of the current user

        Returns:
            True if group was deleted, False if not found
        """
        group = db.query(InsuranceCompanyGroup).filter(
            InsuranceCompanyGroup.id == group_id
        ).first()
        
        if not group:
            return False

        # Also deactivate all child groups
        child_groups = db.query(InsuranceCompanyGroup).filter(
            InsuranceCompanyGroup.parent_group_id == group_id
        ).all()
        
        for child in child_groups:
            child.is_active = False
            child.updated_by = current_user
            child.updated_at = datetime.utcnow()

        group.is_active = False
        group.updated_by = current_user
        group.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            f"Insurance company group deactivated: {group.name} (ID: {group.id})",
            extra={"user": current_user}
        )
        return True

    @staticmethod
    async def get_group_hierarchy(
        db: Session,
        group_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the complete hierarchy for a group, including parents and children.

        Args:
            db: Database session
            group_id: ID of the insurance company group

        Returns:
            Dictionary containing group hierarchy if found, None otherwise
        """
        group = db.query(InsuranceCompanyGroup).filter(
            InsuranceCompanyGroup.id == group_id
        ).first()
        
        if not group:
            return None

        def build_hierarchy(group: InsuranceCompanyGroup) -> Dict[str, Any]:
            return {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "is_active": group.is_active,
                "children": [
                    build_hierarchy(child)
                    for child in group.child_groups
                    if child.is_active
                ]
            }

        # Get parent hierarchy
        parents = []
        current = group.parent_group
        while current and current.is_active:
            parents.append({
                "id": current.id,
                "name": current.name
            })
            current = current.parent_group

        return {
            "group": build_hierarchy(group),
            "parents": list(reversed(parents))
        }
