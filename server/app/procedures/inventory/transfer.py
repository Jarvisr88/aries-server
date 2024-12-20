from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy import select, update, and_
from sqlalchemy.orm import Session

from app.models.inventory import (
    InventoryItem,
    InventoryTransaction,
    InventoryTransactionType,
    WarehouseInventory
)
from app.core.exceptions import ProcedureError
from app.core.logging import logger

class InventoryTransferProcessor:
    """Processes inventory transfers between warehouses"""
    
    def __init__(self, db: Session):
        self.db = db

    def _get_warehouse_inventory(self, 
                               item_id: int, 
                               warehouse_id: int) -> Optional[WarehouseInventory]:
        """Get warehouse inventory record, creating if needed"""
        inventory = (
            self.db.query(WarehouseInventory)
            .filter(
                WarehouseInventory.inventory_item_id == item_id,
                WarehouseInventory.warehouse_id == warehouse_id
            )
            .first()
        )
        
        if not inventory:
            inventory = WarehouseInventory(
                inventory_item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=0,
                last_update_user_id=0
            )
            self.db.add(inventory)
            self.db.flush()
            
        return inventory

    def _validate_transfer(self,
                         src_inventory: WarehouseInventory,
                         quantity: int) -> None:
        """Validate transfer is possible"""
        if src_inventory.quantity < quantity:
            raise ProcedureError(
                f"Insufficient quantity in source warehouse. "
                f"Available: {src_inventory.quantity}, Requested: {quantity}"
            )

    def _create_transaction(self,
                          item_id: int,
                          warehouse_id: int,
                          quantity: int,
                          transaction_type: str,
                          last_update_user_id: int,
                          reference: str) -> InventoryTransaction:
        """Create inventory transaction record"""
        transaction = InventoryTransaction(
            inventory_item_id=item_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            transaction_type=transaction_type,
            transaction_date=datetime.now(),
            reference=reference,
            last_update_user_id=last_update_user_id
        )
        self.db.add(transaction)
        return transaction

    def _update_quantities(self,
                         src_inventory: WarehouseInventory,
                         dst_inventory: WarehouseInventory,
                         quantity: int) -> None:
        """Update warehouse quantities"""
        src_inventory.quantity -= quantity
        dst_inventory.quantity += quantity

    def internal_transfer(self,
                         item_id: int,
                         src_warehouse_id: int,
                         dst_warehouse_id: int,
                         quantity: int,
                         reference: str,
                         last_update_user_id: int) -> Tuple[InventoryTransaction, InventoryTransaction]:
        """
        Internal helper to process inventory transfer
        
        Args:
            item_id: ID of inventory item
            src_warehouse_id: Source warehouse ID
            dst_warehouse_id: Destination warehouse ID
            quantity: Quantity to transfer
            reference: Reference text for transaction
            last_update_user_id: ID of user making update
            
        Returns:
            Tuple of (source transaction, destination transaction)
            
        Raises:
            ProcedureError: If transfer cannot be completed
        """
        try:
            # Get warehouse inventories
            src_inventory = self._get_warehouse_inventory(item_id, src_warehouse_id)
            dst_inventory = self._get_warehouse_inventory(item_id, dst_warehouse_id)
            
            # Validate transfer
            self._validate_transfer(src_inventory, quantity)
            
            # Create transactions
            src_transaction = self._create_transaction(
                item_id=item_id,
                warehouse_id=src_warehouse_id,
                quantity=-quantity,  # Negative for source
                transaction_type='Transfer Out',
                last_update_user_id=last_update_user_id,
                reference=reference
            )
            
            dst_transaction = self._create_transaction(
                item_id=item_id,
                warehouse_id=dst_warehouse_id,
                quantity=quantity,  # Positive for destination
                transaction_type='Transfer In',
                last_update_user_id=last_update_user_id,
                reference=reference
            )
            
            # Update quantities
            self._update_quantities(src_inventory, dst_inventory, quantity)
            
            return src_transaction, dst_transaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in internal transfer: {str(e)}")
            raise

    def _execute(self,
                item_id: int,
                src_warehouse_id: int,
                dst_warehouse_id: int,
                quantity: int,
                last_update_user_id: int) -> Tuple[InventoryTransaction, InventoryTransaction]:
        """
        Process inventory transfer between warehouses
        
        Args:
            item_id: ID of inventory item
            src_warehouse_id: Source warehouse ID
            dst_warehouse_id: Destination warehouse ID
            quantity: Quantity to transfer
            last_update_user_id: ID of user making update
            
        Returns:
            Tuple of (source transaction, destination transaction)
        """
        transactions = self.internal_transfer(
            item_id=item_id,
            src_warehouse_id=src_warehouse_id,
            dst_warehouse_id=dst_warehouse_id,
            quantity=quantity,
            reference='Inventory Transfer',
            last_update_user_id=last_update_user_id
        )
        
        self.db.commit()
        return transactions

    @classmethod
    def execute(cls,
               db: Session,
               item_id: int,
               src_warehouse_id: int,
               dst_warehouse_id: int,
               quantity: int,
               last_update_user_id: int) -> Tuple[InventoryTransaction, InventoryTransaction]:
        """
        Process inventory transfer between warehouses
        
        Args:
            db: Database session
            item_id: ID of inventory item
            src_warehouse_id: Source warehouse ID
            dst_warehouse_id: Destination warehouse ID
            quantity: Quantity to transfer
            last_update_user_id: ID of user making update
            
        Returns:
            Tuple of (source transaction, destination transaction)
        """
        procedure = cls(db)
        return procedure._execute(
            item_id,
            src_warehouse_id,
            dst_warehouse_id,
            quantity,
            last_update_user_id
        )
