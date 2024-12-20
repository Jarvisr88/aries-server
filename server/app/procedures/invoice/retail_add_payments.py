"""
Procedure to add payments to retail invoices.

This module handles the addition of payments to retail invoices,
including payment validation, balance updates, and payment history tracking.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.exceptions import ProcedureError
from app.models.invoice import Invoice, InvoiceTransaction, InvoiceTransactionType
from app.models.payment import Payment, PaymentMethod
from app.models.customer import Customer

class RetailInvoicePaymentAdder:
    """Handles adding payments to retail invoices"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _validate_payment(
        self,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str,
        payment_ref: Optional[str] = None
    ) -> None:
        """Validate payment details before processing
        
        Args:
            invoice: Invoice to add payment to
            amount: Payment amount
            payment_method: Method of payment
            payment_ref: Optional payment reference number
            
        Raises:
            ProcedureError: If payment validation fails
        """
        if not invoice:
            raise ProcedureError("Invoice not found")
            
        if not invoice.is_retail:
            raise ProcedureError("Payment can only be added to retail invoices")
            
        if amount <= 0:
            raise ProcedureError("Payment amount must be positive")
            
        if amount > invoice.balance:
            raise ProcedureError("Payment amount cannot exceed invoice balance")
            
        payment_method_obj = (
            self.db.query(PaymentMethod)
            .filter(PaymentMethod.name == payment_method)
            .first()
        )
        if not payment_method_obj:
            raise ProcedureError(f"Invalid payment method: {payment_method}")
            
        if payment_method_obj.requires_reference and not payment_ref:
            raise ProcedureError(f"Payment reference required for {payment_method}")
            
    def _create_payment(
        self,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str,
        payment_ref: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Payment:
        """Create a new payment record
        
        Args:
            invoice: Invoice being paid
            amount: Payment amount
            payment_method: Method of payment
            payment_ref: Optional payment reference number
            notes: Optional payment notes
            
        Returns:
            Payment: The created payment record
        """
        payment = Payment(
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
            amount=amount,
            payment_method=payment_method,
            payment_reference=payment_ref,
            payment_date=datetime.utcnow(),
            notes=notes
        )
        self.db.add(payment)
        self.db.flush()
        return payment
        
    def _create_transaction(
        self,
        invoice: Invoice,
        payment: Payment,
        amount: Decimal
    ) -> InvoiceTransaction:
        """Create invoice transaction for payment
        
        Args:
            invoice: Invoice being paid
            payment: Associated payment record
            amount: Transaction amount
            
        Returns:
            InvoiceTransaction: The created transaction record
        """
        transaction = InvoiceTransaction(
            invoice_id=invoice.id,
            payment_id=payment.id,
            transaction_type=InvoiceTransactionType.PAYMENT,
            amount=amount,
            transaction_date=datetime.utcnow()
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction
        
    def _update_invoice_balance(
        self,
        invoice: Invoice,
        amount: Decimal
    ) -> None:
        """Update invoice balance after payment
        
        Args:
            invoice: Invoice to update
            amount: Payment amount
        """
        invoice.balance -= amount
        invoice.last_payment_date = datetime.utcnow()
        
        if invoice.balance == 0:
            invoice.paid_date = datetime.utcnow()
            invoice.status = 'Paid'
        elif invoice.balance > 0:
            invoice.status = 'Partial'
            
    def _execute(
        self,
        invoice_id: int,
        amount: Decimal,
        payment_method: str,
        payment_ref: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """Execute the payment addition procedure
        
        Args:
            invoice_id: ID of invoice to add payment to
            amount: Payment amount
            payment_method: Method of payment
            payment_ref: Optional payment reference number
            notes: Optional payment notes
            
        Raises:
            ProcedureError: If payment processing fails
        """
        try:
            # Get invoice
            invoice = self.db.query(Invoice).get(invoice_id)
            
            # Validate payment
            self._validate_payment(invoice, amount, payment_method, payment_ref)
            
            # Create payment record
            payment = self._create_payment(
                invoice,
                amount,
                payment_method,
                payment_ref,
                notes
            )
            
            # Create invoice transaction
            self._create_transaction(invoice, payment, amount)
            
            # Update invoice balance
            self._update_invoice_balance(invoice, amount)
            
            self.db.commit()
            logger.info(f"Added payment of {amount} to invoice {invoice_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding payment to invoice {invoice_id}: {str(e)}")
            raise
            
    @classmethod
    def execute(
        cls,
        db: Session,
        invoice_id: int,
        amount: Decimal,
        payment_method: str,
        payment_ref: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """Add payment to retail invoice
        
        Args:
            db: Database session
            invoice_id: ID of invoice to add payment to
            amount: Payment amount
            payment_method: Method of payment
            payment_ref: Optional payment reference number
            notes: Optional payment notes
        """
        adder = cls(db)
        adder._execute(
            invoice_id,
            amount,
            payment_method,
            payment_ref,
            notes
        )
