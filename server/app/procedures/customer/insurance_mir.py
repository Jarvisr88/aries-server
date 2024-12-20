"""
Customer Insurance MIR Update Procedure

Python implementation of the mir_update_customer_insurance stored procedure
for updating Medical Information Record flags.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import Session, joinedload

from app.models.customer import (
    Customer,
    CustomerInsurance,
    InsuranceCompany
)
from app.procedures.base import BaseProcedure


class CustomerInsuranceMIRUpdate(BaseProcedure):
    """
    Updates Medical Information Record (MIR) flags for customer insurance records.
    
    This procedure:
    1. Validates required insurance fields
    2. Checks for missing information
    3. Updates MIR flags for tracking
    """

    # Fields to check for non-commercial accounts
    REQUIRED_FIELDS = {
        'first_name': 'FirstName',
        'last_name': 'LastName',
        'address1': 'Address1',
        'city': 'City',
        'state': 'State',
        'zip': 'Zip',
        'gender': 'Gender',
        'date_of_birth': 'DateofBirth',
        'insurance_type': 'InsuranceType',
        'policy_number': 'PolicyNumber',
        'relationship_code': 'RelationshipCode'
    }

    async def _execute(
        self,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the MIR update procedure"""
        # Build query for insurance records
        query = (
            select(CustomerInsurance)
            .options(
                joinedload(CustomerInsurance.customer),
                joinedload(CustomerInsurance.insurance_company)
            )
        )
        
        if customer_id:
            query = query.where(CustomerInsurance.customer_id == customer_id)

        # Get records to update
        result = await self.db.execute(query)
        policies = result.unique().scalars().all()

        if not policies:
            return {
                'success': False,
                'error': 'No insurance records found'
            }

        # Update each policy
        update_count = 0
        for policy in policies:
            if await self._update_policy_mir(policy):
                update_count += 1

        return {
            'success': True,
            'records_updated': update_count
        }

    async def _update_policy_mir(self, policy: CustomerInsurance) -> bool:
        """Update MIR flags for a single policy"""
        # Skip MIR checks for commercial accounts
        if policy.customer and policy.customer.commercial_account:
            await self._clear_mir(policy)
            return True

        # Collect missing field flags
        mir_flags = []

        # Check personal info fields if not organization
        if policy.relationship_code != '18':  # '18' typically indicates organization
            for field, flag in self.REQUIRED_FIELDS.items():
                if not getattr(policy, field, None):
                    mir_flags.append(flag)

        # Check insurance company
        if not policy.insurance_company_id:
            mir_flags.append('InsuranceCompanyID')
        elif policy.insurance_company and policy.insurance_company.mir:
            mir_flags.append('InsuranceCompany')

        # Update policy MIR flags
        mir_value = ','.join(mir_flags) if mir_flags else ''
        
        update_stmt = (
            update(CustomerInsurance)
            .where(CustomerInsurance.id == policy.id)
            .values(
                mir=mir_value,
                modified_date=func.now()
            )
        )
        await self.db.execute(update_stmt)
        
        return True

    async def _clear_mir(self, policy: CustomerInsurance) -> None:
        """Clear MIR flags for commercial accounts"""
        update_stmt = (
            update(CustomerInsurance)
            .where(CustomerInsurance.id == policy.id)
            .values(
                mir='',
                modified_date=func.now()
            )
        )
        await self.db.execute(update_stmt)
