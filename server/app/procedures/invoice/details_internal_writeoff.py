"""
Invoice Details Internal Writeoff Procedure

Python implementation of the InvoiceDetails_InternalWriteoffBalance stored procedure for
writing off invoice detail balances.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.models.invoice import (
    Invoice,
    InvoiceDetail,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.models.user import User
from app.procedures.base import BaseProcedure


class InvoiceDetailsInternalWriteoff(BaseProcedure):
    """
    Handles internal writeoff of invoice detail balances.
    
    This procedure:
    1. Creates writeoff transactions for invoice details
    2. Handles comma-separated lists of IDs
    3. Only writes off positive balances
    4. Maintains transaction history
    """
    
    async def _execute(
        self,
        invoice_ids: Optional[str],
        invoice_detail_ids: Optional[str],
        last_update_user_id: int
    ) -> Dict[str, Any]:
        """Execute the invoice details writeoff procedure"""
        if not last_update_user_id:
            return {
                'success': False,
                'error': 'User ID required'
            }

        # Get transaction type ID for 'Writeoff'
        tran_type = await self.db.scalar(
            select(InvoiceTransactionType.id)
            .where(InvoiceTransactionType.name == 'Writeoff')
        )
        if not tran_type:
            return {
                'success': False,
                'error': 'Transaction type not found'
            }

        # Get username
        user = await self.db.scalar(
            select(User.login)
            .where(User.id == last_update_user_id)
        )
        if not user:
            return {
                'success': False,
                'error': 'User not found'
            }

        # Create writeoff transactions
        transactions = await self._create_writeoff_transactions(
            invoice_ids=invoice_ids,
            invoice_detail_ids=invoice_detail_ids,
            transaction_type_id=tran_type,
            username=user,
            last_update_user_id=last_update_user_id
        )

        return {
            'success': True,
            'transactions_created': len(transactions)
        }

    async def _create_writeoff_transactions(
        self,
        invoice_ids: Optional[str],
        invoice_detail_ids: Optional[str],
        transaction_type_id: int,
        username: str,
        last_update_user_id: int
    ) -> list[InvoiceTransaction]:
        """Create writeoff transactions"""
        # Build where clause for IDs
        where_conditions = []
        if invoice_ids:
            invoice_id_list = [int(id.strip()) for id in invoice_ids.split(',') if id.strip()]
            if invoice_id_list:
                where_conditions.append(
                    InvoiceDetail.invoice_id.in_(invoice_id_list)
                )

        if invoice_detail_ids:
            detail_id_list = [int(id.strip()) for id in invoice_detail_ids.split(',') if id.strip()]
            if detail_id_list:
                where_conditions.append(
                    InvoiceDetail.id.in_(detail_id_list)
                )

        # Get invoice details to write off
        query = (
            select(InvoiceDetail)
            .where(
                and_(
                    InvoiceDetail.balance >= Decimal('0.01'),
                    or_(*where_conditions) if where_conditions else True
                )
            )
        )
        details = await self.db.execute(query)
        
        transactions = []
        for detail in details.scalars():
            # Create writeoff transaction
            transaction = InvoiceTransaction(
                invoice_details_id=detail.id,
                invoice_id=detail.invoice_id,
                customer_id=detail.customer_id,
                insurance_company_id=detail.current_insurance_company_id,
                customer_insurance_id=detail.current_customer_insurance_id,
                transaction_type_id=transaction_type_id,
                transaction_date=datetime.now(),
                amount=detail.balance,
                quantity=detail.quantity,
                comments=f'Wrote off by {username}',
                taxes=Decimal('0.00'),
                batch_number='',
                extra=None,
                approved=True,
                last_update_user_id=last_update_user_id
            )
            self.db.add(transaction)
            transactions.append(transaction)

        await self.db.flush()
        return transactions
