#!/usr/bin/env python3
"""
Script to fix the jira_field_cache table by adding the missing unique constraint.
Run this to fix the "no unique or exclusion constraint" error.
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

def fix_field_cache_constraint():
    """Add the missing unique constraint to jira_field_cache table"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'jira_sync'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres123')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Check if the constraint already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pg_constraint 
            WHERE conname = 'unique_instance_field'
        """)
        
        constraint_exists = cursor.fetchone()[0] > 0
        
        if constraint_exists:
            print("✓ Constraint 'unique_instance_field' already exists")
        else:
            print("Adding unique constraint to jira_field_cache table...")
            
            # First, remove any duplicate entries if they exist
            cursor.execute("""
                DELETE FROM jira_field_cache a
                USING jira_field_cache b
                WHERE a.id < b.id 
                AND a.instance = b.instance 
                AND a.field_id = b.field_id
            """)
            
            deleted_rows = cursor.rowcount
            if deleted_rows > 0:
                print(f"  Removed {deleted_rows} duplicate entries")
            
            # Add the unique constraint
            cursor.execute("""
                ALTER TABLE jira_field_cache 
                ADD CONSTRAINT unique_instance_field 
                UNIQUE(instance, field_id)
            """)
            
            print("✓ Successfully added unique constraint 'unique_instance_field'")
        
        # Verify the constraint
        cursor.execute("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conrelid = 'jira_field_cache'::regclass 
            AND contype = 'u'
        """)
        
        constraints = cursor.fetchall()
        print(f"\nCurrent unique constraints on jira_field_cache:")
        for constraint in constraints:
            print(f"  - {constraint[0]}")
        
        # Commit the changes
        conn.commit()
        print("\n✓ All changes committed successfully")
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    print("Fixing jira_field_cache table constraint...")
    print("=" * 50)
    
    success = fix_field_cache_constraint()
    
    if success:
        print("\n" + "=" * 50)
        print("✓ Fix completed successfully!")
        print("You can now restart the backend and try field discovery again.")
    else:
        print("\n" + "=" * 50)
        print("✗ Fix failed. Please check the error messages above.")