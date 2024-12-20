from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.inventory import Inventory
from app.procedures.inventory.refresh import InventoryRefresher
from app.procedures.inventory.transaction import InventoryTransactionAdder

class InternalInventoryTransfer:
    """Handles internal transfers of inventory items between warehouses"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_inventory_info(self,
                          inventory_item_id: int,
                          warehouse_id: int) -> Tuple[int, Decimal]:
        """
        Get current inventory information for an item in a warehouse
        
        Args:
            inventory_item_id: ID of inventory item
            warehouse_id: ID of warehouse
            
        Returns:
            Tuple of (on_hand_quantity, cost_per_unit)
            
        Raises:
            ValueError: If inventory record not found
        """
        inventory = (
            self.db.query(Inventory)
            .filter(
                Inventory.inventory_item_id == inventory_item_id,
                Inventory.warehouse_id == warehouse_id
            )
            .first()
        )
        
        if not inventory:
            return (0, Decimal('0.00'))
            
        return (inventory.on_hand or 0, inventory.cost_per_unit or Decimal('0.00'))
        
    def _execute(self,
                inventory_item_id: int,
                source_warehouse_id: int,
                destination_warehouse_id: int,
                quantity: int,
                description: str,
                last_update_user_id: int) -> None:
        """
        Execute the internal inventory transfer
        
        Args:
            inventory_item_id: ID of inventory item to transfer
            source_warehouse_id: ID of source warehouse
            destination_warehouse_id: ID of destination warehouse
            quantity: Quantity to transfer
            description: Description of the transfer
            last_update_user_id: ID of user making update
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        try:
            # Validate inputs
            if not all([
                inventory_item_id,
                source_warehouse_id,
                destination_warehouse_id,
                quantity and quantity > 0
            ]):
                raise ValueError("Missing or invalid transfer parameters")
                
            # Refresh source inventory
            InventoryRefresher.execute(
                self.db,
                source_warehouse_id,
                inventory_item_id
            )
            
            # Get current inventory info
            on_hand, cost_per_unit = self._get_inventory_info(
                inventory_item_id,
                source_warehouse_id
            )
            
            # Validate quantity
            if quantity > on_hand:
                raise ValueError(
                    f"Insufficient quantity in source warehouse. "
                    f"Requested: {quantity}, Available: {on_hand}"
                )
                
            # Add transfer out transaction
            InventoryTransactionAdder.execute(
                db=self.db,
                warehouse_id=source_warehouse_id,
                inventory_item_id=inventory_item_id,
                transaction_type='Transferred Out',
                description=description,
                quantity=quantity,
                cost_per_unit=cost_per_unit,
                last_update_user_id=last_update_user_id
            )
            
            # Add transfer in transaction
            InventoryTransactionAdder.execute(
                db=self.db,
                warehouse_id=destination_warehouse_id,
                inventory_item_id=inventory_item_id,
                transaction_type='Transferred In',
                description=description,
                quantity=quantity,
                cost_per_unit=cost_per_unit,
                last_update_user_id=last_update_user_id
            )
            
            # Refresh both inventories
            InventoryRefresher.execute(
                self.db,
                source_warehouse_id,
                inventory_item_id
            )
            InventoryRefresher.execute(
                self.db,
                destination_warehouse_id,
                inventory_item_id
            )
            
            self.db.commit()
            logger.info(
                f"Successfully transferred {quantity} units of item {inventory_item_id} "
                f"from warehouse {source_warehouse_id} to {destination_warehouse_id}"
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in internal inventory transfer: {str(e)}")
            raise
            
    @classmethod
    def execute(cls,
               db: Session,
               inventory_item_id: int,
               source_warehouse_id: int,
               destination_warehouse_id: int,
               quantity: int,
               description: str,
               last_update_user_id: int) -> None:
        """
        Execute an internal inventory transfer
        
        Args:
            db: Database session
            inventory_item_id: ID of inventory item to transfer
            source_warehouse_id: ID of source warehouse
            destination_warehouse_id: ID of destination warehouse
            quantity: Quantity to transfer
            description: Description of the transfer
            last_update_user_id: ID of user making update
        """
        transfer = cls(db)
        transfer._execute(
            inventory_item_id,
            source_warehouse_id,
            destination_warehouse_id,
            quantity,
            description,
            last_update_user_id
        )
