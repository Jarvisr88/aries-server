from typing import Dict, Any
from .base import MigrationBase

class ProviderMigration(MigrationBase):
    """Migration for healthcare providers and related tables"""

    def up(self, connection) -> bool:
        try:
            with connection.cursor() as cursor:
                # Create healthcare providers
                cursor.execute("""
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
                """)

                # Create provider types
                cursor.execute("""
                    INSERT INTO public.provider_types (
                        id, name, created_at, updated_at
                    )
                    SELECT 
                        id, name, lastupdatedatetime, lastupdatedatetime
                    FROM dmeworks.doctortypes
                """)

                # Verify migration
                if not self.verify_count(connection, 'doctors', 'healthcare_providers'):
                    return False
                if not self.verify_count(connection, 'doctortypes', 'provider_types'):
                    return False

                # Update sequences
                self.update_sequence(connection, 'healthcare_providers')
                self.update_sequence(connection, 'provider_types')

                return True

        except Exception as e:
            self.logger.error(f"Provider migration failed: {str(e)}")
            connection.rollback()
            self.log_migration(connection, False, str(e))
            return False

        self.log_migration(connection, True)
        return True

    def down(self, connection) -> bool:
        try:
            with connection.cursor() as cursor:
                # Remove migrated data
                cursor.execute("DELETE FROM public.healthcare_providers")
                cursor.execute("DELETE FROM public.provider_types")
                return True

        except Exception as e:
            self.logger.error(f"Provider rollback failed: {str(e)}")
            connection.rollback()
            return False
