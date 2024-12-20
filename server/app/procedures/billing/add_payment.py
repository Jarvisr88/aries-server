"""
Invoice Details Payment Addition Procedure

Python implementation of the InvoiceDetails_AddPayment stored procedure for
adding payments to invoice details with XML handling.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from xml.etree import ElementTree as ET
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.models.invoice import (
    InvoiceDetail,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.models.customer import CustomerInsurance
from app.procedures.base import BaseProcedure
from app.procedures.billing.recalculate import InvoiceDetailsRecalculate


class InvoiceDetailsPaymentAdder(BaseProcedure):
    """
    Adds payments to invoice details.
    
    This procedure:
    1. Extracts payment info from XML
    2. Validates payment amounts
    3. Creates payment transactions
    4. Updates invoice balances
    """

    async def _execute(
        self,
        invoice_detail_id: int,
        insurance_company_id: int,
        transaction_date: datetime,
        extra_xml: str,
        comments: Optional[str] = None,
        options: Optional[str] = None,
        last_update_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the payment addition procedure"""
        if not all([invoice_detail_id, insurance_company_id, transaction_date]):
            return {
                'success': False,
                'error': 'Required parameters missing'
            }

        # Extract payment info from XML
        payment_info = self._extract_payment_info(extra_xml)
        if not payment_info['success']:
            return payment_info

        # Get invoice detail info
        detail_info = await self._get_detail_info(
            invoice_detail_id,
            insurance_company_id
        )
        if not detail_info['success']:
            return detail_info

        # Validate payment amounts
        if not self._validate_amounts(payment_info['amounts']):
            return {
                'success': False,
                'error': 'Invalid payment amounts'
            }

        # Create payment transactions
        await self._create_payment_transactions(
            detail_info['detail'],
            payment_info['amounts'],
            transaction_date,
            comments,
            last_update_user_id
        )

        # Recalculate invoice
        recalc = InvoiceDetailsRecalculate(self.db)
        await recalc.execute(invoice_detail_id=invoice_detail_id)

        return {
            'success': True,
            'detail_id': invoice_detail_id
        }

    def _extract_payment_info(self, extra_xml: str) -> Dict[str, Any]:
        """Extract payment information from XML"""
        try:
            root = ET.fromstring(extra_xml)
            amounts = {}
            for value in root.findall(".//v[@n]"):
                name = value.get('n')
                text = value.text or ''
                
                # Convert amounts to Decimal if numeric
                try:
                    if name in ['Paid', 'Allowable', 'Deductible', 
                              'Sequestration', 'ContractualWriteoff']:
                        amounts[name] = Decimal(text) if text.strip() else Decimal('0.00')
                    else:
                        amounts[name] = text
                except:
                    amounts[name] = Decimal('0.00')

            return {
                'success': True,
                'amounts': amounts
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse XML: {str(e)}'
            }

    async def _get_detail_info(
        self,
        invoice_detail_id: int,
        insurance_company_id: int
    ) -> Dict[str, Any]:
        """Get invoice detail information"""
        query = (
            select(InvoiceDetail)
            .join(InvoiceDetail.invoice)
            .outerjoin(
                CustomerInsurance,
                and_(
                    CustomerInsurance.customer_id == InvoiceDetail.customer_id,
                    or_(
                        and_(
                            CustomerInsurance.id == InvoiceDetail.invoice.customer_insurance1_id,
                            InvoiceDetail.bill_ins1 == True
                        ),
                        and_(
                            CustomerInsurance.id == InvoiceDetail.invoice.customer_insurance2_id,
                            InvoiceDetail.bill_ins2 == True
                        ),
                        and_(
                            CustomerInsurance.id == InvoiceDetail.invoice.customer_insurance3_id,
                            InvoiceDetail.bill_ins3 == True
                        ),
                        and_(
                            CustomerInsurance.id == InvoiceDetail.invoice.customer_insurance4_id,
                            InvoiceDetail.bill_ins4 == True
                        )
                    )
                )
            )
            .where(
                and_(
                    InvoiceDetail.id == invoice_detail_id,
                    CustomerInsurance.insurance_company_id == insurance_company_id
                )
            )
        )
        result = await self.db.execute(query)
        detail = result.scalar_one_or_none()

        if not detail:
            return {
                'success': False,
                'error': 'Invoice detail not found'
            }

        return {
            'success': True,
            'detail': detail
        }

    def _validate_amounts(self, amounts: Dict[str, Any]) -> bool:
        """Validate payment amounts"""
        # Paid amount is required
        if not amounts.get('Paid'):
            return False

        # All amounts must be non-negative
        for amount in amounts.values():
            if isinstance(amount, Decimal) and amount < 0:
                return False

        return True

    async def _create_payment_transactions(
        self,
        detail: InvoiceDetail,
        amounts: Dict[str, Any],
        transaction_date: datetime,
        comments: Optional[str],
        last_update_user_id: Optional[int]
    ) -> None:
        """Create payment transactions"""
        # Get transaction types
        types_query = (
            select(InvoiceTransactionType)
            .where(
                InvoiceTransactionType.name.in_([
                    'Payment',
                    'Allowable Adjustment',
                    'Deductible',
                    'Sequestration',
                    'Contractual Writeoff'
                ])
            )
        )
        result = await self.db.execute(types_query)
        tran_types = {t.name: t for t in result.scalars().all()}

        # Create payment transaction
        payment = InvoiceTransaction(
            invoice_detail_id=detail.id,
            invoice_id=detail.invoice_id,
            customer_id=detail.customer_id,
            insurance_company_id=detail.insurance_company_id,
            customer_insurance_id=detail.customer_insurance_id,
            transaction_type_id=tran_types['Payment'].id,
            transaction_date=transaction_date,
            amount=amounts['Paid'],
            quantity=detail.quantity,
            comments=comments,
            last_update_user_id=last_update_user_id,
            check_number=amounts.get('CheckNumber'),
            posting_guid=amounts.get('PostingGuid')
        )
        self.db.add(payment)

        # Create allowable adjustment if needed
        if amounts.get('Allowable'):
            allowable = InvoiceTransaction(
                invoice_detail_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=detail.insurance_company_id,
                customer_insurance_id=detail.customer_insurance_id,
                transaction_type_id=tran_types['Allowable Adjustment'].id,
                transaction_date=transaction_date,
                amount=amounts['Allowable'],
                quantity=detail.quantity,
                comments=comments,
                last_update_user_id=last_update_user_id
            )
            self.db.add(allowable)

        # Create deductible transaction if needed
        if amounts.get('Deductible'):
            deductible = InvoiceTransaction(
                invoice_detail_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=detail.insurance_company_id,
                customer_insurance_id=detail.customer_insurance_id,
                transaction_type_id=tran_types['Deductible'].id,
                transaction_date=transaction_date,
                amount=amounts['Deductible'],
                quantity=detail.quantity,
                comments=comments,
                last_update_user_id=last_update_user_id
            )
            self.db.add(deductible)

        # Create sequestration transaction if needed
        if amounts.get('Sequestration'):
            sequestration = InvoiceTransaction(
                invoice_detail_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=detail.insurance_company_id,
                customer_insurance_id=detail.customer_insurance_id,
                transaction_type_id=tran_types['Sequestration'].id,
                transaction_date=transaction_date,
                amount=amounts['Sequestration'],
                quantity=detail.quantity,
                comments=comments,
                last_update_user_id=last_update_user_id
            )
            self.db.add(sequestration)

        # Create contractual writeoff transaction if needed
        if amounts.get('ContractualWriteoff'):
            writeoff = InvoiceTransaction(
                invoice_detail_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=detail.insurance_company_id,
                customer_insurance_id=detail.customer_insurance_id,
                transaction_type_id=tran_types['Contractual Writeoff'].id,
                transaction_date=transaction_date,
                amount=amounts['ContractualWriteoff'],
                quantity=detail.quantity,
                comments=comments,
                last_update_user_id=last_update_user_id
            )
            self.db.add(writeoff)

        await self.db.flush()
