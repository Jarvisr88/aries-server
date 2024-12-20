from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, and_, join
from sqlalchemy.orm import Session
import xml.etree.ElementTree as ET

from app.models.order import Order, OrderDetails
from app.models.deposit import Deposit, DepositDetails
from app.models.invoice import (
    Invoice, 
    InvoiceDetails,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.procedures.invoice.payment import InvoiceDetailsPayment
from app.procedures.order.balance import OrderInternalBalance
from app.core.exceptions import ProcedureError

class OrderDepositConverter:
    """Converts order deposits into invoice payments"""

    def __init__(self, db: Session):
        self.db = db

    def _create_extra_xml(self, 
                         billable: Decimal,
                         check_date: datetime,
                         paid: Decimal,
                         payment_method: str) -> str:
        """Create XML extra data for payment"""
        root = ET.Element('values')
        
        billable_elem = ET.SubElement(root, 'v', n='Billable')
        billable_elem.text = str(billable or '0.00')
        
        check_date_elem = ET.SubElement(root, 'v', n='CheckDate')
        check_date_elem.text = check_date.strftime('%m/%d/%Y') if check_date else '00/00/0000'
        
        paid_elem = ET.SubElement(root, 'v', n='Paid')
        paid_elem.text = str(paid or '0.00')
        
        method_elem = ET.SubElement(root, 'v', n='PaymentMethod')
        method_elem.text = payment_method or 'Check'
        
        return ET.tostring(root, encoding='unicode')

    def _get_deposits_query(self, order_id: int):
        """Get query for deposits that need to be converted to payments"""
        payment_type = (
            self.db.query(InvoiceTransactionType)
            .filter(InvoiceTransactionType.name == 'Payment')
            .first()
        )
        
        return (
            self.db.query(
                InvoiceDetails.id.label('invoice_details_id'),
                DepositDetails.amount.label('amount'),
                Deposit.date.label('date'),
                Deposit.payment_method.label('payment_method'),
                InvoiceDetails.billable_amount.label('billable_amount')
            )
            .join(Order, Order.id == OrderDetails.order_id)
            .join(OrderDetails, and_(
                OrderDetails.customer_id == Order.customer_id,
                OrderDetails.order_id == Order.id
            ))
            .join(Deposit, and_(
                Deposit.customer_id == OrderDetails.customer_id,
                Deposit.order_id == OrderDetails.order_id
            ))
            .join(DepositDetails, and_(
                DepositDetails.customer_id == OrderDetails.customer_id,
                DepositDetails.order_id == OrderDetails.order_id,
                DepositDetails.order_details_id == OrderDetails.id
            ))
            .join(Invoice, and_(
                Invoice.customer_id == Order.customer_id,
                Invoice.order_id == Order.id
            ))
            .join(InvoiceDetails, and_(
                InvoiceDetails.customer_id == Invoice.customer_id,
                InvoiceDetails.invoice_id == Invoice.id,
                InvoiceDetails.billing_month == 1,
                InvoiceDetails.order_id == OrderDetails.order_id,
                InvoiceDetails.order_details_id == OrderDetails.id
            ))
            .outerjoin(InvoiceTransaction, and_(
                InvoiceTransaction.customer_id == InvoiceDetails.customer_id,
                InvoiceTransaction.invoice_id == InvoiceDetails.invoice_id,
                InvoiceTransaction.invoice_details_id == InvoiceDetails.id,
                InvoiceTransaction.insurance_company_id.is_(None),
                InvoiceTransaction.customer_insurance_id.is_(None),
                InvoiceTransaction.transaction_type_id == payment_type.id,
                InvoiceTransaction.transaction_date == Deposit.date,
                InvoiceTransaction.amount == DepositDetails.amount
            ))
            .filter(
                Order.id == order_id,
                InvoiceTransaction.id.is_(None)
            )
        )

    def _execute(self, order_id: int, user_id: Optional[int] = 1) -> None:
        """
        Convert deposits into payments for an order
        
        Args:
            order_id: ID of order to process
            user_id: ID of user making the change
        """
        # Get deposits that need to be converted
        deposits = self._get_deposits_query(order_id).all()
        
        # Process each deposit
        for deposit in deposits:
            # Create extra XML data
            extra_xml = self._create_extra_xml(
                billable=deposit.billable_amount,
                check_date=deposit.date,
                paid=deposit.amount,
                payment_method=deposit.payment_method
            )
            
            # Add payment
            result = InvoiceDetailsPayment.execute(
                db=self.db,
                invoice_details_id=deposit.invoice_details_id,
                insurance_company_id=None,
                transaction_date=deposit.date,
                extra=extra_xml,
                comments='Deposit',
                options='',
                last_update_user_id=user_id
            )
            
            if result[0] != 'Success':
                raise ProcedureError(f"Failed to add payment: {result[0]}")
                
        # Update order balance
        OrderInternalBalance.execute(self.db, order_id)

    @classmethod
    def execute(cls, db: Session, order_id: int, user_id: Optional[int] = 1) -> None:
        """
        Convert deposits into payments for an order
        
        Args:
            db: Database session
            order_id: ID of order to process
            user_id: ID of user making the change
        """
        procedure = cls(db)
        procedure._execute(order_id, user_id)
