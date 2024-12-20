"""
Procedure to fix and update order policies based on current business rules.

This procedure ensures all orders have correct policy assignments and
updates any outdated or missing policy references.
"""
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.order import Order, OrderPolicy
from app.models.customer import Customer, CustomerPolicy
from app.core.exceptions import ProcedureError

class OrderPolicyFixer:
    """Handles fixing and updating order policies"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_customer_policy(self, customer_id: int) -> Optional[CustomerPolicy]:
        """Get active policy for customer"""
        return (
            self.db.query(CustomerPolicy)
            .filter(
                and_(
                    CustomerPolicy.customer_id == customer_id,
                    CustomerPolicy.is_active == True
                )
            )
            .first()
        )
        
    def _get_orders_without_policy(self) -> List[Order]:
        """Get all orders missing policy assignments"""
        return (
            self.db.query(Order)
            .outerjoin(OrderPolicy)
            .filter(OrderPolicy.id.is_(None))
            .all()
        )
        
    def _get_orders_with_inactive_policy(self) -> List[Order]:
        """Get orders with inactive policy assignments"""
        return (
            self.db.query(Order)
            .join(OrderPolicy)
            .filter(OrderPolicy.is_active == False)
            .all()
        )
        
    def _create_order_policy(
        self,
        order: Order,
        customer_policy: CustomerPolicy
    ) -> None:
        """Create new order policy from customer policy"""
        policy = OrderPolicy(
            order_id=order.id,
            customer_id=order.customer_id,
            policy_type=customer_policy.policy_type,
            billing_cycle=customer_policy.billing_cycle,
            payment_terms=customer_policy.payment_terms,
            discount_percent=customer_policy.discount_percent,
            is_active=True
        )
        self.db.add(policy)
        
    def _update_order_policy(
        self,
        order: Order,
        customer_policy: CustomerPolicy
    ) -> None:
        """Update existing order policy from customer policy"""
        policy = (
            self.db.query(OrderPolicy)
            .filter(OrderPolicy.order_id == order.id)
            .first()
        )
        
        if policy:
            policy.policy_type = customer_policy.policy_type
            policy.billing_cycle = customer_policy.billing_cycle
            policy.payment_terms = customer_policy.payment_terms
            policy.discount_percent = customer_policy.discount_percent
            policy.is_active = True
        
    def _execute(self) -> None:
        """
        Fix order policies
        
        This will:
        1. Assign policies to orders missing them
        2. Update orders with inactive policies
        3. Sync policy details with current customer policies
        """
        # Handle orders without policies
        orders = self._get_orders_without_policy()
        for order in orders:
            customer_policy = self._get_customer_policy(order.customer_id)
            if customer_policy:
                self._create_order_policy(order, customer_policy)
                
        # Handle orders with inactive policies
        orders = self._get_orders_with_inactive_policy()
        for order in orders:
            customer_policy = self._get_customer_policy(order.customer_id)
            if customer_policy:
                self._update_order_policy(order, customer_policy)
                
        self.db.commit()
        
    @classmethod
    def execute(cls, db: Session) -> None:
        """
        Fix order policies
        
        Args:
            db: Database session
        """
        procedure = cls(db)
        procedure._execute()
