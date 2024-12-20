from datetime import datetime
from decimal import Decimal
from typing import Optional
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.invoice import Invoice, InvoiceDetails
from app.procedures.invoice.add_payment import PaymentProcessor

class RetailInvoicePaymentAdder:
    """Adds payments to all details in a retail invoice"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _update_payment_xml(self, extra_xml: str, amount: Decimal) -> str:
        """
        Update the payment amount in the XML
        
        Args:
            extra_xml: Original XML string
            amount: New payment amount
            
        Returns:
            Updated XML string
        """
        try:
            # Parse XML
            root = ET.fromstring(extra_xml)
            
            # Find or create the 'values' element
            values = root.find('values')
            if values is None:
                values = ET.SubElement(root, 'values')
                
            # Find or create the payment element
            paid = values.find('.//v[@n="Paid"]')
            if paid is None:
                paid = ET.SubElement(values, 'v')
                paid.set('n', 'Paid')
                
            # Update the payment amount
            paid.text = str(amount)
            
            # Convert back to string
            return ET.tostring(root, encoding='unicode')
            
        except Exception as e:
            logger.error(f"Error updating payment XML: {str(e)}")
            raise ValueError("Invalid payment XML format")
            
    def _execute(self,
                invoice_id: int,
                transaction_date: datetime,
                extra: str,
                last_update_user_id: int) -> None:
        """
        Add payments to all details in a retail invoice
        
        Args:
            invoice_id: ID of the retail invoice
            transaction_date: Date of the transaction
            extra: XML with payment details
            last_update_user_id: ID of user making update
        """
        try:
            # Get all invoice details
            details = (
                self.db.query(InvoiceDetails)
                .filter(InvoiceDetails.invoice_id == invoice_id)
                .all()
            )
            
            if not details:
                logger.warning(f"No invoice details found for invoice {invoice_id}")
                return
                
            # Process each detail
            for detail in details:
                try:
                    # Update XML with detail's billable amount
                    updated_xml = self._update_payment_xml(extra, detail.billable_amount)
                    
                    # Add payment for this detail
                    PaymentProcessor.execute(
                        db=self.db,
                        invoice_details_id=detail.id,
                        insurance_company_id=None,  # Retail payment, no insurance
                        transaction_date=transaction_date,
                        extra=updated_xml,
                        comments='',  # No comments for retail payments
                        options='',   # No special options
                        last_update_user_id=last_update_user_id
                    )
                    
                except Exception as detail_error:
                    logger.error(f"Error processing payment for detail {detail.id}: {str(detail_error)}")
                    raise
                    
            self.db.commit()
            logger.info(f"Successfully added payments for {len(details)} invoice details")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding retail invoice payments: {str(e)}")
            raise
            
    @classmethod
    def execute(cls,
               db: Session,
               invoice_id: int,
               transaction_date: datetime,
               extra: str,
               last_update_user_id: int) -> None:
        """
        Add payments to all details in a retail invoice
        
        Args:
            db: Database session
            invoice_id: ID of the retail invoice
            transaction_date: Date of the transaction
            extra: XML with payment details
            last_update_user_id: ID of user making update
        """
        adder = cls(db)
        adder._execute(
            invoice_id,
            transaction_date,
            extra,
            last_update_user_id
        )
