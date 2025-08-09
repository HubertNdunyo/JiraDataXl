# JIRA Instances Configuration Guide

## Overview
The JIRA Sync Dashboard now supports flexible configuration of multiple JIRA instances, allowing you to add, remove, or modify instances without changing code.

## Configuration Methods

### Method 1: Environment Variable (Recommended for Production)

Set the `JIRA_INSTANCES` environment variable with a JSON array of instance objects:

```bash
export JIRA_INSTANCES='[
  {
    "url": "https://company1.atlassian.net",
    "username": "user@company1.com",
    "api_token": "your-api-token-1",
    "type": "source",
    "name": "Primary JIRA",
    "enabled": true
  },
  {
    "url": "https://company2.atlassian.net",
    "username": "user@company2.com",
    "api_token": "your-api-token-2",
    "type": "target",
    "name": "Secondary JIRA",
    "enabled": true
  }
]'
```

### Method 2: Configuration File

1. Create a JSON configuration file (e.g., `jira_instances.json`):

```json
{
  "instances": [
    {
      "id": "prod_jira",
      "name": "Production JIRA",
      "url": "https://production.atlassian.net",
      "username": "service-account@company.com",
      "api_token": "token-123456",
      "type": "source",
      "enabled": true
    },
    {
      "id": "staging_jira",
      "name": "Staging JIRA",
      "url": "https://staging.atlassian.net",
      "username": "service-account@company.com",
      "api_token": "token-789012",
      "type": "target",
      "enabled": true
    },
    {
      "id": "dev_jira",
      "name": "Development JIRA",
      "url": "https://dev.atlassian.net",
      "username": "dev-account@company.com",
      "api_token": "token-345678",
      "type": "development",
      "enabled": false
    }
  ]
}
```

2. Set the `JIRA_CONFIG_FILE` environment variable:

```bash
export JIRA_CONFIG_FILE="/path/to/jira_instances.json"
```

### Method 3: Legacy Environment Variables (Backward Compatible)

For backward compatibility, the system still supports the old format:

```bash
export JIRA_URL_1="https://instance1.atlassian.net"
export JIRA_USERNAME_1="user@company.com"
export JIRA_PASSWORD_1="api-token-1"

export JIRA_URL_2="https://instance2.atlassian.net"
export JIRA_USERNAME_2="user@company.com"
export JIRA_PASSWORD_2="api-token-2"
```

⚠️ **Note**: This method only supports exactly 2 instances and is deprecated.

## Instance Configuration Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `url` | Yes | JIRA instance URL | `https://company.atlassian.net` |
| `username` | Yes | JIRA username/email | `user@company.com` |
| `api_token` or `password` | Yes | JIRA API token | `ATATT3xFfGF0...` |
| `type` | No | Instance type/role | `source`, `target`, `development` |
| `name` | No | Display name | `Production JIRA` |
| `id` | No | Unique identifier | `prod_jira` |
| `enabled` | No | Whether to use this instance | `true` or `false` |

## Docker Compose Example

```yaml
services:
  backend:
    environment:
      # Method 1: Inline JSON
      - JIRA_INSTANCES=[{"url":"https://prod.atlassian.net","username":"user@company.com","api_token":"${JIRA_TOKEN_1}","type":"source","name":"Production"},{"url":"https://staging.atlassian.net","username":"user@company.com","api_token":"${JIRA_TOKEN_2}","type":"target","name":"Staging"}]
      
      # OR Method 2: Config file
      - JIRA_CONFIG_FILE=/config/jira_instances.json
    volumes:
      - ./config:/config:ro
```

## .env File Example

```bash
# Database configuration
DB_NAME=jira_sync
DB_USER=postgres
DB_PASSWORD=secure-password
DB_HOST=localhost
DB_PORT=5432

# JIRA instances as JSON
JIRA_INSTANCES='[{"url":"https://company1.atlassian.net","username":"user@company1.com","api_token":"token1","type":"source","name":"Main JIRA","enabled":true},{"url":"https://company2.atlassian.net","username":"user@company2.com","api_token":"token2","type":"target","name":"Backup JIRA","enabled":true}]'

# OR point to config file
# JIRA_CONFIG_FILE=/opt/app/config/jira_instances.json
```

## Adding/Removing Instances

### To Add a New Instance:

1. **Using Environment Variable**: Add the new instance object to the JSON array
2. **Using Config File**: Add the instance to the `instances` array in the file
3. Restart the application

### To Remove an Instance:

1. **Temporary Disable**: Set `"enabled": false` for the instance
2. **Permanent Removal**: Remove the instance object from the configuration
3. Restart the application

## Migration from Legacy Configuration

If you're currently using the legacy `JIRA_URL_1/2` environment variables:

1. Create a new configuration using one of the methods above
2. Test the new configuration in a staging environment
3. Remove the legacy environment variables
4. Deploy the new configuration

## Troubleshooting

### Common Issues

1. **"No JIRA instances configured" error**
   - Ensure either `JIRA_INSTANCES` or `JIRA_CONFIG_FILE` is set
   - Check JSON syntax is valid
   - Verify file permissions if using config file

2. **JSON parsing errors**
   - Validate JSON using `jq` or online validator
   - Ensure proper escaping in environment variables
   - Check for trailing commas

3. **Authentication failures**
   - Verify API tokens are correct
   - Check instance URLs don't have trailing slashes
   - Ensure usernames match JIRA accounts

### Validation Script

Use this script to validate your configuration:

```python
#!/usr/bin/env python3
import json
import os
import sys

def validate_config():
    # Check environment variable
    jira_instances = os.getenv('JIRA_INSTANCES')
    if jira_instances:
        try:
            instances = json.loads(jira_instances)
            print(f"✓ Found {len(instances)} instances in JIRA_INSTANCES")
            for i, inst in enumerate(instances):
                required = ['url', 'username']
                if all(k in inst for k in required):
                    print(f"  ✓ Instance {i+1}: {inst.get('name', 'Unnamed')}")
                else:
                    print(f"  ✗ Instance {i+1}: Missing required fields")
            return True
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in JIRA_INSTANCES: {e}")
            return False
    
    # Check config file
    config_file = os.getenv('JIRA_CONFIG_FILE')
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file) as f:
                config = json.load(f)
                instances = config.get('instances', [])
                print(f"✓ Found {len(instances)} instances in {config_file}")
                return True
        except Exception as e:
            print(f"✗ Error reading config file: {e}")
            return False
    
    # Check legacy variables
    if all(os.getenv(f'JIRA_URL_{i}') for i in [1, 2]):
        print("✓ Found legacy JIRA configuration (limited to 2 instances)")
        return True
    
    print("✗ No JIRA configuration found")
    return False

if __name__ == "__main__":
    sys.exit(0 if validate_config() else 1)
```

## Security Best Practices

1. **Never commit API tokens** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API tokens** regularly
4. **Use read-only service accounts** where possible
5. **Encrypt config files** at rest if storing tokens
6. **Limit instance access** by setting `enabled: false` when not needed