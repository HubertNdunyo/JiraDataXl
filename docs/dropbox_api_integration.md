# Dropbox API Integration Guide

## Overview
The Dropbox metadata viewer currently returns mock data. This guide explains how to implement actual Dropbox API integration.

## Current Implementation
- **Route**: `/dropbox-viewer`
- **API Endpoint**: `/api/dropbox/metadata`
- **Features**:
  - URL parsing and validation
  - Mock metadata response
  - File list display
  - URL history tracking
  - Dark mode support

## Steps to Implement Real Dropbox API

### 1. Create Dropbox App
1. Go to https://www.dropbox.com/developers/apps
2. Click "Create app"
3. Choose:
   - API: Scoped access
   - Access: Full Dropbox or App folder
   - Name: Your app name
4. Save the App key and App secret

### 2. Install Dependencies
```bash
pip install dropbox
```

### 3. Environment Variables
Add to your `.env` file:
```
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_ACCESS_TOKEN=your_access_token  # Optional, for server-side auth
```

### 4. Update the API Endpoint

Replace the mock data section in `/api/dropbox/metadata` with:

```python
import dropbox
from dropbox.exceptions import ApiError, AuthError

# Initialize Dropbox client
dbx = dropbox.Dropbox(os.environ.get('DROPBOX_ACCESS_TOKEN'))

try:
    # Get shared link metadata
    shared_link = dropbox.files.SharedLink(url=url)
    
    # For folders
    if share_type == 'sh':
        folder_metadata = dbx.files_list_folder(
            path='',
            shared_link=shared_link
        )
        
        files = []
        total_size = 0
        
        for entry in folder_metadata.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                files.append({
                    'name': entry.name,
                    'type': entry.mime_type or 'unknown',
                    'size': entry.size,
                    'modified': entry.server_modified.isoformat()
                })
                total_size += entry.size
        
        metadata = {
            'share_type': 'folder',
            'share_id': share_id,
            'url': url,
            'folder_name': 'Shared Folder',
            'file_count': len(files),
            'total_size': total_size,
            'files': files
        }
    
    # For single files
    else:
        file_metadata = dbx.files_get_metadata(
            path='',
            shared_link=shared_link
        )
        
        metadata = {
            'share_type': 'file',
            'share_id': share_id,
            'url': url,
            'file_name': file_metadata.name,
            'file_size': file_metadata.size,
            'modified': file_metadata.server_modified.isoformat()
        }
        
except AuthError as e:
    return jsonify({'error': 'Authentication failed'}), 401
except ApiError as e:
    return jsonify({'error': f'Dropbox API error: {str(e)}'}), 400
```

### 5. OAuth Flow (Optional)
For user-specific access without storing tokens:

```python
from dropbox import DropboxOAuth2Flow

# Initialize OAuth flow
auth_flow = DropboxOAuth2Flow(
    app_key=os.environ.get('DROPBOX_APP_KEY'),
    app_secret=os.environ.get('DROPBOX_APP_SECRET'),
    redirect_uri='http://localhost:3545/dropbox/callback',
    session=session,
    csrf_token_session_key='dropbox-csrf-token'
)

# Get authorization URL
auth_url = auth_flow.get_authorize_url()
```

### 6. Advanced Features
Consider adding:
- File preview generation
- Download links
- Folder tree navigation
- File type filtering
- Batch metadata fetching

## Security Considerations
1. Never expose App secret in client-side code
2. Use environment variables for credentials
3. Implement rate limiting
4. Validate and sanitize URLs
5. Consider using refresh tokens for long-term access

## Testing
Test with various Dropbox URL formats:
- Shared folders: `https://www.dropbox.com/sh/...`
- Shared files: `https://www.dropbox.com/s/...`
- Business links: `https://www.dropbox.com/work/...`

## Error Handling
Handle common scenarios:
- Invalid or expired links
- Private folders requiring authentication
- Rate limiting (429 errors)
- Network timeouts
- Large folders (implement pagination)