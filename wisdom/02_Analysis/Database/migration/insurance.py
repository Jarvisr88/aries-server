from typing import Dict, Any
from .base import MigrationBase

class InsuranceMigration(MigrationBase):
    """Migration for insurance companies and related tables"""

    def up(self, connection) -> bool:
        try:
            with connection.cursor() as cursor:
                # Migrate insurance companies
                cursor.execute("""
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
                """)

                # Migrate payers
                cursor.execute("""
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
                """)

                # Create default insurance plans
                cursor.execute("""
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
                """)

                # Create default insurance types
                cursor.execute("""
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
                """)

                # Verify migration
                if not self.verify_count(connection, 'insurancecompanies', 'insurance_companies'):
                    return False
                if not self.verify_count(connection, 'ability_eligibility_payers', 'insurance_payers'):
                    return False

                # Update sequences
                self.update_sequence(connection, 'insurance_companies')
                self.update_sequence(connection, 'insurance_payers')
                self.update_sequence(connection, 'insurance_plans')
                self.update_sequence(connection, 'insurance_types')

                return True

        except Exception as e:
            self.logger.error(f"Insurance migration failed: {str(e)}")
            connection.rollback()
            self.log_migration(connection, False, str(e))
            return False

        self.log_migration(connection, True)
        return True

    def down(self, connection) -> bool:
        try:
            with connection.cursor() as cursor:
                # Remove migrated data in reverse order
                cursor.execute("DELETE FROM public.insurance_types")
                cursor.execute("DELETE FROM public.insurance_plans")
                cursor.execute("DELETE FROM public.insurance_payers")
                cursor.execute("DELETE FROM public.insurance_companies")
                return True

        except Exception as e:
            self.logger.error(f"Insurance rollback failed: {str(e)}")
            connection.rollback()
            return False
