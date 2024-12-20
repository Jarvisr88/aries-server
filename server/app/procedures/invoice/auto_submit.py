from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.invoice import InvoiceDetails, Invoice, InvoiceTransaction, InvoiceTransactionType
from app.models.customer import CustomerInsurance
from app.core.exceptions import ProcedureError

class InvoiceDetailsAutoSubmit:
    def __init__(self, db: Session):
        self.db = db

    def _execute(self, 
                invoice_details_id: int,
                insurance_company_id: int,
                transaction_date: datetime,
                last_update_user_id: int) -> Tuple[str, Optional[InvoiceTransaction]]:
        # Get invoice details and related data
        detail = (
            self.db.query(InvoiceDetails)
            .join(Invoice, and_(
                InvoiceDetails.invoice_id == Invoice.id,
                InvoiceDetails.customer_id == Invoice.customer_id
            ))
            .outerjoin(CustomerInsurance, and_(
                CustomerInsurance.id.in_([
                    Invoice.customer_insurance1_id,
                    Invoice.customer_insurance2_id,
                    Invoice.customer_insurance3_id,
                    Invoice.customer_insurance4_id
                ]),
                CustomerInsurance.customer_id == Invoice.customer_id,
                CustomerInsurance.insurance_company_id == insurance_company_id
            ))
            .filter(InvoiceDetails.id == invoice_details_id)
            .first()
        )

        if not detail:
            return "InvoiceDetailsID is wrong", None

        # Get matching customer insurance
        customer_insurance = None
        for ins_id in [detail.invoice.customer_insurance1_id, 
                      detail.invoice.customer_insurance2_id,
                      detail.invoice.customer_insurance3_id,
                      detail.invoice.customer_insurance4_id]:
            if ins_id:
                ins = self.db.query(CustomerInsurance).get(ins_id)
                if ins and ins.insurance_company_id == insurance_company_id:
                    customer_insurance = ins
                    break

        if not customer_insurance:
            return "Autosubmitted Company ID is wrong", None

        # Check for existing auto submit transaction
        existing = (
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

        if existing:
            return "Transaction already exists", None

        # Get transaction type
        transaction_type = (
            self.db.query(InvoiceTransactionType)
            .filter(InvoiceTransactionType.name == 'Auto Submit')
            .first()
        )

        # Create new transaction
        new_transaction = InvoiceTransaction(
            invoice_details_id=detail.id,
            invoice_id=detail.invoice_id,
            customer_id=detail.customer_id,
            insurance_company_id=insurance_company_id,
            customer_insurance_id=customer_insurance.id,
            transaction_type_id=transaction_type.id,
            transaction_date=transaction_date,
            amount=detail.billable_amount,
            quantity=detail.quantity,
            taxes=0.00,
            batch_number='',
            comments='EDI',
            extra=None,
            approved=True,
            last_update_user_id=last_update_user_id
        )

        self.db.add(new_transaction)
        self.db.commit()

        return "Success", new_transaction

    @classmethod
    def execute(cls, db: Session, 
                invoice_details_id: int,
                insurance_company_id: int,
                transaction_date: datetime,
                last_update_user_id: int) -> Tuple[str, Optional[InvoiceTransaction]]:
        """
        Add auto submit transaction for invoice details

        Args:
            db: Database session
            invoice_details_id: ID of invoice details
            insurance_company_id: ID of insurance company
            transaction_date: Date of transaction
            last_update_user_id: ID of user making update

        Returns:
            Tuple of (result message, new transaction if successful)
        """
        procedure = cls(db)
        return procedure._execute(
            invoice_details_id,
            insurance_company_id, 
            transaction_date,
            last_update_user_id
        )
