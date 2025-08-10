import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { createSession, validateSession, revokeSession } from '@/lib/session'
import { logger } from '@/lib/logger'
import { loginRateLimiter } from '@/lib/rateLimiter'

// Admin authentication endpoint
// This should be the ONLY place that knows the actual admin API key

const ADMIN_API_KEY = process.env.ADMIN_API_KEY || ''

// Helper to get client IP
function getClientIp(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for')
  const ip = forwarded ? forwarded.split(',')[0].trim() : 
             request.headers.get('x-real-ip') || 
             'unknown'
  return ip
}

export async function POST(request: NextRequest) {
  const clientIp = getClientIp(request)
  const userAgent = request.headers.get('user-agent') || 'unknown'
  
  try {
    // Check rate limit
    if (!loginRateLimiter.checkLimit(clientIp)) {
      logger.authAttempt(false, { ip: clientIp, reason: 'Rate limited' })
      return NextResponse.json(
        { error: 'Too many login attempts. Please try again later.' },
        { status: 429 }
      )
    }
    
    const body = await request.json()
    const { password } = body

    if (!ADMIN_API_KEY) {
      logger.error('Admin authentication not configured')
      return NextResponse.json(
        { error: 'Admin authentication not configured' },
        { status: 500 }
      )
    }

    // In production, you'd want to hash and compare passwords properly
    // For now, we're comparing the provided password with the API key
    if (password === ADMIN_API_KEY) {
      // Reset rate limit on successful login
      loginRateLimiter.reset(clientIp)
      
      const cookieStore = cookies()
      const existing = cookieStore.get('admin-session')?.value
      if (existing) {
        revokeSession(existing)
      }

      const sessionToken = createSession({
        ipAddress: clientIp,
        userAgent: userAgent
      })
      
      logger.authAttempt(true, { ip: clientIp, userAgent })
      logger.sessionEvent('created')

      const response = NextResponse.json({
        success: true,
        message: 'Authentication successful'
      })

      response.cookies.set('admin-session', sessionToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 60 * 60 * 24, // 24 hours
        path: '/'
      })

      return response
    }

    logger.authAttempt(false, { ip: clientIp, reason: 'Invalid credentials' })
    return NextResponse.json(
      { error: 'Invalid credentials' },
      { status: 401 }
    )
  } catch (error) {
    logger.error('Auth error:', error)
    return NextResponse.json(
      { error: 'Authentication failed' },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  // Logout endpoint
  const clientIp = getClientIp(request)
  const cookieStore = cookies()
  const token = cookieStore.get('admin-session')?.value
  
  if (token) {
    revokeSession(token)
    logger.sessionEvent('revoked')
    logger.info('User logged out', { ip: clientIp })
  }

  const response = NextResponse.json({
    success: true,
    message: 'Logged out successfully'
  })

  response.cookies.delete('admin-session')

  return response
}

export async function GET(request: NextRequest) {
  // Check if user is authenticated
  const cookieStore = cookies()
  const sessionToken = cookieStore.get('admin-session')?.value

  if (sessionToken && validateSession(sessionToken)) {
    return NextResponse.json({
      authenticated: true
    })
  }

  return NextResponse.json({
    authenticated: false
  })
}