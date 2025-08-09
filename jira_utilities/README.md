# JIRA Utilities

This folder contains JIRA automation utilities and test scripts that are not part of the main application.

## Modules

### Core Utilities
- `jira_issue_manager.py` - Create and manage JIRA issues
- `change_issue_status.py` - Change workflow status of JIRA issues  
- `inua_workflow_helper.py` - Handle INUA project workflow transitions with required fields

### API Route (Currently Disabled)
- `inua_test_routes.py` - FastAPI routes for testing JIRA operations (requires core utilities)

### Test Scripts
- `test_jira_automation.py` - Comprehensive JIRA integration testing
- `test_inua_interface.py` - Test INUA API endpoints
- `test_escalation_path.py` - Test escalation workflow paths
- `create_test_issues_for_upload.py` - Create test issues for upload transitions
- `quick_test.py` - Quick JIRA automation test

## Note
These utilities are not included in the Docker build and are kept separate from the main application. They can be integrated back into the backend when needed by:
1. Moving the core utilities to `backend/core/`
2. Updating imports in `inua_test_routes.py`
3. Re-enabling the route in `backend/main.py`