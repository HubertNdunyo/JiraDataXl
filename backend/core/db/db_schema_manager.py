"""
Database schema management for dynamic field additions.
"""
import logging
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from core.db.db_core import get_db_connection

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schema updates for dynamic fields."""
    
    # Type mapping from field types to PostgreSQL data types
    TYPE_MAPPING = {
        'string': 'TEXT',
        'number': 'NUMERIC',
        'integer': 'INTEGER',
        'boolean': 'BOOLEAN',
        'date': 'DATE',
        'datetime': 'TIMESTAMP',
        'array': 'JSONB',  # Arrays stored as JSONB
        'object': 'JSONB',  # Complex objects as JSONB
        'status': 'VARCHAR(255)'
    }
    
    def __init__(self):
        self.schema = 'jira_sync'
        self.table = 'jira_issues_v2'
    
    def get_existing_columns(self) -> List[str]:
        """Get list of existing columns in the jira_issues_v2 table."""
        query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (self.table,))
                    return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching existing columns: {e}")
            raise
    
    def column_exists(self, column_name: str) -> bool:
        """Check if a column already exists."""
        existing_columns = self.get_existing_columns()
        return column_name.lower() in [col.lower() for col in existing_columns]
    
    def add_column(self, column_name: str, field_type: str, description: Optional[str] = None) -> bool:
        """
        Add a new column to the jira_issues_v2 table.
        
        Args:
            column_name: Name of the column to add
            field_type: Field type (string, number, integer, etc.)
            description: Optional column comment
            
        Returns:
            True if column was added, False if it already exists
        """
        # Validate column name
        if not column_name or not column_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid column name: {column_name}")
        
        # Check if column already exists
        if self.column_exists(column_name):
            logger.info(f"Column '{column_name}' already exists")
            return False
        
        # Get PostgreSQL data type
        pg_type = self.TYPE_MAPPING.get(field_type, 'TEXT')
        
        try:
            with get_db_connection() as conn:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cursor:
                    # Add the column
                    alter_query = f"""
                    ALTER TABLE {self.table} 
                    ADD COLUMN {column_name} {pg_type}
                    """
                    cursor.execute(alter_query)
                    logger.info(f"Added column '{column_name}' with type '{pg_type}'")
                    
                    # Add comment if provided
                    if description:
                        comment_query = f"""
                        COMMENT ON COLUMN {self.table}.{column_name} 
                        IS %s
                        """
                        cursor.execute(comment_query, (description,))
                        
                    return True
                    
        except Exception as e:
            logger.error(f"Error adding column '{column_name}': {e}")
            raise
    
    def sync_fields_with_schema(self, field_mappings: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Sync field mappings with database schema.
        
        Args:
            field_mappings: Field mapping configuration
            
        Returns:
            Dict with 'added' and 'skipped' column lists
        """
        results = {
            'added': [],
            'skipped': [],
            'errors': []
        }
        
        existing_columns = self.get_existing_columns()
        logger.info(f"Existing columns: {existing_columns}")
        
        # Process each field group
        for group_name, group_data in field_mappings.get('field_groups', {}).items():
            for field_key, field_config in group_data.get('fields', {}).items():
                try:
                    # Generate column name (add ndpu_ prefix if not present)
                    column_name = field_key
                    if not column_name.startswith('ndpu_') and field_key not in ['summary', 'status', 'issue_key', 'project_name', 'location_name', 'last_updated']:
                        column_name = f'ndpu_{field_key}'
                    
                    # Skip if no instances are mapped
                    instance_1 = field_config.get('instance_1')
                    instance_2 = field_config.get('instance_2')
                    if not (instance_1 and instance_1.get('field_id')) and not (instance_2 and instance_2.get('field_id')):
                        logger.debug(f"Skipping '{field_key}' - no instances mapped")
                        results['skipped'].append(field_key)
                        continue
                    
                    # Add column if it doesn't exist
                    field_type = field_config.get('type', 'string')
                    description = field_config.get('description', f'Field: {field_key}')
                    
                    if self.add_column(column_name, field_type, description):
                        results['added'].append(column_name)
                        logger.info(f"Added column '{column_name}' for field '{field_key}'")
                    else:
                        results['skipped'].append(column_name)
                        
                except Exception as e:
                    error_msg = f"Error processing field '{field_key}': {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
        
        return results
    
    def generate_column_mapping(self, field_mappings: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate mapping of field keys to database column names.
        
        Args:
            field_mappings: Field mapping configuration
            
        Returns:
            Dict mapping field keys to column names
        """
        column_mapping = {}
        
        for group_name, group_data in field_mappings.get('field_groups', {}).items():
            for field_key, field_config in group_data.get('fields', {}).items():
                # Generate column name
                column_name = field_key
                if not column_name.startswith('ndpu_') and field_key not in ['summary', 'status', 'issue_key', 'project_name', 'location_name', 'last_updated']:
                    column_name = f'ndpu_{field_key}'
                
                column_mapping[field_key] = column_name
        
        return column_mapping