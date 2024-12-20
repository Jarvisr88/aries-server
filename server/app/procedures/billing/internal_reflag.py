"""
Invoice Internal Reflag Procedure

Python implementation of the InvoiceDetails_InternalReflag stored procedure for
handling internal reflagging of invoice transactions.
"""
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.models.invoice import (
    InvoiceDetail,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.models.user import User
from app.procedures.base import BaseProcedure


class InvoiceInternalReflag(BaseProcedure):
    """
    Handles internal reflagging of invoice transactions.
    
    This procedure:
    1. Creates void transactions for specified invoices
    2. Updates transaction history
    3. Maintains audit trail
    """

    # Insurance flag constants
    INSURANCE_FLAGS = {
        'Ins1': 0x01,
        'Ins2': 0x02,
        'Ins3': 0x04,
        'Ins4': 0x08,
        'Patient': 0x10
    }

    async def _execute(
        self,
        invoice_id: Union[str, List[str]],
        invoice_details_id: Union[str, List[str]],
        last_update_user_id: int
    ) -> Dict[str, Any]:
        """Execute the invoice internal reflag procedure"""
        if not invoice_id or not invoice_details_id or not last_update_user_id:
            return {
                'success': False,
                'error': 'Required parameters missing'
            }

        # Convert single IDs to lists
        invoice_ids = [invoice_id] if isinstance(invoice_id, str) else invoice_id
        detail_ids = [invoice_details_id] if isinstance(invoice_details_id, str) else invoice_details_id

        # Get transaction type ID
        transaction_type = await self._get_transaction_type('Voided Submission')
        if not transaction_type:
            return {
                'success': False,
                'error': 'Transaction type not found'
            }

        # Get username for audit
        username = await self._get_username(last_update_user_id)

        # Create void transactions
        transactions_created = await self._create_void_transactions(
            invoice_ids,
            detail_ids,
            transaction_type.id,
            last_update_user_id,
            username
        )

        return {
            'success': True,
            'transactions_created': transactions_created
        }

    async def _get_transaction_type(
        self,
        type_name: str
    ) -> Optional[InvoiceTransactionType]:
        """Get transaction type by name"""
        query = (
            select(InvoiceTransactionType)
            .where(InvoiceTransactionType.name == type_name)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_username(
        self,
        user_id: int
    ) -> str:
        """Get username for audit trail"""
        query = (
            select(User.login)
            .where(User.id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() or ''

    async def _create_void_transactions(
        self,
        invoice_ids: List[str],
        detail_ids: List[str],
        transaction_type_id: int,
        user_id: int,
        username: str
    ) -> int:
        """Create void transactions for specified invoices"""
        # Get invoice details
        query = (
            select(InvoiceDetail)
            .where(
                and_(
                    InvoiceDetail.invoice_id.in_(invoice_ids),
                    InvoiceDetail.id.in_(detail_ids)
                )
            )
        )
        result = await self.db.execute(query)
        details = result.scalars().all()

        transactions_created = 0
        now = datetime.utcnow()

        for detail in details:
            # Create void transaction
            transaction = InvoiceTransaction(
                invoice_details_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=self._get_insurance_company_id(detail),
                customer_insurance_id=self._get_customer_insurance_id(detail),
                transaction_type_id=transaction_type_id,
                amount=detail.amount,
                quantity=detail.quantity,
                transaction_date=now,
                batch_number=None,
                comments=f'Voided by {username}',
                last_update_user_id=user_id
            )
            self.db.add(transaction)
            transactions_created += 1

        await self.db.flush()
        return transactions_created

    def _get_insurance_company_id(
        self,
        detail: InvoiceDetail
    ) -> Optional[int]:
        """Get appropriate insurance company ID based on current payer"""
        payer_map = {
            'Patient': None,
            'Ins4': detail.insurance_company4_id,
            'Ins3': detail.insurance_company3_id,
            'Ins2': detail.insurance_company2_id,
            'Ins1': detail.insurance_company1_id
        }
        return payer_map.get(detail.current_payer)

    def _get_customer_insurance_id(
        self,
        detail: InvoiceDetail
    ) -> Optional[int]:
        """Get appropriate customer insurance ID based on current payer"""
        payer_map = {
            'Patient': None,
            'Ins4': detail.insurance4_id,
            'Ins3': detail.insurance3_id,
            'Ins2': detail.insurance2_id,
            'Ins1': detail.insurance1_id
        }
        return payer_map.get(detail.current_payer)
