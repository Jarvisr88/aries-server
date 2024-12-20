"""
Procedure to handle inventory reordering based on configured thresholds.

This procedure evaluates inventory levels against reorder points and
generates purchase orders when stock falls below minimum levels.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.inventory import (
    InventoryItem,
    PurchaseOrder,
    PurchaseOrderLine,
    Vendor
)
from app.core.exceptions import ProcedureError

class InventoryReorder:
    """Handles automated inventory reordering"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_items_below_threshold(self) -> List[InventoryItem]:
        """Get all inventory items below their reorder point"""
        return (
            self.db.query(InventoryItem)
            .filter(
                and_(
                    InventoryItem.reorder_point > 0,
                    InventoryItem.quantity <= InventoryItem.reorder_point,
                    InventoryItem.is_active == True
                )
            )
            .all()
        )
        
    def _get_preferred_vendor(self, item: InventoryItem) -> Optional[Vendor]:
        """Get preferred vendor for an item"""
        if not item.preferred_vendor_id:
            return None
            
        return self.db.query(Vendor).get(item.preferred_vendor_id)
        
    def _create_purchase_order(self, vendor: Vendor) -> PurchaseOrder:
        """Create a new purchase order"""
        po = PurchaseOrder(
            vendor_id=vendor.id,
            order_date=datetime.utcnow(),
            status='Draft',
            total_amount=Decimal('0.00')
        )
        self.db.add(po)
        return po
        
    def _add_line_item(
        self,
        po: PurchaseOrder,
        item: InventoryItem,
        quantity: Decimal
    ) -> None:
        """Add line item to purchase order"""
        line = PurchaseOrderLine(
            purchase_order_id=po.id,
            inventory_item_id=item.id,
            quantity=quantity,
            unit_price=item.standard_cost or Decimal('0.00'),
            total_price=(item.standard_cost or Decimal('0.00')) * quantity
        )
        self.db.add(line)
        
        # Update PO total
        po.total_amount += line.total_price
        
    def _calculate_reorder_quantity(self, item: InventoryItem) -> Decimal:
        """Calculate quantity to reorder"""
        # If max quantity set, order up to max
        if item.maximum_quantity:
            return item.maximum_quantity - item.quantity
            
        # Otherwise order standard reorder quantity
        return item.reorder_quantity or Decimal('1.00')
        
    def _execute(self) -> List[int]:
        """
        Process inventory reordering
        
        Returns:
            List of created purchase order IDs
        """
        # Get items needing reorder
        items = self._get_items_below_threshold()
        if not items:
            return []
            
        # Group items by vendor
        vendor_items = {}
        for item in items:
            vendor = self._get_preferred_vendor(item)
            if not vendor:
                continue
                
            if vendor.id not in vendor_items:
                vendor_items[vendor.id] = {
                    'vendor': vendor,
                    'items': []
                }
            vendor_items[vendor.id]['items'].append(item)
            
        # Create POs by vendor
        po_ids = []
        for vendor_data in vendor_items.values():
            vendor = vendor_data['vendor']
            items = vendor_data['items']
            
            # Create PO
            po = self._create_purchase_order(vendor)
            
            # Add line items
            for item in items:
                quantity = self._calculate_reorder_quantity(item)
                if quantity > 0:
                    self._add_line_item(po, item, quantity)
                    
            if po.total_amount > 0:
                po_ids.append(po.id)
                
        self.db.commit()
        return po_ids
        
    @classmethod
    def execute(cls, db: Session) -> List[int]:
        """
        Process inventory reordering
        
        Args:
            db: Database session
            
        Returns:
            List of created purchase order IDs
        """
        procedure = cls(db)
        return procedure._execute()
