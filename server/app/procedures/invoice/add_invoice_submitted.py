"""
Invoice Submission Procedure

Python implementation of the Invoice_AddSubmitted stored procedure for
marking invoice details as submitted to a specific payer.
"""
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.invoice import InvoiceDetails
from app.procedures.base import BaseProcedure
from app.procedures.invoice.add_submitted import InvoiceDetailsSubmittedAdder
from app.procedures.invoice.recalculate import InvoiceDetailsRecalculator


class InvoiceSubmitter(BaseProcedure):
    """Handles marking invoice details as submitted to a specific payer.
    
    This procedure:
    1. Recalculates invoice details
    2. Finds all invoice details for the specified payer
    3. Marks each detail as submitted
    4. Recalculates invoice details again
    """
    
    def __init__(
        self,
        invoice_id: int,
        submitted_to: str,
        submitted_by: str,
        submitted_batch: str,
        last_update_user_id: int
    ):
        """Initialize the invoice submitter.
        
        Args:
            invoice_id: ID of the invoice to submit
            submitted_to: Entity the invoice is being submitted to
            submitted_by: Person submitting the invoice
            submitted_batch: Batch number for submission
            last_update_user_id: ID of user making update
        """
        self.invoice_id = invoice_id
        self.submitted_to = submitted_to
        self.submitted_by = submitted_by
        self.submitted_batch = submitted_batch
        self.last_update_user_id = last_update_user_id

    def _execute(self, session: Session) -> None:
        """Execute the invoice submission procedure.
        
        Args:
            session: Database session to use
        """
        if not self.invoice_id:
            return

        # Initial recalculation
        recalc = InvoiceDetailsRecalculator(session)
        recalc.execute(self.invoice_id, None)

        # Get all invoice details for this payer
        query = (
            select(InvoiceDetails)
            .where(
                InvoiceDetails.invoice_id == self.invoice_id,
                InvoiceDetails.current_payer == self.submitted_to
            )
        )
        details = session.execute(query).scalars().all()

        # Add submitted transaction for each detail
        for detail in details:
            InvoiceDetailsSubmittedAdder.execute(
                db=session,
                invoice_details_id=detail.id,
                amount=Decimal('0.00'),
                submitted_to=self.submitted_to,
                submitted_by=self.submitted_by,
                submitted_batch=self.submitted_batch,
                last_update_user_id=self.last_update_user_id
            )

        # Final recalculation
        recalc.execute(self.invoice_id, None)

    @classmethod
    def execute(
        cls,
        invoice_id: int,
        submitted_to: str,
        submitted_by: str,
        submitted_batch: str,
        last_update_user_id: int
    ) -> None:
        """Execute the invoice submission procedure.
        
        Args:
            invoice_id: ID of the invoice to submit
            submitted_to: Entity the invoice is being submitted to
            submitted_by: Person submitting the invoice
            submitted_batch: Batch number for submission
            last_update_user_id: ID of user making update
        """
        submitter = cls(
            invoice_id=invoice_id,
            submitted_to=submitted_to,
            submitted_by=submitted_by,
            submitted_batch=submitted_batch,
            last_update_user_id=last_update_user_id
        )
        with get_session() as session:
            submitter._execute(session)
            session.commit()
