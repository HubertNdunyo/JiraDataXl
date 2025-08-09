import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { createSession, validateSession, revokeSession } from '@/lib/session'

// Admin authentication endpoint
// This should be the ONLY place that knows the actual admin API key

const ADMIN_API_KEY = process.env.ADMIN_API_KEY || ''

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { password } = body

    if (!ADMIN_API_KEY) {
      return NextResponse.json(
        { error: 'Admin authentication not configured' },
        { status: 500 }
      )
    }

    // In production, you'd want to hash and compare passwords properly
    // For now, we're comparing the provided password with the API key
    if (password === ADMIN_API_KEY) {
      const cookieStore = cookies()
      const existing = cookieStore.get('admin-session')?.value
      if (existing) {
        revokeSession(existing)
      }

      const sessionToken = createSession()

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

    return NextResponse.json(
      { error: 'Invalid credentials' },
      { status: 401 }
    )
  } catch (error) {
    console.error('Auth error:', error)
    return NextResponse.json(
      { error: 'Authentication failed' },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  // Logout endpoint
  const cookieStore = cookies()
  const token = cookieStore.get('admin-session')?.value
  if (token) {
    revokeSession(token)
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