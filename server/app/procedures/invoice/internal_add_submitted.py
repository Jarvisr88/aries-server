"""
Internal Invoice Details Submission Procedure

Python implementation of the InvoiceDetails_InternalAddSubmitted stored procedure for
adding submitted transactions to invoice details.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from app.database import get_session
from app.models.invoice import (
    Invoice,
    InvoiceDetails,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.models.customer import CustomerInsurance
from app.procedures.base import BaseProcedure


class InvoiceDetailsInternalSubmitter(BaseProcedure):
    """Handles adding submitted transactions to invoice details.
    
    This procedure:
    1. Gets transaction type for submissions
    2. Creates appropriate transaction based on submission target (Patient/Insurance)
    3. Links transaction to correct insurance relationship if applicable
    """
    
    def __init__(
        self,
        invoice_details_id: int,
        amount: Decimal,
        submitted_to: str,
        submitted_by: str,
        submitted_batch: str,
        last_update_user_id: int
    ):
        """Initialize the internal submitter.
        
        Args:
            invoice_details_id: ID of invoice details to submit
            amount: Amount being submitted
            submitted_to: Entity the invoice is being submitted to
            submitted_by: Person submitting the invoice
            submitted_batch: Batch number for submission
            last_update_user_id: ID of user making update
        """
        self.invoice_details_id = invoice_details_id
        self.amount = amount
        self.submitted_to = submitted_to
        self.submitted_by = submitted_by
        self.submitted_batch = submitted_batch
        self.last_update_user_id = last_update_user_id

    async def _get_transaction_type(self, session: Session) -> Optional[InvoiceTransactionType]:
        """Get the Submit transaction type."""
        query = (
            select(InvoiceTransactionType)
            .where(InvoiceTransactionType.name == 'Submit')
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _get_invoice_details(self, session: Session) -> Optional[InvoiceDetails]:
        """Get invoice details with related data."""
        query = (
            select(InvoiceDetails)
            .options(
                joinedload(InvoiceDetails.invoice)
                .joinedload(Invoice.customer_insurance1),
                joinedload(InvoiceDetails.invoice)
                .joinedload(Invoice.customer_insurance2),
                joinedload(InvoiceDetails.invoice)
                .joinedload(Invoice.customer_insurance3),
                joinedload(InvoiceDetails.invoice)
                .joinedload(Invoice.customer_insurance4)
            )
            .where(InvoiceDetails.id == self.invoice_details_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _create_transaction(
        self,
        session: Session,
        details: InvoiceDetails,
        tran_type: InvoiceTransactionType,
        insurance: Optional[CustomerInsurance] = None
    ) -> None:
        """Create the submitted transaction."""
        transaction = InvoiceTransaction(
            invoice_details_id=details.id,
            invoice_id=details.invoice_id,
            customer_id=details.customer_id,
            insurance_company_id=insurance.insurance_company_id if insurance else None,
            customer_insurance_id=insurance.id if insurance else None,
            transaction_type_id=tran_type.id,
            amount=self.amount,
            quantity=details.quantity,
            transaction_date=date.today(),
            batch_number=self.submitted_batch,
            comments=f"Submitted by {self.submitted_by}",
            last_update_user_id=self.last_update_user_id
        )
        session.add(transaction)

    def _execute(self, session: Session) -> None:
        """Execute the internal submission procedure.
        
        Args:
            session: Database session to use
        """
        if not self.invoice_details_id:
            return

        # Get transaction type
        tran_type = await self._get_transaction_type(session)
        if not tran_type:
            raise ValueError("Submit transaction type not found")

        # Get invoice details with related data
        details = await self._get_invoice_details(session)
        if not details:
            raise ValueError(f"Invoice details not found: {self.invoice_details_id}")

        # Create transaction based on submission target
        if self.submitted_to == 'Patient':
            await self._create_transaction(session, details, tran_type)
        else:
            # Map insurance number to relationship
            insurance_map = {
                'Ins1': details.invoice.customer_insurance1,
                'Ins2': details.invoice.customer_insurance2,
                'Ins3': details.invoice.customer_insurance3,
                'Ins4': details.invoice.customer_insurance4
            }
            insurance = insurance_map.get(self.submitted_to)
            if insurance:
                await self._create_transaction(session, details, tran_type, insurance)

    @classmethod
    def execute(
        cls,
        invoice_details_id: int,
        amount: Decimal,
        submitted_to: str,
        submitted_by: str,
        submitted_batch: str,
        last_update_user_id: int
    ) -> None:
        """Execute the internal submission procedure.
        
        Args:
            invoice_details_id: ID of invoice details to submit
            amount: Amount being submitted
            submitted_to: Entity the invoice is being submitted to
            submitted_by: Person submitting the invoice
            submitted_batch: Batch number for submission
            last_update_user_id: ID of user making update
        """
        submitter = cls(
            invoice_details_id=invoice_details_id,
            amount=amount,
            submitted_to=submitted_to,
            submitted_by=submitted_by,
            submitted_batch=submitted_batch,
            last_update_user_id=last_update_user_id
        )
        with get_session() as session:
            submitter._execute(session)
            session.commit()
