"""
Procedure to handle inventory adjustments and maintain inventory history.

This procedure processes inventory adjustments, updates quantities,
and maintains a complete audit trail of all inventory changes.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.inventory import (
    InventoryItem,
    InventoryHistory,
    InventoryAdjustmentType
)
from app.core.exceptions import ProcedureError

class InventoryAdjustment:
    """Handles inventory quantity adjustments and history tracking"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _validate_adjustment(
        self,
        item: InventoryItem,
        quantity: Decimal,
        adjustment_type: InventoryAdjustmentType
    ) -> None:
        """
        Validate the proposed inventory adjustment
        
        Args:
            item: Inventory item to adjust
            quantity: Adjustment quantity (positive or negative)
            adjustment_type: Type of adjustment being made
            
        Raises:
            ProcedureError: If adjustment is invalid
        """
        if quantity == 0:
            raise ProcedureError("Adjustment quantity cannot be zero")
            
        # For decreasing adjustments, ensure we have enough quantity
        if quantity < 0 and abs(quantity) > item.quantity:
            raise ProcedureError(
                f"Insufficient quantity for adjustment. "
                f"Current: {item.quantity}, Requested: {abs(quantity)}"
            )
            
        # Validate based on adjustment type
        if adjustment_type == InventoryAdjustmentType.PHYSICAL_COUNT:
            if quantity < 0:
                raise ProcedureError(
                    "Physical count adjustment cannot be negative"
                )
                
        elif adjustment_type == InventoryAdjustmentType.DAMAGE:
            if quantity > 0:
                raise ProcedureError(
                    "Damage adjustment must be negative"
                )
                
    def _create_history(
        self,
        item: InventoryItem,
        quantity: Decimal,
        adjustment_type: InventoryAdjustmentType,
        reference_id: Optional[int],
        notes: Optional[str]
    ) -> InventoryHistory:
        """Create inventory history record for adjustment"""
        history = InventoryHistory(
            inventory_item_id=item.id,
            adjustment_type=adjustment_type,
            quantity_before=item.quantity,
            adjustment_quantity=quantity,
            quantity_after=item.quantity + quantity,
            reference_id=reference_id,
            notes=notes,
            created_at=datetime.utcnow()
        )
        self.db.add(history)
        return history
        
    def _execute(
        self,
        inventory_item_id: int,
        quantity: Decimal,
        adjustment_type: InventoryAdjustmentType,
        reference_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> None:
        """
        Process inventory adjustment
        
        Args:
            inventory_item_id: ID of inventory item to adjust
            quantity: Adjustment quantity (positive or negative)
            adjustment_type: Type of adjustment being made
            reference_id: Optional reference ID (e.g. order ID)
            notes: Optional notes about adjustment
            
        Raises:
            ProcedureError: If item not found or adjustment invalid
        """
        # Get inventory item
        item = self.db.query(InventoryItem).get(inventory_item_id)
        if not item:
            raise ProcedureError(f"Inventory item {inventory_item_id} not found")
            
        # Validate adjustment
        self._validate_adjustment(item, quantity, adjustment_type)
        
        # Create history record
        history = self._create_history(
            item,
            quantity,
            adjustment_type,
            reference_id,
            notes
        )
        
        # Update item quantity
        item.quantity += quantity
        
        # Update last physical count date if applicable
        if adjustment_type == InventoryAdjustmentType.PHYSICAL_COUNT:
            item.last_physical_count = datetime.utcnow()
            
        self.db.commit()
        
    @classmethod
    def execute(
        cls,
        db: Session,
        inventory_item_id: int,
        quantity: Decimal,
        adjustment_type: InventoryAdjustmentType,
        reference_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> None:
        """
        Process inventory adjustment
        
        Args:
            db: Database session
            inventory_item_id: ID of inventory item to adjust
            quantity: Adjustment quantity (positive or negative)
            adjustment_type: Type of adjustment being made
            reference_id: Optional reference ID (e.g. order ID)
            notes: Optional notes about adjustment
        """
        procedure = cls(db)
        procedure._execute(
            inventory_item_id,
            quantity,
            adjustment_type,
            reference_id,
            notes
        )
