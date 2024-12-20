"""
Procedure to update purchase order totals and related calculations.

This procedure recalculates all monetary totals for a purchase order,
including line items, taxes, shipping, and discounts.
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.models.inventory import PurchaseOrder, PurchaseOrderLine
from app.core.exceptions import ProcedureError

class PurchaseOrderTotals:
    """Handles purchase order total calculations"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_line_totals(self, po_id: int) -> Decimal:
        """Calculate sum of all line item totals"""
        result = (
            self.db.query(func.sum(PurchaseOrderLine.total_price))
            .filter(
                and_(
                    PurchaseOrderLine.purchase_order_id == po_id,
                    PurchaseOrderLine.is_active == True
                )
            )
            .scalar()
        )
        return result or Decimal('0.00')
        
    def _calculate_tax(
        self,
        subtotal: Decimal,
        tax_rate: Optional[Decimal]
    ) -> Decimal:
        """Calculate tax amount"""
        if not tax_rate:
            return Decimal('0.00')
            
        return (subtotal * tax_rate).quantize(Decimal('0.01'))
        
    def _calculate_discount(
        self,
        subtotal: Decimal,
        discount_percent: Optional[Decimal],
        discount_amount: Optional[Decimal]
    ) -> Decimal:
        """Calculate total discount"""
        total_discount = Decimal('0.00')
        
        # Apply percentage discount if any
        if discount_percent:
            total_discount += (subtotal * discount_percent / 100)
            
        # Add flat discount if any
        if discount_amount:
            total_discount += discount_amount
            
        return total_discount.quantize(Decimal('0.01'))
        
    def _execute(self, purchase_order_id: int) -> None:
        """
        Update purchase order totals
        
        Args:
            purchase_order_id: ID of purchase order to update
            
        Raises:
            ProcedureError: If purchase order not found
        """
        # Get purchase order
        po = self.db.query(PurchaseOrder).get(purchase_order_id)
        if not po:
            raise ProcedureError(f"Purchase order {purchase_order_id} not found")
            
        # Calculate line item totals
        subtotal = self._get_line_totals(purchase_order_id)
        
        # Calculate tax
        tax_amount = self._calculate_tax(subtotal, po.tax_rate)
        
        # Calculate discount
        discount_amount = self._calculate_discount(
            subtotal,
            po.discount_percent,
            po.discount_amount
        )
        
        # Calculate shipping
        shipping_amount = po.shipping_amount or Decimal('0.00')
        
        # Update PO totals
        po.subtotal = subtotal
        po.tax_amount = tax_amount
        po.total_discount = discount_amount
        po.total_amount = (
            subtotal
            + tax_amount
            + shipping_amount
            - discount_amount
        ).quantize(Decimal('0.01'))
        
        self.db.commit()
        
    @classmethod
    def execute(cls, db: Session, purchase_order_id: int) -> None:
        """
        Update purchase order totals
        
        Args:
            db: Database session
            purchase_order_id: ID of purchase order to update
        """
        procedure = cls(db)
        procedure._execute(purchase_order_id)
