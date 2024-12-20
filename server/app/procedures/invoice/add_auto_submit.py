from decimal import Decimal
from datetime import datetime
from typing import Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.logging import logger
from app.models.invoice import (
    Invoice,
    InvoiceDetails,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.models.customer import CustomerInsurance
from app.procedures.invoice.recalculate import InvoiceDetailsRecalculator

class InvoiceAutoSubmitter:
    """Handles auto-submission of invoices to insurance"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_insurance_info(self,
                          detail: InvoiceDetails,
                          auto_submitted_to: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Get insurance information based on auto submit target
        
        Args:
            detail: Invoice detail record
            auto_submitted_to: Target insurance (Ins1, Ins2, Ins3, or Ins4)
            
        Returns:
            Tuple of (customer_insurance_id, insurance_company_id)
        """
        # Get invoice with insurance info
        invoice = (
            self.db.query(Invoice)
            .filter(
                Invoice.id == detail.invoice_id,
                Invoice.customer_id == detail.customer_id
            )
            .first()
        )
        
        if not invoice:
            return None, None
            
        # Map insurance fields
        insurance_map = {
            'Ins1': (invoice.customer_insurance1_id, detail.bill_ins1),
            'Ins2': (invoice.customer_insurance2_id, detail.bill_ins2),
            'Ins3': (invoice.customer_insurance3_id, detail.bill_ins3),
            'Ins4': (invoice.customer_insurance4_id, detail.bill_ins4)
        }
        
        if auto_submitted_to not in insurance_map:
            return None, None
            
        insurance_id, should_bill = insurance_map[auto_submitted_to]
        if not insurance_id or not should_bill:
            return None, None
            
        # Get customer insurance record
        insurance = (
            self.db.query(CustomerInsurance)
            .filter(
                CustomerInsurance.id == insurance_id,
                CustomerInsurance.customer_id == detail.customer_id
            )
            .first()
        )
        
        if not insurance:
            return None, None
            
        return insurance.id, insurance.insurance_company_id
        
    def _add_auto_submit_transaction(self,
                                   detail: InvoiceDetails,
                                   auto_submitted_to: str,
                                   last_update_user_id: int) -> str:
        """
        Add auto submit transaction to invoice detail
        
        Args:
            detail: Invoice detail to process
            auto_submitted_to: Target insurance (Ins1, Ins2, Ins3, or Ins4)
            last_update_user_id: ID of user making update
            
        Returns:
            Result message
        """
        try:
            # Get insurance info
            customer_insurance_id, insurance_company_id = self._get_insurance_info(
                detail,
                auto_submitted_to
            )
            
            if not customer_insurance_id or not insurance_company_id:
                return "Autosubmitted Payer is wrong"
                
            # Check for existing auto submit transaction
            exists = (
                self.db.query(InvoiceTransaction)
                .join(InvoiceTransactionType)
                .filter(
                    InvoiceTransactionType.name == 'Auto Submit',
                    InvoiceTransaction.customer_id == detail.customer_id,
                    InvoiceTransaction.invoice_id == detail.invoice_id,
                    InvoiceTransaction.invoice_details_id == detail.id,
                    InvoiceTransaction.insurance_company_id == insurance_company_id
                )
                .first()
            )
            
            if exists:
                return "Transaction already exists"
                
            # Create auto submit transaction
            transaction = InvoiceTransaction(
                invoice_details_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=insurance_company_id,
                customer_insurance_id=customer_insurance_id,
                transaction_type='Auto Submit',
                transaction_date=datetime.now().date(),
                amount=detail.billable_amount,
                quantity=detail.quantity,
                taxes=Decimal('0.00'),
                batch_number='',
                comments='Manual',
                extra=None,
                approved=True,
                last_update_user_id=last_update_user_id
            )
            
            self.db.add(transaction)
            self.db.commit()
            return "Success"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding auto submit transaction: {str(e)}")
            raise
            
    def _execute(self,
                invoice_id: int,
                auto_submitted_to: str,
                last_update_user_id: int) -> None:
        """
        Process auto submit for all details in an invoice
        
        Args:
            invoice_id: ID of invoice to process
            auto_submitted_to: Target insurance (Ins1, Ins2, Ins3, or Ins4)
            last_update_user_id: ID of user making update
        """
        try:
            # Initial recalculation
            InvoiceDetailsRecalculator.execute(self.db, invoice_id, None)
            
            # Get all invoice details
            details = (
                self.db.query(InvoiceDetails)
                .filter(InvoiceDetails.invoice_id == invoice_id)
                .all()
            )
            
            # Process each detail
            for detail in details:
                try:
                    result = self._add_auto_submit_transaction(
                        detail,
                        auto_submitted_to,
                        last_update_user_id
                    )
                    if result != "Success":
                        logger.warning(
                            f"Auto submit failed for detail {detail.id}: {result}"
                        )
                except Exception as detail_error:
                    logger.error(
                        f"Error processing detail {detail.id}: {str(detail_error)}"
                    )
                    
            # Final recalculation
            InvoiceDetailsRecalculator.execute(self.db, invoice_id, None)
            
            self.db.commit()
            logger.info(f"Completed auto submit for invoice {invoice_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in auto submit process: {str(e)}")
            raise
            
    @classmethod
    def execute(cls,
               db: Session,
               invoice_id: int,
               auto_submitted_to: str,
               last_update_user_id: int) -> None:
        """
        Add auto submit transactions to an invoice
        
        Args:
            db: Database session
            invoice_id: ID of invoice to process
            auto_submitted_to: Target insurance (Ins1, Ins2, Ins3, or Ins4)
            last_update_user_id: ID of user making update
        """
        submitter = cls(db)
        submitter._execute(
            invoice_id,
            auto_submitted_to,
            last_update_user_id
        )
