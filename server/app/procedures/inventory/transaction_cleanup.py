"""
Procedure to clean up orphaned or invalid inventory transactions.

This procedure identifies and resolves inconsistencies between
inventory transactions and their related orders, ensuring data integrity
and accurate inventory tracking.
"""
from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.models.inventory import (
    InventoryTransaction,
    InventoryTransactionType,
    InventoryItem
)
from app.models.order import Order, OrderDetails
from app.core.exceptions import ProcedureError

class InventoryTransactionCleanup:
    """Handles cleanup of inventory transactions"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_orphaned_transactions(self) -> List[InventoryTransaction]:
        """Get transactions with missing or invalid order references"""
        return (
            self.db.query(InventoryTransaction)
            .outerjoin(
                Order,
                InventoryTransaction.reference_id == Order.id
            )
            .filter(
                and_(
                    InventoryTransaction.transaction_type.in_([
                        InventoryTransactionType.ORDER_FULFILLMENT,
                        InventoryTransactionType.ORDER_RETURN
                    ]),
                    or_(
                        Order.id.is_(None),
                        Order.status == 'Void'
                    )
                )
            )
            .all()
        )
        
    def _get_duplicate_transactions(self) -> List[Tuple[int, int, int]]:
        """Get duplicate transactions for same order/item combination"""
        return (
            self.db.query(
                InventoryTransaction.reference_id,
                InventoryTransaction.inventory_item_id,
                InventoryTransaction.id
            )
            .filter(InventoryTransaction.reference_id.isnot(None))
            .group_by(
                InventoryTransaction.reference_id,
                InventoryTransaction.inventory_item_id,
                InventoryTransaction.id
            )
            .having(
                func.count() > 1
            )
            .all()
        )
        
    def _get_mismatched_transactions(self) -> List[InventoryTransaction]:
        """Get transactions with quantities not matching order details"""
        return (
            self.db.query(InventoryTransaction)
            .join(
                OrderDetails,
                and_(
                    InventoryTransaction.reference_id == OrderDetails.order_id,
                    InventoryTransaction.inventory_item_id == OrderDetails.inventory_item_id
                )
            )
            .filter(
                and_(
                    InventoryTransaction.transaction_type == InventoryTransactionType.ORDER_FULFILLMENT,
                    InventoryTransaction.quantity != OrderDetails.fulfilled_quantity
                )
            )
            .all()
        )
        
    def _reverse_transaction(
        self,
        transaction: InventoryTransaction,
        reason: str
    ) -> None:
        """Create reversing transaction and update inventory"""
        # Create reversal transaction
        reversal = InventoryTransaction(
            inventory_item_id=transaction.inventory_item_id,
            transaction_type=InventoryTransactionType.CLEANUP,
            quantity=-transaction.quantity,
            reference_id=transaction.reference_id,
            notes=f"Cleanup reversal: {reason}",
            created_at=datetime.utcnow()
        )
        self.db.add(reversal)
        
        # Update inventory quantity
        item = self.db.query(InventoryItem).get(transaction.inventory_item_id)
        if item:
            item.quantity -= transaction.quantity
            
    def _fix_mismatched_transaction(
        self,
        transaction: InventoryTransaction,
        order_detail: OrderDetails
    ) -> None:
        """Adjust transaction to match order detail quantity"""
        difference = order_detail.fulfilled_quantity - transaction.quantity
        
        if difference != 0:
            # Create adjustment transaction
            adjustment = InventoryTransaction(
                inventory_item_id=transaction.inventory_item_id,
                transaction_type=InventoryTransactionType.CLEANUP,
                quantity=difference,
                reference_id=transaction.reference_id,
                notes="Quantity adjustment to match order detail",
                created_at=datetime.utcnow()
            )
            self.db.add(adjustment)
            
            # Update inventory quantity
            item = self.db.query(InventoryItem).get(transaction.inventory_item_id)
            if item:
                item.quantity += difference
                
    def _execute(self) -> None:
        """
        Clean up inventory transactions
        
        This will:
        1. Reverse orphaned transactions
        2. Fix duplicate transactions
        3. Correct mismatched quantities
        """
        # Handle orphaned transactions
        orphaned = self._get_orphaned_transactions()
        for transaction in orphaned:
            self._reverse_transaction(
                transaction,
                "Orphaned transaction - no valid order reference"
            )
            
        # Handle duplicate transactions
        duplicates = self._get_duplicate_transactions()
        for ref_id, item_id, trans_id in duplicates:
            transaction = (
                self.db.query(InventoryTransaction)
                .filter(InventoryTransaction.id == trans_id)
                .first()
            )
            if transaction:
                self._reverse_transaction(
                    transaction,
                    "Duplicate transaction for order/item combination"
                )
                
        # Handle mismatched quantities
        mismatched = self._get_mismatched_transactions()
        for transaction in mismatched:
            order_detail = (
                self.db.query(OrderDetails)
                .filter(
                    and_(
                        OrderDetails.order_id == transaction.reference_id,
                        OrderDetails.inventory_item_id == transaction.inventory_item_id
                    )
                )
                .first()
            )
            if order_detail:
                self._fix_mismatched_transaction(transaction, order_detail)
                
        self.db.commit()
        
    @classmethod
    def execute(cls, db: Session) -> None:
        """
        Clean up inventory transactions
        
        Args:
            db: Database session
        """
        procedure = cls(db)
        procedure._execute()
