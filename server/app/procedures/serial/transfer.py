"""
Serial Transfer Procedure

Python implementation of the serial_transfer stored procedure for
transferring serial numbers between warehouses.
"""
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.serial import Serial, SerialTransaction
from app.procedures.base import BaseProcedure
from app.procedures.serial.add_transaction import SerialAddTransaction


class SerialTransfer(BaseProcedure):
    """
    Handles transferring serial numbers between warehouses.
    
    This procedure:
    1. Records transfer out from source
    2. Records transfer in to destination
    3. Maintains transaction history
    4. Validates transfer integrity
    """

    async def _execute(
        self,
        serial_id: int,
        src_warehouse_id: int,
        dst_warehouse_id: int,
        last_update_user_id: int
    ) -> Dict[str, Any]:
        """Execute the serial transfer procedure"""
        if not all([serial_id, src_warehouse_id, dst_warehouse_id, last_update_user_id]):
            return {
                'success': False,
                'error': 'All parameters required'
            }

        # Get serial info
        serial_info = await self._get_serial_info(serial_id)
        if not serial_info:
            return {
                'success': False,
                'error': f'Serial {serial_id} not found'
            }

        # Get transaction counts before
        count_before = await self._get_transaction_count(serial_id)

        # Create transfer transactions
        add_transaction = SerialAddTransaction(self.db)
        now = datetime.utcnow()

        # Transfer out from source
        await add_transaction.execute(
            tran_type='Transferred Out',
            tran_time=now,
            serial_id=serial_id,
            warehouse_id=src_warehouse_id,
            vendor_id=None,
            customer_id=None,
            order_id=None,
            order_details_id=None,
            lot_number=None,
            last_update_user_id=last_update_user_id
        )

        # Transfer in to destination
        await add_transaction.execute(
            tran_type='Transferred In',
            tran_time=now,
            serial_id=serial_id,
            warehouse_id=dst_warehouse_id,
            vendor_id=None,
            customer_id=None,
            order_id=None,
            order_details_id=None,
            lot_number=None,
            last_update_user_id=last_update_user_id
        )

        # Get transaction counts after
        count_after = await self._get_transaction_count(serial_id)

        # Verify transfer
        if count_after != count_before + 2:
            return {
                'success': False,
                'error': 'Transfer verification failed'
            }

        return {
            'success': True,
            'serial_id': serial_id,
            'inventory_item_id': serial_info[1],
            'src_warehouse': src_warehouse_id,
            'dst_warehouse': dst_warehouse_id,
            'transactions_added': 2
        }

    async def _get_serial_info(
        self,
        serial_id: int
    ) -> Optional[Tuple[int, int]]:
        """Get serial information"""
        query = (
            select(Serial.id, Serial.inventory_item_id)
            .where(Serial.id == serial_id)
        )
        result = await self.db.execute(query)
        return result.one_or_none()

    async def _get_transaction_count(
        self,
        serial_id: int
    ) -> int:
        """Get count of transactions for a serial"""
        query = (
            select(func.count())
            .select_from(SerialTransaction)
            .where(SerialTransaction.serial_id == serial_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
