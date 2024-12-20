from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.purchase import PurchaseOrder, PurchaseOrderDetails
from app.core.exceptions import ProcedureError

class RecurringPurchaseOrderProcessor:
    """Processes recurring purchase orders by creating new orders"""
    
    def __init__(self, db: Session):
        self.db = db

    def _create_new_order(self, source_order: PurchaseOrder) -> PurchaseOrder:
        """Create new purchase order from source order"""
        new_order = PurchaseOrder(
            approved=False,
            recurring=True,
            cost=source_order.cost,
            freight=source_order.freight,
            tax=source_order.tax,
            total_due=source_order.total_due,
            vendor_id=source_order.vendor_id,
            ship_to_name=source_order.ship_to_name,
            ship_to_address1=source_order.ship_to_address1,
            ship_to_address2=source_order.ship_to_address2,
            ship_to_city=source_order.ship_to_city,
            ship_to_state=source_order.ship_to_state,
            ship_to_zip=source_order.ship_to_zip,
            ship_to_phone=source_order.ship_to_phone,
            order_date=source_order.order_date + timedelta(days=30),  # Add 1 month
            company_name=source_order.company_name,
            company_address1=source_order.company_address1,
            company_address2=source_order.company_address2,
            company_city=source_order.company_city,
            company_state=source_order.company_state,
            company_zip=source_order.company_zip,
            ship_via=source_order.ship_via,
            fob=source_order.fob,
            vendor_sales_rep=source_order.vendor_sales_rep,
            terms=source_order.terms,
            company_phone=source_order.company_phone,
            tax_rate_id=source_order.tax_rate_id,
            last_update_user_id=0
        )
        
        self.db.add(new_order)
        self.db.flush()  # Get new order ID
        return new_order

    def _copy_order_details(self, 
                          source_order_id: int, 
                          new_order_id: int) -> None:
        """Copy order details to new order"""
        # Get source details
        source_details = (
            self.db.query(PurchaseOrderDetails)
            .filter(PurchaseOrderDetails.purchase_order_id == source_order_id)
            .all()
        )
        
        # Create new details
        for detail in source_details:
            new_detail = PurchaseOrderDetails(
                back_order=0,
                ordered=detail.ordered,
                received=0,
                price=detail.price,
                customer=detail.customer,
                date_promised=detail.date_promised + timedelta(days=30),  # Add 1 month
                date_received=None,
                drop_ship_to_customer=detail.drop_ship_to_customer,
                inventory_item_id=detail.inventory_item_id,
                purchase_order_id=new_order_id,
                warehouse_id=detail.warehouse_id,
                last_update_user_id=detail.last_update_user_id,
                last_update_datetime=func.current_date(),
                vendor_stk_number=detail.vendor_stk_number,
                reference_number=detail.reference_number
            )
            self.db.add(new_detail)

    def _mark_source_non_recurring(self, order_id: int) -> None:
        """Mark source order as non-recurring"""
        self.db.execute(
            update(PurchaseOrder)
            .where(
                PurchaseOrder.id == order_id,
                PurchaseOrder.recurring == True
            )
            .values(recurring=False)
        )

    def _execute(self, purchase_order_id: int) -> Optional[int]:
        """
        Process a recurring purchase order
        
        Args:
            purchase_order_id: ID of purchase order to process
            
        Returns:
            ID of new purchase order if created, None otherwise
        """
        # Get source order
        source_order = (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id == purchase_order_id,
                PurchaseOrder.recurring == True
            )
            .first()
        )
        
        if not source_order:
            return None
            
        # Create new order
        new_order = self._create_new_order(source_order)
        
        if new_order.id:
            # Copy order details
            self._copy_order_details(purchase_order_id, new_order.id)
            
            # Mark source as non-recurring
            self._mark_source_non_recurring(purchase_order_id)
            
            # Commit changes
            self.db.commit()
            
            return new_order.id
            
        return None

    @classmethod
    def execute(cls, db: Session, purchase_order_id: int) -> Optional[int]:
        """
        Process a recurring purchase order
        
        Args:
            db: Database session
            purchase_order_id: ID of purchase order to process
            
        Returns:
            ID of new purchase order if created, None otherwise
        """
        procedure = cls(db)
        return procedure._execute(purchase_order_id)
