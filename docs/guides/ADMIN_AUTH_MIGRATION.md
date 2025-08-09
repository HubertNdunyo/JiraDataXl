# Admin Authentication Migration Guide

## Overview

As of January 2025, the admin panel requires authentication for security reasons. This guide will help you migrate from the old system (with hard-coded API keys) to the new secure authentication system.

## What Changed

### Before (Security Risk ❌)
- Admin API key was hard-coded in frontend: `jira-admin-key-2024`
- Any user could inspect the source and see the admin key
- No authentication required to access admin pages
- Direct API calls from browser to backend

### After (Secure ✅)
- Admin API key only exists in environment variables
- Frontend never sees the actual API key
- Login required to access admin pages
- All admin API calls proxy through secure server-side routes
- Session-based authentication with HTTP-only cookies

## Migration Steps

### Step 1: Update Environment Variables

#### Backend Configuration
Add to your backend `.env` file:
```bash
# Admin API key - choose a strong, unique key
ADMIN_API_KEY=your-secure-admin-key-here
```

⚠️ **Important**: If you were using the default `jira-admin-key-2024`, you MUST change it to a secure key.

#### Frontend Configuration
Create or update your frontend `.env.local` file:
```bash
# Must match the backend ADMIN_API_KEY
ADMIN_API_KEY=your-secure-admin-key-here

# Random secret for signing session cookies
SESSION_SECRET=generate-random-string-here

# Backend API URL (if not using default)
NEXT_PUBLIC_API_URL=http://localhost:8987
```

To generate a secure session secret:
```bash
# Linux/Mac
openssl rand -hex 32

# Or use Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Step 2: Restart Services

#### Docker Users
```bash
# Stop services
docker-compose down

# Restart with new environment
docker-compose up -d
```

#### Manual Setup Users
```bash
# Restart backend
cd backend
# Stop the server (Ctrl+C)
./run.sh

# Restart frontend
cd frontend
# Stop the server (Ctrl+C)
npm run dev
```

### Step 3: Access Admin Panel

1. Navigate to your application (e.g., `http://localhost:5648`)
2. Click on "Admin Panel" in the sidebar
3. You'll be redirected to `/admin/login`
4. Enter your `ADMIN_API_KEY` as the password
5. Click "Login"

### Step 4: Verify Authentication

After logging in:
- You should be redirected to the admin dashboard
- A secure session cookie is created (HTTP-only)
- Session lasts 24 hours by default
- All admin routes are now accessible

## Security Best Practices

### 1. Choose Strong API Keys
```bash
# Good ✅
ADMIN_API_KEY=xK9$mP2@nL5^qR8&wY3*hG6!fD4#sA7

# Bad ❌
ADMIN_API_KEY=admin123
ADMIN_API_KEY=password
ADMIN_API_KEY=jira-admin-key-2024
```

### 2. Protect Environment Files
```bash
# Ensure .env files are in .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore

# Set proper file permissions
chmod 600 .env
chmod 600 frontend/.env.local
```

### 3. Use Different Keys per Environment
- Development: Use a simple key for convenience
- Staging: Use a different, stronger key
- Production: Use a unique, very strong key

### 4. Rotate Keys Regularly
- Change API keys every 3-6 months
- Update both backend and frontend together
- Clear browser cookies after key rotation

## Troubleshooting

### "Unauthorized - Please login" Error
- **Cause**: Session expired or not authenticated
- **Solution**: Go to `/admin/login` and login again

### "Admin API key not configured" Error
- **Cause**: `ADMIN_API_KEY` not set in environment
- **Solution**: Set the environment variable and restart services

### "Invalid credentials" Error
- **Cause**: Password doesn't match `ADMIN_API_KEY`
- **Solution**: Ensure the same key is set in both backend and frontend

### Can't Access Admin After Login
- **Cause**: Cookie not being set properly
- **Solution**: 
  - Check browser console for errors
  - Ensure you're accessing via the correct URL (not mixing localhost/IP)
  - Clear cookies and try again

### Frontend Can't Connect to Backend
- **Cause**: `NEXT_PUBLIC_API_URL` misconfigured
- **Solution**: Set correct backend URL in frontend `.env.local`

## API Changes for Developers

### Old Way (Deprecated)
```javascript
// ❌ Don't do this - exposes API key
fetch('/api/admin/config', {
  headers: {
    'X-Admin-Key': 'jira-admin-key-2024'
  }
})
```

### New Way (Secure)
```javascript
// ✅ Use the admin API helper
import { adminFetch } from '@/lib/admin-api'

// Automatically handles authentication
const response = await adminFetch('/api/admin/config')
```

### Authentication Check
```javascript
import { checkAdminAuth } from '@/lib/admin-api'

// Check if user is authenticated
const isAuthenticated = await checkAdminAuth()
if (!isAuthenticated) {
  router.push('/admin/login')
}
```

## Session Management

### Session Duration
- Default: 24 hours
- Configurable in `/frontend/app/api/admin/auth/route.ts`

### Logout
- Tokens are rotated on each login and stored server-side
- Logout endpoint revokes the current session token immediately

### Multiple Users
- Current: Single admin key shared
- Future: Individual user accounts planned

## Rollback Plan

If you need to temporarily disable authentication (not recommended):

1. **Disable Middleware** (frontend/middleware.ts):
```typescript
export function middleware(request: NextRequest) {
  // TEMPORARY - Remove in production
  return NextResponse.next()
}
```

2. **Use Direct API Calls** (not recommended):
- Revert to old fetch calls with API key
- This will expose the key again

⚠️ **Warning**: Only use rollback in development. Never disable authentication in production.

## Future Enhancements

Planned improvements for the authentication system:

1. **User Management**
   - Multiple admin accounts
   - Role-based access control (RBAC)
   - User invitation system

2. **Enhanced Security**
   - Two-factor authentication (2FA)
   - API key rotation reminders
   - Audit logging for admin actions

3. **Better UX**
   - "Remember me" option
   - Logout button in UI
   - Session timeout warnings

## Support

If you encounter issues with the migration:

1. Check this guide first
2. Review error messages in browser console
3. Check backend logs: `docker-compose logs backend`
4. Check frontend logs: `docker-compose logs frontend`
5. Open an issue on GitHub with details

## Summary

The new authentication system significantly improves security by:
- Removing hard-coded credentials from frontend code
- Implementing proper session management
- Using secure HTTP-only cookies
- Proxying admin requests through server-side routes

While this is a breaking change, the security benefits far outweigh the one-time migration effort.