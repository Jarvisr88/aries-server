"""
Serial Transaction Fix Procedure

Python implementation of the fix_serial_transactions stored procedure.
"""
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import select, text, and_, or_, desc
from sqlalchemy.dialects.postgresql import insert
from app.models.inventory import (
    SerialNumber,
    SerialTransaction,
    SerialTransactionType,
    Warehouse
)
from app.models.order import Order, OrderDetail
from app.procedures.base import BaseProcedure


class FixSerialTransactions(BaseProcedure):
    """
    Fixes and reorganizes serial number transactions.
    
    This procedure:
    1. Creates a temporary table of serial events
    2. Generates transaction priorities
    3. Processes transactions in correct order
    4. Updates serial status and location
    """

    async def _execute(self, serial_id: int) -> None:
        """Execute the serial transaction fix procedure"""
        # Step 1: Create temporary table of serial events
        serial_events = await self._collect_serial_events(serial_id)
        
        # Step 2: Generate transaction priorities
        prioritized_transactions = await self._generate_transaction_priorities(
            serial_events
        )
        
        # Step 3: Process transactions in order
        await self._process_transactions(prioritized_transactions)

    async def _collect_serial_events(self, serial_id: int) -> List[Dict]:
        """Collect all events related to the serial number"""
        query = (
            select(
                OrderDetail.serial_id,
                OrderDetail.customer_id,
                OrderDetail.order_id,
                OrderDetail.id.label('order_details_id'),
                OrderDetail.warehouse_id,
                Order.delivery_date.label('date_reserved'),
                SerialTransaction.time.label('date_transferred'),
                # Rental events
                func.case(
                    (
                        and_(
                            Order.approved == 1,
                            OrderDetail.is_rented == 1
                        ),
                        Order.delivery_date
                    ),
                    else_=None
                ).label('date_rented'),
                # Rental sold events
                func.case(
                    (
                        and_(
                            Order.approved == 1,
                            OrderDetail.is_rented == 1,
                            OrderDetail.is_active == 0,
                            OrderDetail.is_canceled == 0,
                            OrderDetail.is_pickedup == 0
                        ),
                        OrderDetail.end_date
                    ),
                    else_=None
                ).label('date_rent_sold'),
                # Pickup events
                func.case(
                    (
                        and_(
                            Order.approved == 1,
                            OrderDetail.is_rented == 1,
                            OrderDetail.is_active == 0,
                            OrderDetail.is_canceled == 0,
                            OrderDetail.is_pickedup == 1
                        ),
                        OrderDetail.end_date
                    ),
                    else_=None
                ).label('date_pickedup'),
                # Sale events
                func.case(
                    (
                        and_(
                            Order.approved == 1,
                            OrderDetail.is_sold == 1
                        ),
                        Order.delivery_date
                    ),
                    else_=None
                ).label('date_sold')
            )
            .select_from(OrderDetail)
            .join(Order)
            .outerjoin(
                SerialTransaction,
                and_(
                    SerialTransaction.serial_id == OrderDetail.serial_id,
                    SerialTransaction.type == 'Transferred'
                )
            )
            .where(OrderDetail.serial_id == serial_id)
            .distinct()
        )
        
        result = await self.db.execute(query)
        return [dict(row) for row in result]

    async def _generate_transaction_priorities(
        self,
        serial_events: List[Dict]
    ) -> List[Dict]:
        """Generate prioritized list of transactions"""
        transactions = []
        
        for event in serial_events:
            # Initial transfer or maintenance return
            if event.get('is_first') or event.get('date_transferred'):
                transactions.append({
                    'priority': 0,
                    'customer_id': event['customer_id'],
                    'order_id': event['order_id'],
                    'order_details_id': event['order_details_id'],
                    'serial_id': event['serial_id'],
                    'warehouse_id': event['warehouse_id'],
                    'tran_type': 'Transferred In',
                    'tran_time': event['date_transferred']
                })

            # Reservation
            if event.get('date_reserved'):
                transactions.append({
                    'priority': 1,
                    'customer_id': event['customer_id'],
                    'order_id': event['order_id'],
                    'order_details_id': event['order_details_id'],
                    'serial_id': event['serial_id'],
                    'warehouse_id': event['warehouse_id'],
                    'tran_type': 'Reserved',
                    'tran_time': event['date_reserved']
                })

            # Rental
            if event.get('date_rented'):
                transactions.append({
                    'priority': 2,
                    'customer_id': event['customer_id'],
                    'order_id': event['order_id'],
                    'order_details_id': event['order_details_id'],
                    'serial_id': event['serial_id'],
                    'warehouse_id': event['warehouse_id'],
                    'tran_type': 'Rented',
                    'tran_time': event['date_rented']
                })

            # Handle other transaction types...

        # Sort by date and priority
        transactions.sort(
            key=lambda x: (x['tran_time'], x['priority'])
        )
        
        return transactions

    async def _process_transactions(
        self,
        transactions: List[Dict]
    ) -> None:
        """Process transactions in priority order"""
        # Delete existing transactions
        await self.db.execute(
            delete(SerialTransaction)
            .where(SerialTransaction.serial_id == transactions[0]['serial_id'])
        )

        # Create new transactions
        for transaction in transactions:
            new_transaction = SerialTransaction(
                serial_id=transaction['serial_id'],
                customer_id=transaction['customer_id'],
                order_id=transaction['order_id'],
                order_details_id=transaction['order_details_id'],
                warehouse_id=transaction['warehouse_id'],
                type=transaction['tran_type'],
                time=transaction['tran_time']
            )
            self.db.add(new_transaction)

        # Update serial number status
        await self._update_serial_status(
            transactions[-1]  # Use most recent transaction
        )

    async def _update_serial_status(self, last_transaction: Dict) -> None:
        """Update serial number status based on last transaction"""
        status_mapping = {
            'Transferred In': 'Available',
            'Reserved': 'Reserved',
            'Rented': 'Rented',
            'Sold': 'Sold',
            'Picked Up': 'Available'
        }

        await self.db.execute(
            update(SerialNumber)
            .where(SerialNumber.id == last_transaction['serial_id'])
            .values(
                status=status_mapping.get(
                    last_transaction['tran_type'],
                    'Unknown'
                ),
                warehouse_id=last_transaction['warehouse_id'],
                customer_id=last_transaction['customer_id'],
                order_id=last_transaction['order_id'],
                modified_date=func.now(),
                modified_by='system'
            )
        )
