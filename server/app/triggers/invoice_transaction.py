"""
Invoice Transaction Trigger Handler

This module implements the before-insert trigger functionality for invoice transactions,
handling various transaction types and their associated updates to invoice details.
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

from app.models.invoice import (
    InvoiceTransaction,
    InvoiceTransactionType,
    InvoiceDetails
)
from app.core.logging import logger

Base = declarative_base()

class InvoiceTransactionTrigger:
    """Handles before-insert trigger logic for invoice transactions"""

    def __init__(self, session: Session):
        self.session = session
        self.old_value: Decimal = Decimal('0.00')
        self.quantity: float = 0.0
        self.transaction_type: Optional[str] = None

    async def _get_transaction_type(self, type_id: int) -> str:
        """Retrieve the transaction type name"""
        stmt = select(InvoiceTransactionType.name).where(
            InvoiceTransactionType.id == type_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_invoice_detail_values(
        self,
        customer_id: int,
        invoice_id: int,
        detail_id: int,
        field: str
    ) -> tuple[Decimal, float]:
        """Get current values from invoice details"""
        stmt = select(
            getattr(InvoiceDetails, field),
            InvoiceDetails.quantity
        ).where(
            InvoiceDetails.customer_id == customer_id,
            InvoiceDetails.invoice_id == invoice_id,
            InvoiceDetails.id == detail_id
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        return (Decimal(str(row[0])) if row else Decimal('0.00'),
                float(row[1]) if row else 0.0)

    async def _update_invoice_detail(
        self,
        customer_id: int,
        invoice_id: int,
        detail_id: int,
        field: str,
        value: Decimal
    ) -> None:
        """Update invoice detail field with new value"""
        stmt = (
            InvoiceDetails.__table__.update()
            .where(
                InvoiceDetails.customer_id == customer_id,
                InvoiceDetails.invoice_id == invoice_id,
                InvoiceDetails.id == detail_id
            )
            .values(**{field: value})
        )
        await self.session.execute(stmt)

    async def before_insert(self, transaction: InvoiceTransaction) -> None:
        """Handle before-insert trigger logic"""
        try:
            # Get transaction type
            self.transaction_type = await self._get_transaction_type(
                transaction.transaction_type_id
            )
            if not self.transaction_type:
                logger.warning(
                    f"Transaction type {transaction.transaction_type_id} not found"
                )
                return

            # Handle different transaction types
            if self.transaction_type == 'Adjust Allowable':
                field = 'allowable_amount'
            elif self.transaction_type == 'Adjust Customary':
                field = 'billable_amount'
            elif self.transaction_type == 'Adjust Taxes':
                field = 'taxes'
            else:
                return

            # Get current values
            self.old_value, self.quantity = await self._get_invoice_detail_values(
                transaction.customer_id,
                transaction.invoice_id,
                transaction.invoice_details_id,
                field
            )

            # Update transaction
            transaction.quantity = self.quantity
            transaction.comments = f'Previous Value={self.old_value}'

            # Update invoice details if value changed
            if abs(self.old_value - transaction.amount) > Decimal('0.001'):
                await self._update_invoice_detail(
                    transaction.customer_id,
                    transaction.invoice_id,
                    transaction.invoice_details_id,
                    field,
                    transaction.amount
                )

        except Exception as e:
            logger.error(
                f"Error in invoice transaction trigger: {str(e)}",
                exc_info=True
            )
            raise


# Register SQLAlchemy event listeners
@event.listens_for(InvoiceTransaction, 'before_insert')
def invoice_transaction_before_insert(mapper, connection, target):
    """SQLAlchemy before-insert event listener"""
    session = Session(bind=connection)
    trigger = InvoiceTransactionTrigger(session)
    
    # Use asyncio.run in a separate thread if needed
    # For now, assuming synchronous execution in the trigger
    trigger.before_insert(target)
