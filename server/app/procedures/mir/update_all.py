from sqlalchemy.orm import Session
from app.core.logging import logger
from app.procedures.mir.update_facility import FacilityMIRUpdater
from app.procedures.mir.update_insurance import InsuranceCompanyMIRUpdater
from app.procedures.mir.update_customer_insurance import CustomerInsuranceMIRUpdater
from app.procedures.mir.update_doctor import DoctorMIRUpdater
from app.procedures.mir.update_customer import CustomerMIRUpdater
from app.procedures.mir.update_cmn import CMNFormMIRUpdater
from app.procedures.mir.update_order_details import OrderDetailsMIRUpdater
from app.procedures.mir.update_order import OrderMIRUpdater

class MIRMasterUpdater:
    """
    Master class for coordinating Medical Information Record (MIR) updates across multiple entities.
    This procedure updates MIR information for facilities, insurance companies, customer insurance,
    doctors, customers, CMN forms, and orders.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def _execute(self) -> None:
        """
        Execute all MIR updates in the correct sequence.
        Updates are performed in a specific order to maintain data consistency.
        """
        try:
            # Update facility MIR records
            logger.info("Starting facility MIR updates")
            FacilityMIRUpdater.execute(self.db, None)
            
            # Update insurance company MIR records
            logger.info("Starting insurance company MIR updates")
            InsuranceCompanyMIRUpdater.execute(self.db, None)
            
            # Update customer insurance MIR records
            logger.info("Starting customer insurance MIR updates")
            CustomerInsuranceMIRUpdater.execute(self.db, None)
            
            # Update doctor MIR records
            logger.info("Starting doctor MIR updates")
            DoctorMIRUpdater.execute(self.db, None)
            
            # Update customer MIR records
            logger.info("Starting customer MIR updates")
            CustomerMIRUpdater.execute(self.db, None)
            
            # Update CMN form MIR records
            logger.info("Starting CMN form MIR updates")
            CMNFormMIRUpdater.execute(self.db, None)
            
            # Update order details MIR records (active only)
            logger.info("Starting order details MIR updates")
            OrderDetailsMIRUpdater.execute(self.db, 'ActiveOnly')
            
            # Update order MIR records (active only)
            logger.info("Starting order MIR updates")
            OrderMIRUpdater.execute(self.db, 'ActiveOnly')
            
            # Commit all changes
            self.db.commit()
            logger.info("All MIR updates completed successfully")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during MIR updates: {str(e)}")
            raise
            
    @classmethod
    def execute(cls, db: Session) -> None:
        """
        Execute the MIR master update procedure.
        
        Args:
            db: Database session
        """
        updater = cls(db)
        updater._execute()
