from typing import Optional
from sqlalchemy import select, update, text
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.customer import Customer
from app.models.doctor import Doctor
from app.procedures.base import BaseProcedure


class CustomerMIRUpdater(BaseProcedure):
    """Updates the Medical Information Record (MIR) field for customers.
    
    This procedure checks various required fields for a customer and marks any missing
    or invalid data in the MIR field. It also validates the associated doctor's information.
    """
    
    def __init__(self, customer_id: Optional[int] = None):
        """Initialize the MIR updater.
        
        Args:
            customer_id: Optional ID of the specific customer to update. If None,
                        updates all customers.
        """
        self.customer_id = customer_id
        
    def _execute(self, session: Session) -> None:
        """Execute the MIR update procedure.
        
        Args:
            session: The database session to use for the update.
        """
        # Build the base query to update customers
        query = (
            update(Customer)
            .outerjoin(Doctor, Customer.doctor1_id == Doctor.id)
            .values(
                mir=text("""
                    CASE 
                        WHEN commercial_account = 0 THEN
                            array_to_string(ARRAY[
                                CASE WHEN account_number IS NULL OR account_number = '' THEN 'AccountNumber' END,
                                CASE WHEN first_name IS NULL OR first_name = '' THEN 'FirstName' END,
                                CASE WHEN last_name IS NULL OR last_name = '' THEN 'LastName' END,
                                CASE WHEN address1 IS NULL OR address1 = '' THEN 'Address1' END,
                                CASE WHEN city IS NULL OR city = '' THEN 'City' END,
                                CASE WHEN state IS NULL OR state = '' THEN 'State' END,
                                CASE WHEN zip IS NULL OR zip = '' THEN 'Zip' END,
                                CASE WHEN employment_status IS NULL OR employment_status = '' THEN 'EmploymentStatus' END,
                                CASE WHEN gender IS NULL OR gender = '' THEN 'Gender' END,
                                CASE WHEN marital_status IS NULL OR marital_status = '' THEN 'MaritalStatus' END,
                                CASE WHEN military_branch IS NULL OR military_branch = '' THEN 'MilitaryBranch' END,
                                CASE WHEN military_status IS NULL OR military_status = '' THEN 'MilitaryStatus' END,
                                CASE WHEN student_status IS NULL OR student_status = '' THEN 'StudentStatus' END,
                                CASE WHEN months_valid IS NULL OR months_valid = 0 THEN 'MonthsValid' END,
                                CASE WHEN date_of_birth IS NULL THEN 'DateofBirth' END,
                                CASE WHEN signature_on_file IS NULL THEN 'SignatureOnFile' END,
                                CASE WHEN doctor1_id IS NULL THEN 'Doctor1_ID' END,
                                CASE WHEN doctor.mir != '' THEN 'Doctor1' END
                            ]::text[], ',')
                        ELSE ''
                    END
                """)
            )
        )
        
        # Add customer ID filter if specified
        if self.customer_id is not None:
            query = query.where(Customer.id == self.customer_id)
            
        # Execute the update
        session.execute(query)
        session.commit()

    @classmethod
    def execute(cls, customer_id: Optional[int] = None) -> None:
        """Class method to execute the MIR update procedure.
        
        Args:
            customer_id: Optional ID of the specific customer to update. If None,
                        updates all customers.
        """
        updater = cls(customer_id)
        with get_session() as session:
            updater._execute(session)
