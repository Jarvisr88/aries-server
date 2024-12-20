from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
import xml.etree.ElementTree as ET
import re

from app.models.invoice import (
    Invoice,
    InvoiceDetails,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.models.customer import CustomerInsurance
from app.models.user import User
from app.procedures.invoice.recalculate import InvoiceDetailsRecalculator
from app.core.exceptions import ProcedureError
from app.core.logging import logger

class PaymentProcessor:
    """Processes payments and adjustments for invoice details"""
    
    NUMERIC_PATTERN = r'^(-|\+)?([0-9]+\.[0-9]*|[0-9]*\.[0-9]+|[0-9]+)$'
    EPSILON = Decimal('0.01')  # For floating point comparisons

    def __init__(self, db: Session):
        self.db = db

    def _extract_payment_values(self, extra_xml: str) -> Dict[str, Optional[Decimal]]:
        """Extract payment values from XML"""
        try:
            root = ET.fromstring(extra_xml)
            values = {}
            
            # Extract all possible payment values
            fields = [
                'Paid', 'Allowable', 'Deductible', 
                'Sequestration', 'ContractualWriteoff'
            ]
            
            for field in fields:
                value = root.find(f'.//v[@n="{field}"]')
                if value is not None and value.text:
                    if re.match(self.NUMERIC_PATTERN, value.text):
                        values[field] = Decimal(value.text)
                    else:
                        values[field] = None
                else:
                    values[field] = None
                    
            return values
            
        except Exception as e:
            logger.error(f"Error parsing payment XML: {str(e)}")
            raise ProcedureError("Invalid payment XML format")

    def _get_invoice_details(self, 
                           invoice_details_id: int,
                           insurance_company_id: Optional[int]) -> Tuple[InvoiceDetails, Dict[str, Any]]:
        """Get invoice details and related data"""
        # Build query
        query = (
            self.db.query(
                InvoiceDetails,
                CustomerInsurance.id.label('customer_insurance_id'),
                CustomerInsurance.insurance_company_id,
                CustomerInsurance.basis,
            )
            .join(Invoice, and_(
                InvoiceDetails.invoice_id == Invoice.id,
                InvoiceDetails.customer_id == Invoice.customer_id
            ))
            .outerjoin(CustomerInsurance, and_(
                or_(
                    and_(CustomerInsurance.id == Invoice.customer_insurance1_id,
                         InvoiceDetails.bill_ins1 == True),
                    and_(CustomerInsurance.id == Invoice.customer_insurance2_id,
                         InvoiceDetails.bill_ins2 == True),
                    and_(CustomerInsurance.id == Invoice.customer_insurance3_id,
                         InvoiceDetails.bill_ins3 == True),
                    and_(CustomerInsurance.id == Invoice.customer_insurance4_id,
                         InvoiceDetails.bill_ins4 == True)
                ),
                CustomerInsurance.customer_id == Invoice.customer_id,
                CustomerInsurance.insurance_company_id == insurance_company_id
            ))
            .filter(InvoiceDetails.id == invoice_details_id)
        )
        
        result = query.first()
        if not result:
            raise ProcedureError("Invoice details not found")
            
        # Extract data
        detail = result[0]
        insurance_data = {
            'customer_insurance_id': result[1],
            'insurance_company_id': result[2],
            'basis_allowable': result[3] == 'Allowed' if result[3] else False,
            'first_insurance': True  # TODO: Implement proper first insurance logic
        }
        
        return detail, insurance_data

    def _validate_check_number(self,
                             detail: InvoiceDetails,
                             insurance_company_id: Optional[int],
                             check_number: str,
                             posting_guid: str) -> None:
        """Validate check number and posting GUID"""
        if check_number and posting_guid:
            # Check for existing transactions
            count = (
                self.db.query(InvoiceTransaction)
                .join(InvoiceTransactionType)
                .filter(
                    InvoiceTransactionType.name.in_(['Denied', 'Payment']),
                    InvoiceTransaction.customer_id == detail.customer_id,
                    InvoiceTransaction.invoice_id == detail.invoice_id,
                    InvoiceTransaction.invoice_details_id == detail.id,
                    InvoiceTransaction.insurance_company_id == insurance_company_id,
                    InvoiceTransaction.extra.like(f'%CheckNumber>{check_number}</%'),
                    ~InvoiceTransaction.extra.like(f'%PostingGuid>{posting_guid}</%')
                )
                .count()
            )
            
            if count > 0:
                raise ProcedureError(f"Payment for check# {check_number} already exists")

    def _add_transaction(self,
                        detail: InvoiceDetails,
                        insurance_data: Dict[str, Any],
                        transaction_type: str,
                        amount: Decimal,
                        transaction_date: datetime,
                        comments: str,
                        extra: Optional[str],
                        last_update_user_id: int) -> None:
        """Add a transaction record"""
        transaction = InvoiceTransaction(
            invoice_details_id=detail.id,
            invoice_id=detail.invoice_id,
            customer_id=detail.customer_id,
            insurance_company_id=insurance_data.get('insurance_company_id'),
            customer_insurance_id=insurance_data.get('customer_insurance_id'),
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            amount=amount,
            quantity=detail.quantity,
            taxes=Decimal('0.00'),
            batch_number='',
            comments=comments,
            extra=extra,
            approved=True,
            last_update_user_id=last_update_user_id
        )
        self.db.add(transaction)

    def _handle_allowable_adjustment(self,
                                   detail: InvoiceDetails,
                                   insurance_data: Dict[str, Any],
                                   payment_values: Dict[str, Optional[Decimal]],
                                   transaction_date: datetime,
                                   comments: str,
                                   last_update_user_id: int,
                                   options: str) -> None:
        """Handle allowable amount adjustment"""
        if ('Adjust Allowable' in options and
            insurance_data['customer_insurance_id'] and
            insurance_data['insurance_company_id'] and
            insurance_data['first_insurance']):
            
            new_allowable = payment_values.get('Allowable')
            if new_allowable and abs(new_allowable - detail.allowable_amount) >= self.EPSILON:
                # Check if adjustment already exists
                exists = (
                    self.db.query(InvoiceTransaction)
                    .join(InvoiceTransactionType)
                    .filter(
                        InvoiceTransactionType.name == 'Adjust Allowable',
                        InvoiceTransaction.customer_id == detail.customer_id,
                        InvoiceTransaction.invoice_id == detail.invoice_id,
                        InvoiceTransaction.invoice_details_id == detail.id,
                        InvoiceTransaction.insurance_company_id == insurance_data['insurance_company_id']
                    )
                    .first()
                )
                
                if not exists:
                    self._add_transaction(
                        detail=detail,
                        insurance_data=insurance_data,
                        transaction_type='Adjust Allowable',
                        amount=new_allowable,
                        transaction_date=transaction_date,
                        comments=comments,
                        extra=None,
                        last_update_user_id=last_update_user_id
                    )
                    detail.allowable_amount = new_allowable

    def _handle_denied_payment(self,
                             detail: InvoiceDetails,
                             insurance_data: Dict[str, Any],
                             payment_values: Dict[str, Optional[Decimal]],
                             transaction_date: datetime,
                             comments: str,
                             extra: str,
                             last_update_user_id: int,
                             options: str) -> None:
        """Handle denied payment"""
        if 'Post Denied' in options and payment_values.get('Paid', Decimal('0')) == Decimal('0'):
            self._add_transaction(
                detail=detail,
                insurance_data=insurance_data,
                transaction_type='Denied',
                amount=Decimal('0'),
                transaction_date=transaction_date,
                comments=comments,
                extra=extra,
                last_update_user_id=last_update_user_id
            )
        else:
            self._add_transaction(
                detail=detail,
                insurance_data=insurance_data,
                transaction_type='Payment',
                amount=payment_values.get('Paid', Decimal('0')),
                transaction_date=transaction_date,
                comments=comments,
                extra=extra,
                last_update_user_id=last_update_user_id
            )

    def _handle_writeoffs(self,
                         detail: InvoiceDetails,
                         insurance_data: Dict[str, Any],
                         payment_values: Dict[str, Optional[Decimal]],
                         transaction_date: datetime,
                         comments: str,
                         last_update_user_id: int) -> None:
        """Handle various writeoff types"""
        if insurance_data['customer_insurance_id'] and insurance_data['insurance_company_id']:
            # Sequestration writeoff
            seq_amount = payment_values.get('Sequestration')
            if seq_amount and abs(seq_amount) >= self.EPSILON:
                self._add_transaction(
                    detail=detail,
                    insurance_data=insurance_data,
                    transaction_type='Writeoff',
                    amount=seq_amount,
                    transaction_date=transaction_date,
                    comments='Sequestration Writeoff',
                    extra=None,
                    last_update_user_id=last_update_user_id
                )
            
            # Contractual writeoff
            if insurance_data['first_insurance']:
                writeoff_amount = payment_values.get('ContractualWriteoff')
                if writeoff_amount and abs(writeoff_amount) >= self.EPSILON:
                    self._add_transaction(
                        detail=detail,
                        insurance_data=insurance_data,
                        transaction_type='Contractual Writeoff',
                        amount=writeoff_amount,
                        transaction_date=transaction_date,
                        comments=comments,
                        extra=None,
                        last_update_user_id=last_update_user_id
                    )
                elif (insurance_data['basis_allowable'] and 
                      detail.billable_amount - detail.allowable_amount >= self.EPSILON):
                    # Check if writeoff already exists
                    exists = (
                        self.db.query(InvoiceTransaction)
                        .join(InvoiceTransactionType)
                        .filter(
                            InvoiceTransactionType.name == 'Contractual Writeoff',
                            InvoiceTransaction.customer_id == detail.customer_id,
                            InvoiceTransaction.invoice_id == detail.invoice_id,
                            InvoiceTransaction.invoice_details_id == detail.id,
                            InvoiceTransaction.insurance_company_id == insurance_data['insurance_company_id']
                        )
                        .first()
                    )
                    
                    if not exists:
                        self._add_transaction(
                            detail=detail,
                            insurance_data=insurance_data,
                            transaction_type='Contractual Writeoff',
                            amount=detail.billable_amount - detail.allowable_amount,
                            transaction_date=transaction_date,
                            comments=comments,
                            extra=None,
                            last_update_user_id=last_update_user_id
                        )
            
            # Deductible
            if (insurance_data['first_insurance'] and 
                payment_values.get('Deductible', Decimal('0')) >= self.EPSILON):
                # Check if deductible already exists
                exists = (
                    self.db.query(InvoiceTransaction)
                    .join(InvoiceTransactionType)
                    .filter(
                        InvoiceTransactionType.name == 'Deductible',
                        InvoiceTransaction.customer_id == detail.customer_id,
                        InvoiceTransaction.invoice_id == detail.invoice_id,
                        InvoiceTransaction.invoice_details_id == detail.id,
                        InvoiceTransaction.insurance_company_id == insurance_data['insurance_company_id']
                    )
                    .first()
                )
                
                if not exists:
                    self._add_transaction(
                        detail=detail,
                        insurance_data=insurance_data,
                        transaction_type='Deductible',
                        amount=payment_values['Deductible'],
                        transaction_date=transaction_date,
                        comments=comments,
                        extra=None,
                        last_update_user_id=last_update_user_id
                    )

    def _handle_balance_writeoff(self,
                               detail: InvoiceDetails,
                               last_update_user_id: int,
                               options: str) -> None:
        """Handle balance writeoff"""
        if detail.balance >= self.EPSILON:
            if detail.hardship and detail.current_payer == 'Patient':
                comments = 'Hardship Writeoff'
            elif 'Writeoff Balance' in options:
                user = self.db.query(User).get(last_update_user_id)
                comments = f'Wrote off by {user.login if user else "?"}'
            else:
                return
                
            self._add_transaction(
                detail=detail,
                insurance_data={
                    'customer_insurance_id': detail.current_customer_insurance_id,
                    'insurance_company_id': detail.current_insurance_company_id
                },
                transaction_type='Writeoff',
                amount=detail.balance,
                transaction_date=datetime.now(),
                comments=comments,
                extra=None,
                last_update_user_id=last_update_user_id
            )

    def _execute(self,
                invoice_details_id: int,
                insurance_company_id: Optional[int],
                transaction_date: datetime,
                extra: str,
                comments: str,
                options: str,
                last_update_user_id: int) -> str:
        """
        Add payment to invoice details
        
        Args:
            invoice_details_id: ID of invoice details
            insurance_company_id: ID of insurance company (optional)
            transaction_date: Date of transaction
            extra: XML with payment details
            comments: Transaction comments
            options: Comma-separated options
            last_update_user_id: ID of user making update
            
        Returns:
            Result message
            
        Raises:
            ProcedureError: If payment cannot be processed
        """
        try:
            # Parse options
            options = options.split(',') if options else []
            
            # Get payment values
            payment_values = self._extract_payment_values(extra)
            if payment_values.get('Paid') is None:
                return "Paid amount is not specified"
                
            # Get invoice details
            detail, insurance_data = self._get_invoice_details(
                invoice_details_id,
                insurance_company_id
            )
            
            # Validate insurance company
            if bool(insurance_company_id) != bool(insurance_data['insurance_company_id']):
                return "InsuranceCompanyID is wrong"
                
            # Validate check number
            check_number = ET.fromstring(extra).findtext('.//v[@n="CheckNumber"]', '')
            posting_guid = ET.fromstring(extra).findtext('.//v[@n="PostingGuid"]', '')
            self._validate_check_number(detail, insurance_company_id, check_number, posting_guid)
            
            # Process transactions
            self._handle_allowable_adjustment(
                detail, insurance_data, payment_values,
                transaction_date, comments, last_update_user_id, options
            )
            
            self._handle_denied_payment(
                detail, insurance_data, payment_values,
                transaction_date, comments, extra, last_update_user_id, options
            )
            
            self._handle_writeoffs(
                detail, insurance_data, payment_values,
                transaction_date, comments, last_update_user_id
            )
            
            # Recalculate internals
            InvoiceDetailsRecalculator.execute(self.db, None, invoice_details_id)
            
            # Handle balance writeoff
            self._handle_balance_writeoff(detail, last_update_user_id, options)
            
            # Final recalculation if needed
            if detail.balance >= self.EPSILON:
                InvoiceDetailsRecalculator.execute(self.db, None, invoice_details_id)
            
            self.db.commit()
            return "Success"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing payment: {str(e)}")
            raise

    @classmethod
    def execute(cls,
               db: Session,
               invoice_details_id: int,
               insurance_company_id: Optional[int],
               transaction_date: datetime,
               extra: str,
               comments: str,
               options: str,
               last_update_user_id: int) -> str:
        """
        Add payment to invoice details
        
        Args:
            db: Database session
            invoice_details_id: ID of invoice details
            insurance_company_id: ID of insurance company (optional)
            transaction_date: Date of transaction
            extra: XML with payment details
            comments: Transaction comments
            options: Comma-separated options
            last_update_user_id: ID of user making update
            
        Returns:
            Result message
        """
        procedure = cls(db)
        return procedure._execute(
            invoice_details_id,
            insurance_company_id,
            transaction_date,
            extra,
            comments,
            options,
            last_update_user_id
        )
