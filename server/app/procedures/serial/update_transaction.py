"""
Serial Transaction Update Procedure

Updates serial number transaction details and refreshes serial status.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, and_, update
from sqlalchemy.orm import Session

from app.models.serial import SerialTransaction, SerialNumber
from app.procedures.base import BaseProcedure
from app.procedures.serial.refresh import SerialRefresh


class SerialUpdateTransaction(BaseProcedure):
    """
    Updates a serial number transaction and refreshes the serial status.
    
    This procedure:
    1. Updates transaction details
    2. Maintains transaction history
    3. Refreshes serial status
    """

    async def _execute(
        self,
        transaction_id: int,
        tran_time: Optional[datetime] = None,
        warehouse_id: Optional[int] = None,
        vendor_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        lot_number: Optional[str] = None,
        last_update_user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the serial transaction update procedure"""
        if not transaction_id:
            return {
                'success': False,
                'error': 'Transaction ID required'
            }

        # Get serial ID from transaction
        query = (
            select(SerialTransaction.serial_id)
            .where(SerialTransaction.id == transaction_id)
        )
        result = await self.db.execute(query)
        serial_id = result.scalar_one_or_none()

        if not serial_id:
            return {
                'success': False,
                'error': 'Serial transaction not found'
            }

        # Update transaction
        update_stmt = (
            update(SerialTransaction)
            .where(SerialTransaction.id == transaction_id)
            .values(
                transaction_datetime=tran_time or datetime.now(),
                vendor_id=vendor_id,
                warehouse_id=warehouse_id,
                customer_id=customer_id,
                lot_number=lot_number or '',
                last_update_datetime=datetime.now(),
                last_update_user_id=last_update_user_id or 1
            )
        )
        await self.db.execute(update_stmt)

        # Refresh serial status
        refresh = SerialRefresh(self.db)
        await refresh._execute(serial_id)

        return {
            'success': True,
            'serial_id': serial_id
        }
