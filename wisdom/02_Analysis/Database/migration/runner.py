import psycopg2
import logging
from typing import List
from .base import MigrationBase
from .providers import ProviderMigration
from .insurance import InsuranceMigration

class MigrationRunner:
    """Handles execution of migrations in the correct order"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
        self.migrations: List[MigrationBase] = [
            ProviderMigration(),
            InsuranceMigration()
        ]

    def run_migrations(self) -> bool:
        """Run all migrations in order"""
        try:
            with psycopg2.connect(self.connection_string) as connection:
                # Create migration log table if it doesn't exist
                self._create_log_table(connection)

                # Run each migration
                for migration in self.migrations:
                    self.logger.info(f"Running migration: {migration.__class__.__name__}")
                    if not migration.up(connection):
                        self.logger.error(f"Migration failed: {migration.__class__.__name__}")
                        return False
                    self.logger.info(f"Migration completed: {migration.__class__.__name__}")

                return True

        except Exception as e:
            self.logger.error(f"Migration runner failed: {str(e)}")
            return False

    def rollback_migrations(self) -> bool:
        """Rollback all migrations in reverse order"""
        try:
            with psycopg2.connect(self.connection_string) as connection:
                # Run each migration's down method in reverse order
                for migration in reversed(self.migrations):
                    self.logger.info(f"Rolling back migration: {migration.__class__.__name__}")
                    if not migration.down(connection):
                        self.logger.error(f"Rollback failed: {migration.__class__.__name__}")
                        return False
                    self.logger.info(f"Rollback completed: {migration.__class__.__name__}")

                return True

        except Exception as e:
            self.logger.error(f"Migration rollback failed: {str(e)}")
            return False

    def _create_log_table(self, connection) -> None:
        """Create migration log table if it doesn't exist"""
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_logs (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(100) NOT NULL,
                    executed_at TIMESTAMP NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT
                )
            """)
