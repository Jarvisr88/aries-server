"""Insurance migration procedure"""

from typing import Dict, Any
from app.procedures.base import BaseProcedure
from app.core.logging import logger


class InsuranceMigrationProcedure(BaseProcedure):
    """Handles migration of insurance-related data"""

    async def _execute(self, *args, **kwargs) -> None:
        """Execute insurance migration"""
        try:
            # Migrate insurance companies
            await self._migrate_insurance_companies()
            
            # Migrate payers
            await self._migrate_payers()
            
            # Create default plans and types
            await self._create_default_plans()
            await self._create_default_types()
            
            # Update sequences
            await self._update_sequences()
            
            self._results['success'] = True
            self._results['message'] = 'Insurance migration completed successfully'
            
        except Exception as e:
            logger.error(f"Insurance migration failed: {str(e)}")
            self._results['success'] = False
            self._results['error'] = str(e)
            raise

    async def _migrate_insurance_companies(self) -> None:
        """Migrate insurance companies data"""
        sql = """
            INSERT INTO public.insurance_companies (
                id, name, payer_id, address1, address2,
                city, state, zip_code, phone, fax,
                is_active, created_at, updated_at
            )
            SELECT 
                id, name, COALESCE(payerid, id::text),
                address1, address2, city, state, zip,
                phone, fax, true,
                lastupdatedatetime, lastupdatedatetime
            FROM dmeworks.insurancecompanies
        """
        await self._execute_raw_sql(sql)

    async def _migrate_payers(self) -> None:
        """Migrate payers data"""
        sql = """
            INSERT INTO public.insurance_payers (
                id, payer_code, name, type,
                contact_info, is_active,
                created_at, updated_at
            )
            SELECT 
                id, code, name, 'PRIMARY',
                jsonb_build_object(
                    'comments', comments,
                    'allows_submission', allowssubmission
                ),
                true,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM dmeworks.ability_eligibility_payers
        """
        await self._execute_raw_sql(sql)

    async def _create_default_plans(self) -> None:
        """Create default insurance plans"""
        sql = """
            INSERT INTO public.insurance_plans (
                insurance_company_id, plan_name, plan_type,
                claims_address, claims_phone, payer_id,
                supports_electronic_filing, is_active,
                created_at, updated_at
            )
            SELECT 
                id, name || ' - Default Plan', 'DEFAULT',
                address1, phone, COALESCE(payerid, id::text),
                true, true,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            FROM dmeworks.insurancecompanies
        """
        await self._execute_raw_sql(sql)

    async def _create_default_types(self) -> None:
        """Create default insurance types"""
        sql = """
            INSERT INTO public.insurance_types (
                name, description, coverage_type,
                is_primary, is_active,
                created_at, updated_at
            )
            VALUES 
                ('Medicare', 'Medicare coverage', 'MEDICARE', true, true,
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                ('Medicaid', 'Medicaid coverage', 'MEDICAID', false, true,
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                ('Commercial', 'Commercial insurance', 'COMMERCIAL', false, true,
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                ('Workers Comp', 'Workers compensation', 'WORKERS_COMP', false, true,
                 CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        await self._execute_raw_sql(sql)

    async def _update_sequences(self) -> None:
        """Update sequences for migrated tables"""
        tables = [
            'insurance_companies',
            'insurance_payers',
            'insurance_plans',
            'insurance_types'
        ]
        for table in tables:
            sql = f"""
                SELECT setval(
                    pg_get_serial_sequence('public.{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM public.{table}), 1)
                )
            """
            await self._execute_raw_sql(sql)

    async def rollback(self) -> Dict[str, Any]:
        """Rollback insurance migration"""
        try:
            async with self.db.begin() as transaction:
                self._transaction = transaction
                # Remove data in reverse order
                await self._execute_raw_sql("DELETE FROM public.insurance_types")
                await self._execute_raw_sql("DELETE FROM public.insurance_plans")
                await self._execute_raw_sql("DELETE FROM public.insurance_payers")
                await self._execute_raw_sql("DELETE FROM public.insurance_companies")
                return {'success': True, 'message': 'Insurance migration rolled back successfully'}
        except Exception as e:
            logger.error(f"Insurance migration rollback failed: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            self._transaction = None
