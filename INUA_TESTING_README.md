# INUA Testing Interface

## Overview

The INUA Testing interface provides a simple web-based UI for creating and managing test cards in the INUA JIRA project. It allows you to:

- Create test cards with custom summaries
- Move cards through the entire workflow
- Handle required fields (photo count, revision notes)
- Delete test cards when done

## Access

1. Start the backend: `cd backend && python main.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Navigate to: http://localhost:5648/admin/inua-test

## Features

### Create Test Card
- Enter a descriptive summary
- Card is automatically prefixed with timestamp
- Created in "Scheduled" status

### Workflow Navigation
- Visual workflow progress indicator
- Available transitions shown as buttons
- Automatic handling of required fields:
  - **Shoot Complete → Uploaded**: Number of photos required
  - **Final Review → Escalated Editing**: Revision notes required

### Card Management
- View current status and available transitions
- Refresh card to see latest status
- Open card in JIRA with one click
- Delete card when testing is complete

## Workflow Path

```
Scheduled
    ↓
ACKNOWLEDGED
    ↓
At Listing
    ↓
Shoot Complete
    ↓ (requires photo count)
Uploaded
    ↓
Edit
    ↓
Final Review
    ├→ Closed (standard path)
    └→ Escalated Editing (requires notes)
```

## API Endpoints

The interface uses these backend endpoints:

- `POST /api/admin/inua-test/create-issue` - Create test card
- `GET /api/admin/inua-test/issue/{key}` - Get card details
- `POST /api/admin/inua-test/transition` - Move card status
- `DELETE /api/admin/inua-test/issue/{key}` - Delete card
- `GET /api/admin/inua-test/workflow-info` - Get workflow details

## Testing the API

Run the test script to verify API functionality:

```bash
python3 test_inua_interface.py
```

## Troubleshooting

### Backend Issues
- Ensure `.env` contains JIRA credentials
- Check backend is running on port 8987
- Verify JIRA API access

### Frontend Issues  
- Check frontend is running on port 5648
- Clear browser cache if UI doesn't update
- Check browser console for errors

### JIRA Issues
- Verify account has permissions for INUA project
- Check workflow hasn't changed
- Ensure required fields are configured

## Notes

- Only one test card can be active at a time
- All test cards are prefixed with "TEST_" for easy identification
- The interface follows JIRA's workflow rules and validations
- Some transitions may fail if JIRA has additional validators