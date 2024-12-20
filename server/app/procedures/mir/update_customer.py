from typing import Optional, List
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.customer import Customer, CustomerInsurance
from app.models.order import Order
from app.models.invoice import InvoiceTransaction
from datetime import datetime, timedelta

class CustomerMIRUpdater:
    """Updates Medical Information Records (MIR) for customers"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _validate_customer(self, customer: Customer) -> List[str]:
        """Validate customer data and return list of issues"""
        issues = []
        
        # Required fields
        if not customer.first_name:
            issues.append("FirstName")
        if not customer.last_name:
            issues.append("LastName")
        if not customer.address1:
            issues.append("Address1")
        if not customer.city:
            issues.append("City")
        if not customer.state:
            issues.append("State")
        if not customer.zip_code:
            issues.append("ZipCode")
            
        # Phone number validation
        if customer.phone and len(customer.phone.replace('-', '').replace('(', '').replace(')', '')) != 10:
            issues.append("Phone.Invalid")
            
        # Active customer checks
        if customer.is_active:
            # Must have at least one active insurance
            insurance_count = (
                self.db.query(func.count(CustomerInsurance.id))
                .filter(
                    and_(
                        CustomerInsurance.customer_id == customer.id,
                        CustomerInsurance.is_active == True
                    )
                )
                .scalar()
            )
            if insurance_count == 0:
                issues.append("NoActiveInsurance")
                
            # Check for recent orders
            recent_order_count = (
                self.db.query(func.count(Order.id))
                .filter(
                    and_(
                        Order.customer_id == customer.id,
                        Order.order_date >= func.date_sub(func.now(), interval='180 day')
                    )
                )
                .scalar()
            )
            if recent_order_count == 0:
                issues.append("NoRecentOrders")
                
            # Check for outstanding balance
            outstanding_balance = (
                self.db.query(func.sum(InvoiceTransaction.amount))
                .filter(
                    and_(
                        InvoiceTransaction.customer_id == customer.id,
                        InvoiceTransaction.transaction_date <= func.date_sub(func.now(), interval='90 day'),
                        InvoiceTransaction.is_paid == False
                    )
                )
                .scalar() or 0
            )
            if outstanding_balance > 0:
                issues.append("OutstandingBalance")
                
            # Demographic validation
            if not customer.date_of_birth:
                issues.append("NoDOB")
            if not customer.gender:
                issues.append("NoGender")
                
        return issues
        
    def _execute(self, customer_id: Optional[int] = None) -> None:
        """
        Update MIR records for customers
        
        Args:
            customer_id: Optional ID of specific customer to update. If None, updates all.
        """
        try:
            # Build base query
            query = self.db.query(Customer)
            
            # Filter by customer ID if provided
            if customer_id is not None:
                query = query.filter(Customer.id == customer_id)
                
            # Update MIR info for matching customers
            customers = query.all()
            for customer in customers:
                # Validate customer and update MIR
                issues = self._validate_customer(customer)
                customer.mir = ','.join(issues) if issues else None
                
            self.db.commit()
            logger.info(f"Updated MIR for {len(customers)} customers")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating customer MIR: {str(e)}")
            raise
            
    @classmethod
    def execute(cls, db: Session, customer_id: Optional[int] = None) -> None:
        """
        Execute the customer MIR update procedure
        
        Args:
            db: Database session
            customer_id: Optional ID of specific customer to update
        """
        updater = cls(db)
        updater._execute(customer_id)
