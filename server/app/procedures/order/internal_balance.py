"""
Internal procedure to update order balance calculations.

This procedure recalculates order balances based on invoice amounts,
payments, and other financial transactions.
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.models.order import Order, OrderDetails
from app.models.invoice import Invoice, InvoiceDetails, InvoiceTransaction
from app.core.exceptions import ProcedureError

class OrderInternalBalance:
    """Handles internal order balance calculations"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_invoice_totals(self, order_id: int) -> tuple[Decimal, Decimal]:
        """Get total invoice amounts and payments for an order"""
        result = (
            self.db.query(
                func.sum(InvoiceDetails.amount).label('total_amount'),
                func.sum(InvoiceTransaction.amount).label('total_paid')
            )
            .join(Invoice, and_(
                Invoice.customer_id == InvoiceDetails.customer_id,
                Invoice.id == InvoiceDetails.invoice_id
            ))
            .outerjoin(InvoiceTransaction, and_(
                InvoiceTransaction.customer_id == InvoiceDetails.customer_id,
                InvoiceTransaction.invoice_id == InvoiceDetails.invoice_id,
                InvoiceTransaction.invoice_details_id == InvoiceDetails.id
            ))
            .filter(
                Invoice.order_id == order_id,
                InvoiceDetails.status != 'Void'
            )
            .first()
        )
        
        return (
            result.total_amount or Decimal('0.00'),
            result.total_paid or Decimal('0.00')
        )
        
    def _get_order_quantities(self, order_id: int) -> tuple[int, int]:
        """Get total ordered and fulfilled quantities for an order"""
        result = (
            self.db.query(
                func.sum(OrderDetails.ordered_quantity).label('ordered'),
                func.sum(OrderDetails.fulfilled_quantity).label('fulfilled')
            )
            .filter(
                OrderDetails.order_id == order_id,
                OrderDetails.is_active == True
            )
            .first()
        )
        
        return (
            result.ordered or 0,
            result.fulfilled or 0
        )
        
    def _execute(self, order_id: int) -> None:
        """
        Update order balance calculations
        
        Args:
            order_id: ID of order to update
        """
        # Get order
        order = self.db.query(Order).get(order_id)
        if not order:
            raise ProcedureError(f"Order {order_id} not found")
            
        # Get invoice totals
        total_amount, total_paid = self._get_invoice_totals(order_id)
        
        # Get quantities
        ordered_qty, fulfilled_qty = self._get_order_quantities(order_id)
        
        # Update order
        order.total_amount = total_amount
        order.payment_amount = total_paid
        order.balance_amount = total_amount - total_paid
        order.ordered_quantity = ordered_qty
        order.fulfilled_quantity = fulfilled_qty
        
        # Update status based on quantities and balance
        if fulfilled_qty >= ordered_qty and order.balance_amount <= Decimal('0.00'):
            order.status = 'Closed'
        elif fulfilled_qty > 0:
            order.status = 'Partial'
        else:
            order.status = 'Open'
            
        self.db.commit()
        
    @classmethod
    def execute(cls, db: Session, order_id: int) -> None:
        """
        Update order balance calculations
        
        Args:
            db: Database session
            order_id: ID of order to update
        """
        procedure = cls(db)
        procedure._execute(order_id)
