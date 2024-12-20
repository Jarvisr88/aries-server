from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.invoice import InvoiceDetails, InvoiceTransaction, InvoiceTransactionType
from app.procedures.invoice.recalculate import InvoiceDetailsRecalculator

class InvoiceDetailsSubmittedAdder:
    """Adds submitted transaction to invoice details"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _add_submitted_transaction(self,
                                 invoice_details_id: int,
                                 amount: Decimal,
                                 submitted_to: str,
                                 submitted_by: str,
                                 submitted_batch: str,
                                 last_update_user_id: int) -> None:
        """
        Internal method to add a submitted transaction
        
        Args:
            invoice_details_id: ID of invoice details
            amount: Submitted amount
            submitted_to: Entity the invoice was submitted to
            submitted_by: Person who submitted the invoice
            submitted_batch: Batch number for submission
            last_update_user_id: ID of user making update
        """
        try:
            # Get invoice details
            detail = (
                self.db.query(InvoiceDetails)
                .filter(InvoiceDetails.id == invoice_details_id)
                .first()
            )
            
            if not detail:
                raise ValueError(f"Invoice details not found: {invoice_details_id}")
                
            # Create submitted transaction
            transaction = InvoiceTransaction(
                invoice_details_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=detail.current_insurance_company_id,
                customer_insurance_id=detail.current_customer_insurance_id,
                transaction_type='Submitted',
                amount=amount,
                quantity=detail.quantity,
                taxes=Decimal('0.00'),
                batch_number=submitted_batch,
                comments=f"Submitted to {submitted_to} by {submitted_by}",
                extra=None,
                approved=True,
                last_update_user_id=last_update_user_id
            )
            
            self.db.add(transaction)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding submitted transaction: {str(e)}")
            raise
            
    def _execute(self,
                invoice_details_id: int,
                amount: Decimal,
                submitted_to: str,
                submitted_by: str,
                submitted_batch: str,
                last_update_user_id: int) -> None:
        """
        Add submitted transaction and recalculate invoice details
        
        Args:
            invoice_details_id: ID of invoice details
            amount: Submitted amount
            submitted_to: Entity the invoice was submitted to
            submitted_by: Person who submitted the invoice
            submitted_batch: Batch number for submission
            last_update_user_id: ID of user making update
        """
        try:
            # Add submitted transaction
            self._add_submitted_transaction(
                invoice_details_id,
                amount,
                submitted_to,
                submitted_by,
                submitted_batch,
                last_update_user_id
            )
            
            # Recalculate internals
            InvoiceDetailsRecalculator.execute(self.db, None, invoice_details_id)
            
        except Exception as e:
            logger.error(f"Error in AddSubmitted procedure: {str(e)}")
            raise
            
    @classmethod
    def execute(cls,
               db: Session,
               invoice_details_id: int,
               amount: Decimal,
               submitted_to: str,
               submitted_by: str,
               submitted_batch: str,
               last_update_user_id: int) -> None:
        """
        Add submitted transaction to invoice details
        
        Args:
            db: Database session
            invoice_details_id: ID of invoice details
            amount: Submitted amount
            submitted_to: Entity the invoice was submitted to
            submitted_by: Person who submitted the invoice
            submitted_batch: Batch number for submission
            last_update_user_id: ID of user making update
        """
        adder = cls(db)
        adder._execute(
            invoice_details_id,
            amount,
            submitted_to,
            submitted_by,
            submitted_batch,
            last_update_user_id
        )
