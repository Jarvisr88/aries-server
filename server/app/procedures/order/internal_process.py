"""
Internal order processing procedure that handles invoice generation and updates.

This procedure processes orders and generates invoices based on billing parameters,
taking into account various conditions that may affect billing such as insurance,
modifiers, and billing frequency.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.order import Order, OrderDetails
from app.models.invoice import Invoice, InvoiceDetails
from app.models.customer import CustomerInsurance
from app.models.inventory import InventoryItem
from app.models.pricing import PriceCode
from app.procedures.order.order_must_be_skipped import order_must_be_skipped
from app.procedures.invoice.invoice_must_be_skipped import invoice_must_be_skipped
from app.procedures.scheduling.next_dos_to import get_next_dos_to
from app.procedures.invoice.invoice_modifier import get_invoice_modifier
from app.procedures.order.order_must_be_closed import order_must_be_closed
from app.procedures.order.convert_deposits import OrderDepositConverter
from app.core.exceptions import ProcedureError

class OrderInternalProcess:
    """Handles internal order processing and invoice generation"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_order_details(self, order_id: int, billing_month: int, billing_flags: int) -> list:
        """Get order details that need to be processed"""
        return (
            self.db.query(OrderDetails)
            .join(Order)
            .join(PriceCode)
            .filter(
                OrderDetails.order_id == order_id,
                OrderDetails.is_active == True,
                OrderDetails.billing_month == billing_month,
                # Complex billing flags calculation
                ((Order.customer_insurance1_id.isnot(None) & OrderDetails.bill_ins1) * 1 +
                 (Order.customer_insurance2_id.isnot(None) & OrderDetails.bill_ins2) * 2 +
                 (Order.customer_insurance3_id.isnot(None) & OrderDetails.bill_ins3) * 4 +
                 (Order.customer_insurance4_id.isnot(None) & OrderDetails.bill_ins4) * 8 +
                 (OrderDetails.end_date.isnot(None)) * 32 +
                 (OrderDetails.accept_assignment == True) * 16) == billing_flags,
                OrderDetails.mir.is_(None) | (OrderDetails.mir == '')
            )
            .all()
        )
        
    def _create_invoice(self, order: Order, invoice_date: datetime) -> Invoice:
        """Create a new invoice for the order"""
        invoice = Invoice(
            customer_id=order.customer_id,
            order_id=order.id,
            date=invoice_date,
            status='Open',
            last_update_user_id=1
        )
        self.db.add(invoice)
        self.db.flush()
        return invoice
        
    def _create_invoice_detail(self, 
                             invoice: Invoice,
                             order_detail: OrderDetails,
                             dos_from: datetime,
                             dos_to: datetime,
                             amount: Decimal) -> InvoiceDetails:
        """Create a new invoice detail line item"""
        return InvoiceDetails(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            order_id=invoice.order_id,
            order_details_id=order_detail.id,
            inventory_item_id=order_detail.inventory_item_id,
            dos_from=dos_from,
            dos_to=dos_to,
            quantity=order_detail.billed_quantity,
            amount=amount,
            status='Open',
            last_update_user_id=1
        )
        
    def _execute(self,
                order_id: int,
                billing_month: int,
                billing_flags: int,
                invoice_date: datetime) -> Optional[int]:
        """
        Process an order and generate invoice if needed
        
        Args:
            order_id: ID of order to process
            billing_month: Billing month number
            billing_flags: Billing flags indicating insurance and other conditions
            invoice_date: Date for the invoice
            
        Returns:
            Optional[int]: ID of created invoice, or None if no invoice created
        """
        # Get order details that need processing
        order_details = self._get_order_details(order_id, billing_month, billing_flags)
        if not order_details:
            return None
            
        # Get the order
        order = self.db.query(Order).get(order_id)
        if not order:
            raise ProcedureError(f"Order {order_id} not found")
            
        # Create invoice
        invoice = self._create_invoice(order, invoice_date)
        
        # Process each order detail
        for detail in order_details:
            # Check if order should be skipped
            if order_must_be_skipped(
                delivery_date=order.delivery_date,
                dos_from=detail.dos_from,
                actual_sale_rent_type=detail.actual_sale_rent_type,
                billing_month=detail.billing_month,
                modifier1=detail.modifier1,
                modifier2=detail.modifier2,
                modifier3=detail.modifier3,
                modifier4=detail.modifier4
            ):
                continue
                
            # Calculate DOS To
            dos_to = get_next_dos_to(
                dos_from=detail.dos_from,
                sale_rent_type=detail.actual_sale_rent_type,
                billing_month=detail.billing_month,
                billed_when=detail.actual_billed_when,
                frequency=detail.frequency,
                frequency_days=detail.frequency_days,
                end_date=detail.end_date
            )
            if not dos_to:
                continue
                
            # Check if invoice should be skipped
            if invoice_must_be_skipped(
                delivery_date=order.delivery_date,
                dos_from=detail.dos_from,
                actual_sale_rent_type=detail.actual_sale_rent_type,
                billing_month=detail.billing_month,
                modifier1=detail.modifier1,
                modifier2=detail.modifier2,
                modifier3=detail.modifier3,
                modifier4=detail.modifier4,
                is_active=detail.is_active
            ):
                continue
                
            # Get invoice modifier
            modifier, _ = get_invoice_modifier(
                sale_rent_type=detail.actual_sale_rent_type,
                billing_month=detail.billing_month,
                dos_from=detail.dos_from,
                dos_to=dos_to,
                end_date=detail.end_date,
                modifier1=detail.modifier1,
                modifier2=detail.modifier2,
                modifier3=detail.modifier3,
                modifier4=detail.modifier4
            )
            
            # Calculate final amount
            base_amount = (
                detail.billable_price if detail.flat_rate
                else detail.billable_price * detail.billed_quantity
            )
            final_amount = base_amount * modifier
            
            # Create invoice detail
            invoice_detail = self._create_invoice_detail(
                invoice=invoice,
                order_detail=detail,
                dos_from=detail.dos_from,
                dos_to=dos_to,
                amount=final_amount
            )
            self.db.add(invoice_detail)
            
        # Convert any deposits to payments
        OrderDepositConverter.execute(self.db, order_id)
        
        # Check if order should be closed
        if order_must_be_closed(
            order_id=order.id,
            customer_id=order.customer_id,
            order_date=order.order_date,
            delivery_date=order.delivery_date,
            end_date=order.end_date,
            total_amount=order.total_amount,
            payment_amount=order.payment_amount,
            ordered_quantity=order.ordered_quantity,
            fulfilled_quantity=order.fulfilled_quantity,
            sale_rent_type=order.sale_rent_type,
            billing_month=billing_month
        ):
            order.status = 'Closed'
            
        self.db.commit()
        return invoice.id

    @classmethod
    def execute(cls,
               db: Session,
               order_id: int,
               billing_month: int,
               billing_flags: int,
               invoice_date: datetime) -> Optional[int]:
        """
        Process an order and generate invoice if needed
        
        Args:
            db: Database session
            order_id: ID of order to process
            billing_month: Billing month number
            billing_flags: Billing flags indicating insurance and other conditions
            invoice_date: Date for the invoice
            
        Returns:
            Optional[int]: ID of created invoice, or None if no invoice created
        """
        procedure = cls(db)
        return procedure._execute(order_id, billing_month, billing_flags, invoice_date)
