"""
Database operations for JIRA field cache management.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager

from core.db.db_core import get_db_connection

logger = logging.getLogger(__name__)


class FieldCacheManager:
    """Manages JIRA field cache in the database."""
    
    def __init__(self):
        # Use public schema (tables are in public, not jira_sync)
        self.schema = 'public'
        
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Get a database cursor."""
        cursor = None
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor if dict_cursor else None)
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def create_tables(self):
        """Create field cache tables if they don't exist."""
        # First ensure schema exists
        with self.get_cursor(dict_cursor=False) as cursor:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS jira_field_cache (
            id SERIAL PRIMARY KEY,
            instance VARCHAR(50) NOT NULL,
            field_id VARCHAR(255) NOT NULL,
            field_name VARCHAR(255) NOT NULL,
            field_type VARCHAR(100),
            is_custom BOOLEAN DEFAULT false,
            is_array BOOLEAN DEFAULT false,
            schema_info JSONB,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_instance_field UNIQUE(instance, field_id)
        );
        
        -- Add the unique constraint if it doesn't exist (for existing tables)
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'unique_instance_field'
            ) THEN
                ALTER TABLE jira_field_cache 
                ADD CONSTRAINT unique_instance_field 
                UNIQUE(instance, field_id);
            END IF;
        END $$;
        
        CREATE INDEX IF NOT EXISTS idx_field_cache_instance 
            ON jira_field_cache(instance);
        CREATE INDEX IF NOT EXISTS idx_field_cache_field_id 
            ON jira_field_cache(field_id);
        CREATE INDEX IF NOT EXISTS idx_field_cache_discovered_at 
            ON jira_field_cache(discovered_at);
        """
        
        with self.get_cursor(dict_cursor=False) as cursor:
            cursor.execute(create_table_sql)
            logger.info("Field cache tables created successfully")
    
    def cache_fields(self, instance: str, fields: List[Dict[str, Any]]) -> int:
        """
        Cache field metadata from JIRA.
        
        Args:
            instance: 'instance_1' or 'instance_2'
            fields: List of field dictionaries from JIRA API
            
        Returns:
            Number of fields cached
        """
        if not fields:
            return 0
            
        # Clear existing cache for this instance - in its own transaction
        try:
            with self.get_cursor(dict_cursor=False) as cursor:
                cursor.execute(
                    f"DELETE FROM jira_field_cache WHERE instance = %s",
                    (instance,)
                )
            logger.info(f"Cleared existing cache for {instance}")
        except Exception as e:
            logger.warning(f"Could not clear existing cache for {instance}: {e}")
        
        # Insert new field data
        insert_sql = f"""
        INSERT INTO jira_field_cache 
            (instance, field_id, field_name, field_type, is_custom, is_array, schema_info)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (instance, field_id) 
        DO UPDATE SET
            field_name = EXCLUDED.field_name,
            field_type = EXCLUDED.field_type,
            is_custom = EXCLUDED.is_custom,
            is_array = EXCLUDED.is_array,
            schema_info = EXCLUDED.schema_info,
            discovered_at = CURRENT_TIMESTAMP
        """
        
        count = 0
        # Process each field in a separate transaction to avoid aborting on error
        for field in fields:
            try:
                # Extract field information
                field_id = field.get('id', '')
                field_name = field.get('name', '')
                is_custom = field.get('custom', False)
                
                # Extract schema information
                schema = field.get('schema', {})
                field_type = schema.get('type', 'unknown')
                is_array = field_type == 'array'
                
                # If it's an array, get the item type
                if is_array and 'items' in schema:
                    field_type = f"array[{schema['items']}]"
                
                # Each field gets its own transaction
                with self.get_cursor(dict_cursor=False) as cursor:
                    cursor.execute(insert_sql, (
                        instance,
                        field_id,
                        field_name,
                        field_type,
                        is_custom,
                        is_array,
                        Json(schema) if schema else None
                    ))
                count += 1
            except Exception as e:
                logger.error(f"Error caching field {field.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Cached {count} fields for {instance}")
        return count
    
    def get_cached_fields(self, instance: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get cached fields from the database.
        
        Args:
            instance: Optional instance filter ('instance_1', 'instance_2', or None for both)
            
        Returns:
            List of field dictionaries
        """
        query = f"""
        SELECT 
            instance,
            field_id,
            field_name,
            field_type,
            is_custom,
            is_array,
            schema_info,
            discovered_at
        FROM jira_field_cache
        """
        
        params = []
        if instance:
            query += " WHERE instance = %s"
            params.append(instance)
        
        query += " ORDER BY instance, is_custom, field_name"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def search_fields(self, search_term: str, instance: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for fields by name or ID.
        
        Args:
            search_term: Search term (case-insensitive)
            instance: Optional instance filter
            
        Returns:
            List of matching fields
        """
        query = f"""
        SELECT 
            instance,
            field_id,
            field_name,
            field_type,
            is_custom,
            is_array,
            schema_info,
            discovered_at
        FROM jira_field_cache
        WHERE (
            LOWER(field_name) LIKE LOWER(%s) OR
            LOWER(field_id) LIKE LOWER(%s)
        )
        """
        
        params = [f'%{search_term}%', f'%{search_term}%']
        
        if instance:
            query += " AND instance = %s"
            params.append(instance)
        
        query += " ORDER BY instance, is_custom, field_name"
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_field_suggestions(self, field_name: str, exclude_mapped: List[str] = None) -> Dict[str, Any]:
        """
        Get field suggestions based on name similarity.
        
        Args:
            field_name: Field name to match
            exclude_mapped: List of field IDs to exclude (already mapped)
            
        Returns:
            Dictionary with suggestions for each instance
        """
        # Normalize the search term
        search_term = field_name.lower().replace('_', ' ').replace('-', ' ')
        
        suggestions = {
            'instance_1': [],
            'instance_2': []
        }
        
        # Query for similar fields
        query = f"""
        SELECT 
            instance,
            field_id,
            field_name,
            field_type,
            is_custom,
            similarity(LOWER(field_name), LOWER(%s)) as name_similarity
        FROM jira_field_cache
        WHERE similarity(LOWER(field_name), LOWER(%s)) > 0.3
        """
        
        params = [search_term, search_term]
        
        if exclude_mapped:
            placeholders = ','.join(['%s'] * len(exclude_mapped))
            query += f" AND field_id NOT IN ({placeholders})"
            params.extend(exclude_mapped)
        
        query += " ORDER BY name_similarity DESC, field_name"
        
        with self.get_cursor() as cursor:
            # Enable pg_trgm extension for similarity search
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                instance = row['instance']
                if instance in suggestions:
                    suggestions[instance].append({
                        'field_id': row['field_id'],
                        'field_name': row['field_name'],
                        'field_type': row['field_type'],
                        'is_custom': row['is_custom'],
                        'similarity': row['name_similarity']
                    })
        
        return suggestions
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the field cache."""
        query = f"""
        SELECT 
            instance,
            COUNT(*) as total_fields,
            COUNT(CASE WHEN is_custom THEN 1 END) as custom_fields,
            COUNT(CASE WHEN NOT is_custom THEN 1 END) as system_fields,
            MAX(discovered_at) as last_updated
        FROM jira_field_cache
        GROUP BY instance
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            stats = {}
            for row in results:
                stats[row['instance']] = {
                    'total_fields': row['total_fields'],
                    'custom_fields': row['custom_fields'],
                    'system_fields': row['system_fields'],
                    'last_updated': row['last_updated']
                }
            
            return stats