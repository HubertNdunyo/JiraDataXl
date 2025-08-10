import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { validateSession, getSessionStats, clearAllSessions } from '@/lib/session'
import { loginRateLimiter } from '@/lib/rateLimiter'
import { logger } from '@/lib/logger'

// GET /api/admin/sessions - Get session statistics
export async function GET(request: NextRequest) {
  // Check if user is authenticated as admin
  const cookieStore = cookies()
  const sessionToken = cookieStore.get('admin-session')?.value
  
  if (!sessionToken || !validateSession(sessionToken)) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    )
  }
  
  try {
    const sessionStats = getSessionStats()
    const rateLimitStatus = loginRateLimiter.getStatus()
    
    const stats = {
      sessions: sessionStats,
      rateLimit: rateLimitStatus,
      timestamp: new Date().toISOString()
    }
    
    logger.info('Session stats requested', stats)
    
    return NextResponse.json(stats)
  } catch (error) {
    logger.error('Failed to get session stats', error)
    return NextResponse.json(
      { error: 'Failed to retrieve session statistics' },
      { status: 500 }
    )
  }
}

// DELETE /api/admin/sessions - Clear all sessions (emergency logout all users)
export async function DELETE(request: NextRequest) {
  // Check if user is authenticated as admin
  const cookieStore = cookies()
  const sessionToken = cookieStore.get('admin-session')?.value
  
  if (!sessionToken || !validateSession(sessionToken)) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    )
  }
  
  try {
    const stats = getSessionStats()
    clearAllSessions()
    
    logger.securityAlert('All sessions cleared by admin', {
      clearedSessions: stats.total
    })
    
    // Note: This will also invalidate the current admin's session
    // They will need to log in again
    const response = NextResponse.json({
      success: true,
      message: `Cleared ${stats.total} sessions`,
      clearedCount: stats.total
    })
    
    // Clear the admin's cookie as well
    response.cookies.delete('admin-session')
    
    return response
  } catch (error) {
    logger.error('Failed to clear sessions', error)
    return NextResponse.json(
      { error: 'Failed to clear sessions' },
      { status: 500 }
    )
  }
}