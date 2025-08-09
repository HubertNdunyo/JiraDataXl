import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import crypto from 'crypto'

// Admin authentication endpoint
// This should be the ONLY place that knows the actual admin API key

const ADMIN_API_KEY = process.env.ADMIN_API_KEY || ''
const SESSION_SECRET = process.env.SESSION_SECRET || 'dev-session-secret'

// Simple session token generation
function generateSessionToken(): string {
  return crypto.randomBytes(32).toString('hex')
}

// Hash password for comparison
function hashPassword(password: string): string {
  return crypto.createHash('sha256').update(password).digest('hex')
}

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
      // Generate session token
      const sessionToken = generateSessionToken()
      
      // Store session (in production, use a database or Redis)
      // For now, we'll use a cookie
      const response = NextResponse.json({ 
        success: true,
        message: 'Authentication successful'
      })

      // Set secure HTTP-only cookie
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
  const sessionToken = cookieStore.get('admin-session')

  if (sessionToken) {
    // In production, validate the session token against a store
    return NextResponse.json({ 
      authenticated: true 
    })
  }

  return NextResponse.json({ 
    authenticated: false 
  })
}