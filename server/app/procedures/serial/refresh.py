"""
Serial Refresh Procedure

Python implementation of the serial_refresh stored procedure for
refreshing serial number status and transactions.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.procedures.base import BaseProcedure
from app.procedures.serial.add_transaction import SerialTransactionAdder


class SerialRefresh(BaseProcedure):
    """
    Refreshes serial number status by reprocessing transactions.
    
    This procedure:
    1. Reprocesses serial transactions
    2. Updates serial status
    3. Maintains transaction history
    """
    
    async def _execute(
        self,
        serial_id: int
    ) -> Dict[str, Any]:
        """Execute the serial refresh procedure"""
        if not serial_id:
            return {
                'success': False,
                'error': 'Serial ID required'
            }

        # Create a new transaction adder with minimal info to trigger refresh
        adder = SerialTransactionAdder(
            tran_type=None,
            serial_id=serial_id
        )
        await adder.execute()

        return {
            'success': True,
            'serial_id': serial_id
        }

    @classmethod
    def execute(cls, serial_id: int) -> None:
        """Execute the serial refresh procedure.
        
        Args:
            serial_id: ID of serial number to refresh
        """
        refresher = cls()
        with get_session() as session:
            refresher._execute(serial_id)
            session.commit()
