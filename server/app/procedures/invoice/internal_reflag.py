"""
Invoice Internal Reflag Procedure

Python implementation of the Invoice_InternalReflag stored procedure for
handling invoice transaction reflagging.
"""
from datetime import date
from enum import IntFlag
from typing import Dict, Any, Optional
from sqlalchemy import select, and_, or_, text
from sqlalchemy.orm import Session

from app.models.invoice import (
    Invoice,
    InvoiceTransaction,
    InvoiceTransactionType,
    ViewInvoiceTransactionStatistics
)
from app.models.user import User
from app.procedures.base import BaseProcedure


class PayerFlags(IntFlag):
    """Payer type flags"""
    INSURANCE_1 = 0x01
    INSURANCE_2 = 0x02
    INSURANCE_3 = 0x04
    INSURANCE_4 = 0x08
    PATIENT = 0x10


class InvoiceInternalReflag(BaseProcedure):
    """
    Handles internal reflagging of invoice transactions.
    
    This procedure:
    1. Creates voided submission transactions
    2. Maps current payers to insurance companies
    3. Handles XML extra data
    4. Maintains transaction history
    """

    async def _execute(
        self,
        invoice_id: int,
        extra: Optional[str],
        last_update_user_id: int
    ) -> Dict[str, Any]:
        """Execute the invoice internal reflag procedure"""
        if not invoice_id or not last_update_user_id:
            return {
                'success': False,
                'error': 'Invoice ID and User ID required'
            }

        # Validate XML extra data
        if extra and not (
            extra.startswith('<values>') and extra.endswith('</values>') or
            extra.startswith('<values') and extra.endswith('/>')
        ):
            extra = None

        # Get transaction type ID for 'Voided Submission'
        tran_type = await self.db.scalar(
            select(InvoiceTransactionType.id)
            .where(InvoiceTransactionType.name == 'Voided Submission')
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

        # Create new transactions
        transactions = await self._create_transactions(
            invoice_id=invoice_id,
            transaction_type_id=tran_type,
            username=user,
            extra=extra,
            last_update_user_id=last_update_user_id
        )

        return {
            'success': True,
            'transactions_created': len(transactions)
        }

    async def _create_transactions(
        self,
        invoice_id: int,
        transaction_type_id: int,
        username: str,
        extra: Optional[str],
        last_update_user_id: int
    ) -> list[InvoiceTransaction]:
        """Create voided submission transactions"""
        # Get invoice statistics
        query = (
            select(ViewInvoiceTransactionStatistics)
            .where(ViewInvoiceTransactionStatistics.invoice_id == invoice_id)
        )
        stats = await self.db.execute(query)
        
        transactions = []
        for stat in stats:
            # Check if transaction should be created based on payer flags
            create_transaction = False
            if stat.current_payer == 'Patient' and stat.submits & PayerFlags.PATIENT:
                create_transaction = True
            elif stat.current_payer == 'Ins4' and stat.submits & PayerFlags.INSURANCE_4:
                create_transaction = True
            elif stat.current_payer == 'Ins3' and stat.submits & PayerFlags.INSURANCE_3:
                create_transaction = True
            elif stat.current_payer == 'Ins2' and stat.submits & PayerFlags.INSURANCE_2:
                create_transaction = True
            elif stat.current_payer == 'Ins1' and stat.submits & PayerFlags.INSURANCE_1:
                create_transaction = True

            if not create_transaction:
                continue

            # Map insurance company and customer insurance IDs
            insurance_company_id = None
            customer_insurance_id = None
            if stat.current_payer == 'Ins4':
                insurance_company_id = stat.insurance_company4_id
                customer_insurance_id = stat.insurance4_id
            elif stat.current_payer == 'Ins3':
                insurance_company_id = stat.insurance_company3_id
                customer_insurance_id = stat.insurance3_id
            elif stat.current_payer == 'Ins2':
                insurance_company_id = stat.insurance_company2_id
                customer_insurance_id = stat.insurance2_id
            elif stat.current_payer == 'Ins1':
                insurance_company_id = stat.insurance_company1_id
                customer_insurance_id = stat.insurance1_id

            # Create transaction
            transaction = InvoiceTransaction(
                invoice_details_id=stat.invoice_details_id,
                invoice_id=stat.invoice_id,
                customer_id=stat.customer_id,
                insurance_company_id=insurance_company_id,
                customer_insurance_id=customer_insurance_id,
                transaction_type_id=transaction_type_id,
                amount=stat.billable_amount,
                quantity=stat.quantity,
                transaction_date=date.today(),
                batch_number=None,
                comments=f'Reflagged by {username}',
                extra=extra,
                last_update_user_id=last_update_user_id
            )
            self.db.add(transaction)
            transactions.append(transaction)

        await self.db.flush()
        return transactions
