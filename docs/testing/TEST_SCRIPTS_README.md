# JIRA Testing Documentation

## Overview

This document describes testing approaches for the JIRA Sync Dashboard. While dedicated test scripts have been removed, testing can be performed through the API and utilities.

## Testing Methods

### 1. API Testing

Test the sync functionality through the REST API:

```bash
# Test sync endpoint
curl -X POST http://localhost:8987/api/sync/run \
  -H "Content-Type: application/json"

# Test admin endpoints
curl -X GET http://localhost:8987/api/admin/test \
  -H "X-Admin-Key: jira-admin-key-2024"

# Test field discovery
curl -X POST http://localhost:8987/api/admin/fields/discover \
  -H "X-Admin-Key: jira-admin-key-2024"
```

### 2. JIRA Utilities

The `/jira_utilities/` folder contains helper scripts for testing JIRA workflows:

- `test_jira_automation.py` - Test automation workflows
- `test_inua_interface.py` - Test INUA interface integration
- `quick_test.py` - Quick functionality verification
- `test_escalation_path.py` - Test escalation workflows

Run from the jira_utilities directory:
```bash
cd jira_utilities
python3 test_inua_interface.py
```

### 3. Manual Testing Through UI

1. **Field Mapping Test**
   - Navigate to http://localhost:5648/admin/field-mappings
   - Use the Setup Wizard to test field discovery
   - Preview field data before saving

2. **Sync Test**
   - Click "Run Manual Sync" on the dashboard
   - Monitor progress in real-time
   - Check sync history for results
3. **Cancellation Path** - Failed shoot scenario
4. **Escalation Path** - Quality issues escalation
5. **Field Validation** - Required field testing

**Options:**
- `--project PROJ` - Test in different project (default: INUA)
- `--prefix PREFIX` - Custom test issue prefix (default: TEST_AUTO_)
- `--cleanup` - Delete test issues after completion
- `--cleanup-old DAYS` - Delete test issues older than DAYS
- `--no-confirm` - Skip confirmation prompts
- `--tests [basic workflow cancel escalate fields]` - Run specific tests

### 3. Test Configuration (`test_config.json`)

Configuration file containing:
- Test settings and defaults
- Test data (addresses, photo counts, etc.)
- Field mappings
- Transition IDs
- Cleanup options

## Safety Features

1. **Test Prefix**: All test issues are prefixed (e.g., "TEST_AUTO_") for easy identification
2. **Confirmation Prompts**: Deletion operations require confirmation
3. **Detailed Logging**: All operations are logged with timestamps
4. **Test Reports**: Comprehensive reports saved to timestamped files
5. **Cleanup Options**: Multiple ways to clean up test data

## Example Usage

### Basic Testing Flow

```bash
# 1. Run quick test to verify basic functionality
python3 quick_test.py

# 2. If successful, run comprehensive tests
python3 test_jira_automation.py

# 3. Review the generated test report
cat test_report_*.txt

# 4. Clean up test issues
python3 test_jira_automation.py --cleanup-old 0
```

### Continuous Testing

```bash
# Run specific workflow test with auto-cleanup
python3 test_jira_automation.py --tests workflow --cleanup --no-confirm

# Test escalation path only
python3 test_jira_automation.py --tests escalate
```

### Cleanup Operations

```bash
# Interactive cleanup of all TEST_AUTO_ issues
python3 test_jira_automation.py --cleanup-old 0

# Delete test issues older than 3 days
python3 test_jira_automation.py --cleanup-old 3

# Quick cleanup of QUICK_TEST_ issues
python3 quick_test.py --cleanup
```

## Test Reports

Test reports are automatically generated and include:
- Test run timestamp
- Pass/fail status for each test
- Detailed error messages
- List of created issues
- Overall success rate

Example report location: `test_report_20241101_143022.txt`

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify `.env` file contains correct credentials
   - Check JIRA_CREATE_EMAIL and JIRA_CREATE_TOKEN

2. **Permission Errors**
   - Ensure account has create/delete permissions
   - Verify project access

3. **Transition Failures**
   - Check workflow hasn't changed
   - Verify field requirements are met

4. **Cleanup Issues**
   - Some issues may be in states that prevent deletion
   - Manual cleanup may be required

## Best Practices

1. **Regular Testing**: Run tests after any JIRA configuration changes
2. **Clean Environment**: Clean up old test issues regularly
3. **Review Reports**: Check test reports for any failures
4. **Update Tests**: Modify tests when workflow changes
5. **Safe Testing**: Always use test projects when possible

## Integration with CI/CD

The test scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run JIRA Tests
  run: |
    python3 test_jira_automation.py --no-confirm
    
- name: Cleanup Test Issues
  if: always()
  run: |
    python3 test_jira_automation.py --cleanup --no-confirm
```

## Extending the Tests

To add new test scenarios:

1. Add test method to `JiraAutomationTester` class
2. Update `run_all_tests()` to include new test
3. Add configuration to `test_config.json`
4. Document the new test scenario

## Support

For issues or questions:
1. Check the main documentation in `/docs`
2. Review test reports for detailed error messages
3. Verify JIRA permissions and workflow configuration