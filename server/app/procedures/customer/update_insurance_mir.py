"""
Customer Insurance MIR Update Procedure

Python implementation of the mir_update_customer_insurance stored procedure for
updating Medical Information Record (MIR) fields in customer insurance records.
"""
from typing import Optional
from sqlalchemy import select, update, and_, or_, text
from sqlalchemy.orm import Session, joinedload

from app.database import get_session
from app.models.customer import Customer, CustomerInsurance
from app.models.insurance import InsuranceCompany
from app.procedures.base import BaseProcedure


class CustomerInsuranceMIRUpdater(BaseProcedure):
    """Updates Medical Information Record (MIR) fields for customer insurance records.
    
    This procedure:
    1. Checks for missing required fields in customer insurance records
    2. Validates insurance company relationships
    3. Updates MIR field with list of missing information
    """
    
    def __init__(self, customer_id: Optional[int] = None):
        """Initialize the MIR updater.
        
        Args:
            customer_id: Optional ID of specific customer to update. If None,
                        updates all customer insurance records.
        """
        self.customer_id = customer_id

    def _execute(self, session: Session) -> None:
        """Execute the MIR update procedure.
        
        Args:
            session: Database session to use
        """
        # Build the query to update customer insurance records
        query = (
            update(CustomerInsurance)
            .where(
                or_(
                    CustomerInsurance.customer_id == self.customer_id,
                    self.customer_id.is_(None)
                )
            )
            .values(
                mir=text("""
                    CASE 
                        WHEN customer.commercial_account = 0 THEN
                            array_to_string(ARRAY[
                                CASE 
                                    WHEN relationship_code != '18' AND 
                                         (first_name IS NULL OR first_name = '') 
                                    THEN 'FirstName' 
                                END,
                                CASE 
                                    WHEN relationship_code != '18' AND 
                                         (last_name IS NULL OR last_name = '') 
                                    THEN 'LastName' 
                                END,
                                CASE 
                                    WHEN relationship_code != '18' AND 
                                         (address1 IS NULL OR address1 = '') 
                                    THEN 'Address1' 
                                END,
                                CASE 
                                    WHEN relationship_code != '18' AND 
                                         (city IS NULL OR city = '') 
                                    THEN 'City' 
                                END,
                                CASE 
                                    WHEN relationship_code != '18' AND 
                                         (state IS NULL OR state = '') 
                                    THEN 'State' 
                                END,
                                CASE 
                                    WHEN relationship_code != '18' AND 
                                         (zip IS NULL OR zip = '') 
                                    THEN 'Zip' 
                                END,
                                CASE 
                                    WHEN relationship_code != '18' AND 
                                         (gender IS NULL OR gender = '') 
                                    THEN 'Gender' 
                                END,
                                CASE 
                                    WHEN relationship_code != '18' AND 
                                         date_of_birth IS NULL 
                                    THEN 'DateofBirth' 
                                END,
                                CASE 
                                    WHEN insurance_type IS NULL OR insurance_type = '' 
                                    THEN 'InsuranceType' 
                                END,
                                CASE 
                                    WHEN policy_number IS NULL OR policy_number = '' 
                                    THEN 'PolicyNumber' 
                                END,
                                CASE 
                                    WHEN relationship_code IS NULL OR relationship_code = '' 
                                    THEN 'RelationshipCode' 
                                END,
                                CASE 
                                    WHEN insurance_company_id IS NULL 
                                    THEN 'InsuranceCompanyID' 
                                END,
                                CASE 
                                    WHEN insurance_company.mir != '' 
                                    THEN 'InsuranceCompany' 
                                END
                            ]::text[], ',')
                        ELSE ''
                    END
                """)
            )
            .execution_options(synchronize_session=False)
        )
        
        # Add joins for validation
        query = (
            query.join(Customer, CustomerInsurance.customer_id == Customer.id)
            .outerjoin(
                InsuranceCompany,
                CustomerInsurance.insurance_company_id == InsuranceCompany.id
            )
        )
        
        # Execute the update
        session.execute(query)

    @classmethod
    def execute(cls, customer_id: Optional[int] = None) -> None:
        """Execute the MIR update procedure.
        
        Args:
            customer_id: Optional ID of specific customer to update. If None,
                        updates all customer insurance records.
        """
        updater = cls(customer_id)
        with get_session() as session:
            updater._execute(session)
            session.commit()
