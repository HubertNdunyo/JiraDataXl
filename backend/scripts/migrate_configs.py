#!/usr/bin/env python3
"""
Script to initialize configuration tables and migrate existing configs
"""
import logging

from ..core.db.db_config import create_config_tables, migrate_file_configs_to_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Create configuration tables
        logger.info("Creating configuration tables...")
        create_config_tables()
        
        # Migrate existing file configs
        logger.info("Migrating file-based configurations to database...")
        migrate_file_configs_to_db()
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()