"""
Customer Management Services
Version: 2024-12-14_19-14

This module implements services for the Customer Management domain.
"""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, func
from sqlalchemy import Decimal
from datetime import datetime

from app.core.service import BaseService
from app.models.customer import (
    Customer,
    CustomerAddress,
    InsuranceCompany,
    InsurancePlan,
    CustomerInsurance,
    CustomerStatusHistory,
    Order,
    OrderStatus,
    Payment,
    PaymentStatus,
    CustomerStatus
)
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerAddressCreate,
    CustomerAddressUpdate,
    InsuranceCompanyCreate,
    InsuranceCompanyUpdate,
    InsurancePlanCreate,
    InsurancePlanUpdate,
    CustomerInsuranceCreate,
    CustomerInsuranceUpdate
)
from app.core.logging import logger

class CustomerService(BaseService[Customer, CustomerCreate, CustomerUpdate]):
    """Service for managing customers"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Customer, db)
    
    async def create(self, schema: CustomerCreate, current_user_id: int, **kwargs) -> Customer:
        """Create a new customer"""
        try:
            # Check for duplicate customer by SSN/Tax ID
            if schema.ssn_tax_id:
                query = select(Customer).where(Customer.ssn_tax_id == schema.ssn_tax_id)
                result = await self.db.execute(query)
                if result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Customer with this SSN/Tax ID already exists"
                    )
            
            # Create customer
            data = schema.model_dump()
            data.update(kwargs)
            db_customer = Customer(**data)
            self.db.add(db_customer)
            
            await self.db.commit()
            await self.db.refresh(db_customer)
            
            logger.info(f"Created new customer: {db_customer.id}")
            return db_customer
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create customer"
            ) from e
    
    async def get_customer_addresses(self, customer_id: int) -> List[CustomerAddress]:
        """Get all addresses for a customer"""
        try:
            customer = await self.get(customer_id)
            return customer.addresses
        except Exception as e:
            logger.error(f"Error retrieving customer addresses: {str(e)}")
            return []
    
    async def get_customer_insurance(self, customer_id: int) -> List[CustomerInsurance]:
        """Get all insurance information for a customer"""
        try:
            customer = await self.get(customer_id)
            return customer.insurance_info
        except Exception as e:
            logger.error(f"Error retrieving customer insurance: {str(e)}")
            return []
    
    async def search_customers(
        self,
        search_term: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Customer]:
        """Search customers by name, email, or phone"""
        try:
            query = select(Customer).where(
                Customer.search_vector.match(search_term)
            ).limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching customers: {str(e)}")
            return []

    async def update(self, id: int, customer_update: CustomerUpdate) -> Customer:
        """Update a customer"""
        try:
            db_customer = await self.get(id)
            if not db_customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )
            
            # Update customer
            data = customer_update.model_dump()
            for key, value in data.items():
                setattr(db_customer, key, value)
            
            await self.db.commit()
            await self.db.refresh(db_customer)
            
            logger.info(f"Updated customer: {db_customer.id}")
            return db_customer
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update customer"
            ) from e

    async def verify_insurance(
        self,
        customer_id: int,
        insurance_id: int,
        verification_date: Optional[datetime] = None
    ) -> CustomerInsurance:
        """Verify customer insurance information"""
        try:
            # Get customer insurance record
            insurance = await self.db.get(CustomerInsurance, insurance_id)
            if not insurance or insurance.customer_id != customer_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Insurance record not found"
                )
            
            # Check if insurance is expired
            if insurance.expiry_date and insurance.expiry_date < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insurance has expired"
                )
            
            # Update verification status
            insurance.verified = True
            insurance.last_verified = verification_date or datetime.now()
            insurance.verification_notes = "Verified successfully"
            
            await self.db.commit()
            await self.db.refresh(insurance)
            
            logger.info(f"Verified insurance for customer: {customer_id}")
            return insurance
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying insurance: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not verify insurance"
            ) from e

    async def update_customer_status(
        self,
        customer_id: int,
        new_status: CustomerStatus,
        reason: str,
        current_user_id: int
    ) -> Customer:
        """Update customer status with audit trail"""
        try:
            customer = await self.get(customer_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )
            
            # Create status history record
            status_history = CustomerStatusHistory(
                customer_id=customer_id,
                old_status=customer.status,
                new_status=new_status,
                reason=reason,
                changed_by=current_user_id
            )
            self.db.add(status_history)
            
            # Update customer status
            customer.status = new_status
            customer.last_status_change = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(customer)
            
            logger.info(f"Updated status for customer: {customer_id}")
            return customer
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating customer status: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update customer status"
            ) from e

    async def merge_customer_records(
        self,
        primary_id: int,
        secondary_id: int,
        current_user_id: int
    ) -> Customer:
        """Merge two customer records, keeping the primary and archiving the secondary"""
        try:
            # Get both customers
            primary = await self.get(primary_id)
            secondary = await self.get(secondary_id)
            
            if not primary or not secondary:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or both customers not found"
                )
            
            # Begin merging process
            # 1. Update orders
            await self.db.execute(
                update(Order)
                .where(Order.customer_id == secondary_id)
                .values(customer_id=primary_id)
            )
            
            # 2. Update insurance records
            await self.db.execute(
                update(CustomerInsurance)
                .where(CustomerInsurance.customer_id == secondary_id)
                .values(customer_id=primary_id)
            )
            
            # 3. Update addresses
            await self.db.execute(
                update(CustomerAddress)
                .where(CustomerAddress.customer_id == secondary_id)
                .values(customer_id=primary_id)
            )
            
            # 4. Archive secondary customer
            await self.archive_customer(secondary_id, f"Merged into customer {primary_id}")
            
            # 5. Add merge note to primary customer
            primary.notes = (primary.notes or "") + f"\nMerged with customer {secondary_id}"
            
            await self.db.commit()
            await self.db.refresh(primary)
            
            logger.info(f"Merged customer {secondary_id} into {primary_id}")
            return primary
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error merging customers: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not merge customer records"
            ) from e

    async def archive_customer(
        self,
        customer_id: int,
        reason: str,
        archive_related: bool = True
    ) -> None:
        """Archive a customer and optionally their related records"""
        try:
            customer = await self.get(customer_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )
            
            # Archive customer
            customer.status = CustomerStatus.ARCHIVED
            customer.archived_date = datetime.now()
            customer.archive_reason = reason
            
            if archive_related:
                # Archive addresses
                await self.db.execute(
                    update(CustomerAddress)
                    .where(CustomerAddress.customer_id == customer_id)
                    .values(archived=True, archived_date=datetime.now())
                )
                
                # Archive insurance records
                await self.db.execute(
                    update(CustomerInsurance)
                    .where(CustomerInsurance.customer_id == customer_id)
                    .values(archived=True, archived_date=datetime.now())
                )
            
            await self.db.commit()
            
            logger.info(f"Archived customer: {customer_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error archiving customer: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not archive customer"
            ) from e

    async def calculate_customer_balance(
        self,
        customer_id: int,
        as_of_date: Optional[datetime] = None
    ) -> Decimal:
        """Calculate customer's current balance including all charges and payments"""
        try:
            customer = await self.get(customer_id)
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )
            
            # Set as_of_date to now if not provided
            as_of_date = as_of_date or datetime.now()
            
            # Calculate total charges
            charges_query = select(func.sum(Order.total_amount)).where(
                and_(
                    Order.customer_id == customer_id,
                    Order.created_at <= as_of_date,
                    Order.status.in_([
                        OrderStatus.COMPLETED,
                        OrderStatus.PENDING_PAYMENT
                    ])
                )
            )
            result = await self.db.execute(charges_query)
            total_charges = result.scalar_one_or_none() or Decimal('0')
            
            # Calculate total payments
            payments_query = select(func.sum(Payment.amount)).where(
                and_(
                    Payment.customer_id == customer_id,
                    Payment.payment_date <= as_of_date,
                    Payment.status == PaymentStatus.COMPLETED
                )
            )
            result = await self.db.execute(payments_query)
            total_payments = result.scalar_one_or_none() or Decimal('0')
            
            # Calculate balance
            balance = total_charges - total_payments
            
            logger.info(f"Calculated balance for customer: {customer_id}")
            return balance
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calculating customer balance: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not calculate customer balance"
            ) from e

class CustomerAddressService(BaseService[CustomerAddress, CustomerAddressCreate, CustomerAddressUpdate]):
    """Service for managing customer addresses"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(CustomerAddress, db)
    
    async def create(self, schema: CustomerAddressCreate, current_user_id: int, **kwargs) -> CustomerAddress:
        """Create a new customer address"""
        try:
            # If this is primary address, unset other primary addresses
            if schema.is_primary:
                query = select(CustomerAddress).where(
                    and_(
                        CustomerAddress.customer_id == schema.customer_id,
                        CustomerAddress.is_primary == True
                    )
                )
                result = await self.db.execute(query)
                existing_primary = result.scalar_one_or_none()
                if existing_primary:
                    existing_primary.is_primary = False
            
            # Create address
            data = schema.model_dump()
            data.update(kwargs)
            db_address = CustomerAddress(**data)
            self.db.add(db_address)
            
            await self.db.commit()
            await self.db.refresh(db_address)
            
            logger.info(f"Created new customer address: {db_address.id}")
            return db_address
            
        except Exception as e:
            logger.error(f"Error creating customer address: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create customer address"
            ) from e

class InsuranceCompanyService(BaseService[InsuranceCompany, InsuranceCompanyCreate, InsuranceCompanyUpdate]):
    """Service for managing insurance companies"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InsuranceCompany, db)
    
    async def create(self, schema: InsuranceCompanyCreate, current_user_id: int, **kwargs) -> InsuranceCompany:
        """Create a new insurance company"""
        try:
            # Check for duplicate company
            query = select(InsuranceCompany).where(InsuranceCompany.name == schema.name)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insurance company with this name already exists"
                )
            
            # Create company
            data = schema.model_dump()
            data.update(kwargs)
            db_company = InsuranceCompany(**data)
            self.db.add(db_company)
            
            await self.db.commit()
            await self.db.refresh(db_company)
            
            logger.info(f"Created new insurance company: {db_company.name}")
            return db_company
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating insurance company: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create insurance company"
            ) from e
    
    async def get_company_plans(self, company_id: int) -> List[InsurancePlan]:
        """Get all plans for an insurance company"""
        try:
            company = await self.get(company_id)
            return company.plans
        except Exception as e:
            logger.error(f"Error retrieving company plans: {str(e)}")
            return []

class InsurancePlanService(BaseService[InsurancePlan, InsurancePlanCreate, InsurancePlanUpdate]):
    """Service for managing insurance plans"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InsurancePlan, db)
    
    async def create(self, schema: InsurancePlanCreate, current_user_id: int, **kwargs) -> InsurancePlan:
        """Create a new insurance plan"""
        try:
            # Check for duplicate plan
            query = select(InsurancePlan).where(
                and_(
                    InsurancePlan.company_id == schema.company_id,
                    InsurancePlan.plan_number == schema.plan_number
                )
            )
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insurance plan with this number already exists for this company"
                )
            
            # Create plan
            data = schema.model_dump()
            data.update(kwargs)
            db_plan = InsurancePlan(**data)
            self.db.add(db_plan)
            
            await self.db.commit()
            await self.db.refresh(db_plan)
            
            logger.info(f"Created new insurance plan: {db_plan.plan_number}")
            return db_plan
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating insurance plan: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create insurance plan"
            ) from e

class CustomerInsuranceService(BaseService[CustomerInsurance, CustomerInsuranceCreate, CustomerInsuranceUpdate]):
    """Service for managing customer insurance information"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(CustomerInsurance, db)
    
    async def create(self, schema: CustomerInsuranceCreate, current_user_id: int, **kwargs) -> CustomerInsurance:
        """Create new customer insurance information"""
        try:
            # If this is primary insurance, unset other primary insurance
            if schema.is_primary:
                query = select(CustomerInsurance).where(
                    and_(
                        CustomerInsurance.customer_id == schema.customer_id,
                        CustomerInsurance.is_primary == True
                    )
                )
                result = await self.db.execute(query)
                existing_primary = result.scalar_one_or_none()
                if existing_primary:
                    existing_primary.is_primary = False
            
            # Create insurance info
            data = schema.model_dump()
            data.update(kwargs)
            db_insurance = CustomerInsurance(**data)
            self.db.add(db_insurance)
            
            await self.db.commit()
            await self.db.refresh(db_insurance)
            
            logger.info(f"Created new customer insurance: {db_insurance.id}")
            return db_insurance
            
        except Exception as e:
            logger.error(f"Error creating customer insurance: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create customer insurance"
            ) from e
    
    async def verify_insurance(self, insurance_id: int) -> bool:
        """Verify insurance information with provider"""
        try:
            insurance = await self.get(insurance_id)
            # TODO: Implement actual verification logic with provider's API
            logger.info(f"Verified insurance for customer: {insurance.customer_id}")
            return True
        except Exception as e:
            logger.error(f"Error verifying insurance: {str(e)}")
            return False
