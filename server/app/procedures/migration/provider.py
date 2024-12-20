"""Provider migration procedure"""

from typing import Dict, Any
from app.procedures.base import BaseProcedure
from app.core.logging import logger


class ProviderMigrationProcedure(BaseProcedure):
    """Handles migration of healthcare provider data"""

    async def _execute(self, *args, **kwargs) -> None:
        """Execute provider migration"""
        try:
            # Migrate healthcare providers
            await self._migrate_providers()
            
            # Migrate provider types
            await self._migrate_provider_types()
            
            # Update sequences
            await self._update_sequences()
            
            self._results['success'] = True
            self._results['message'] = 'Provider migration completed successfully'
            
        except Exception as e:
            logger.error(f"Provider migration failed: {str(e)}")
            self._results['success'] = False
            self._results['error'] = str(e)
            raise

    async def _migrate_providers(self) -> None:
        """Migrate healthcare providers data"""
        sql = """
            INSERT INTO public.healthcare_providers (
                id, first_name, last_name, middle_name,
                license_number, license_expiry_date, medicaid_number,
                dea_number, upin_number, tax_id, npi, pecos_enrolled,
                address_line1, address_line2, city, state, postal_code,
                phone, phone2, fax, provider_type_id,
                created_at, updated_at
            )
            SELECT 
                id, firstname, lastname, middlename,
                licensenumber, licenseexpired, medicaidnumber,
                deanumber, upinnumber, fedtaxid, npi, pecosenrolled,
                address1, address2, city, state, zip,
                phone, phone2, fax, typeid,
                lastupdatedatetime, lastupdatedatetime
            FROM dmeworks.doctors
        """
        await self._execute_raw_sql(sql)

    async def _migrate_provider_types(self) -> None:
        """Migrate provider types data"""
        sql = """
            INSERT INTO public.provider_types (
                id, name, created_at, updated_at
            )
            SELECT 
                id, name, lastupdatedatetime, lastupdatedatetime
            FROM dmeworks.doctortypes
        """
        await self._execute_raw_sql(sql)

    async def _update_sequences(self) -> None:
        """Update sequences for migrated tables"""
        tables = ['healthcare_providers', 'provider_types']
        for table in tables:
            sql = f"""
                SELECT setval(
                    pg_get_serial_sequence('public.{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM public.{table}), 1)
                )
            """
            await self._execute_raw_sql(sql)

    async def rollback(self) -> Dict[str, Any]:
        """Rollback provider migration"""
        try:
            async with self.db.begin() as transaction:
                self._transaction = transaction
                await self._execute_raw_sql("DELETE FROM public.healthcare_providers")
                await self._execute_raw_sql("DELETE FROM public.provider_types")
                return {'success': True, 'message': 'Provider migration rolled back successfully'}
        except Exception as e:
            logger.error(f"Provider migration rollback failed: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            self._transaction = None
