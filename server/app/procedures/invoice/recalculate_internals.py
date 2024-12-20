from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.logging import get_logger
from app.models.invoice import InvoiceDetails, Invoice, CustomerInsurance
from app.models.transaction import InvoiceTransaction, InvoiceTransactionType

logger = get_logger(__name__)

class InvoiceDetailsRecalculator:
    """Recalculates internal values for invoice details based on current payer and insurance information."""

    # Insurance flags
    F_INSCO_1 = 1
    F_INSCO_2 = 2
    F_INSCO_3 = 4
    F_INSCO_4 = 8
    F_PATIENT = 16

    def __init__(self, session: Session):
        self.session = session
        self.logger = logger

    def recalculate_internals(self, invoice_ids: Optional[List[str]] = None, invoice_details_ids: Optional[List[str]] = None):
        """
        Recalculates internal values for invoice details based on transactions and insurance information.
        
        Args:
            invoice_ids: Optional list of invoice IDs to process
            invoice_details_ids: Optional list of invoice details IDs to process
        """
        # Build base query
        query = self.session.query(
            InvoiceDetails.customer_id,
            InvoiceDetails.invoice_id,
            InvoiceDetails.id.label('invoice_details_id'),
            InvoiceTransaction.id.label('tran_id'),
            InvoiceTransactionType.name.label('tran_type'),
            InvoiceTransaction.amount.label('tran_amount'),
            InvoiceTransaction.transaction_date.label('tran_date'),
            InvoiceTransaction.owner.label('tran_owner'),
            Invoice.insurances.label('insurances'),
            Invoice.customer_insurance1_id,
            Invoice.customer_insurance2_id,
            Invoice.customer_insurance3_id,
            Invoice.customer_insurance4_id
        ).join(
            Invoice,
            (Invoice.customer_id == InvoiceDetails.customer_id) &
            (Invoice.id == InvoiceDetails.invoice_id)
        ).outerjoin(
            InvoiceTransaction,
            (InvoiceTransaction.invoice_details_id == InvoiceDetails.id) &
            (InvoiceTransaction.invoice_id == InvoiceDetails.invoice_id) &
            (InvoiceTransaction.customer_id == InvoiceDetails.customer_id)
        ).outerjoin(
            InvoiceTransactionType,
            InvoiceTransactionType.id == InvoiceTransaction.transaction_type_id
        )

        # Apply filters
        if invoice_ids:
            query = query.filter(Invoice.id.in_(invoice_ids))
        if invoice_details_ids:
            query = query.filter(InvoiceDetails.id.in_(invoice_details_ids))

        # Order results
        query = query.order_by(
            InvoiceDetails.customer_id,
            InvoiceDetails.invoice_id,
            InvoiceDetails.id,
            InvoiceTransaction.id
        )

        # Process results
        prev_customer_id = None
        prev_invoice_id = None
        prev_details_id = None
        
        # Transaction accumulators
        payment_amount_insco_1 = 0.0
        payment_amount_insco_2 = 0.0
        payment_amount_insco_3 = 0.0
        payment_amount_insco_4 = 0.0
        payment_amount_patient = 0.0
        payment_amount = 0.0
        writeoff_amount = 0.0
        deductible_amount = 0.0
        proposed_payer = None
        insurances = 0
        pendings = 0
        submits = 0
        zero_payments = 0
        submit_date_1 = None
        submit_date_2 = None
        submit_date_3 = None
        submit_date_4 = None
        submit_date_p = None
        
        for row in query:
            # Process new invoice detail
            if (prev_customer_id != row.customer_id or 
                prev_invoice_id != row.invoice_id or 
                prev_details_id != row.invoice_details_id):
                
                # Update previous record if exists
                if prev_customer_id and prev_invoice_id and prev_details_id:
                    self._update_invoice_detail(
                        prev_customer_id, prev_invoice_id, prev_details_id,
                        payment_amount, writeoff_amount, deductible_amount,
                        payment_amount_insco_1, payment_amount_insco_2,
                        payment_amount_insco_3, payment_amount_insco_4,
                        payment_amount_patient, proposed_payer, insurances,
                        pendings, submits, zero_payments,
                        submit_date_1, submit_date_2, submit_date_3,
                        submit_date_4, submit_date_p
                    )

                # Reset accumulators
                prev_customer_id = row.customer_id
                prev_invoice_id = row.invoice_id
                prev_details_id = row.invoice_details_id
                payment_amount_insco_1 = 0.0
                payment_amount_insco_2 = 0.0
                payment_amount_insco_3 = 0.0
                payment_amount_insco_4 = 0.0
                payment_amount_patient = 0.0
                payment_amount = 0.0
                writeoff_amount = 0.0
                deductible_amount = 0.0
                proposed_payer = None
                insurances = row.insurances
                pendings = 0
                submits = 0
                zero_payments = 0
                submit_date_1 = None
                submit_date_2 = None
                submit_date_3 = None
                submit_date_4 = None
                submit_date_p = None

            # Process transaction if exists
            if row.tran_id:
                if row.tran_type in ('Contractual Writeoff', 'Writeoff'):
                    writeoff_amount += row.tran_amount or 0

                elif row.tran_type in ('Submit', 'Auto Submit'):
                    submits |= row.tran_owner
                    if row.tran_owner == self.F_INSCO_1:
                        submit_date_1 = row.tran_date
                    elif row.tran_owner == self.F_INSCO_2:
                        submit_date_2 = row.tran_date
                    elif row.tran_owner == self.F_INSCO_3:
                        submit_date_3 = row.tran_date
                    elif row.tran_owner == self.F_INSCO_4:
                        submit_date_4 = row.tran_date
                    elif row.tran_owner == self.F_PATIENT:
                        submit_date_p = row.tran_date

                elif row.tran_type == 'Voided Submission':
                    submits &= ~row.tran_owner
                    if row.tran_owner == self.F_INSCO_1:
                        submit_date_1 = None
                    elif row.tran_owner == self.F_INSCO_2:
                        submit_date_2 = None
                    elif row.tran_owner == self.F_INSCO_3:
                        submit_date_3 = None
                    elif row.tran_owner == self.F_INSCO_4:
                        submit_date_4 = None
                    elif row.tran_owner == self.F_PATIENT:
                        submit_date_p = None

                elif row.tran_type == 'Pending Submission':
                    pendings |= row.tran_owner

                elif row.tran_type == 'Change Current Payee':
                    if ((row.tran_owner == self.F_INSCO_1 and insurances & self.F_INSCO_1) or
                        (row.tran_owner == self.F_INSCO_2 and insurances & self.F_INSCO_2) or
                        (row.tran_owner == self.F_INSCO_3 and insurances & self.F_INSCO_3) or
                        (row.tran_owner == self.F_INSCO_4 and insurances & self.F_INSCO_4) or
                        row.tran_owner == self.F_PATIENT):
                        proposed_payer = row.tran_owner

                elif row.tran_type == 'Payment':
                    if abs(row.tran_amount) < 0.01:
                        zero_payments |= row.tran_owner
                    else:
                        zero_payments &= ~row.tran_owner

                    if row.tran_owner == self.F_INSCO_1:
                        payment_amount_insco_1 += row.tran_amount
                    elif row.tran_owner == self.F_INSCO_2:
                        payment_amount_insco_2 += row.tran_amount
                    elif row.tran_owner == self.F_INSCO_3:
                        payment_amount_insco_3 += row.tran_amount
                    elif row.tran_owner == self.F_INSCO_4:
                        payment_amount_insco_4 += row.tran_amount
                    elif row.tran_owner == self.F_PATIENT:
                        payment_amount_patient += row.tran_amount

                    payment_amount += row.tran_amount

                    if row.tran_owner == proposed_payer and row.tran_amount >= 0:
                        proposed_payer = None

                elif row.tran_type == 'Deductible' and row.tran_owner == self.F_INSCO_1:
                    deductible_amount = row.tran_amount or 0.0

        # Update final record if exists
        if prev_customer_id and prev_invoice_id and prev_details_id:
            self._update_invoice_detail(
                prev_customer_id, prev_invoice_id, prev_details_id,
                payment_amount, writeoff_amount, deductible_amount,
                payment_amount_insco_1, payment_amount_insco_2,
                payment_amount_insco_3, payment_amount_insco_4,
                payment_amount_patient, proposed_payer, insurances,
                pendings, submits, zero_payments,
                submit_date_1, submit_date_2, submit_date_3,
                submit_date_4, submit_date_p
            )

    def _update_invoice_detail(self, customer_id: str, invoice_id: str, details_id: str,
                             payment_amount: float, writeoff_amount: float, deductible_amount: float,
                             payment_amount_insco_1: float, payment_amount_insco_2: float,
                             payment_amount_insco_3: float, payment_amount_insco_4: float,
                             payment_amount_patient: float, proposed_payer: Optional[int],
                             insurances: int, pendings: int, submits: int, zero_payments: int,
                             submit_date_1: Optional[str], submit_date_2: Optional[str],
                             submit_date_3: Optional[str], submit_date_4: Optional[str],
                             submit_date_p: Optional[str]):
        """Updates an invoice detail record with calculated values."""
        detail = self.session.query(InvoiceDetails).filter(
            InvoiceDetails.customer_id == customer_id,
            InvoiceDetails.invoice_id == invoice_id,
            InvoiceDetails.id == details_id
        ).first()

        if not detail:
            self.logger.warning(f"Invoice detail not found: {customer_id}/{invoice_id}/{details_id}")
            return

        # Calculate current payer based on proposed payer and payment status
        current_payer = None
        if proposed_payer in (self.F_INSCO_1, self.F_INSCO_2, self.F_INSCO_3, self.F_INSCO_4, self.F_PATIENT):
            current_payer = proposed_payer
        elif (insurances & self.F_INSCO_1 and payment_amount_insco_1 < 0.01 and 
              not (zero_payments & self.F_INSCO_1)):
            current_payer = self.F_INSCO_1
        elif (insurances & self.F_INSCO_2 and payment_amount_insco_2 < 0.01 and 
              not (zero_payments & self.F_INSCO_2)):
            current_payer = self.F_INSCO_2
        elif (insurances & self.F_INSCO_3 and payment_amount_insco_3 < 0.01 and 
              not (zero_payments & self.F_INSCO_3)):
            current_payer = self.F_INSCO_3
        elif (insurances & self.F_INSCO_4 and payment_amount_insco_4 < 0.01 and 
              not (zero_payments & self.F_INSCO_4)):
            current_payer = self.F_INSCO_4
        else:
            current_payer = self.F_PATIENT

        # Update invoice detail
        detail.balance = detail.billable_amount - payment_amount - writeoff_amount
        detail.payment_amount = payment_amount
        detail.writeoff_amount = writeoff_amount
        detail.deductible_amount = deductible_amount

        # Set current payer
        if detail.balance < 0.01:
            detail.current_payer = 'None'
        elif current_payer == self.F_INSCO_1:
            detail.current_payer = 'Ins1'
        elif current_payer == self.F_INSCO_2:
            detail.current_payer = 'Ins2'
        elif current_payer == self.F_INSCO_3:
            detail.current_payer = 'Ins3'
        elif current_payer == self.F_INSCO_4:
            detail.current_payer = 'Ins4'
        elif current_payer == self.F_PATIENT:
            detail.current_payer = 'Patient'
        else:
            detail.current_payer = 'None'

        # Set submitted date based on current payer
        if detail.balance < 0.01:
            detail.submitted_date = None
        elif current_payer == self.F_INSCO_1:
            detail.submitted_date = submit_date_1
        elif current_payer == self.F_INSCO_2:
            detail.submitted_date = submit_date_2
        elif current_payer == self.F_INSCO_3:
            detail.submitted_date = submit_date_3
        elif current_payer == self.F_INSCO_4:
            detail.submitted_date = submit_date_4
        elif current_payer == self.F_PATIENT:
            detail.submitted_date = submit_date_p

        # Set current insurance company and customer insurance IDs
        if detail.balance < 0.01:
            detail.current_insurance_company_id = None
            detail.current_customer_insurance_id = None
        else:
            invoice = self.session.query(Invoice).filter(
                Invoice.customer_id == customer_id,
                Invoice.id == invoice_id
            ).first()

            if invoice:
                if current_payer == self.F_INSCO_1:
                    detail.current_customer_insurance_id = invoice.customer_insurance1_id
                elif current_payer == self.F_INSCO_2:
                    detail.current_customer_insurance_id = invoice.customer_insurance2_id
                elif current_payer == self.F_INSCO_3:
                    detail.current_customer_insurance_id = invoice.customer_insurance3_id
                elif current_payer == self.F_INSCO_4:
                    detail.current_customer_insurance_id = invoice.customer_insurance4_id
                else:
                    detail.current_customer_insurance_id = None

                if detail.current_customer_insurance_id:
                    insurance = self.session.query(CustomerInsurance).filter(
                        CustomerInsurance.id == detail.current_customer_insurance_id,
                        CustomerInsurance.customer_id == customer_id
                    ).first()
                    if insurance:
                        detail.current_insurance_company_id = insurance.insurance_company_id
                    else:
                        detail.current_insurance_company_id = None
                else:
                    detail.current_insurance_company_id = None

        # Set debugging fields
        detail.pendings = pendings
        detail.submits = submits
        detail.payments = (
            (self.F_INSCO_1 if payment_amount_insco_1 >= 0.01 or zero_payments & self.F_INSCO_1 else 0) +
            (self.F_INSCO_2 if payment_amount_insco_2 >= 0.01 or zero_payments & self.F_INSCO_2 else 0) +
            (self.F_INSCO_3 if payment_amount_insco_3 >= 0.01 or zero_payments & self.F_INSCO_3 else 0) +
            (self.F_INSCO_4 if payment_amount_insco_4 >= 0.01 or zero_payments & self.F_INSCO_4 else 0) +
            (self.F_PATIENT if payment_amount_patient >= 0.01 else 0)
        )

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error updating invoice detail {customer_id}/{invoice_id}/{details_id}: {str(e)}")
            raise
