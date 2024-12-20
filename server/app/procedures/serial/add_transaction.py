"""
Serial Transaction Management

This module handles the addition and processing of serial number transactions,
tracking the movement and status of serialized items through the system.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.serial import SerialTransaction, SerialTransactionType, Serial
from app.procedures.base import BaseProcedure


class SerialTransactionAdder(BaseProcedure):
    """Handles the addition of serial number transactions and updates serial status.
    
    This procedure tracks the movement of serialized items through various states:
    - Reserved (added to unapproved order)
    - Sold (added to approved order)
    - Returned (customer return)
    - O2 Tank states (Empty, Sent for filling, Filled)
    - Transfer states (Out/In between warehouses)
    """
    
    def __init__(
        self,
        tran_type: str,
        serial_id: int,
        tran_time: Optional[datetime] = None,
        warehouse_id: Optional[int] = None,
        vendor_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        order_id: Optional[int] = None,
        order_details_id: Optional[int] = None,
        lot_number: Optional[str] = None,
        last_update_user_id: Optional[int] = None
    ):
        """Initialize the transaction adder.
        
        Args:
            tran_type: Type of transaction (e.g. 'Reserved', 'Sold', 'Returned')
            serial_id: ID of the serial number
            tran_time: Time of transaction (defaults to current time)
            warehouse_id: ID of the warehouse involved
            vendor_id: ID of the vendor involved
            customer_id: ID of the customer involved
            order_id: ID of the related order
            order_details_id: ID of the related order details
            lot_number: Lot number for the item
            last_update_user_id: ID of user making the update
        """
        self.tran_type = tran_type
        self.serial_id = serial_id
        self.tran_time = tran_time or datetime.now()
        self.warehouse_id = warehouse_id
        self.vendor_id = vendor_id
        self.customer_id = customer_id
        self.order_id = order_id
        self.order_details_id = order_details_id
        self.lot_number = lot_number
        self.last_update_user_id = last_update_user_id

    def _execute(self, session: Session) -> None:
        """Execute the transaction addition procedure.
        
        Args:
            session: Database session to use
        """
        if not self.serial_id:
            return

        # Get existing transactions for this serial
        existing_trans = (
            select(SerialTransaction)
            .join(SerialTransactionType)
            .filter(SerialTransaction.serial_id == self.serial_id)
            .order_by(
                SerialTransaction.transaction_datetime,
                SerialTransaction.id
            )
        )
        
        # Get transaction type
        tran_type = (
            session.query(SerialTransactionType)
            .filter(SerialTransactionType.name == self.tran_type)
            .first()
        )
        if not tran_type:
            return

        # Process existing transactions to determine current state
        status = "Unknown"
        current_vendor_id = None
        current_warehouse_id = None
        current_lot_number = None
        sold_date = None
        last_customer_id = None
        current_customer_id = None

        for trans in session.execute(existing_trans).scalars():
            self._update_state(
                trans,
                status,
                current_vendor_id,
                current_warehouse_id,
                current_lot_number,
                sold_date,
                last_customer_id,
                current_customer_id
            )

        # Validate new transaction
        if not self._is_valid_transition(
            status,
            self.tran_type,
            current_warehouse_id,
            current_vendor_id,
            current_customer_id
        ):
            return

        # Create new transaction
        new_trans = SerialTransaction(
            type_id=tran_type.id,
            serial_id=self.serial_id,
            transaction_datetime=self.tran_time,
            warehouse_id=self.warehouse_id,
            vendor_id=self.vendor_id,
            customer_id=self.customer_id,
            order_id=self.order_id,
            order_details_id=self.order_details_id,
            lot_number=self.lot_number,
            last_update_user_id=self.last_update_user_id
        )
        session.add(new_trans)

        # Update serial status
        new_status = self._get_new_status(status, self.tran_type)
        if new_status:
            session.execute(
                update(Serial)
                .where(Serial.id == self.serial_id)
                .values(
                    status=new_status,
                    warehouse_id=self.warehouse_id,
                    vendor_id=self.vendor_id,
                    customer_id=self.customer_id,
                    lot_number=self.lot_number,
                    sold_date=sold_date,
                    last_customer_id=last_customer_id,
                    last_update_user_id=self.last_update_user_id
                )
            )

    def _update_state(
        self,
        trans: SerialTransaction,
        status: str,
        vendor_id: Optional[int],
        warehouse_id: Optional[int],
        lot_number: Optional[str],
        sold_date: Optional[datetime],
        last_customer_id: Optional[int],
        current_customer_id: Optional[int]
    ) -> None:
        """Update the state based on a transaction.
        
        Args:
            trans: Transaction to process
            status: Current status to update
            vendor_id: Current vendor ID to update
            warehouse_id: Current warehouse ID to update
            lot_number: Current lot number to update
            sold_date: Current sold date to update
            last_customer_id: Previous customer ID to update
            current_customer_id: Current customer ID to update
        """
        tran_type = trans.type.name

        if status in ('Unknown', 'On Hand') and tran_type == 'Reserved':
            status = 'Reserved'
            warehouse_id = trans.warehouse_id
            current_customer_id = trans.customer_id

        elif status in ('Unknown', 'Reserved') and tran_type == 'Sold':
            status = 'Sold'
            warehouse_id = trans.warehouse_id
            current_customer_id = trans.customer_id
            sold_date = trans.transaction_datetime.date()

        elif status in ('Unknown', 'Sold', 'On Hand') and tran_type == 'Returned':
            status = 'On Hand'
            warehouse_id = trans.warehouse_id
            last_customer_id = current_customer_id
            current_customer_id = None

        elif status in ('Unknown', 'Empty') and tran_type == 'O2 Tank out for filling':
            status = 'Sent'
            vendor_id = trans.vendor_id
            warehouse_id = None
            current_customer_id = None

        elif status in ('Unknown', 'Sent') and tran_type == 'O2 Tank returned filled':
            status = 'Filled'
            vendor_id = None
            warehouse_id = trans.warehouse_id

        elif status in ('Unknown', 'On Hand') and tran_type == 'Transferred Out':
            status = 'Transferred Out'
            warehouse_id = None

        elif status in ('Unknown', 'Transferred Out') and tran_type == 'Transferred In':
            status = 'On Hand'
            vendor_id = None
            warehouse_id = trans.warehouse_id

    def _is_valid_transition(
        self,
        current_status: str,
        new_tran_type: str,
        warehouse_id: Optional[int],
        vendor_id: Optional[int],
        customer_id: Optional[int]
    ) -> bool:
        """Check if the new transaction represents a valid state transition.
        
        Args:
            current_status: Current status of the serial
            new_tran_type: Type of new transaction
            warehouse_id: Current warehouse ID
            vendor_id: Current vendor ID
            customer_id: Current customer ID
            
        Returns:
            bool: True if transition is valid, False otherwise
        """
        # Reserved can only come from On Hand or Unknown
        if new_tran_type == 'Reserved':
            return current_status in ('Unknown', 'On Hand')

        # Sold can only come from Reserved or Unknown
        elif new_tran_type == 'Sold':
            return current_status in ('Unknown', 'Reserved')

        # Return can come from Sold, On Hand, or Unknown
        elif new_tran_type == 'Returned':
            return current_status in ('Unknown', 'Sold', 'On Hand')

        # O2 Tank out for filling can only come from Empty or Unknown
        elif new_tran_type == 'O2 Tank out for filling':
            return current_status in ('Unknown', 'Empty')

        # O2 Tank returned filled can only come from Sent or Unknown
        elif new_tran_type == 'O2 Tank returned filled':
            return current_status in ('Unknown', 'Sent')

        # Transfer Out can only come from On Hand or Unknown
        elif new_tran_type == 'Transferred Out':
            return current_status in ('Unknown', 'On Hand')

        # Transfer In can only come from Transferred Out or Unknown
        elif new_tran_type == 'Transferred In':
            return current_status in ('Unknown', 'Transferred Out')

        return False

    def _get_new_status(self, current_status: str, tran_type: str) -> Optional[str]:
        """Get the new status based on transaction type and current status.
        
        Args:
            current_status: Current status of the serial
            tran_type: Type of new transaction
            
        Returns:
            Optional[str]: New status if transition is valid, None otherwise
        """
        status_map = {
            'Reserved': {
                ('Unknown', 'On Hand'): 'Reserved'
            },
            'Sold': {
                ('Unknown', 'Reserved'): 'Sold'
            },
            'Returned': {
                ('Unknown', 'Sold', 'On Hand'): 'On Hand'
            },
            'O2 Tank out for filling': {
                ('Unknown', 'Empty'): 'Sent'
            },
            'O2 Tank returned filled': {
                ('Unknown', 'Sent'): 'Filled'
            },
            'Transferred Out': {
                ('Unknown', 'On Hand'): 'Transferred Out'
            },
            'Transferred In': {
                ('Unknown', 'Transferred Out'): 'On Hand'
            }
        }

        if tran_type in status_map:
            for valid_current, new_status in status_map[tran_type].items():
                if current_status in valid_current:
                    return new_status
        return None

    @classmethod
    def execute(
        cls,
        tran_type: str,
        serial_id: int,
        tran_time: Optional[datetime] = None,
        warehouse_id: Optional[int] = None,
        vendor_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        order_id: Optional[int] = None,
        order_details_id: Optional[int] = None,
        lot_number: Optional[str] = None,
        last_update_user_id: Optional[int] = None
    ) -> None:
        """Execute the serial transaction addition procedure.
        
        Args:
            tran_type: Type of transaction (e.g. 'Reserved', 'Sold', 'Returned')
            serial_id: ID of the serial number
            tran_time: Time of transaction (defaults to current time)
            warehouse_id: ID of the warehouse involved
            vendor_id: ID of the vendor involved
            customer_id: ID of the customer involved
            order_id: ID of the related order
            order_details_id: ID of the related order details
            lot_number: Lot number for the item
            last_update_user_id: ID of user making the update
        """
        adder = cls(
            tran_type=tran_type,
            serial_id=serial_id,
            tran_time=tran_time,
            warehouse_id=warehouse_id,
            vendor_id=vendor_id,
            customer_id=customer_id,
            order_id=order_id,
            order_details_id=order_details_id,
            lot_number=lot_number,
            last_update_user_id=last_update_user_id
        )
        with get_session() as session:
            adder._execute(session)
            session.commit()
