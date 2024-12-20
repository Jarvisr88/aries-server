"""
Deposit Conversion Procedure

Python implementation of the Order_ConvertDepositsIntoPayments stored procedure.
"""
from decimal import Decimal
from datetime import date
from typing import List, Dict, Optional, Any
from sqlalchemy import select, and_, or_, not_, exists
from sqlalchemy.orm import joinedload
from app.models.order import Order, OrderDetail
from app.models.billing import (
    Deposit,
    DepositDetail,
    Invoice,
    InvoiceDetail,
    InvoiceTransaction,
    InvoiceTransactionType
)
from app.procedures.base import BaseProcedure


class ConvertDepositsToPayments(BaseProcedure):
    """
    Converts order deposits into invoice payments.
    
    This procedure:
    1. Identifies deposits without corresponding payments
    2. Creates payment transactions for each deposit
    3. Links payments to invoice details
    4. Updates deposit status
    """

    async def _execute(self, order_id: int) -> Dict[str, Any]:
        """Execute the deposit conversion procedure"""
        # Step 1: Get deposits needing conversion
        deposits = await self._get_unconverted_deposits(order_id)
        
        if not deposits:
            return {'converted_count': 0}

        # Step 2: Create payment transactions
        await self._create_payment_transactions(deposits)
        
        return {'converted_count': len(deposits)}

    async def _get_unconverted_deposits(self, order_id: int) -> List[Dict]:
        """Find deposits that need to be converted to payments"""
        # Get payment transaction type
        payment_type = await self._get_payment_transaction_type()

        # Build query for unconverted deposits
        query = (
            select(
                InvoiceDetail.id.label('invoice_details_id'),
                DepositDetail.amount,
                Deposit.date,
                Deposit.payment_method,
                InvoiceDetail.billable_amount
            )
            .select_from(Order)
            .join(
                OrderDetail,
                and_(
                    OrderDetail.customer_id == Order.customer_id,
                    OrderDetail.order_id == Order.id
                )
            )
            .join(
                Deposit,
                and_(
                    Deposit.customer_id == OrderDetail.customer_id,
                    Deposit.order_id == OrderDetail.order_id
                )
            )
            .join(
                DepositDetail,
                and_(
                    DepositDetail.customer_id == OrderDetail.customer_id,
                    DepositDetail.order_id == OrderDetail.order_id,
                    DepositDetail.order_details_id == OrderDetail.id
                )
            )
            .join(
                Invoice,
                and_(
                    Invoice.customer_id == Order.customer_id,
                    Invoice.order_id == Order.id
                )
            )
            .join(
                InvoiceDetail,
                and_(
                    InvoiceDetail.customer_id == Invoice.customer_id,
                    InvoiceDetail.invoice_id == Invoice.id,
                    InvoiceDetail.billing_month == 1,  # Only first billing month
                    InvoiceDetail.order_id == OrderDetail.order_id,
                    InvoiceDetail.order_details_id == OrderDetail.id
                )
            )
            # Left join to check for existing payments
            .outerjoin(
                InvoiceTransaction,
                and_(
                    InvoiceTransaction.customer_id == InvoiceDetail.customer_id,
                    InvoiceTransaction.invoice_id == InvoiceDetail.invoice_id,
                    InvoiceTransaction.invoice_details_id == InvoiceDetail.id,
                    InvoiceTransaction.insurance_company_id.is_(None),
                    InvoiceTransaction.customer_insurance_id.is_(None),
                    InvoiceTransaction.transaction_type_id == payment_type.id,
                    InvoiceTransaction.transaction_date == Deposit.date,
                    InvoiceTransaction.amount == DepositDetail.amount
                )
            )
            .where(
                and_(
                    Order.id == order_id,
                    InvoiceTransaction.id.is_(None)  # No existing payment
                )
            )
        )

        result = await self.db.execute(query)
        return [dict(row) for row in result]

    async def _get_payment_transaction_type(self) -> InvoiceTransactionType:
        """Get or create Payment transaction type"""
        query = (
            select(InvoiceTransactionType)
            .where(InvoiceTransactionType.name == 'Payment')
        )
        payment_type = (await self.db.execute(query)).scalar_one_or_none()

        if not payment_type:
            payment_type = InvoiceTransactionType(
                name='Payment',
                description='Payment transaction'
            )
            self.db.add(payment_type)
            await self.db.flush()

        return payment_type

    async def _create_payment_transactions(
        self,
        deposits: List[Dict]
    ) -> None:
        """Create payment transactions for deposits"""
        payment_type = await self._get_payment_transaction_type()

        for deposit in deposits:
            # Create payment transaction
            transaction = InvoiceTransaction(
                invoice_details_id=deposit['invoice_details_id'],
                transaction_type_id=payment_type.id,
                transaction_date=deposit['date'],
                amount=deposit['amount'],
                payment_method=deposit['payment_method'],
                description='Converted from deposit',
                created_date=func.now(),
                created_by='system'
            )
            self.db.add(transaction)

            # Update invoice detail if needed
            if deposit['amount'] == deposit['billable_amount']:
                await self._update_invoice_detail_status(
                    deposit['invoice_details_id']
                )

    async def _update_invoice_detail_status(
        self,
        invoice_details_id: int
    ) -> None:
        """Update invoice detail status when fully paid"""
        update_stmt = (
            update(InvoiceDetail)
            .where(InvoiceDetail.id == invoice_details_id)
            .values(
                status='Paid',
                modified_date=func.now(),
                modified_by='system'
            )
        )
        await self.db.execute(update_stmt)
