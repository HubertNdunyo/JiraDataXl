# Field Mapping Testing Guide

**Critical Component**: Field mapping is the core functionality of the JIRA Sync Dashboard. Comprehensive testing is essential.

## Table of Contents
1. [Pre-Test Setup](#pre-test-setup)
2. [Database Initialization Tests](#database-initialization-tests)
3. [Field Discovery Tests](#field-discovery-tests)
4. [Field Mapping Configuration Tests](#field-mapping-configuration-tests)
5. [Field Extraction Tests](#field-extraction-tests)
6. [End-to-End Sync Tests](#end-to-end-sync-tests)
7. [Performance Tests](#performance-tests)
8. [Recovery Tests](#recovery-tests)
9. [Automated Test Suite](#automated-test-suite)

## Pre-Test Setup

### 1. Environment Verification
```bash
# Check all services are running
docker ps --format "table {{.Names}}\t{{.Status}}"

# Verify environment variables
docker exec jira-sync-backend env | grep JIRA

# Check database connection
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "SELECT version();"
```

### 2. Initialize Clean Database
```bash
# Reset database (WARNING: Destroys all data)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to start
sleep 30

# Initialize with defaults
docker exec jira-sync-backend python scripts/init_database.py
```

## Database Initialization Tests

### Test 1: Verify Configuration Tables
```sql
-- Run in PostgreSQL
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%config%'
ORDER BY table_name;"
```

**Expected**: Should see `configuration`, `configuration_history` tables

### Test 2: Verify Field Mappings Loaded
```bash
curl -s -H "X-Admin-Key: secure-admin-key-2024" \
  http://localhost:8987/api/admin/config/field-mappings | \
  jq '{
    version,
    total_instances: .instances | length,
    total_field_groups: .field_groups | length,
    total_fields: [.field_groups[].fields | length] | add
  }'
```

**Expected**: 
- version: "2.0"
- total_instances: 2
- total_field_groups: 9
- total_fields: 30+

### Test 3: Verify Schema Columns
```sql
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
SELECT COUNT(*) as total_columns
FROM information_schema.columns 
WHERE table_name = 'jira_issues_v2';"
```

**Expected**: 30+ columns including all ndpu_* fields

## Field Discovery Tests

### Test 1: Discover Fields from JIRA
```bash
# Trigger field discovery
curl -X POST http://localhost:8987/api/admin/fields/discover \
  -H "X-Admin-Key: secure-admin-key-2024"
```

**Expected**: 200+ fields discovered from each instance

### Test 2: Verify Field Cache
```sql
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
SELECT 
    instance_type,
    COUNT(*) as field_count,
    COUNT(CASE WHEN custom = true THEN 1 END) as custom_fields
FROM jira_field_cache
GROUP BY instance_type;"
```

**Expected**: 250+ fields per instance, 200+ custom fields

## Field Mapping Configuration Tests

### Test 1: Verify Column Name Mapping
```python
docker exec jira-sync-backend python -c "
from core.db.column_mappings import get_field_key_for_column

# Test critical mappings
test_cases = [
    ('ndpu_order_number', 'order_number'),
    ('ndpu_client_name', 'client_name'),
    ('ndpu_listing_address', 'listing_address'),
    ('dropbox_raw_link', 'dropbox_raw'),
    ('ndpu_editing_team', 'editing_team')
]

for db_col, expected_key in test_cases:
    actual_key = get_field_key_for_column(db_col)
    status = '✅' if actual_key == expected_key else '❌'
    print(f'{status} {db_col} -> {actual_key} (expected: {expected_key})')
"
```

**Expected**: All mappings should show ✅

### Test 2: Verify Field IDs in Configuration
```bash
# Check specific field configuration
curl -s -H "X-Admin-Key: secure-admin-key-2024" \
  http://localhost:8987/api/admin/config/field-mappings | \
  jq '.field_groups.order_details.fields.order_number'
```

**Expected**: Should show field_id for both instances (e.g., customfield_10501)

## Field Extraction Tests

### Test 1: Test Issue Processor
```python
docker exec jira-sync-backend python -c "
from core.jira.jira_issues import IssueProcessor
from core.jira import JiraClient

# Initialize processor
client = JiraClient('instance_1')
processor = IssueProcessor(client, 'instance_1')

# Check field mappings loaded
print(f'Field groups loaded: {len(processor.field_mappings)}')

# Get required fields
fields = processor.get_required_fields()
print(f'Required fields: {len(fields)}')
print(f'System fields: {[f for f in fields if not f.startswith(\"customfield_\")][:5]}')
print(f'Custom fields: {len([f for f in fields if f.startswith(\"customfield_\")])}')

# Test column mapping
for col in ['ndpu_order_number', 'ndpu_client_name', 'ndpu_listing_address']:
    mapping = processor.get_field_mapping_for_column(col)
    if mapping:
        print(f'✅ {col}: field_id={mapping.get(\"field_id\")}')
    else:
        print(f'❌ {col}: No mapping found')
"
```

**Expected**: 
- 9 field groups loaded
- 30+ required fields
- All test columns should show ✅ with field IDs

### Test 2: Single Issue Sync Test
```bash
# Sync a single project with known issues
curl -X POST http://localhost:8987/api/sync/start \
  -H "Content-Type: application/json" \
  -d '{"force": false, "projects": ["TEST"]}'
```

Wait 30 seconds, then verify:
```sql
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
SELECT 
    issue_key,
    CASE WHEN ndpu_order_number IS NOT NULL THEN '✅' ELSE '❌' END as order_number,
    CASE WHEN ndpu_client_name IS NOT NULL THEN '✅' ELSE '❌' END as client_name,
    CASE WHEN ndpu_listing_address IS NOT NULL THEN '✅' ELSE '❌' END as address,
    CASE WHEN status IS NOT NULL THEN '✅' ELSE '❌' END as status
FROM jira_issues_v2
WHERE project_name = 'TEST'
LIMIT 10;"
```

## End-to-End Sync Tests

### Test 1: Full Sync with Verification
```bash
# Start full sync
curl -X POST http://localhost:8987/api/sync/start \
  -H "Content-Type: application/json" \
  -d '{"force": true}'

# Monitor progress
watch -n 5 'curl -s http://localhost:8987/api/status/system | jq .sync_progress'
```

### Test 2: Verify Field Population Statistics
```sql
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
WITH field_stats AS (
    SELECT 
        COUNT(*) as total_issues,
        COUNT(ndpu_order_number) as has_order,
        COUNT(ndpu_client_name) as has_client,
        COUNT(ndpu_listing_address) as has_address,
        COUNT(ndpu_editing_team) as has_team,
        COUNT(ndpu_dropbox_raw) as has_dropbox
    FROM jira_issues_v2
)
SELECT 
    total_issues,
    ROUND(100.0 * has_order / NULLIF(total_issues, 0), 2) as pct_order,
    ROUND(100.0 * has_client / NULLIF(total_issues, 0), 2) as pct_client,
    ROUND(100.0 * has_address / NULLIF(total_issues, 0), 2) as pct_address,
    ROUND(100.0 * has_team / NULLIF(total_issues, 0), 2) as pct_team,
    ROUND(100.0 * has_dropbox / NULLIF(total_issues, 0), 2) as pct_dropbox
FROM field_stats;"
```

**Expected**: At least 20% population rate for key fields

## Performance Tests

### Test 1: Sync Speed Measurement
```bash
# Time a full sync
time curl -X POST http://localhost:8987/api/sync/start \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

**Expected**: < 2 minutes for 45,000 issues

### Test 2: Field Extraction Performance
```sql
-- Check processing speed
docker exec jira-sync-postgres psql -U postgres -d jira_sync -c "
SELECT 
    project_name,
    COUNT(*) as issue_count,
    MAX(last_updated) - MIN(last_updated) as sync_duration
FROM jira_issues_v2
WHERE last_updated > NOW() - INTERVAL '10 minutes'
GROUP BY project_name
ORDER BY issue_count DESC
LIMIT 10;"
```

## Recovery Tests

### Test 1: Database Recovery After Loss
```bash
# Simulate data loss
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
sleep 30

# Recover
docker exec jira-sync-backend python scripts/init_database.py

# Verify recovery
curl -s -H "X-Admin-Key: secure-admin-key-2024" \
  http://localhost:8987/api/admin/config/field-mappings | \
  jq '.field_groups | keys'
```

**Expected**: All field groups restored

### Test 2: Partial Sync Recovery
```bash
# Kill sync mid-process
curl -X POST http://localhost:8987/api/sync/start -d '{"force": true}'
sleep 10
curl -X POST http://localhost:8987/api/sync/stop

# Restart sync
curl -X POST http://localhost:8987/api/sync/start -d '{"force": false}'
```

**Expected**: Sync should resume and complete successfully

## Automated Test Suite

### Create Test Script
```bash
cat > /home/hubert/dataApp/backend/tests/test_field_mappings.py << 'EOF'
#!/usr/bin/env python3
"""
Automated field mapping test suite
"""
import requests
import psycopg2
import time
import json
from typing import Dict, List

class FieldMappingTester:
    def __init__(self):
        self.api_url = "http://localhost:8987"
        self.api_key = "secure-admin-key-2024"
        self.db_conn = psycopg2.connect(
            host="localhost",
            database="jira_sync",
            user="postgres",
            password="postgres"
        )
        
    def test_initialization(self) -> bool:
        """Test database initialization"""
        print("Testing database initialization...")
        
        # Check field mappings
        response = requests.get(
            f"{self.api_url}/api/admin/config/field-mappings",
            headers={"X-Admin-Key": self.api_key}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get field mappings: {response.status_code}")
            return False
            
        config = response.json()
        if len(config.get('field_groups', {})) < 5:
            print(f"❌ Not enough field groups: {len(config.get('field_groups', {}))}")
            return False
            
        print(f"✅ Field mappings initialized: {len(config['field_groups'])} groups")
        return True
        
    def test_field_extraction(self) -> bool:
        """Test field extraction from JIRA"""
        print("Testing field extraction...")
        
        # Start a sync
        response = requests.post(
            f"{self.api_url}/api/sync/start",
            json={"force": False, "projects": ["TEST"]}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to start sync: {response.status_code}")
            return False
            
        # Wait for sync
        time.sleep(30)
        
        # Check results
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(ndpu_order_number) as has_order,
                COUNT(ndpu_client_name) as has_client
            FROM jira_issues_v2
            WHERE project_name = 'TEST'
        """)
        
        row = cursor.fetchone()
        if row[1] == 0:  # No order numbers
            print(f"❌ No order numbers extracted: {row}")
            return False
            
        print(f"✅ Fields extracted: {row[1]} orders, {row[2]} clients out of {row[0]} issues")
        return True
        
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 50)
        print("FIELD MAPPING TEST SUITE")
        print("=" * 50)
        
        tests = [
            self.test_initialization,
            self.test_field_extraction,
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test failed with error: {e}")
                results.append(False)
                
        # Summary
        print("=" * 50)
        passed = sum(results)
        total = len(results)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ ALL TESTS PASSED")
        else:
            print("❌ SOME TESTS FAILED")
            
        return passed == total

if __name__ == "__main__":
    tester = FieldMappingTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
EOF

# Make executable
chmod +x /home/hubert/dataApp/backend/tests/test_field_mappings.py
```

### Run Automated Tests
```bash
docker exec jira-sync-backend python tests/test_field_mappings.py
```

## Troubleshooting Common Issues

### Issue: Fields Not Populating
1. Check field mappings are loaded
2. Verify column name mappings exist
3. Ensure JIRA credentials are correct
4. Check field IDs match JIRA instance
5. Restart backend after configuration changes

### Issue: Sync Fails
1. Check JIRA connectivity
2. Verify rate limits not exceeded
3. Check database space
4. Review error logs: `docker logs jira-sync-backend`

### Issue: Performance Degradation
1. Check database indexes
2. Verify Redis cache is working
3. Review connection pool settings
4. Check for memory leaks

## Success Criteria

✅ **Core Functionality**
- [ ] Database initialization completes without errors
- [ ] Field mappings load from JSON files
- [ ] Field discovery returns 200+ fields per instance
- [ ] Column name mapping works for all ndpu_* fields
- [ ] Custom fields populate during sync
- [ ] At least 20% of issues have custom field data

✅ **Performance**
- [ ] Full sync completes in < 2 minutes
- [ ] Processing speed > 300 issues/second
- [ ] No memory leaks during extended operation
- [ ] Database queries return in < 100ms

✅ **Reliability**
- [ ] Recovery from database loss works
- [ ] Partial sync resume functions correctly
- [ ] Error handling prevents data corruption
- [ ] Scheduler continues after failures

## Next Steps

1. **Automate testing** with GitHub Actions
2. **Add integration tests** for JIRA API
3. **Implement load testing** for scalability
4. **Create regression test suite**
5. **Add monitoring and alerting**