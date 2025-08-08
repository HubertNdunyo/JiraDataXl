# JIRA Integration Guide

## Overview

This guide documents the JIRA integration capabilities for the JIRA Sync Dashboard, including authentication, permissions, issue management, and workflow transitions.

## Table of Contents

1. [Authentication](#authentication)
2. [Account Permissions](#account-permissions)
3. [Core Functionality](#core-functionality)
4. [INUA Project Workflow](#inua-project-workflow)
5. [Implementation Files](#implementation-files)
6. [API Reference](#api-reference)

---

## Authentication

### Working Credentials

The system uses two sets of credentials:

1. **Read/Write Account** (jmwangi@inuaai.net)
   - Used for: General sync operations, status changes
   - Access: 101 projects across both instances
   - Limitations: Some projects may have restricted access

2. **Admin Account** (jira@inuaai.com)
   - Used for: Creating, cloning, and deleting issues
   - Access: 56 projects (10 on Instance 1, 46 on Instance 2)
   - Special permissions: Administrator role on INUA project

### Environment Variables

```bash
# Primary sync account
JIRA_EMAIL="jmwangi@inuaai.net"
JIRA_ACCESS_TOKEN="<token>"

# Admin/create account
JIRA_CREATE_EMAIL="jira@inuaai.com"  
JIRA_CREATE_TOKEN="<password/token>"
```

### Important Notes

- JIRA API tokens are different from passwords but both can work with Basic Auth
- Tokens must be created by the account that will use them
- Accounts must be added to JIRA instances before API access works

---

## Account Permissions

### jira@inuaai.com Capabilities

✅ **Full Permissions on INUA Project:**
- Create issues
- Edit issues  
- Delete issues
- Change status/transitions
- Add comments
- Administrator role

✅ **Verified Operations:**
- Created: IT-2, INUA-449, INUA-450, INUA-451, INUA-453, INUA-454, INUA-455, INUA-456, INUA-457
- Deleted: INUA-449
- Status transitions: All standard workflow paths including escalation
- Field updates: customfield_12602, customfield_10716

---

## Core Functionality

### 1. Issue Creation

```python
from jira_issue_manager import JiraIssueManager

manager = JiraIssueManager(use_create_account=True)

# Create issue
issue = manager.create_issue(
    project_key="INUA",
    summary="Issue title",
    issue_type="NDP Photo / Video Service",
    # description and other fields may be restricted
)
```

**Key Findings:**
- INUA project has restricted fields - only `summary` is guaranteed to work
- Issue type must match exactly (e.g., "NDP Photo / Video Service" not "Task")
- Description, labels, and many custom fields are not allowed on create

### 2. Status Changes

```python
from change_issue_status import change_issue_status

# Change status with comment
success = change_issue_status(
    issue_key="INUA-123",
    target_status="In Progress",
    comment_text="Status update comment"
)
```

**Key Findings:**
- Status transitions are workflow-dependent
- Each project may have different workflow rules
- Some transitions have validators/conditions

### 3. Issue Deletion

```python
import requests
from requests.auth import HTTPBasicAuth

def delete_issue(issue_key):
    auth = HTTPBasicAuth("jira@inuaai.com", "<token>")
    url = f"https://betteredits2.atlassian.net/rest/api/2/issue/{issue_key}"
    response = requests.delete(url, auth=auth)
    return response.status_code == 204
```

**Key Findings:**
- Requires administrator or specific delete permissions
- Permanent action - no recycle bin
- Returns 204 on success

---

## INUA Project Workflow

### Project Details
- **Name**: Inua Hub Staging
- **Key**: INUA
- **Type**: Photography/Media Service Management
- **URL**: https://betteredits2.atlassian.net/jira/core/projects/INUA/board

### Workflow States

```
Scheduled
    ↓ (31: MP Acknowledges Assignment)
ACKNOWLEDGED  
    ↓ (171: MP Arrive at Listing)
At Listing
    ↓ (201: Shoot Complete)
Shoot Complete
    ↓ (51: Upload Raw Media) OR (311: failed shoot)
    ├─→ Uploaded          └─→ Closed
    ↓ (71: Editing started)
Edit
    ↓ (161: Edit Complete)
Final Review
    ├─→ (91: NDP Media Delivered) → Closed
    └─→ (181: Not Approved) → Escalated Editing
```

### Transition Requirements

#### ✅ Upload Raw Media (Shoot Complete → Uploaded)
**Status**: Confirmed and working
**Required Field**: `customfield_12602` (NDPU Number of Raw Photos)

```python
# Must update field BEFORE transition
update_issue_field(issue_key, "customfield_12602", "25")  # Number of photos
time.sleep(1)  # Allow field update to propagate
# Then transition
change_issue_status(issue_key, "Uploaded", "Media uploaded")
```

#### ✅ Failed Shoot (Shoot Complete → Closed)
**Status**: Working
**Use Case**: When shoot cannot be completed
```python
# Transition ID: 311
change_issue_status(issue_key, "Closed", "Reason for failed shoot")
```

#### ✅ Not Approved (Final Review → Escalated Editing)
**Status**: Confirmed and working
**Required Field**: `customfield_10716` (NDPU Edited Media Revision Notes)

```python
# Must update field BEFORE transition
update_issue_field(issue_key, "customfield_10716", "Needs color correction")
time.sleep(1)
# Then transition using "Not Approved" (ID: 181)
transition_issue(issue_key, "181", "Not approved: revision needed")
```

### Custom Fields

The INUA project has 200+ custom fields for managing photography workflows:

**Key Fields:**
- Order Number: `customfield_10501`
- Client Name: `customfield_10600`
- Client Email: `customfield_10601`
- Listing Address: `customfield_10603`
- Access Instructions: `customfield_12611`
- Special Instructions: `customfield_12612`
- Number of Raw Photos: `customfield_12602`
- Raw Media Folder Link: `customfield_10713`
- Edited Media Folder Link: `customfield_10714`

---

## Implementation Files

### Core Files

1. **jira_issue_manager.py**
   - Main class for issue operations
   - Handles creation, cloning, retrieval
   - Supports both account types

2. **change_issue_status.py**
   - Standalone status change functionality
   - Shows available transitions
   - Handles transition validation

### Usage Examples

```python
# Create issue in INUA
manager = JiraIssueManager(use_create_account=True)
issue = manager.create_issue(
    project_key="INUA",
    summary="123 Main St - Photo Shoot",
    issue_type="NDP Photo / Video Service"
)

# Change status
change_issue_status(issue['key'], "ACKNOWLEDGED")

# Clone issue
cloned = manager.clone_issue(
    source_issue_key=issue['key'],
    target_project_key="INUA"
)

# Delete issue
delete_issue(issue['key'])
```

---

## API Reference

### Base URLs
- Instance 1: `https://betteredits.atlassian.net`
- Instance 2: `https://betteredits2.atlassian.net`

### Key Endpoints

#### Get Issue
```
GET /rest/api/2/issue/{issueKey}
```

#### Create Issue  
```
POST /rest/api/2/issue
```

#### Update Issue
```
PUT /rest/api/2/issue/{issueKey}
```

#### Delete Issue
```
DELETE /rest/api/2/issue/{issueKey}
```

#### Get Transitions
```
GET /rest/api/2/issue/{issueKey}/transitions
```

#### Execute Transition
```
POST /rest/api/2/issue/{issueKey}/transitions
```

### Authentication Header
```python
auth = HTTPBasicAuth(email, token)
```

---

## Best Practices

1. **Always check available transitions** before attempting status changes
2. **Use minimal fields** when creating issues in restricted projects
3. **Handle 400 errors** gracefully - they often indicate field restrictions
4. **Test in IT project** first before working with production projects
5. **Document required fields** for each project's workflows

---

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check token is valid
   - Ensure account has access to JIRA instance
   - Verify email matches token owner

2. **400 Bad Request on Create**
   - Remove description and custom fields
   - Check issue type matches exactly
   - Some fields may be screen-restricted

3. **Transition Failures**
   - Check available transitions first
   - Some transitions have validators
   - May require specific fields or conditions

4. **404 Not Found**
   - Issue may be in different instance
   - Check project key to determine instance
   - Verify account has project access

---

## Next Steps

1. **Field Requirements Complete** ✅
   - Upload transition requires customfield_12602 (set before transition)
   - Escalation requires customfield_10716 (set before transition)
   - All workflow paths documented and tested

2. **Integration Opportunities**
   - Automated status tracking
   - Bulk operations
   - Workflow automation
   - Custom field management
   - Helper functions available in `inua_workflow_helper.py`