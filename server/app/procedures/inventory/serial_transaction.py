"""
Serial Transaction Addition Procedure

Python implementation of the serial_add_transaction stored procedure.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import joinedload
from app.models.inventory import (
    SerialNumber,
    SerialTransaction,
    SerialTransactionType,
    Warehouse,
    Vendor
)
from app.models.order import Order, OrderDetail
from app.procedures.base import BaseProcedure


class SerialStatus(str, Enum):
    """Serial number status enumeration"""
    UNKNOWN = 'Unknown'
    ON_HAND = 'On Hand'
    RESERVED = 'Reserved'
    RENTED = 'Rented'
    SOLD = 'Sold'
    EMPTY = 'Empty'
    SENT = 'Sent'
    FILLED = 'Filled'
    TRANSFERRED_OUT = 'Transferred Out'


class AddSerialTransaction(BaseProcedure):
    """
    Adds a new serial number transaction and updates serial status.
    
    This procedure:
    1. Validates transaction type and current status
    2. Creates new transaction record
    3. Updates serial number status and relationships
    4. Maintains transaction history
    """

    async def _execute(
        self,
        tran_type: str,
        tran_time: datetime,
        serial_id: int,
        warehouse_id: Optional[int] = None,
        vendor_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        order_id: Optional[int] = None,
        order_details_id: Optional[int] = None,
        lot_number: Optional[str] = None,
        last_update_user_id: int
    ) -> Dict[str, Any]:
        """Execute the serial transaction addition procedure"""
        if not serial_id:
            return {'success': False, 'error': 'Serial ID required'}

        # Get current serial status
        current_status = await self._get_current_serial_status(serial_id)
        
        # Validate transaction
        if not await self._validate_transaction(
            current_status,
            tran_type,
            serial_id
        ):
            return {
                'success': False,
                'error': f'Invalid transaction {tran_type} for status {current_status}'
            }

        # Create transaction
        transaction = await self._create_transaction(
            tran_type,
            tran_time,
            serial_id,
            warehouse_id,
            vendor_id,
            customer_id,
            order_id,
            order_details_id,
            lot_number,
            last_update_user_id
        )

        # Update serial status
        await self._update_serial_status(
            serial_id,
            tran_type,
            warehouse_id,
            vendor_id,
            customer_id,
            order_id,
            lot_number,
            last_update_user_id
        )

        return {'success': True, 'transaction_id': transaction.id}

    async def _get_current_serial_status(self, serial_id: int) -> str:
        """Get current status of serial number"""
        query = (
            select(SerialNumber.status)
            .where(SerialNumber.id == serial_id)
        )
        result = await self.db.execute(query)
        status = result.scalar_one_or_none()
        return status or SerialStatus.UNKNOWN

    async def _validate_transaction(
        self,
        current_status: str,
        tran_type: str,
        serial_id: int
    ) -> bool:
        """Validate if transaction is allowed for current status"""
        # Get transaction type
        tran_type_query = (
            select(SerialTransactionType)
            .where(SerialTransactionType.name == tran_type)
        )
        tran_type_obj = (await self.db.execute(tran_type_query)).scalar_one_or_none()
        
        if not tran_type_obj:
            return False

        # Define valid status transitions
        valid_transitions = {
            ('Unknown', 'Reserved'): True,
            ('On Hand', 'Reserved'): True,
            ('Reserved', 'Rented'): True,
            ('Rented', 'Returned'): True,
            ('Reserved', 'Sold'): True,
            ('On Hand', 'Sold'): True,
            ('Unknown', 'O2 Tank out for filling'): True,
            ('Empty', 'O2 Tank out for filling'): True,
            ('Sent', 'O2 Tank filled'): True,
            ('Unknown', 'Transferred Out'): True,
            ('On Hand', 'Transferred Out'): True,
            ('Unknown', 'Transferred In'): True,
            ('Transferred Out', 'Transferred In'): True
        }

        return valid_transitions.get((current_status, tran_type), False)

    async def _create_transaction(
        self,
        tran_type: str,
        tran_time: datetime,
        serial_id: int,
        warehouse_id: Optional[int],
        vendor_id: Optional[int],
        customer_id: Optional[int],
        order_id: Optional[int],
        order_details_id: Optional[int],
        lot_number: Optional[str],
        last_update_user_id: int
    ) -> SerialTransaction:
        """Create new serial transaction"""
        # Get transaction type
        tran_type_query = (
            select(SerialTransactionType)
            .where(SerialTransactionType.name == tran_type)
        )
        tran_type_obj = (await self.db.execute(tran_type_query)).scalar_one_or_none()

        # Create transaction
        transaction = SerialTransaction(
            serial_id=serial_id,
            transaction_type_id=tran_type_obj.id,
            transaction_datetime=tran_time,
            warehouse_id=warehouse_id,
            vendor_id=vendor_id,
            customer_id=customer_id,
            order_id=order_id,
            order_details_id=order_details_id,
            lot_number=lot_number,
            created_by=last_update_user_id,
            created_date=func.now()
        )
        self.db.add(transaction)
        await self.db.flush()
        return transaction

    async def _update_serial_status(
        self,
        serial_id: int,
        tran_type: str,
        warehouse_id: Optional[int],
        vendor_id: Optional[int],
        customer_id: Optional[int],
        order_id: Optional[int],
        lot_number: Optional[str],
        last_update_user_id: int
    ) -> None:
        """Update serial number status based on transaction"""
        # Define status mapping
        status_mapping = {
            'Reserved': SerialStatus.RESERVED,
            'Rented': SerialStatus.RENTED,
            'Returned': SerialStatus.ON_HAND,
            'Sold': SerialStatus.SOLD,
            'O2 Tank out for filling': SerialStatus.SENT,
            'O2 Tank filled': SerialStatus.FILLED,
            'Transferred Out': SerialStatus.TRANSFERRED_OUT,
            'Transferred In': SerialStatus.ON_HAND
        }

        new_status = status_mapping.get(tran_type)
        if not new_status:
            return

        # Update serial number
        update_stmt = (
            update(SerialNumber)
            .where(SerialNumber.id == serial_id)
            .values(
                status=new_status,
                warehouse_id=warehouse_id,
                vendor_id=vendor_id,
                customer_id=customer_id,
                order_id=order_id,
                lot_number=lot_number,
                modified_by=last_update_user_id,
                modified_date=func.now()
            )
        )
        await self.db.execute(update_stmt)
