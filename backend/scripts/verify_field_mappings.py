#!/usr/bin/env python3
"""
Script to verify and update field mappings between JIRA instances.
This script helps identify which custom field IDs correspond to the business fields.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.db.db_field_cache import get_cached_fields


def load_core_mappings():
    """Load the core field mappings configuration."""
    config_path = Path(__file__).parent.parent / "config" / "core_field_mappings.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def find_field_by_keywords(cached_fields, keywords, instance="instance_1"):
    """
    Find fields that match given keywords.
    
    Args:
        cached_fields: Dict of cached field data
        keywords: List of keywords to search for
        instance: Which instance to search in
    
    Returns:
        List of matching fields
    """
    matches = []
    
    if instance not in cached_fields.get('fields', {}):
        return matches
    
    instance_fields = cached_fields['fields'][instance]
    all_fields = instance_fields.get('system', []) + instance_fields.get('custom', [])
    
    for field in all_fields:
        field_name_lower = field['field_name'].lower()
        field_id_lower = field['field_id'].lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in field_name_lower or keyword_lower in field_id_lower:
                matches.append(field)
                break
    
    return matches


def verify_mappings():
    """Verify and suggest field mappings."""
    
    print("Loading core field mappings...")
    config = load_core_mappings()
    
    print("Fetching cached fields from database...")
    cached_fields = get_cached_fields()
    
    if not cached_fields:
        print("❌ No cached fields found. Please run field discovery first.")
        return
    
    print(f"Found {len(cached_fields.get('fields', {}).get('instance_1', {}).get('custom', []))} custom fields in instance_1")
    print(f"Found {len(cached_fields.get('fields', {}).get('instance_2', {}).get('custom', []))} custom fields in instance_2")
    print()
    
    # Track missing mappings
    missing_mappings = []
    
    # Check each field group
    for group_name, group_data in config['field_groups'].items():
        print(f"\n📁 {group_name}")
        print("=" * 50)
        
        for field_key, field_config in group_data['fields'].items():
            field_desc = field_config.get('description', field_key)
            print(f"\n🔍 Checking: {field_desc}")
            
            # Check instance 1
            inst1_config = field_config.get('instance_1', {})
            inst1_field_id = inst1_config.get('field_id')
            
            if not inst1_field_id:
                print(f"  ⚠️  Instance 1: No field ID configured")
                # Try to find matching fields
                keywords = field_key.split('_')
                matches = find_field_by_keywords(cached_fields, keywords, 'instance_1')
                if matches:
                    print(f"  💡 Possible matches in instance_1:")
                    for match in matches[:3]:  # Show top 3 matches
                        print(f"     - {match['field_id']}: {match['field_name']}")
                missing_mappings.append(('instance_1', field_key, field_desc))
            else:
                print(f"  ✅ Instance 1: {inst1_field_id}")
            
            # Check instance 2
            inst2_config = field_config.get('instance_2', {})
            inst2_field_id = inst2_config.get('field_id')
            
            if not inst2_field_id:
                print(f"  ⚠️  Instance 2: No field ID configured")
                # Try to find matching fields
                keywords = field_key.split('_')
                matches = find_field_by_keywords(cached_fields, keywords, 'instance_2')
                if matches:
                    print(f"  💡 Possible matches in instance_2:")
                    for match in matches[:3]:  # Show top 3 matches
                        print(f"     - {match['field_id']}: {match['field_name']}")
                missing_mappings.append(('instance_2', field_key, field_desc))
            else:
                print(f"  ✅ Instance 2: {inst2_field_id}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    total_fields = sum(len(g['fields']) for g in config['field_groups'].values())
    configured_fields = total_fields * 2 - len(missing_mappings)  # Each field has 2 instances
    
    print(f"Total fields: {total_fields}")
    print(f"Configured mappings: {configured_fields}/{total_fields * 2}")
    print(f"Missing mappings: {len(missing_mappings)}")
    
    if missing_mappings:
        print("\n⚠️  Fields needing attention:")
        for instance, field_key, field_desc in missing_mappings:
            print(f"  - {field_desc} ({field_key}) in {instance}")
    
    print("\n💡 Next steps:")
    print("1. Use the Field Mapping Wizard to configure missing fields")
    print("2. Search for fields using the suggested matches above")
    print("3. Update the configuration file with the correct field IDs")


def search_specific_field(field_name):
    """Search for a specific field by name across both instances."""
    
    print(f"Searching for field: {field_name}")
    print("=" * 50)
    
    cached_fields = get_cached_fields()
    
    if not cached_fields:
        print("❌ No cached fields found. Please run field discovery first.")
        return
    
    for instance in ['instance_1', 'instance_2']:
        print(f"\n{instance}:")
        matches = find_field_by_keywords(cached_fields, [field_name], instance)
        
        if matches:
            for match in matches:
                print(f"  - {match['field_id']}: {match['field_name']}")
                print(f"    Type: {match.get('field_type', 'unknown')}")
                print(f"    Custom: {match.get('is_custom', False)}")
        else:
            print(f"  No matches found")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify and update field mappings")
    parser.add_argument('--search', help="Search for a specific field by name")
    
    args = parser.parse_args()
    
    if args.search:
        search_specific_field(args.search)
    else:
        verify_mappings()