"""
Serial Order Refresh Procedure

Python implementation of the serial_order_refresh stored procedure for
managing serial number transactions in orders.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.models.order import Order, OrderDetail
from app.models.inventory import (
    SerialNumber,
    SerialTransaction,
    SerialTransactionType
)
from app.procedures.base import BaseProcedure


@dataclass
class SerialTransactionInfo:
    """Information for creating a serial transaction"""
    priority: int
    customer_id: int
    order_id: int
    order_detail_id: int
    serial_id: int
    warehouse_id: Optional[int]
    tran_type: str
    tran_time: datetime


class SerialOrderRefresh(BaseProcedure):
    """
    Refreshes serial number transactions for orders.
    
    This procedure:
    1. Handles reservations for unapproved orders
    2. Cancels reservations when needed
    3. Updates serial statuses
    4. Maintains transaction history
    """

    async def _execute(
        self,
        order_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the serial order refresh procedure"""
        # Get transactions to process
        transactions = await self._get_transactions(order_id)
        
        if not transactions:
            return {
                'success': False,
                'error': 'No transactions to process'
            }

        # Process each transaction in priority order
        processed_count = 0
        for transaction in sorted(transactions, key=lambda x: x.priority):
            if await self._process_transaction(transaction):
                processed_count += 1

        return {
            'success': True,
            'transactions_processed': processed_count
        }

    async def _get_transactions(
        self,
        order_id: Optional[int]
    ) -> List[SerialTransactionInfo]:
        """Get transactions to process"""
        transactions = []

        # Priority 1: Reserve serials for unapproved orders
        reserve_query = (
            select(
                OrderDetail.customer_id,
                OrderDetail.order_id,
                OrderDetail.id.label('order_detail_id'),
                SerialNumber.id.label('serial_id'),
                Order.order_date
            )
            .join(Order, OrderDetail.order_id == Order.id)
            .join(SerialNumber, and_(
                OrderDetail.serial_id == SerialNumber.id,
                OrderDetail.inventory_item_id == SerialNumber.inventory_item_id
            ))
            .outerjoin(
                SerialTransaction,
                and_(
                    SerialTransaction.customer_id == OrderDetail.customer_id,
                    SerialTransaction.order_id == OrderDetail.order_id,
                    SerialTransaction.order_detail_id == OrderDetail.id,
                    SerialTransaction.transaction_type == 'Reserved'
                )
            )
            .where(
                and_(
                    Order.approved == False,
                    SerialTransaction.id.is_(None)
                )
            )
        )
        
        if order_id:
            reserve_query = reserve_query.where(Order.id == order_id)

        reserve_results = await self.db.execute(reserve_query)
        for row in reserve_results:
            transactions.append(
                SerialTransactionInfo(
                    priority=1,
                    customer_id=row.customer_id,
                    order_id=row.order_id,
                    order_detail_id=row.order_detail_id,
                    serial_id=row.serial_id,
                    warehouse_id=None,
                    tran_type='Reserved',
                    tran_time=row.order_date or datetime.now()
                )
            )

        # Priority 2: Cancel reservations for removed serials
        cancel_query = (
            select(
                SerialTransaction.customer_id,
                SerialTransaction.order_id,
                SerialTransaction.order_detail_id,
                SerialTransaction.serial_id,
                func.now().label('tran_time')
            )
            .outerjoin(
                OrderDetail,
                and_(
                    OrderDetail.id == SerialTransaction.order_detail_id,
                    OrderDetail.serial_id == SerialTransaction.serial_id
                )
            )
            .where(
                and_(
                    SerialTransaction.transaction_type == 'Reserved',
                    OrderDetail.id.is_(None)
                )
            )
        )

        if order_id:
            cancel_query = cancel_query.where(SerialTransaction.order_id == order_id)

        cancel_results = await self.db.execute(cancel_query)
        for row in cancel_results:
            transactions.append(
                SerialTransactionInfo(
                    priority=2,
                    customer_id=row.customer_id,
                    order_id=row.order_id,
                    order_detail_id=row.order_detail_id,
                    serial_id=row.serial_id,
                    warehouse_id=None,
                    tran_type='Reserve Cancelled',
                    tran_time=row.tran_time
                )
            )

        return transactions

    async def _process_transaction(
        self,
        transaction: SerialTransactionInfo
    ) -> bool:
        """Process a single transaction"""
        # Get transaction type
        tran_type_query = (
            select(SerialTransactionType)
            .where(SerialTransactionType.name == transaction.tran_type)
        )
        tran_type = (await self.db.execute(tran_type_query)).scalar_one_or_none()
        
        if not tran_type:
            return False

        # Create transaction
        new_transaction = SerialTransaction(
            customer_id=transaction.customer_id,
            order_id=transaction.order_id,
            order_detail_id=transaction.order_detail_id,
            serial_id=transaction.serial_id,
            warehouse_id=transaction.warehouse_id,
            transaction_type_id=tran_type.id,
            transaction_datetime=transaction.tran_time,
            created_by=1,  # System user
            modified_by=1
        )
        self.db.add(new_transaction)
        await self.db.flush()

        # Update serial status based on transaction type
        status_map = {
            'Reserved': 'Reserved',
            'Reserve Cancelled': 'On Hand'
        }

        if new_status := status_map.get(transaction.tran_type):
            update_stmt = (
                update(SerialNumber)
                .where(SerialNumber.id == transaction.serial_id)
                .values(
                    status=new_status,
                    modified_by=1,
                    modified_date=func.now()
                )
            )
            await self.db.execute(update_stmt)

        return True
