"""
Database operations for configuration management
"""
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.db.db_core import get_db_connection
import logging

logger = logging.getLogger(__name__)


def create_config_tables():
    """Create configuration-related tables if they don't exist"""
    queries = [
        # Main configuration table
        """
        CREATE TABLE IF NOT EXISTS configurations (
            id SERIAL PRIMARY KEY,
            config_type VARCHAR(50) NOT NULL,
            config_key VARCHAR(100) NOT NULL,
            config_value JSONB NOT NULL,
            version INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(255),
            updated_by VARCHAR(255),
            UNIQUE(config_type, config_key, version)
        )
        """,
        
        # Configuration history table
        """
        CREATE TABLE IF NOT EXISTS configuration_history (
            id SERIAL PRIMARY KEY,
            config_id INTEGER REFERENCES configurations(id),
            config_type VARCHAR(50) NOT NULL,
            config_key VARCHAR(100) NOT NULL,
            old_value JSONB,
            new_value JSONB NOT NULL,
            change_type VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete'
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            changed_by VARCHAR(255),
            change_reason TEXT
        )
        """,
        
        # Configuration backups table
        """
        CREATE TABLE IF NOT EXISTS configuration_backups (
            id SERIAL PRIMARY KEY,
            backup_name VARCHAR(255) NOT NULL,
            backup_type VARCHAR(50) NOT NULL, -- 'manual', 'auto', 'pre_update'
            backup_data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(255),
            description TEXT
        )
        """,
        
        # Add indexes
        """
        CREATE INDEX IF NOT EXISTS idx_configurations_type_key 
        ON configurations(config_type, config_key) WHERE is_active = true
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_configuration_history_config_id 
        ON configuration_history(config_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_configuration_backups_created_at 
        ON configuration_backups(created_at DESC)
        """
    ]
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for query in queries:
                cursor.execute(query)
        conn.commit()
        logger.info("Configuration tables created successfully")


def get_configuration(config_type: str, config_key: str) -> Optional[Dict[str, Any]]:
    """Get active configuration by type and key"""
    query = """
    SELECT config_value, version, updated_at
    FROM configurations
    WHERE config_type = %s AND config_key = %s AND is_active = true
    ORDER BY version DESC
    LIMIT 1
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (config_type, config_key))
            result = cursor.fetchone()
            
            if result:
                return {
                    'value': result['config_value'],
                    'version': result['version'],
                    'updated_at': result['updated_at']
                }
            return None


def save_configuration(
    config_type: str, 
    config_key: str, 
    config_value: Dict[str, Any],
    user: str = 'system',
    reason: str = None
) -> int:
    """Save configuration with version control and history"""
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get current configuration
            cursor.execute("""
                SELECT id, config_value, version 
                FROM configurations 
                WHERE config_type = %s AND config_key = %s AND is_active = true
                ORDER BY version DESC
                LIMIT 1
            """, (config_type, config_key))
            
            current = cursor.fetchone()
            
            if current:
                # Deactivate current version
                cursor.execute("""
                    UPDATE configurations 
                    SET is_active = false 
                    WHERE id = %s
                """, (current['id'],))
                
                # Insert new version
                new_version = current['version'] + 1
                cursor.execute("""
                    INSERT INTO configurations 
                    (config_type, config_key, config_value, version, created_by, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (config_type, config_key, Json(config_value), new_version, user, user))
                
                new_id = cursor.fetchone()['id']
                
                # Log history
                cursor.execute("""
                    INSERT INTO configuration_history 
                    (config_id, config_type, config_key, old_value, new_value, 
                     change_type, changed_by, change_reason)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_id, config_type, config_key, 
                    Json(current['config_value']), Json(config_value),
                    'update', user, reason
                ))
            else:
                # Insert first version
                cursor.execute("""
                    INSERT INTO configurations 
                    (config_type, config_key, config_value, version, created_by, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (config_type, config_key, Json(config_value), 1, user, user))
                
                new_id = cursor.fetchone()['id']
                
                # Log history
                cursor.execute("""
                    INSERT INTO configuration_history 
                    (config_id, config_type, config_key, new_value, 
                     change_type, changed_by, change_reason)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    new_id, config_type, config_key, Json(config_value),
                    'create', user, reason
                ))
            
            conn.commit()
            return new_id


def create_backup(
    backup_name: str,
    backup_type: str = 'manual',
    description: str = None,
    user: str = 'system'
) -> int:
    """Create a full configuration backup"""
    
    # Get all active configurations
    query = """
    SELECT config_type, config_key, config_value
    FROM configurations
    WHERE is_active = true
    ORDER BY config_type, config_key
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            configs = cursor.fetchall()
            
            # Structure backup data
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'configurations': {
                    f"{row['config_type']}.{row['config_key']}": row['config_value']
                    for row in configs
                },
                'total_configs': len(configs)
            }
            
            # Insert backup
            cursor.execute("""
                INSERT INTO configuration_backups 
                (backup_name, backup_type, backup_data, created_by, description)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (backup_name, backup_type, Json(backup_data), user, description))
            
            backup_id = cursor.fetchone()['id']
            conn.commit()
            
            logger.info(f"Created backup '{backup_name}' with {len(configs)} configurations")
            return backup_id


def list_backups(limit: int = 20) -> List[Dict[str, Any]]:
    """List recent configuration backups"""
    query = """
    SELECT id, backup_name, backup_type, created_at, created_by, description,
           backup_data->>'total_configs' as total_configs
    FROM configuration_backups
    ORDER BY created_at DESC
    LIMIT %s
    """
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (limit,))
            return cursor.fetchall()


def restore_backup(backup_id: int, user: str = 'system') -> bool:
    """Restore configuration from a backup"""
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get backup data
            cursor.execute("""
                SELECT backup_data
                FROM configuration_backups
                WHERE id = %s
            """, (backup_id,))
            
            backup = cursor.fetchone()
            if not backup:
                return False
            
            # Create pre-restore backup
            create_backup(
                f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'pre_update',
                f"Automatic backup before restoring backup ID {backup_id}",
                user
            )
            
            # Restore each configuration
            configs = backup['backup_data']['configurations']
            for config_full_key, config_value in configs.items():
                config_type, config_key = config_full_key.split('.', 1)
                save_configuration(
                    config_type, 
                    config_key, 
                    config_value, 
                    user,
                    f"Restored from backup ID {backup_id}"
                )
            
            logger.info(f"Restored {len(configs)} configurations from backup {backup_id}")
            return True


def get_configuration_history(
    config_type: str = None, 
    config_key: str = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get configuration change history"""
    
    query = """
    SELECT h.*, c.version
    FROM configuration_history h
    LEFT JOIN configurations c ON h.config_id = c.id
    WHERE 1=1
    """
    params = []
    
    if config_type:
        query += " AND h.config_type = %s"
        params.append(config_type)
    
    if config_key:
        query += " AND h.config_key = %s"
        params.append(config_key)
    
    query += " ORDER BY h.changed_at DESC LIMIT %s"
    params.append(limit)
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def get_field_mapping_config() -> Optional[Dict[str, Any]]:
    """Get the active field mapping configuration from database"""
    config = get_configuration('jira', 'field_mappings')
    if config:
        return config['value']
    return None


def save_field_mapping_config(
    field_mappings: Dict[str, Any],
    user: str = 'system',
    reason: str = None
) -> int:
    """Save field mapping configuration to database"""
    return save_configuration(
        'jira',
        'field_mappings', 
        field_mappings,
        user,
        reason or 'Field mapping configuration update'
    )


def migrate_file_configs_to_db():
    """One-time migration of file-based configs to database"""
    import os
    
    config_dir = os.path.join(os.path.dirname(__file__), '../../../config')
    
    # Migrate field_mappings.json
    field_mappings_path = os.path.join(config_dir, 'field_mappings.json')
    if os.path.exists(field_mappings_path):
        with open(field_mappings_path, 'r') as f:
            field_mappings = json.load(f)
            save_configuration(
                'jira',
                'field_mappings',
                field_mappings,
                'migration',
                'Initial migration from file-based config'
            )
            logger.info("Migrated field_mappings.json to database")
    
    # Migrate sync_config.json
    sync_config_path = os.path.join(config_dir, 'sync_config.json')
    if os.path.exists(sync_config_path):
        with open(sync_config_path, 'r') as f:
            sync_config = json.load(f)
            save_configuration(
                'sync',
                'settings',
                sync_config,
                'migration',
                'Initial migration from file-based config'
            )
            logger.info("Migrated sync_config.json to database")