from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging
from datetime import datetime

class MigrationBase(ABC):
    """Base class for all migrations"""
    
    def __init__(self, source_schema: str = 'dmeworks', target_schema: str = 'public'):
        self.source_schema = source_schema
        self.target_schema = target_schema
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def up(self, connection) -> bool:
        """Execute the migration"""
        pass

    @abstractmethod
    def down(self, connection) -> bool:
        """Rollback the migration"""
        pass

    def verify_count(self, connection, source_table: str, target_table: str) -> bool:
        """Verify record counts match between source and target tables"""
        source_count = self._get_count(connection, f"{self.source_schema}.{source_table}")
        target_count = self._get_count(connection, f"{self.target_schema}.{target_table}")
        
        if source_count != target_count:
            self.logger.error(f"Count mismatch: {source_table}({source_count}) vs {target_table}({target_count})")
            return False
        return True

    def _get_count(self, connection, table: str) -> int:
        """Get record count for a table"""
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            return cursor.fetchone()[0]

    def update_sequence(self, connection, table: str) -> None:
        """Update sequence for a table to match the max id"""
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT setval(
                    pg_get_serial_sequence('{self.target_schema}.{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {self.target_schema}.{table}), 1)
                )
            """)

    def log_migration(self, connection, success: bool, error: str = None) -> None:
        """Log migration execution"""
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO migration_logs 
                (migration_name, executed_at, success, error_message)
                VALUES (%s, %s, %s, %s)
            """, (
                self.__class__.__name__,
                datetime.now(),
                success,
                error
            ))
