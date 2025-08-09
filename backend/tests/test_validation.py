#!/usr/bin/env python3
"""Test the validation endpoint"""
import requests
import json
from core.db.db_config import get_configuration

# Get the current config from DB
config = get_configuration('jira', 'field_mappings')
if config:
    data = config['value']
    print("Config structure:")
    print(f"- version: {data.get('version')}")
    print(f"- has instances: {'instances' in data}")
    print(f"- has field_groups: {'field_groups' in data}")
    print(f"- has description: {'description' in data}")
    print(f"- has last_updated: {'last_updated' in data}")
    
    # Try to validate it
    response = requests.post(
        'http://127.0.0.1:8987/api/admin/config/field-mappings/validate',
        json=data,
        headers={'X-Admin-Key': 'jira-admin-key-2024'}
    )
    
    print(f"\nValidation response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error response: {response.text}")
else:
    print("No config found in DB")