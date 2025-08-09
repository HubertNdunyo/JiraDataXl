#!/usr/bin/env python3
"""
Test script for JIRA field discovery functionality
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def test_field_discovery():
    """Test field discovery with correct environment variables"""
    
    # Import required modules
    from backend.core.db.db_field_cache import FieldCacheManager
    from backend.core.jira.jira_client import JiraClient
    
    print("Testing JIRA Field Discovery")
    print("=" * 50)
    
    # Check environment variables
    jira_email = os.getenv('JIRA_USERNAME_1') or os.getenv('JIRA_CREATE_EMAIL')
    jira_token = os.getenv('JIRA_PASSWORD_1') or os.getenv('JIRA_CREATE_TOKEN')
    jira_url_1 = os.getenv('JIRA_URL_1')
    jira_url_2 = os.getenv('JIRA_URL_2')
    
    print(f"Email: {jira_email}")
    print(f"Token: {'***' + jira_token[-10:] if jira_token else 'Not set'}")
    print(f"Instance 1: {jira_url_1}")
    print(f"Instance 2: {jira_url_2}")
    print()
    
    if not jira_email or not jira_token:
        print("ERROR: JIRA credentials not configured!")
        print("Please set JIRA_USERNAME_1 and JIRA_PASSWORD_1 in .env file")
        return False
    
    # Initialize field cache manager
    field_cache = FieldCacheManager()
    
    # Create tables if they don't exist
    print("Creating/verifying database tables...")
    try:
        field_cache.create_tables()
        print("✓ Database tables ready")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False
    
    results = {
        "instance_1": {"discovered": 0, "error": None},
        "instance_2": {"discovered": 0, "error": None}
    }
    
    # Discover fields from Instance 1
    if jira_url_1:
        print(f"\nDiscovering fields from Instance 1: {jira_url_1}")
        try:
            jira1 = JiraClient(jira_url_1, jira_email, jira_token)
            fields_1 = jira1.get_fields()
            count = field_cache.cache_fields('instance_1', fields_1)
            results["instance_1"]["discovered"] = count
            print(f"✓ Discovered {count} fields from Instance 1")
        except Exception as e:
            results["instance_1"]["error"] = str(e)
            print(f"✗ Error: {e}")
    
    # Discover fields from Instance 2
    if jira_url_2:
        print(f"\nDiscovering fields from Instance 2: {jira_url_2}")
        try:
            jira2_email = os.getenv('JIRA_USERNAME_2') or jira_email
            jira2_token = os.getenv('JIRA_PASSWORD_2') or jira_token
            jira2 = JiraClient(jira_url_2, jira2_email, jira2_token)
            fields_2 = jira2.get_fields()
            count = field_cache.cache_fields('instance_2', fields_2)
            results["instance_2"]["discovered"] = count
            print(f"✓ Discovered {count} fields from Instance 2")
        except Exception as e:
            results["instance_2"]["error"] = str(e)
            print(f"✗ Error: {e}")
    
    # Get cache statistics
    print("\nCache Statistics:")
    print("-" * 30)
    stats = field_cache.get_cache_stats()
    for instance, data in stats.items():
        print(f"{instance}:")
        print(f"  Total fields: {data['total_fields']}")
        print(f"  Custom fields: {data['custom_fields']}")
        print(f"  System fields: {data['system_fields']}")
    
    print("\n" + "=" * 50)
    print("Field Discovery Complete!")
    print(json.dumps(results, indent=2))
    
    return True

if __name__ == "__main__":
    success = test_field_discovery()
    sys.exit(0 if success else 1)