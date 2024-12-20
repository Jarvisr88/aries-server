from typing import Optional, List
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.facility import Facility
from app.models.order import Order
from app.models.customer import Customer

class FacilityMIRUpdater:
    """Updates Medical Information Records (MIR) for facilities"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _validate_facility(self, facility: Facility) -> List[str]:
        """Validate facility data and return list of issues"""
        issues = []
        
        # Required fields
        if not facility.name:
            issues.append("Name")
        if not facility.address1:
            issues.append("Address1")
        if not facility.city:
            issues.append("City")
        if not facility.state:
            issues.append("State")
        if not facility.zip_code:
            issues.append("ZipCode")
            
        # Phone number validation
        if facility.phone and len(facility.phone.replace('-', '').replace('(', '').replace(')', '')) != 10:
            issues.append("Phone.Invalid")
            
        # Active facility checks
        if facility.is_active:
            # Must have active customers
            customer_count = (
                self.db.query(func.count(Customer.id))
                .filter(
                    and_(
                        Customer.facility_id == facility.id,
                        Customer.is_active == True
                    )
                )
                .scalar()
            )
            if customer_count == 0:
                issues.append("NoActiveCustomers")
                
            # Must have recent orders
            recent_order_count = (
                self.db.query(func.count(Order.id))
                .join(Customer)
                .filter(
                    and_(
                        Customer.facility_id == facility.id,
                        Order.order_date >= func.date_sub(func.now(), interval='90 day')
                    )
                )
                .scalar()
            )
            if recent_order_count == 0:
                issues.append("NoRecentOrders")
                
        return issues
        
    def _execute(self, facility_id: Optional[int] = None) -> None:
        """
        Update MIR records for facilities
        
        Args:
            facility_id: Optional ID of specific facility to update. If None, updates all facilities.
        """
        try:
            # Build base query
            query = self.db.query(Facility)
            
            # Filter by facility ID if provided
            if facility_id is not None:
                query = query.filter(Facility.id == facility_id)
                
            # Update MIR info for matching facilities
            facilities = query.all()
            for facility in facilities:
                # Validate facility and update MIR
                issues = self._validate_facility(facility)
                facility.mir = ','.join(issues) if issues else None
                
            self.db.commit()
            logger.info(f"Updated MIR for {len(facilities)} facilities")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating facility MIR: {str(e)}")
            raise
            
    @classmethod
    def execute(cls, db: Session, facility_id: Optional[int] = None) -> None:
        """
        Execute the facility MIR update procedure
        
        Args:
            db: Database session
            facility_id: Optional ID of specific facility to update
        """
        updater = cls(db)
        updater._execute(facility_id)
