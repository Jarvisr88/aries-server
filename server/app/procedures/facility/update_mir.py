"""
Facility MIR Update Procedure

Python implementation of the mir_update_facility stored procedure for
updating Medical Information Record (MIR) fields in facility records.
"""
import re
from typing import Dict, Any, Optional
from sqlalchemy import select, update, and_, or_, text
from sqlalchemy.orm import Session

from app.models.facility import Facility
from app.procedures.base import BaseProcedure


class FacilityMIRUpdater(BaseProcedure):
    """
    Updates Medical Information Record (MIR) fields for facility records.
    
    This procedure:
    1. Checks for missing required fields in facility records
    2. Validates NPI format
    3. Updates MIR field with list of missing information
    """
    
    async def _execute(
        self,
        facility_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the MIR update procedure.
        
        Args:
            facility_id: Optional ID of specific facility to update. If None,
                        updates all facility records.
        """
        # Build the query to update facility records
        query = (
            update(Facility)
            .where(
                or_(
                    Facility.id == facility_id,
                    facility_id.is_(None)
                )
            )
            .values(
                mir=text("""
                    array_to_string(ARRAY[
                        CASE 
                            WHEN name IS NULL OR name = '' 
                            THEN 'Name' 
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
                            WHEN pos_type_id IS NULL OR pos_type_id = '' 
                            THEN 'POSTypeID' 
                        END,
                        CASE 
                            WHEN npi !~ '^[0-9]{10}\\s*$'
                            THEN 'NPI' 
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
    def execute(cls, facility_id: Optional[int] = None) -> None:
        """Execute the MIR update procedure.
        
        Args:
            facility_id: Optional ID of specific facility to update. If None,
                        updates all facility records.
        """
        updater = cls()
        with get_session() as session:
            updater._execute(facility_id)
            session.commit()
