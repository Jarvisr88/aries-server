"""
Invoice Internal Writeoff Balance Procedure

Python implementation of the InvoiceDetails_InternalWriteoffBalance stored procedure for
writing off invoice detail balances.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Union, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.models.invoice import (
    InvoiceDetail,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.models.user import User
from app.procedures.base import BaseProcedure


class InvoiceInternalWriteoff(BaseProcedure):
    """
    Handles writing off invoice detail balances.
    
    This procedure:
    1. Creates writeoff transactions
    2. Updates transaction history
    3. Maintains audit trail
    """

    MIN_BALANCE = Decimal('0.01')

    async def _execute(
        self,
        invoice_id: Optional[Union[str, List[str]]] = None,
        invoice_details_id: Optional[Union[str, List[str]]] = None,
        last_update_user_id: int = None
    ) -> Dict[str, Any]:
        """Execute the invoice internal writeoff procedure"""
        if not last_update_user_id:
            return {
                'success': False,
                'error': 'Last Update User ID required'
            }

        # Convert single IDs to lists if provided
        invoice_ids = None
        if invoice_id:
            invoice_ids = [invoice_id] if isinstance(invoice_id, str) else invoice_id

        detail_ids = None
        if invoice_details_id:
            detail_ids = [invoice_details_id] if isinstance(invoice_details_id, str) else invoice_details_id

        # Get transaction type
        transaction_type = await self._get_transaction_type('Writeoff')
        if not transaction_type:
            return {
                'success': False,
                'error': 'Writeoff transaction type not found'
            }

        # Get username for audit
        username = await self._get_username(last_update_user_id)

        # Create writeoff transactions
        transactions_created = await self._create_writeoff_transactions(
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

    async def _create_writeoff_transactions(
        self,
        invoice_ids: Optional[List[str]],
        detail_ids: Optional[List[str]],
        transaction_type_id: int,
        user_id: int,
        username: str
    ) -> int:
        """Create writeoff transactions for specified invoices"""
        # Build base query
        query = select(InvoiceDetail).where(InvoiceDetail.balance >= self.MIN_BALANCE)

        # Add ID filters if provided
        if invoice_ids:
            query = query.where(InvoiceDetail.invoice_id.in_(invoice_ids))
        if detail_ids:
            query = query.where(InvoiceDetail.id.in_(detail_ids))

        result = await self.db.execute(query)
        details = result.scalars().all()

        transactions_created = 0
        now = datetime.utcnow()

        for detail in details:
            # Create writeoff transaction
            transaction = InvoiceTransaction(
                invoice_details_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=detail.current_insurance_company_id,
                customer_insurance_id=detail.current_customer_insurance_id,
                transaction_type_id=transaction_type_id,
                transaction_date=now,
                amount=detail.balance,
                quantity=detail.quantity,
                comments=f'Wrote off by {username}',
                taxes=Decimal('0.00'),
                batch_number='',
                extra=None,
                approved=True,
                last_update_user_id=user_id
            )
            self.db.add(transaction)
            transactions_created += 1

        await self.db.flush()
        return transactions_created
