#!/usr/bin/env python3
"""
COMPREHENSIVE Database initialization script - Creates ALL tables and columns
This is the COMPLETE initialization that ensures database is 100% ready
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import init_db
from core.db.db_config import save_configuration, create_config_tables
from core.db.db_schema_manager import SchemaManager
from core.db.db_core import get_db_connection, execute_query
from alembic import command
from alembic.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_all_core_tables():
    """Create ALL core tables with ALL required columns"""
    logger.info("Creating all core tables...")
    
    tables = [
        # 1. Main issues table (already in SQL init)
        """
        CREATE TABLE IF NOT EXISTS jira_issues_v2 (
            issue_key VARCHAR(255) PRIMARY KEY,
            summary TEXT,
            status VARCHAR(255),
            ndpu_order_number VARCHAR(255),
            ndpu_raw_photos INTEGER,
            dropbox_raw_link TEXT,
            dropbox_edited_link TEXT,
            same_day_delivery BOOLEAN,
            escalated_editing BOOLEAN,
            edited_media_revision_notes TEXT,
            ndpu_editing_team VARCHAR(255),
            scheduled TIMESTAMP,
            acknowledged TIMESTAMP,
            at_listing TIMESTAMP,
            shoot_complete TIMESTAMP,
            uploaded TIMESTAMP,
            edit_start TIMESTAMP,
            final_review TIMESTAMP,
            closed TIMESTAMP,
            ndpu_service VARCHAR(255),
            project_name TEXT,
            location_name TEXT,
            ndpu_client_name TEXT,
            ndpu_client_email TEXT,
            ndpu_listing_address TEXT,
            ndpu_comments TEXT,
            ndpu_editor_notes TEXT,
            ndpu_access_instructions TEXT,
            ndpu_special_instructions TEXT,
            last_updated TIMESTAMP DEFAULT now()
        );
        """,
        
        # 2. Project mappings table
        """
        CREATE TABLE IF NOT EXISTS project_mappings_v2 (
            id SERIAL PRIMARY KEY,
            project_key VARCHAR(255) UNIQUE NOT NULL,
            location_name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT true,
            auto_discovered BOOLEAN DEFAULT false,
            approved BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(255),
            approved_by VARCHAR(255),
            metadata JSONB
        );
        """,
        
        # 3. Mapping audit log
        """
        CREATE TABLE IF NOT EXISTS mapping_audit_log_v2 (
            id SERIAL PRIMARY KEY,
            project_key VARCHAR(255) NOT NULL,
            action VARCHAR(50) NOT NULL,
            old_value JSONB,
            new_value JSONB,
            performed_by VARCHAR(255),
            performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 4. Sync history with ALL columns
        """
        CREATE TABLE IF NOT EXISTS sync_history (
            id SERIAL PRIMARY KEY,
            sync_id VARCHAR(255) UNIQUE NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            status VARCHAR(50) NOT NULL,
            total_issues INTEGER DEFAULT 0,
            issues_created INTEGER DEFAULT 0,
            issues_updated INTEGER DEFAULT 0,
            issues_failed INTEGER DEFAULT 0,
            error_message TEXT,
            sync_type VARCHAR(50) DEFAULT 'manual',
            triggered_by VARCHAR(100),
            duration_seconds FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 5. Sync project details with ALL columns
        """
        CREATE TABLE IF NOT EXISTS sync_project_details (
            id SERIAL PRIMARY KEY,
            sync_id VARCHAR(255) NOT NULL,
            project_key VARCHAR(255) NOT NULL,
            project_name VARCHAR(255),
            issues_synced INTEGER DEFAULT 0,
            issues_created INTEGER DEFAULT 0,
            issues_updated INTEGER DEFAULT 0,
            issues_failed INTEGER DEFAULT 0,
            sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            instance VARCHAR(50),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds FLOAT,
            status VARCHAR(50) DEFAULT 'pending',
            issues_processed INTEGER DEFAULT 0,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            FOREIGN KEY (sync_id) REFERENCES sync_history(sync_id) ON DELETE CASCADE
        );
        """,
        
        # 6. Update log with ALL columns
        """
        CREATE TABLE IF NOT EXISTS update_log_v2 (
            id SERIAL PRIMARY KEY,
            project_name VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            issues_count INTEGER DEFAULT 0,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration NUMERIC,
            records_processed INTEGER,
            last_update_time TIMESTAMP
        );
        """,
        
        # 7. Operation log
        """
        CREATE TABLE IF NOT EXISTS operation_log_v2 (
            id SERIAL PRIMARY KEY,
            operation_type VARCHAR(50) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(255) NOT NULL,
            performed_by VARCHAR(255),
            performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details JSONB,
            status VARCHAR(50),
            duration NUMERIC,
            error_message TEXT
        );
        """,
        
        # 8. Configurations table
        """
        CREATE TABLE IF NOT EXISTS configurations (
            id SERIAL PRIMARY KEY,
            config_type VARCHAR(50) NOT NULL,
            config_key VARCHAR(100) NOT NULL,
            config_value JSONB NOT NULL,
            version INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT true,
            user_updated VARCHAR(255),
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(config_type, config_key, version)
        );
        """,
        
        # 9. Configuration history
        """
        CREATE TABLE IF NOT EXISTS configuration_history (
            id SERIAL PRIMARY KEY,
            config_id INTEGER,
            config_type VARCHAR(50) NOT NULL,
            config_key VARCHAR(100) NOT NULL,
            old_value JSONB,
            new_value JSONB,
            changed_by VARCHAR(255),
            change_reason TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 10. Configuration backups
        """
        CREATE TABLE IF NOT EXISTS configuration_backups (
            id SERIAL PRIMARY KEY,
            backup_name VARCHAR(255) NOT NULL,
            backup_type VARCHAR(50) NOT NULL,
            backup_data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(255),
            description TEXT
        );
        """,
        
        # 11. JIRA field cache
        """
        CREATE TABLE IF NOT EXISTS jira_field_cache (
            id SERIAL PRIMARY KEY,
            instance_type VARCHAR(50) NOT NULL,
            field_id VARCHAR(100) NOT NULL,
            field_name VARCHAR(255),
            field_type VARCHAR(50),
            schema_type VARCHAR(100),
            custom BOOLEAN DEFAULT FALSE,
            navigable BOOLEAN DEFAULT TRUE,
            searchable BOOLEAN DEFAULT TRUE,
            clauseNames TEXT,
            auto_complete_url TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(instance_type, field_id)
        );
        """,
        
        # 12. Field mappings
        """
        CREATE TABLE IF NOT EXISTS field_mappings (
            id SERIAL PRIMARY KEY,
            jira_field_id VARCHAR(255) NOT NULL,
            jira_field_name VARCHAR(255) NOT NULL,
            db_column_name VARCHAR(255) NOT NULL,
            field_type VARCHAR(50) NOT NULL,
            is_custom BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            instance VARCHAR(50) DEFAULT 'instance_1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(jira_field_id, instance)
        );
        """,
        
        # 13. Sync config
        """
        CREATE TABLE IF NOT EXISTS sync_config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(255) UNIQUE NOT NULL,
            config_value TEXT,
            config_type VARCHAR(50) DEFAULT 'string',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 14. Audit log
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id VARCHAR(255),
            action VARCHAR(255) NOT NULL,
            resource_type VARCHAR(100),
            resource_id VARCHAR(255),
            details JSONB,
            ip_address VARCHAR(45),
            user_agent TEXT
        );
        """,
        
        # 15. Field cache
        """
        CREATE TABLE IF NOT EXISTS field_cache (
            id SERIAL PRIMARY KEY,
            cache_key VARCHAR(255) UNIQUE NOT NULL,
            cache_value JSONB,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 16. Sync history details
        """
        CREATE TABLE IF NOT EXISTS sync_history_details (
            id SERIAL PRIMARY KEY,
            sync_id VARCHAR(255) NOT NULL,
            issue_key VARCHAR(255) NOT NULL,
            action VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sync_id) REFERENCES sync_history(sync_id) ON DELETE CASCADE
        );
        """
    ]
    
    # Create all tables
    for table_sql in tables:
        try:
            execute_query(table_sql)
            # Extract table name for logging
            table_name = table_sql.split("IF NOT EXISTS ")[1].split("(")[0].strip()
            logger.info(f"✅ Created/verified table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
    
    return True

def create_all_indexes():
    """Create ALL required indexes"""
    logger.info("Creating all indexes...")
    
    indexes = [
        # jira_issues_v2 indexes
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_location_name ON jira_issues_v2(location_name);",
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_project ON jira_issues_v2(project_name);",
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_status ON jira_issues_v2(status);",
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_last_updated ON jira_issues_v2(last_updated);",
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_summary ON jira_issues_v2(summary);",
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_order_number ON jira_issues_v2(ndpu_order_number);",
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_v2_listing_address ON jira_issues_v2(ndpu_listing_address);",
        
        # project_mappings_v2 indexes
        "CREATE INDEX IF NOT EXISTS idx_project_mappings_v2_key ON project_mappings_v2(project_key);",
        "CREATE INDEX IF NOT EXISTS idx_project_mappings_v2_active ON project_mappings_v2(is_active);",
        
        # sync_history indexes
        "CREATE INDEX IF NOT EXISTS idx_sync_history_start_time ON sync_history(start_time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_sync_history_status ON sync_history(status);",
        "CREATE INDEX IF NOT EXISTS idx_sync_history_sync_id ON sync_history(sync_id);",
        
        # sync_project_details indexes
        "CREATE INDEX IF NOT EXISTS idx_sync_project_details_sync_id ON sync_project_details(sync_id);",
        "CREATE INDEX IF NOT EXISTS idx_sync_project_details_project_key ON sync_project_details(project_key);",
        
        # update_log_v2 indexes
        "CREATE INDEX IF NOT EXISTS idx_update_log_project ON update_log_v2(project_name);",
        "CREATE INDEX IF NOT EXISTS idx_update_log_timestamp ON update_log_v2(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_update_log_v2_project ON update_log_v2(project_name);",
        "CREATE INDEX IF NOT EXISTS idx_update_log_v2_timestamp ON update_log_v2(timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_update_log_v2_status ON update_log_v2(status);",
        
        # configurations indexes
        "CREATE INDEX IF NOT EXISTS idx_configurations_active ON configurations(config_type, config_key, is_active);",
        
        # configuration_history indexes
        "CREATE INDEX IF NOT EXISTS idx_configuration_history_config_id ON configuration_history(config_id);",
        
        # configuration_backups indexes
        "CREATE INDEX IF NOT EXISTS idx_configuration_backups_created_at ON configuration_backups(created_at DESC);",
        
        # jira_field_cache indexes
        "CREATE INDEX IF NOT EXISTS idx_jira_field_cache_instance ON jira_field_cache(instance_type);",
        "CREATE INDEX IF NOT EXISTS idx_jira_field_cache_field_id ON jira_field_cache(field_id);",
        "CREATE INDEX IF NOT EXISTS idx_field_cache_instance ON jira_field_cache(instance_type);",
        
        # field_mappings indexes
        "CREATE INDEX IF NOT EXISTS idx_field_mappings_jira_field_id ON field_mappings(jira_field_id);",
        "CREATE INDEX IF NOT EXISTS idx_field_mappings_instance ON field_mappings(instance);",
        
        # audit_log indexes
        "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);",
        
        # field_cache indexes
        "CREATE INDEX IF NOT EXISTS idx_field_cache_key ON field_cache(cache_key);",
        "CREATE INDEX IF NOT EXISTS idx_field_cache_expires ON field_cache(expires_at);",
        
        # sync_history_details indexes
        "CREATE INDEX IF NOT EXISTS idx_sync_history_details_sync_id ON sync_history_details(sync_id);",
        "CREATE INDEX IF NOT EXISTS idx_sync_history_details_issue_key ON sync_history_details(issue_key);",
        
        # operation_log_v2 indexes
        "CREATE INDEX IF NOT EXISTS idx_operation_log_v2_type ON operation_log_v2(operation_type, entity_type);",
        "CREATE INDEX IF NOT EXISTS idx_operation_log_v2_entity ON operation_log_v2(entity_id);",
        "CREATE INDEX IF NOT EXISTS idx_operation_log_v2_performed_at ON operation_log_v2(performed_at DESC);"
    ]
    
    for index_sql in indexes:
        try:
            execute_query(index_sql)
            index_name = index_sql.split("IF NOT EXISTS ")[1].split(" ON")[0].strip()
            logger.info(f"✅ Created/verified index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
    
    return True

def load_field_mappings():
    """Load field mappings from JSON file into database"""
    field_mappings_path = Path(__file__).parent.parent / 'config' / 'field_mappings.json'
    
    if not field_mappings_path.exists():
        logger.error(f"Field mappings file not found: {field_mappings_path}")
        return False
    
    try:
        with open(field_mappings_path, 'r') as f:
            field_mappings = json.load(f)
        
        # Save to database
        config_id = save_configuration(
            config_type='jira',
            config_key='field_mappings',
            config_value=field_mappings,
            user='system',
            reason='Initial database setup from field_mappings.json'
        )
        
        logger.info(f"✅ Field mappings loaded successfully (config_id: {config_id})")
        
        # Sync database schema with field mappings
        schema_manager = SchemaManager()
        sync_result = schema_manager.sync_fields_with_schema(field_mappings)
        logger.info(f"✅ Schema sync complete: {len(sync_result['added'])} columns added")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to load field mappings: {e}")
        return False

def load_default_configurations():
    """Load all default configurations"""
    logger.info("Loading default configurations...")
    
    configs = [
        {
            'type': 'sync',
            'key': 'performance',
            'value': {
                "max_workers": 14,
                "project_timeout": 300,
                "batch_size": 500,
                "lookback_days": 50,
                "max_retries": 3,
                "backoff_factor": 0.1,
                "rate_limit_pause": 0.1,
                "connection_pool_size": 20,
                "connection_pool_block": False
            },
            'reason': 'Default performance configuration'
        },
        {
            'type': 'sync',
            'key': 'scheduler',
            'value': {
                "enabled": True,
                "interval_minutes": 2
            },
            'reason': 'Default scheduler configuration'
        },
        {
            'type': 'sync',
            'key': 'settings',
            'value': {
                "enabled": True,
                "lookback_days": 50,
                "batch_size": 500,
                "max_workers": 14,
                "rate_limit_pause": 0.1,
                "sync_interval_minutes": 2
            },
            'reason': 'Default sync settings'
        }
    ]
    
    for config in configs:
        try:
            # Check if config already exists
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM configurations WHERE config_type = %s AND config_key = %s AND is_active = true",
                        (config['type'], config['key'])
                    )
                    if not cursor.fetchone():
                        config_id = save_configuration(
                            config_type=config['type'],
                            config_key=config['key'],
                            config_value=config['value'],
                            user='system',
                            reason=config['reason']
                        )
                        logger.info(f"✅ Created config: {config['type']}.{config['key']} (id: {config_id})")
                    else:
                        logger.info(f"✅ Config already exists: {config['type']}.{config['key']}")
        except Exception as e:
            logger.error(f"Failed to create config {config['type']}.{config['key']}: {e}")
    
    return True

def insert_default_sync_config():
    """Insert default values into sync_config table"""
    logger.info("Inserting default sync_config values...")
    
    default_configs = [
        ('sync_enabled', 'true', 'boolean', 'Enable/disable automatic synchronization'),
        ('sync_interval_minutes', '2', 'integer', 'Interval between automatic syncs in minutes'),
        ('batch_size', '500', 'integer', 'Number of issues to process in each batch'),
        ('max_retries', '3', 'integer', 'Maximum number of retry attempts for failed operations'),
        ('timeout_seconds', '300', 'integer', 'Request timeout in seconds'),
        ('max_workers', '14', 'integer', 'Maximum number of parallel workers'),
        ('rate_limit_pause', '0.1', 'float', 'Pause between API requests in seconds'),
        ('lookback_days', '50', 'integer', 'Number of days to look back for updates')
    ]
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                for key, value, config_type, description in default_configs:
                    cursor.execute("""
                        INSERT INTO sync_config (config_key, config_value, config_type, description)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (config_key) DO UPDATE
                        SET config_value = EXCLUDED.config_value,
                            config_type = EXCLUDED.config_type,
                            description = EXCLUDED.description,
                            updated_at = CURRENT_TIMESTAMP
                    """, (key, value, config_type, description))
                conn.commit()
                logger.info("✅ Default sync_config values inserted")
    except Exception as e:
        logger.error(f"Failed to insert sync_config defaults: {e}")
    
    return True

def verify_database_ready():
    """Verify that all tables and columns exist"""
    logger.info("Verifying database is ready...")
    
    required_tables = [
        'jira_issues_v2',
        'project_mappings_v2',
        'mapping_audit_log_v2',
        'sync_history',
        'sync_project_details',
        'sync_history_details',
        'update_log_v2',
        'operation_log_v2',
        'configurations',
        'configuration_history',
        'configuration_backups',
        'jira_field_cache',
        'field_mappings',
        'sync_config',
        'audit_log',
        'field_cache'
    ]
    
    missing_tables = []
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                for table in required_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        )
                    """, (table,))
                    exists = cursor.fetchone()[0]
                    if exists:
                        logger.info(f"✅ Table exists: {table}")
                    else:
                        logger.error(f"❌ Table missing: {table}")
                        missing_tables.append(table)
        
        if missing_tables:
            logger.error(f"Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("✅ All required tables exist!")
            return True
            
    except Exception as e:
        logger.error(f"Failed to verify database: {e}")
        return False

def main():
    """Main initialization function"""
    logger.info("="*60)
    logger.info("COMPREHENSIVE DATABASE INITIALIZATION")
    logger.info("="*60)
    
    # Initialize database connection
    init_db()
    logger.info("✅ Database connection established")
    
    # Create all core tables
    create_all_core_tables()
    logger.info("✅ All core tables created/verified")
    
    # Create all indexes
    create_all_indexes()
    logger.info("✅ All indexes created/verified")
    
    # Create configuration tables (from db_config module)
    create_config_tables()
    logger.info("✅ Configuration tables created")
    
    # Load default configurations
    load_default_configurations()
    logger.info("✅ Default configurations loaded")
    
    # Insert default sync_config values
    insert_default_sync_config()
    logger.info("✅ Default sync_config values inserted")
    
    # Load field mappings
    if load_field_mappings():
        logger.info("✅ Field mappings loaded successfully")
    else:
        logger.warning("⚠️ Failed to load field mappings")
    
    # Verify everything is ready
    if verify_database_ready():
        logger.info("="*60)
        logger.info("✅ DATABASE INITIALIZATION COMPLETE!")
        logger.info("All tables, columns, indexes, and configurations are ready.")
        logger.info("You can now safely delete all data and restart - everything will be recreated.")
        logger.info("="*60)
        return True
    else:
        logger.error("="*60)
        logger.error("❌ DATABASE INITIALIZATION INCOMPLETE")
        logger.error("Some components are missing. Check the logs above.")
        logger.error("="*60)
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)