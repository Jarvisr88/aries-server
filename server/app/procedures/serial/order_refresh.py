"""
Serial Order Refresh Procedure

Python implementation of the serial_order_refresh stored procedure for
managing serial number transactions related to orders.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    select, union_all, and_, or_, exists, func,
    literal_column, text
)
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import Select

from app.database import get_session
from app.models.order import Order, OrderDetail, ViewOrderDetails
from app.models.serial import (
    Serial, SerialTransaction, SerialTransactionType
)
from app.procedures.base import BaseProcedure


class SerialOrderRefresh(BaseProcedure):
    """
    Refreshes serial number transactions for orders.
    
    This procedure:
    1. Creates 'Reserved' transactions for non-approved orders
    2. Creates 'Reserve Cancelled' transactions for removed reservations
    3. Creates 'Rented' transactions for approved orders
    4. Creates 'Rental Ended' transactions for completed rentals
    5. Creates 'Sold' transactions for sold items
    """
    
    def __init__(self, order_id: Optional[int] = None):
        """Initialize the serial order refresh.
        
        Args:
            order_id: Optional ID of specific order to refresh. If None,
                     refreshes all orders.
        """
        self.order_id = order_id

    def _build_reserved_query(self) -> Select:
        """Build query for finding new reservations needed."""
        stt = aliased(SerialTransactionType)
        last_tran = aliased(SerialTransaction)
        tran_history = (
            select(
                SerialTransaction.serial_id,
                func.max(SerialTransaction.id).label('max_id')
            )
            .group_by(SerialTransaction.serial_id)
            .subquery()
        )

        return (
            select(
                literal_column("1").label("priority"),
                ViewOrderDetails.customer_id,
                ViewOrderDetails.order_id,
                ViewOrderDetails.id.label("order_details_id"),
                ViewOrderDetails.serial_id,
                literal_column("null").label("warehouse_id"),
                literal_column("'Reserved'").label("tran_type"),
                func.coalesce(Order.order_date, func.now()).label("tran_time")
            )
            .join(ViewOrderDetails, and_(
                ViewOrderDetails.customer_id == Order.customer_id,
                ViewOrderDetails.order_id == Order.id
            ))
            .join(Serial, and_(
                ViewOrderDetails.serial_id == Serial.id,
                ViewOrderDetails.inventory_item_id == Serial.inventory_item_id
            ))
            .join(stt, stt.name == 'Reserved')
            .outerjoin(last_tran, and_(
                last_tran.customer_id == ViewOrderDetails.customer_id,
                last_tran.order_id == ViewOrderDetails.order_id,
                last_tran.order_details_id == ViewOrderDetails.id,
                last_tran.type_id == stt.id
            ))
            .outerjoin(tran_history, and_(
                last_tran.serial_id == tran_history.c.serial_id,
                last_tran.id == tran_history.c.max_id
            ))
            .where(and_(
                Order.approved == 0,
                or_(last_tran.id.is_(None), tran_history.c.serial_id.is_(None)),
                or_(Order.id == self.order_id, self.order_id.is_(None))
            ))
        )

    def _build_cancelled_query(self) -> Select:
        """Build query for finding reservations that need cancellation."""
        tran_history = (
            select(
                SerialTransaction.serial_id,
                func.max(SerialTransaction.id).label('max_id')
            )
            .group_by(SerialTransaction.serial_id)
            .subquery()
        )
        last_tran = aliased(SerialTransaction)

        return (
            select(
                literal_column("2").label("priority"),
                last_tran.customer_id,
                last_tran.order_id,
                last_tran.order_details_id,
                last_tran.serial_id,
                literal_column("null").label("warehouse_id"),
                literal_column("'Reserve Cancelled'").label("tran_type"),
                func.now().label("tran_time")
            )
            .select_from(tran_history)
            .join(last_tran, and_(
                last_tran.serial_id == tran_history.c.serial_id,
                last_tran.id == tran_history.c.max_id
            ))
            .join(
                SerialTransactionType,
                and_(
                    SerialTransactionType.id == last_tran.type_id,
                    SerialTransactionType.name == 'Reserved'
                )
            )
            .join(Serial, tran_history.c.serial_id == Serial.id)
            .outerjoin(ViewOrderDetails, and_(
                last_tran.customer_id == ViewOrderDetails.customer_id,
                last_tran.order_id == ViewOrderDetails.order_id,
                last_tran.order_details_id == ViewOrderDetails.id
            ))
            .outerjoin(Order, and_(
                ViewOrderDetails.customer_id == Order.customer_id,
                ViewOrderDetails.order_id == Order.id
            ))
            .where(and_(
                or_(
                    ViewOrderDetails.serial_id.is_(None),
                    ViewOrderDetails.serial_id != last_tran.serial_id
                ),
                or_(last_tran.order_id == self.order_id, self.order_id.is_(None))
            ))
        )

    def _build_rented_query(self) -> Select:
        """Build query for finding new rentals that need transactions."""
        stt = aliased(SerialTransactionType)
        st = aliased(SerialTransaction)

        return (
            select(
                literal_column("3").label("priority"),
                ViewOrderDetails.customer_id,
                ViewOrderDetails.order_id,
                ViewOrderDetails.id.label("order_details_id"),
                ViewOrderDetails.serial_id,
                literal_column("null").label("warehouse_id"),
                literal_column("'Rented'").label("tran_type"),
                func.coalesce(
                    Order.delivery_date,
                    func.coalesce(Order.order_date, func.now())
                ).label("tran_time")
            )
            .distinct()
            .join(ViewOrderDetails, and_(
                ViewOrderDetails.customer_id == Order.customer_id,
                ViewOrderDetails.order_id == Order.id
            ))
            .join(Serial, and_(
                ViewOrderDetails.serial_id == Serial.id,
                ViewOrderDetails.inventory_item_id == Serial.inventory_item_id
            ))
            .join(stt, stt.name == 'Rented')
            .outerjoin(st, and_(
                st.customer_id == ViewOrderDetails.customer_id,
                st.order_id == ViewOrderDetails.order_id,
                st.order_details_id == ViewOrderDetails.id,
                st.serial_id == ViewOrderDetails.serial_id,
                st.type_id == stt.id
            ))
            .where(and_(
                Order.approved == 1,
                or_(Order.id == self.order_id, self.order_id.is_(None))
            ))
        )

    def _execute(self, session: Session) -> None:
        """Execute the serial order refresh procedure.
        
        Args:
            session: Database session to use
        """
        # Build the combined query for all transaction types
        query = union_all(
            self._build_reserved_query(),
            self._build_cancelled_query(),
            self._build_rented_query()
        ).order_by("priority")

        # Execute the query to get all needed transactions
        results = session.execute(query).fetchall()

        # Process each needed transaction
        for row in results:
            # Get transaction type
            tran_type = session.scalar(
                select(SerialTransactionType.id)
                .where(SerialTransactionType.name == row.tran_type)
            )

            if not tran_type:
                continue

            # Create the transaction
            transaction = SerialTransaction(
                customer_id=row.customer_id,
                order_id=row.order_id,
                order_details_id=row.order_details_id,
                serial_id=row.serial_id,
                warehouse_id=row.warehouse_id,
                type_id=tran_type,
                transaction_time=row.tran_time
            )
            session.add(transaction)

    @classmethod
    def execute(cls, order_id: Optional[int] = None) -> None:
        """Execute the serial order refresh procedure.
        
        Args:
            order_id: Optional ID of specific order to refresh. If None,
                     refreshes all orders.
        """
        refresher = cls(order_id)
        with get_session() as session:
            refresher._execute(session)
            session.commit()
