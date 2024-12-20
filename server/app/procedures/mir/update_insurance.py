from typing import Optional, List
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.insurance import InsuranceCompany, InsuranceCompanyEDI
from app.models.customer import CustomerInsurance
from app.models.invoice import InvoiceTransaction

class InsuranceCompanyMIRUpdater:
    """Updates Medical Information Records (MIR) for insurance companies"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def _validate_insurance(self, insurance: InsuranceCompany) -> List[str]:
        """Validate insurance company data and return list of issues"""
        issues = []
        
        # Required fields
        if not insurance.name:
            issues.append("Name")
        if not insurance.address1:
            issues.append("Address1")
        if not insurance.city:
            issues.append("City")
        if not insurance.state:
            issues.append("State")
        if not insurance.zip_code:
            issues.append("ZipCode")
            
        # Phone number validation
        if insurance.phone and len(insurance.phone.replace('-', '').replace('(', '').replace(')', '')) != 10:
            issues.append("Phone.Invalid")
            
        # Active insurance checks
        if insurance.is_active:
            # Must have active customer insurances
            customer_count = (
                self.db.query(func.count(CustomerInsurance.id))
                .filter(
                    and_(
                        CustomerInsurance.insurance_company_id == insurance.id,
                        CustomerInsurance.is_active == True
                    )
                )
                .scalar()
            )
            if customer_count == 0:
                issues.append("NoActiveCustomers")
                
            # Must have recent payments
            recent_payment_count = (
                self.db.query(func.count(InvoiceTransaction.id))
                .filter(
                    and_(
                        InvoiceTransaction.insurance_company_id == insurance.id,
                        InvoiceTransaction.transaction_date >= func.date_sub(func.now(), interval='90 day')
                    )
                )
                .scalar()
            )
            if recent_payment_count == 0:
                issues.append("NoRecentPayments")
                
            # EDI validation for electronic payers
            if insurance.is_electronic_payer:
                edi_config = (
                    self.db.query(InsuranceCompanyEDI)
                    .filter(InsuranceCompanyEDI.insurance_company_id == insurance.id)
                    .first()
                )
                if not edi_config:
                    issues.append("NoEDIConfig")
                elif not edi_config.payer_id:
                    issues.append("NoPayerID")
                elif not edi_config.receiver_id:
                    issues.append("NoReceiverID")
                
        return issues
        
    def _execute(self, insurance_id: Optional[int] = None) -> None:
        """
        Update MIR records for insurance companies
        
        Args:
            insurance_id: Optional ID of specific insurance to update. If None, updates all.
        """
        try:
            # Build base query
            query = self.db.query(InsuranceCompany)
            
            # Filter by insurance ID if provided
            if insurance_id is not None:
                query = query.filter(InsuranceCompany.id == insurance_id)
                
            # Update MIR info for matching insurance companies
            insurances = query.all()
            for insurance in insurances:
                # Validate insurance and update MIR
                issues = self._validate_insurance(insurance)
                insurance.mir = ','.join(issues) if issues else None
                
            self.db.commit()
            logger.info(f"Updated MIR for {len(insurances)} insurance companies")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating insurance MIR: {str(e)}")
            raise
            
    @classmethod
    def execute(cls, db: Session, insurance_id: Optional[int] = None) -> None:
        """
        Execute the insurance company MIR update procedure
        
        Args:
            db: Database session
            insurance_id: Optional ID of specific insurance to update
        """
        updater = cls(db)
        updater._execute(insurance_id)
