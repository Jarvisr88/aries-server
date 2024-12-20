from sqlalchemy import update, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.models.invoice import Invoice
from app.models.customer import CustomerInsurance
from app.core.logging import logger

class InvoicePolicyFixer:
    """Fixes insurance policy references in invoices"""
    
    def __init__(self, db: Session):
        self.db = db

    def _fix_insurance_slot(self, slot_number: int) -> int:
        """
        Fix insurance references for a specific slot
        
        Args:
            slot_number: Insurance slot number (1-4)
            
        Returns:
            Number of records updated
        """
        insurance_field = f'customer_insurance{slot_number}_id'
        
        # Build the update query
        stmt = (
            update(Invoice)
            .where(and_(
                getattr(Invoice, insurance_field).isnot(None),
                CustomerInsurance.insurance_company_id == getattr(Invoice, insurance_field),
                CustomerInsurance.customer_id == Invoice.customer_id
            ))
            .values(**{insurance_field: CustomerInsurance.id})
            .execution_options(synchronize_session=False)
        )
        
        # Execute the update
        result = self.db.execute(stmt)
        return result.rowcount

    def _execute(self) -> dict:
        """
        Fix all invoice insurance policy references
        
        Returns:
            Dictionary with update counts per slot
        """
        try:
            updates = {}
            
            # Fix each insurance slot
            for slot in range(1, 5):
                count = self._fix_insurance_slot(slot)
                updates[f'slot_{slot}'] = count
                logger.info(f"Fixed {count} insurance references in slot {slot}")
            
            # Commit changes
            self.db.commit()
            
            return updates
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error fixing invoice policies: {str(e)}")
            raise

    @classmethod
    def execute(cls, db: Session) -> dict:
        """
        Fix all invoice insurance policy references
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with update counts per slot
        """
        procedure = cls(db)
        return procedure._execute()

    @classmethod
    def execute_raw(cls, db: Session) -> dict:
        """
        Fix all invoice policies using raw SQL for better performance
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with update counts per slot
        """
        updates = {}
        
        try:
            # Fix each insurance slot using raw SQL
            for slot in range(1, 5):
                sql = text(f"""
                    UPDATE tbl_invoice
                    INNER JOIN tbl_customer_insurance 
                        ON tbl_customer_insurance.insurance_company_id = tbl_invoice.customer_insurance{slot}_id
                        AND tbl_customer_insurance.customer_id = tbl_invoice.customer_id
                    SET tbl_invoice.customer_insurance{slot}_id = tbl_customer_insurance.id
                """)
                
                result = db.execute(sql)
                updates[f'slot_{slot}'] = result.rowcount
                logger.info(f"Fixed {result.rowcount} insurance references in slot {slot}")
            
            db.commit()
            return updates
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error fixing invoice policies with raw SQL: {str(e)}")
            raise
