"""
Doctor MIR Update Procedure

Python implementation of the mir_update_doctor stored procedure for
updating Medical Information Record (MIR) fields in doctor records.
"""
from typing import Dict, Any, Optional
from sqlalchemy import select, update, and_, or_, text
from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.procedures.base import BaseProcedure


class DoctorMIRUpdater(BaseProcedure):
    """
    Updates Medical Information Record (MIR) fields for doctor records.
    
    This procedure:
    1. Checks for missing required fields in doctor records
    2. Updates MIR field with list of missing information
    """
    
    async def _execute(
        self,
        doctor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the MIR update procedure.
        
        Args:
            doctor_id: Optional ID of specific doctor to update. If None,
                      updates all doctor records.
        """
        # Build the query to update doctor records
        query = (
            update(Doctor)
            .where(
                or_(
                    Doctor.id == doctor_id,
                    doctor_id.is_(None)
                )
            )
            .values(
                mir=text("""
                    array_to_string(ARRAY[
                        CASE 
                            WHEN first_name IS NULL OR first_name = '' 
                            THEN 'FirstName' 
                        END,
                        CASE 
                            WHEN last_name IS NULL OR last_name = '' 
                            THEN 'LastName' 
                        END,
                        CASE 
                            WHEN npi IS NULL OR npi = '' 
                            THEN 'NPI' 
                        END,
                        CASE 
                            WHEN upin IS NULL OR upin = '' 
                            THEN 'UPIN' 
                        END,
                        CASE 
                            WHEN specialty IS NULL OR specialty = '' 
                            THEN 'Specialty' 
                        END,
                        CASE 
                            WHEN address1 IS NULL OR address1 = '' 
                            THEN 'Address1' 
                        END,
                        CASE 
                            WHEN city IS NULL OR city = '' 
                            THEN 'City' 
                        END,
                        CASE 
                            WHEN state IS NULL OR state = '' 
                            THEN 'State' 
                        END,
                        CASE 
                            WHEN zip IS NULL OR zip = '' 
                            THEN 'Zip' 
                        END,
                        CASE 
                            WHEN phone IS NULL OR phone = '' 
                            THEN 'Phone' 
                        END,
                        CASE 
                            WHEN fax IS NULL OR fax = '' 
                            THEN 'Fax' 
                        END
                    ]::text[], ',')
                """)
            )
            .execution_options(synchronize_session=False)
        )
        
        # Execute the update
        result = await self.db.execute(query)
        
        return {
            'success': True,
            'rows_updated': result.rowcount
        }

    @classmethod
    def execute(cls, doctor_id: Optional[int] = None) -> None:
        """Execute the MIR update procedure.
        
        Args:
            doctor_id: Optional ID of specific doctor to update. If None,
                      updates all doctor records.
        """
        updater = cls()
        with get_session() as session:
            updater._execute(doctor_id)
            session.commit()
