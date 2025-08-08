# INUA Project Workflow Guide

## Project Overview

- **Project Name**: Inua Hub Staging
- **Project Key**: INUA
- **Project Type**: Photography/Media Service Management
- **Total Issues**: 334+
- **Issue Type**: NDP Photo / Video Service

## Workflow Diagram

```
┌─────────────┐
│  Scheduled  │ (Initial state when photo shoot is booked)
└──────┬──────┘
       │ ID: 31 - "MP Acknowledges Assignment"
       ▼
┌─────────────────┐
│  ACKNOWLEDGED   │ (Photographer confirms assignment)
└────────┬────────┘
         │ ID: 171 - "MP Arrive at Listing"
         ▼
┌─────────────┐
│ At Listing  │ (Photographer at property)
└──────┬──────┘
       │ ID: 201 - "Shoot Complete"
       ▼
┌──────────────────┐
│ Shoot Complete   │ (Photos taken, ready for upload)
└─────────┬────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
ID: 51       ID: 311
"Upload      "failed
Raw Media"    shoot"
    │           │
    ▼           │
┌──────────┐    │
│ Uploaded │    │ (Alternative path for
└────┬─────┘    │  cancelled/failed shoots)
     │          │
ID: 71         │
"Editing       │
started"       │
     │          │
     ▼          │
┌────────┐      │
│  Edit  │      │
└────┬───┘      │
     │          │
ID: 161        │
"Edit          │
Complete"      │
     │          │
     ▼          │
┌──────────────┐│
│ Final Review ││
└──────┬───────┘│
       │        │
       │        │
  ┌────┴────┐   │
  │         │   │
ID: 91    ID: 181│
"NDP Media "Not  │
Delivered" Approved"
  │         │   │
  │         ▼   │
  │    ┌─────────────┐
  │    │ Escalated   │
  │    │  Editing    │
  │    └─────────────┘
  │              │
  ▼              ▼
┌──────────────────┐
│      Closed      │ (Final state)
└──────────────────┘
```

## Transition Details

### ✅ Working Transitions

| From | To | Transition ID | Name | Notes |
|------|----|--------------:|------|-------|
| Scheduled | ACKNOWLEDGED | 31 | MP Acknowledges Assignment | Photographer confirms |
| ACKNOWLEDGED | At Listing | 171 | MP Arrive at Listing | On-site arrival |
| At Listing | Shoot Complete | 201 | Shoot Complete | Photos taken |
| Shoot Complete | Closed | 311 | failed shoot | Cancellation path |
| Uploaded | Edit | 71 | Editing started | Begin post-processing |
| Edit | Final Review | 161 | Edit Complete | QA check |
| Final Review | Closed | 91 | NDP Media Delivered | Client delivery |

### ✅ Transitions with Field Requirements

| From | To | Transition ID | Name | Required Field |
|------|----|--------------|------|----------------|
| Shoot Complete | Uploaded | 51 | Upload Raw Media | **customfield_12602** (NDPU Number of Raw Photos) - must be set BEFORE transition |
| Final Review | Escalated Editing | 181 | Not Approved | **customfield_10716** (NDPU Edited Media Revision Notes) |

## Field Restrictions

### On Issue Creation
- ✅ **Allowed**: `summary` only
- ❌ **Not Allowed**: `description`, `labels`, most custom fields

### Custom Fields Available

**Order Management:**
- `customfield_10501`: NDPU Order Number
- `customfield_11900`: NDPU Appointment Number

**Client Information:**
- `customfield_10600`: NDPU Client Name
- `customfield_10601`: NDPU Client Email
- `customfield_10602`: NDPU Client Cell No.

**Property Details:**
- `customfield_10603`: NDPU Listing Address
- `customfield_10604`: NDPU City State Zip
- `customfield_10700`: NDPU Access Instructions
- `customfield_11100`: NDPU Special Instructions

**Photo Shoot Details:**
- `customfield_12602`: NDPU Number of Raw Photos
- `customfield_10713`: NDPU Raw Media Folder Link
- `customfield_10714`: NDPU Edited Media Folder Link
- `customfield_10711`: NDPU Shoot Start Time

**Timestamps:**
- `customfield_12699`: NDPU Acknowledged Timestamp
- `customfield_12609`: NDPU At Listing Timestamp
- `customfield_12606`: NDPU Shoot Complete Timestamp
- `customfield_12608`: NDPU Uploaded Timestamp
- `customfield_12603`: NDPE Editing Start Timestamp
- `customfield_12604`: NDPE Editing End Timestamp
- `customfield_12703`: NDPU Final Review Timestamp
- `customfield_12704`: NDPU Closed Timestamp

## Upload Transition Requirements

### Current Status: ✅ Fully Tested and Confirmed

The "Upload Raw Media" transition from Shoot Complete → Uploaded has been fully tested and documented.

### Confirmed Field Requirements

```markdown
## Upload Transition - Required Fields

✅ **Tested and Confirmed**

Required fields discovered:
1. Field: NDPU Number of Raw Photos (customfield_12602)
   - Type: String
   - Format: Numeric string (e.g., "10", "25", "0")
   - Example: "10"
   - Notes: Must be set BEFORE transition, not during

2. Field: NDPU Edited Media Revision Notes (customfield_10716)
   - Type: Text string
   - Format: Free text
   - Example: "Initial review notes"
   - Used for: Final Review → Escalated Editing transition (via "Not Approved")
```

## Code Examples

### Create INUA Issue
```python
from jira_issue_manager import JiraIssueManager

manager = JiraIssueManager(use_create_account=True)
issue = manager.create_issue(
    project_key="INUA",
    summary="123 Main St - Professional Photography",
    issue_type="NDP Photo / Video Service"
)
```

### Follow Standard Workflow
```python
# Acknowledge assignment
change_issue_status(issue_key, "ACKNOWLEDGED", "Photographer confirmed")

# Arrive at listing
change_issue_status(issue_key, "At Listing", "On site")

# Complete shoot
change_issue_status(issue_key, "Shoot Complete", "25 photos taken")

# Update field BEFORE transition
update_issue_field(issue_key, "customfield_12602", "25")  # Set number of photos

# Then transition to Uploaded
change_issue_status(issue_key, "Uploaded", "Media uploaded")
```

### Alternative Cancellation Path
```python
# From Shoot Complete directly to Closed
change_issue_status(issue_key, "Closed", "Shoot cancelled due to weather")
```

## Business Logic

The INUA workflow represents a complete photography service lifecycle:

1. **Scheduling**: Client books photo shoot
2. **Assignment**: Photographer acknowledges job
3. **Execution**: Photographer arrives and completes shoot
4. **Upload**: Media transferred to processing system
5. **Post-Processing**: Photos edited
6. **Quality Control**: Final review before delivery
7. **Delivery**: Completed media sent to client

The "failed shoot" path handles real-world scenarios:
- Weather cancellations
- Property access issues
- Equipment failures
- Client no-shows

## Complete Workflow Summary

All transitions have been tested and documented. The INUA workflow supports:

1. **Standard Path**: Scheduled → ACKNOWLEDGED → At Listing → Shoot Complete → Uploaded → Edit → Final Review → Closed
2. **Cancellation Path**: Shoot Complete → Closed (for failed shoots)
3. **Escalation Path**: Final Review → Escalated Editing (for quality issues)

### Key Implementation Notes

1. **Field Updates Must Precede Transitions**
   - Update customfield_12602 BEFORE transitioning to Uploaded
   - Update customfield_10716 BEFORE transitioning to Escalated Editing

2. **Helper Functions Available**
   - See `inua_workflow_helper.py` for convenience functions
   - Handles field updates and transitions automatically

3. **Tested Issues**
   - INUA-455, INUA-456: Demonstrated Upload transition
   - INUA-457: Demonstrated Escalation path