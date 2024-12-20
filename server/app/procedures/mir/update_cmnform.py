from typing import Optional, List
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.cmn import CMNForm, CMNFormItem
from app.models.order import Order
from datetime import datetime, timedelta

class CMNFormMIRUpdater:
    """Updates Medical Information Records (MIR) for Certificate of Medical Necessity forms"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _validate_cmnform(self, form: CMNForm) -> List[str]:
        """Validate CMN form data and return list of issues"""
        issues = []
        
        # Required fields
        if not form.physician_name:
            issues.append("PhysicianName")
        if not form.physician_npi:
            issues.append("PhysicianNPI")
        if not form.diagnosis_code:
            issues.append("DiagnosisCode")
        if not form.start_date:
            issues.append("StartDate")
            
        # Active form checks
        if form.is_active:
            # Check for expired forms
            if form.end_date and form.end_date < datetime.now():
                issues.append("Expired")
                
            # Check for missing items
            item_count = (
                self.db.query(func.count(CMNFormItem.id))
                .filter(CMNFormItem.cmn_form_id == form.id)
                .scalar()
            )
            if item_count == 0:
                issues.append("NoItems")
                
            # Check for missing signatures
            if not form.physician_signature_date:
                issues.append("NoPhysicianSignature")
            if not form.customer_signature_date:
                issues.append("NoCustomerSignature")
                
            # Check for recent orders
            recent_order_count = (
                self.db.query(func.count(Order.id))
                .filter(
                    and_(
                        Order.cmn_form_id == form.id,
                        Order.order_date >= func.date_sub(func.now(), interval='180 day')
                    )
                )
                .scalar()
            )
            if recent_order_count == 0:
                issues.append("NoRecentOrders")
                
            # Validate length of need
            if form.length_of_need is None or form.length_of_need <= 0:
                issues.append("InvalidLengthOfNeed")
                
            # Check for upcoming expiration
            if form.end_date and form.end_date < datetime.now() + timedelta(days=30):
                issues.append("ExpiringWithin30Days")
                
        return issues
        
    def _execute(self, form_id: Optional[int] = None) -> None:
        """
        Update MIR records for CMN forms
        
        Args:
            form_id: Optional ID of specific CMN form to update. If None, updates all.
        """
        try:
            # Build base query
            query = self.db.query(CMNForm)
            
            # Filter by form ID if provided
            if form_id is not None:
                query = query.filter(CMNForm.id == form_id)
                
            # Update MIR info for matching forms
            forms = query.all()
            for form in forms:
                # Validate form and update MIR
                issues = self._validate_cmnform(form)
                form.mir = ','.join(issues) if issues else None
                
            self.db.commit()
            logger.info(f"Updated MIR for {len(forms)} CMN forms")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating CMN form MIR: {str(e)}")
            raise
            
    @classmethod
    def execute(cls, db: Session, form_id: Optional[int] = None) -> None:
        """
        Execute the CMN form MIR update procedure
        
        Args:
            db: Database session
            form_id: Optional ID of specific CMN form to update
        """
        updater = cls(db)
        updater._execute(form_id)
