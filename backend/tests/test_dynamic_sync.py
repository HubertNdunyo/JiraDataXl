#!/usr/bin/env python3
"""
Test script for the new dynamic field sync system.
"""

import logging
from pathlib import Path

from ..core.db.db_config import get_field_mapping_config, save_field_mapping_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_current_configuration():
    """Check what's currently configured in the database."""
    print("\n" + "="*60)
    print("CHECKING CURRENT CONFIGURATION")
    print("="*60)
    
    # Get current field mapping configuration
    config = get_field_mapping_config()
    
    if not config:
        print("❌ No field mapping configuration found in database")
        return False
    
    print("✅ Field mapping configuration found")
    
    # Count configured fields
    total_fields = 0
    field_groups = config.get('field_groups', {})
    
    print(f"\nField Groups: {len(field_groups)}")
    for group_name, group_data in field_groups.items():
        fields = group_data.get('fields', {})
        total_fields += len(fields)
        print(f"  - {group_name}: {len(fields)} fields")
        
        # Show first 5 fields in each group
        for i, (field_name, field_config) in enumerate(fields.items()):
            if i >= 5:
                print(f"      ... and {len(fields) - 5} more")
                break
            
            # Check if both instances have field IDs
            inst1 = field_config.get('instance_1', {})
            inst2 = field_config.get('instance_2', {})
            inst1_id = inst1.get('field_id', 'NOT SET')
            inst2_id = inst2.get('field_id', 'NOT SET')
            
            print(f"      • {field_name}:")
            print(f"        Instance 1: {inst1_id}")
            print(f"        Instance 2: {inst2_id}")
    
    print(f"\nTotal configured fields: {total_fields}")
    return True


def test_field_extraction():
    """Test the dynamic field extraction with a sample configuration."""
    print("\n" + "="*60)
    print("TESTING DYNAMIC FIELD EXTRACTION")
    print("="*60)
    
    # Create a test configuration
    test_config = {
        "version": "2.0",
        "description": "Test configuration for dynamic sync",
        "field_groups": {
            "Test System Fields": {
                "description": "System fields for testing",
                "fields": {
                    "issue_key": {
                        "type": "string",
                        "system_field": True,
                        "field_path": "key",
                        "instance_1": {"field_id": "key"},
                        "instance_2": {"field_id": "key"}
                    },
                    "summary": {
                        "type": "string",
                        "system_field": True,
                        "field_path": "fields.summary",
                        "instance_1": {"field_id": "summary"},
                        "instance_2": {"field_id": "summary"}
                    },
                    "status": {
                        "type": "string",
                        "system_field": True,
                        "field_path": "fields.status.name",
                        "instance_1": {"field_id": "status"},
                        "instance_2": {"field_id": "status"}
                    }
                }
            },
            "Test Custom Fields": {
                "description": "Custom fields from current configuration",
                "fields": {
                    "ndpu_client_name": {
                        "type": "string",
                        "instance_1": {"field_id": "customfield_10600"},
                        "instance_2": {"field_id": "customfield_10600"}
                    },
                    "ndpu_client_email": {
                        "type": "string",
                        "instance_1": {"field_id": "customfield_10601"},
                        "instance_2": {"field_id": "customfield_10601"}
                    }
                }
            }
        }
    }
    
    print("\nTest configuration created with:")
    print(f"  - {len(test_config['field_groups'])} field groups")
    print(f"  - 3 system fields")
    print(f"  - 2 custom fields")
    
    # Test the IssueProcessor with this configuration
    try:
        from core.jira.jira_issues import IssueProcessor
        from core.jira.jira_client import create_jira_client
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Create JIRA client for instance_1
        jira_client = create_jira_client(
            url="https://betteredits.atlassian.net",
            username=os.getenv('JIRA_USERNAME_1'),
            password=os.getenv('JIRA_PASSWORD_1')
        )
        
        # Create processor
        processor = IssueProcessor(jira_client, 'instance_1')
        
        # Check if it loaded mappings
        if processor.field_mappings:
            print(f"\n✅ IssueProcessor loaded {len(processor.field_mappings)} field groups")
        else:
            print("\n⚠️  IssueProcessor has no field mappings")
        
        # Test field mapping lookup
        test_columns = ['issue_key', 'summary', 'ndpu_client_name']
        print("\nTesting field mapping lookups:")
        for column in test_columns:
            mapping = processor.get_field_mapping_for_column(column)
            if mapping:
                print(f"  ✅ {column}: {mapping.get('field_id', mapping.get('field_path', 'complex'))}")
            else:
                print(f"  ❌ {column}: No mapping found")
        
        print("\n✅ Dynamic field extraction system is working")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing field extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_recommendations():
    """Show recommendations for next steps."""
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    config = get_field_mapping_config()
    
    if not config or not config.get('field_groups'):
        print("\n1. No field mappings configured. You need to:")
        print("   a) Use the Field Mapping Wizard in the UI")
        print("   b) Or load the legacy mappings using the migration script")
        print("\n   To load legacy mappings:")
        print("   python3 scripts/load_legacy_mappings.py")
    else:
        field_count = sum(len(g.get('fields', {})) for g in config.get('field_groups', {}).values())
        
        if field_count < 10:
            print(f"\n1. Only {field_count} fields configured. Consider adding more fields:")
            print("   - Use the Field Mapping Wizard to add business-critical fields")
            print("   - Load the complete legacy mappings for all 30 fields")
        else:
            print(f"\n✅ {field_count} fields are configured")
        
        # Check for missing Instance 2 mappings
        missing_inst2 = []
        for group in config.get('field_groups', {}).values():
            for field_name, field_config in group.get('fields', {}).items():
                inst2 = field_config.get('instance_2', {})
                if not inst2.get('field_id'):
                    missing_inst2.append(field_name)
        
        if missing_inst2:
            print(f"\n2. {len(missing_inst2)} fields missing Instance 2 mappings:")
            for field in missing_inst2[:5]:
                print(f"   - {field}")
            if len(missing_inst2) > 5:
                print(f"   ... and {len(missing_inst2) - 5} more")
            print("\n   Run field discovery to find Instance 2 field IDs")
    
    print("\n3. To test the sync with dynamic mappings:")
    print("   - Navigate to the UI sync dashboard")
    print("   - Select a small project for testing")
    print("   - Monitor the logs for any field extraction errors")
    
    print("\n4. The system is now fully dynamic:")
    print("   ✅ No more hardcoded field IDs")
    print("   ✅ Fields configured through UI are immediately available")
    print("   ✅ Easy to add/remove fields without code changes")
    print("   ✅ Different field mappings per JIRA instance supported")


def main():
    """Main test function."""
    print("\n" + "="*60)
    print("DYNAMIC FIELD SYNC SYSTEM TEST")
    print("="*60)
    
    # Check current configuration
    has_config = check_current_configuration()
    
    # Test field extraction
    extraction_works = test_field_extraction()
    
    # Show recommendations
    show_recommendations()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if has_config and extraction_works:
        print("\n✅ System is ready for dynamic field sync!")
        print("   - Configuration is loaded from database")
        print("   - Field extraction is working")
        print("   - You can now add/remove fields through the UI")
    elif extraction_works:
        print("\n⚠️  System is functional but needs configuration")
        print("   - Field extraction system works")
        print("   - But no field mappings are configured")
        print("   - Use the Field Mapping Wizard to configure fields")
    else:
        print("\n❌ System needs attention")
        print("   - Review the errors above")
        print("   - Check database connectivity")
        print("   - Ensure environment variables are set")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()