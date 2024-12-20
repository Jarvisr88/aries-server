"""
Facility MIR Update Procedure

Python implementation of the mir_update_facility stored procedure for
updating Medical Information Record (MIR) flags for facilities.
"""
import re
from typing import Dict, Any, Optional, List
from sqlalchemy import select, or_, update
from sqlalchemy.orm import Session

from app.models.facility import Facility
from app.procedures.base import BaseProcedure


class FacilityMIRUpdate(BaseProcedure):
    """
    Updates Medical Information Record (MIR) flags for facilities.
    
    This procedure:
    1. Validates required fields
    2. Updates MIR flags
    3. Maintains data quality
    """

    # Required fields and their MIR flags
    REQUIRED_FIELDS = {
        'name': 'Name',
        'address1': 'Address1',
        'city': 'City',
        'state': 'State',
        'zip': 'Zip',
        'pos_type_id': 'POSTypeID'
    }

    # NPI validation pattern (10 digits)
    NPI_PATTERN = re.compile(r'^\d{10}\s*$')

    async def _execute(
        self,
        facility_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the facility MIR update procedure"""
        # Build query
        query = select(Facility)
        if facility_id:
            query = query.where(Facility.id == facility_id)

        # Get facilities to update
        result = await self.db.execute(query)
        facilities = result.scalars().all()

        if not facilities:
            return {
                'success': False,
                'error': f'No facilities found{" for ID " + str(facility_id) if facility_id else ""}'
            }

        # Update each facility
        facilities_updated = 0
        for facility in facilities:
            mir_flags = await self._calculate_mir_flags(facility)
            facility.mir = ','.join(mir_flags) if mir_flags else None
            facilities_updated += 1

        await self.db.flush()

        return {
            'success': True,
            'facilities_updated': facilities_updated
        }

    async def _calculate_mir_flags(
        self,
        facility: Facility
    ) -> List[str]:
        """Calculate MIR flags for a facility"""
        mir_flags = []

        # Check required fields
        for field_name, flag_name in self.REQUIRED_FIELDS.items():
            value = getattr(facility, field_name, None)
            if not value or str(value).strip() == '':
                mir_flags.append(flag_name)

        # Special NPI validation
        if facility.npi:
            if not self.NPI_PATTERN.match(str(facility.npi)):
                mir_flags.append('NPI')

        return mir_flags
