from typing import Optional, List
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.inventory import InventoryItem, InventoryTransaction
from app.models.order import Order, OrderLine
from datetime import datetime, timedelta

class InventoryMIRUpdater:
    """Updates Medical Information Records (MIR) for inventory items"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _validate_inventory(self, item: InventoryItem) -> List[str]:
        """Validate inventory item data and return list of issues"""
        issues = []
        
        # Required fields
        if not item.item_number:
            issues.append("ItemNumber")
        if not item.description:
            issues.append("Description")
        if not item.category:
            issues.append("Category")
        if not item.unit_of_measure:
            issues.append("UnitOfMeasure")
            
        # Active item checks
        if item.is_active:
            # Check for negative quantity
            if item.quantity < 0:
                issues.append("NegativeQuantity")
                
            # Check for items below reorder point
            if item.quantity <= item.reorder_point:
                issues.append("BelowReorderPoint")
                
            # Check for recent transactions
            recent_transaction_count = (
                self.db.query(func.count(InventoryTransaction.id))
                .filter(
                    and_(
                        InventoryTransaction.inventory_item_id == item.id,
                        InventoryTransaction.transaction_date >= func.date_sub(func.now(), interval='90 day')
                    )
                )
                .scalar()
            )
            if recent_transaction_count == 0:
                issues.append("NoRecentTransactions")
                
            # Check for recent orders
            recent_order_count = (
                self.db.query(func.count(OrderLine.id))
                .join(Order)
                .filter(
                    and_(
                        OrderLine.inventory_item_id == item.id,
                        Order.order_date >= func.date_sub(func.now(), interval='180 day')
                    )
                )
                .scalar()
            )
            if recent_order_count == 0:
                issues.append("NoRecentOrders")
                
            # Pricing validation
            if item.unit_price <= 0:
                issues.append("InvalidPrice")
            if item.cost_price <= 0:
                issues.append("InvalidCost")
                
            # Serial number validation for serialized items
            if item.is_serialized:
                serial_count = (
                    self.db.query(func.count(InventoryTransaction.id))
                    .filter(
                        and_(
                            InventoryTransaction.inventory_item_id == item.id,
                            InventoryTransaction.serial_number.is_(None)
                        )
                    )
                    .scalar()
                )
                if serial_count > 0:
                    issues.append("MissingSerials")
                
        return issues
        
    def _execute(self, inventory_id: Optional[int] = None) -> None:
        """
        Update MIR records for inventory items
        
        Args:
            inventory_id: Optional ID of specific inventory item to update. If None, updates all.
        """
        try:
            # Build base query
            query = self.db.query(InventoryItem)
            
            # Filter by inventory ID if provided
            if inventory_id is not None:
                query = query.filter(InventoryItem.id == inventory_id)
                
            # Update MIR info for matching inventory items
            items = query.all()
            for item in items:
                # Validate inventory and update MIR
                issues = self._validate_inventory(item)
                item.mir = ','.join(issues) if issues else None
                
            self.db.commit()
            logger.info(f"Updated MIR for {len(items)} inventory items")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating inventory MIR: {str(e)}")
            raise
            
    @classmethod
    def execute(cls, db: Session, inventory_id: Optional[int] = None) -> None:
        """
        Execute the inventory MIR update procedure
        
        Args:
            db: Database session
            inventory_id: Optional ID of specific inventory item to update
        """
        updater = cls(db)
        updater._execute(inventory_id)
