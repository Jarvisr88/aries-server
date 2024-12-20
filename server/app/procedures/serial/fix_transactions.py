"""
Serial Transaction Fix Procedure

Fixes and reorganizes serial number transactions to maintain proper history.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import (
    select, and_, or_, delete, func,
    Table, Column, Integer, String, DateTime, Boolean,
    MetaData
)
from sqlalchemy.orm import Session

from app.models.serial import (
    SerialNumber,
    SerialTransaction,
    SerialTransactionType
)
from app.models.order import Order, OrderDetail
from app.procedures.base import BaseProcedure
from app.procedures.serial.add_transaction import SerialAddTransaction


class FixSerialTransactions(BaseProcedure):
    """
    Fixes serial number transactions.
    
    This procedure:
    1. Validates transaction history
    2. Removes invalid transactions
    3. Recreates transaction chain
    4. Maintains data integrity
    """

    async def _execute(
        self,
        serial_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the serial transaction fix procedure"""
        # Create temporary tables
        temp_tables = await self._create_temp_tables()

        # Populate initial data
        await self._populate_initial_data(serial_id, temp_tables)

        # Process first transactions
        await self._process_first_transactions(temp_tables)

        # Remove bad entries
        bad_serials = await self._remove_bad_entries(temp_tables)

        # Create transaction chain
        await self._create_transaction_chain(temp_tables)

        # Recreate transactions
        await self._recreate_transactions(temp_tables)

        # Drop temporary tables
        await self._drop_temp_tables(temp_tables)

        return {
            'success': True,
            'bad_serials': bad_serials
        }

    async def _create_temp_tables(self) -> Dict[str, Table]:
        """Create temporary tables for processing"""
        metadata = MetaData()

        # Initial data table
        initial_table = Table(
            'temp_serial_initial',
            metadata,
            Column('serial_id', Integer),
            Column('customer_id', Integer),
            Column('order_id', Integer),
            Column('order_detail_id', Integer),
            Column('warehouse_id', Integer),
            Column('date_reserved', DateTime),
            Column('date_transferred', DateTime),
            Column('date_rented', DateTime),
            Column('date_rent_sold', DateTime),
            Column('date_pickedup', DateTime),
            Column('date_sold', DateTime),
            Column('number', Integer, primary_key=True),
            Column('is_first', Boolean),
            prefixes=['TEMPORARY']
        )

        # Bad entries table
        bad_table = Table(
            'temp_serial_bad',
            metadata,
            Column('serial_id', Integer),
            prefixes=['TEMPORARY']
        )

        # Transaction chain table
        chain_table = Table(
            'temp_serial_chain',
            metadata,
            Column('priority', Integer),
            Column('date_reserved', DateTime),
            Column('customer_id', Integer),
            Column('order_id', Integer),
            Column('order_detail_id', Integer),
            Column('serial_id', Integer),
            Column('warehouse_id', Integer),
            Column('tran_type', String(50)),
            Column('tran_time', DateTime),
            prefixes=['TEMPORARY']
        )

        # Create tables
        await self.db.execute(initial_table.create())
        await self.db.execute(bad_table.create())
        await self.db.execute(chain_table.create())

        return {
            'initial': initial_table,
            'bad': bad_table,
            'chain': chain_table
        }

    async def _populate_initial_data(
        self,
        serial_id: Optional[int],
        tables: Dict[str, Table]
    ) -> None:
        """Populate initial data table"""
        # Build query
        query = (
            select([
                OrderDetail.serial_id,
                OrderDetail.customer_id,
                OrderDetail.order_id,
                OrderDetail.id.label('order_detail_id'),
                OrderDetail.warehouse_id,
                Order.delivery_date.label('date_reserved'),
                func.min(SerialTransaction.transaction_datetime)
                .filter(SerialTransactionType.name == 'Transferred In')
                .label('date_transferred'),
                func.case(
                    (and_(
                        Order.approved == True,
                        OrderDetail.is_rented == True
                    ), Order.delivery_date),
                    else_=None
                ).label('date_rented'),
                func.case(
                    (and_(
                        Order.approved == True,
                        OrderDetail.is_rented == True,
                        OrderDetail.is_active == False,
                        OrderDetail.is_canceled == False,
                        OrderDetail.is_pickedup == False
                    ), OrderDetail.end_date),
                    else_=None
                ).label('date_rent_sold'),
                func.case(
                    (and_(
                        Order.approved == True,
                        OrderDetail.is_rented == True,
                        OrderDetail.is_active == False,
                        OrderDetail.is_canceled == False,
                        OrderDetail.is_pickedup == True
                    ), OrderDetail.end_date),
                    else_=None
                ).label('date_pickedup'),
                func.case(
                    (and_(
                        Order.approved == True,
                        OrderDetail.is_sold == True
                    ), Order.delivery_date),
                    else_=None
                ).label('date_sold')
            ])
            .select_from(Order)
            .join(OrderDetail)
            .join(SerialNumber)
            .outerjoin(
                SerialTransaction,
                and_(
                    SerialTransaction.serial_id == OrderDetail.serial_id,
                    SerialTransaction.warehouse_id == OrderDetail.warehouse_id
                )
            )
            .outerjoin(
                SerialTransactionType,
                SerialTransactionType.id == SerialTransaction.type_id
            )
            .where(
                and_(
                    Order.delivery_date.isnot(None),
                    SerialNumber.inventory_item_id == OrderDetail.inventory_item_id,
                    or_(serial_id.is_(None), SerialNumber.id == serial_id)
                )
            )
            .group_by(
                OrderDetail.serial_id,
                OrderDetail.customer_id,
                OrderDetail.order_id,
                OrderDetail.id,
                OrderDetail.warehouse_id,
                Order.delivery_date,
                Order.approved,
                OrderDetail.is_rented,
                OrderDetail.is_sold,
                OrderDetail.is_active,
                OrderDetail.is_canceled,
                OrderDetail.is_pickedup,
                OrderDetail.end_date
            )
            .order_by(
                OrderDetail.serial_id,
                Order.delivery_date,
                OrderDetail.id
            )
        )

        # Insert data
        await self.db.execute(
            tables['initial'].insert().from_select(
                ['serial_id', 'customer_id', 'order_id', 'order_detail_id',
                 'warehouse_id', 'date_reserved', 'date_transferred',
                 'date_rented', 'date_rent_sold', 'date_pickedup', 'date_sold'],
                query
            )
        )

    async def _process_first_transactions(
        self,
        tables: Dict[str, Table]
    ) -> None:
        """Process and mark first transactions"""
        # Find first transactions
        query = (
            select([
                tables['initial'].c.serial_id,
                func.min(tables['initial'].c.number).label('number')
            ])
            .group_by(tables['initial'].c.serial_id)
        )
        result = await self.db.execute(query)
        first_trans = result.fetchall()

        # Mark first transactions
        for trans in first_trans:
            await self.db.execute(
                tables['initial'].update()
                .where(
                    and_(
                        tables['initial'].c.serial_id == trans.serial_id,
                        tables['initial'].c.number == trans.number
                    )
                )
                .values(is_first=True)
            )

    async def _remove_bad_entries(
        self,
        tables: Dict[str, Table]
    ) -> List[int]:
        """Remove bad entries and return affected serial IDs"""
        # Find bad entries (multiple active rentals/sales)
        query = (
            select([tables['initial'].c.serial_id])
            .group_by(tables['initial'].c.serial_id)
            .having(
                func.sum(
                    func.case(
                        (and_(
                            tables['initial'].c.date_rent_sold.is_(None),
                            tables['initial'].c.date_pickedup.is_(None)
                        ), 1),
                        else_=0
                    )
                ) >= 2
            )
        )
        result = await self.db.execute(query)
        bad_serials = [row.serial_id for row in result]

        # Insert into bad entries table
        if bad_serials:
            await self.db.execute(
                tables['bad'].insert(),
                [{'serial_id': serial_id} for serial_id in bad_serials]
            )

            # Remove bad entries
            await self.db.execute(
                delete(tables['initial'])
                .where(tables['initial'].c.serial_id.in_(bad_serials))
            )

        return bad_serials

    async def _create_transaction_chain(
        self,
        tables: Dict[str, Table]
    ) -> None:
        """Create transaction chain with proper priorities"""
        valid_types = [
            'Reserved', 'Reserve Cancelled', 'Rented', 'Sold',
            'Returned', 'In from Maintenance', 'Transferred In'
        ]

        # Insert transaction chain
        insert_stmt = tables['chain'].insert().from_select(
            ['priority', 'date_reserved', 'customer_id', 'order_id',
             'order_detail_id', 'serial_id', 'warehouse_id',
             'tran_type', 'tran_time'],
            select([
                func.case(
                    (and_(
                        tables['initial'].c.is_first == True,
                        SerialTransactionType.name == 'Transferred In'
                    ), 0),
                    (and_(
                        tables['initial'].c.is_first == False,
                        SerialTransactionType.name == 'In from Maintenance'
                    ), 0),
                    (and_(
                        tables['initial'].c.date_reserved.isnot(None),
                        SerialTransactionType.name == 'Reserved'
                    ), 1),
                    (and_(
                        tables['initial'].c.date_sold.isnot(None),
                        SerialTransactionType.name == 'Sold'
                    ), 2),
                    (and_(
                        tables['initial'].c.date_rented.isnot(None),
                        SerialTransactionType.name == 'Rented'
                    ), 2),
                    (and_(
                        tables['initial'].c.date_rent_sold.isnot(None),
                        SerialTransactionType.name == 'Sold'
                    ), 3),
                    (and_(
                        tables['initial'].c.date_pickedup.isnot(None),
                        SerialTransactionType.name == 'Returned'
                    ), 3)
                ).label('priority'),
                tables['initial'].c.date_reserved,
                tables['initial'].c.customer_id,
                tables['initial'].c.order_id,
                tables['initial'].c.order_detail_id,
                tables['initial'].c.serial_id,
                tables['initial'].c.warehouse_id,
                SerialTransactionType.name.label('tran_type'),
                func.case(
                    (and_(
                        tables['initial'].c.is_first == True,
                        SerialTransactionType.name == 'Transferred In'
                    ), func.coalesce(tables['initial'].c.date_transferred,
                                   tables['initial'].c.date_reserved)),
                    (and_(
                        tables['initial'].c.is_first == False,
                        SerialTransactionType.name == 'In from Maintenance'
                    ), tables['initial'].c.date_reserved),
                    (and_(
                        tables['initial'].c.date_reserved.isnot(None),
                        SerialTransactionType.name == 'Reserved'
                    ), tables['initial'].c.date_reserved),
                    (and_(
                        tables['initial'].c.date_sold.isnot(None),
                        SerialTransactionType.name == 'Sold'
                    ), tables['initial'].c.date_sold),
                    (and_(
                        tables['initial'].c.date_rented.isnot(None),
                        SerialTransactionType.name == 'Rented'
                    ), tables['initial'].c.date_rented),
                    (and_(
                        tables['initial'].c.date_rent_sold.isnot(None),
                        SerialTransactionType.name == 'Sold'
                    ), tables['initial'].c.date_rent_sold),
                    (and_(
                        tables['initial'].c.date_pickedup.isnot(None),
                        SerialTransactionType.name == 'Returned'
                    ), tables['initial'].c.date_pickedup)
                ).label('tran_time')
            ])
            .select_from(SerialTransactionType)
            .join(
                tables['initial'],
                or_(
                    and_(
                        tables['initial'].c.is_first == True,
                        SerialTransactionType.name == 'Transferred In'
                    ),
                    and_(
                        tables['initial'].c.is_first == False,
                        SerialTransactionType.name == 'In from Maintenance'
                    ),
                    and_(
                        tables['initial'].c.date_reserved.isnot(None),
                        SerialTransactionType.name == 'Reserved'
                    ),
                    and_(
                        tables['initial'].c.date_sold.isnot(None),
                        SerialTransactionType.name == 'Sold'
                    ),
                    and_(
                        tables['initial'].c.date_rented.isnot(None),
                        SerialTransactionType.name == 'Rented'
                    ),
                    and_(
                        tables['initial'].c.date_rent_sold.isnot(None),
                        SerialTransactionType.name == 'Sold'
                    ),
                    and_(
                        tables['initial'].c.date_pickedup.isnot(None),
                        SerialTransactionType.name == 'Returned'
                    )
                )
            )
            .where(SerialTransactionType.name.in_(valid_types))
            .order_by(
                tables['initial'].c.serial_id,
                tables['initial'].c.date_reserved,
                tables['initial'].c.order_detail_id,
                'priority'
            )
        )
        await self.db.execute(insert_stmt)

    async def _recreate_transactions(
        self,
        tables: Dict[str, Table]
    ) -> None:
        """Recreate transactions from chain"""
        # Delete existing transactions
        delete_stmt = (
            delete(SerialTransaction)
            .where(
                SerialTransaction.serial_id.in_(
                    select([tables['chain'].c.serial_id])
                    .distinct()
                )
            )
        )
        await self.db.execute(delete_stmt)

        # Get transaction chain
        query = (
            select([
                tables['chain'].c.priority,
                tables['chain'].c.customer_id,
                tables['chain'].c.order_id,
                tables['chain'].c.order_detail_id,
                tables['chain'].c.serial_id,
                tables['chain'].c.warehouse_id,
                tables['chain'].c.tran_type,
                tables['chain'].c.tran_time
            ])
            .order_by(
                tables['chain'].c.serial_id,
                tables['chain'].c.date_reserved,
                tables['chain'].c.order_detail_id,
                tables['chain'].c.priority
            )
        )
        result = await self.db.execute(query)

        # Create new transactions
        add_transaction = SerialAddTransaction(self.db)
        for row in result:
            await add_transaction._execute(
                tran_type=row.tran_type,
                tran_time=row.tran_time,
                serial_id=row.serial_id,
                warehouse_id=row.warehouse_id,
                customer_id=row.customer_id,
                order_id=row.order_id,
                order_detail_id=row.order_detail_id,
                last_update_user_id=1
            )

    async def _drop_temp_tables(
        self,
        tables: Dict[str, Table]
    ) -> None:
        """Drop temporary tables"""
        for table in tables.values():
            await self.db.execute(table.drop())
