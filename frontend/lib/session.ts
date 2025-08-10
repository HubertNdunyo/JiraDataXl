import crypto from 'crypto'

// Session configuration
const SESSION_DURATION = 24 * 60 * 60 * 1000 // 24 hours in milliseconds
const CLEANUP_INTERVAL = 60 * 60 * 1000 // Clean up every hour

// Enforce SESSION_SECRET in production
const SESSION_SECRET = process.env.SESSION_SECRET || (() => {
  if (process.env.NODE_ENV === 'production') {
    throw new Error('SESSION_SECRET environment variable is required in production')
  }
  console.warn('⚠️  Using insecure default SESSION_SECRET - only for development!')
  return 'dev-session-secret-change-in-production'
})()

interface SessionData {
  createdAt: number
  lastActivity: number
  ipAddress?: string
  userAgent?: string
  loginAttempts?: number
}

const sessions = new Map<string, SessionData>()

// Automatic cleanup of expired sessions
if (typeof setInterval !== 'undefined') {
  setInterval(() => {
    const now = Date.now()
    let cleaned = 0
    for (const [id, data] of sessions.entries()) {
      if (now - data.createdAt > SESSION_DURATION) {
        sessions.delete(id)
        cleaned++
      }
    }
    if (cleaned > 0) {
      console.log(`[Session Cleanup] Removed ${cleaned} expired sessions`)
    }
  }, CLEANUP_INTERVAL)
}

function base64url(input: Buffer | string): string {
  return Buffer.from(input)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
}

function base64urlDecode(input: string): Buffer {
  input = input.replace(/-/g, '+').replace(/_/g, '/')
  const pad = input.length % 4
  if (pad) {
    input += '='.repeat(4 - pad)
  }
  return Buffer.from(input, 'base64')
}

function sign(payload: object): string {
  const header = base64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = base64url(JSON.stringify(payload))
  const data = `${header}.${body}`
  const signature = base64url(
    crypto.createHmac('sha256', SESSION_SECRET).update(data).digest()
  )
  return `${data}.${signature}`
}

function verify(token: string): any {
  const parts = token.split('.')
  if (parts.length !== 3) {
    throw new Error('Invalid token')
  }
  const [headerB64, bodyB64, signature] = parts
  const data = `${headerB64}.${bodyB64}`
  const expectedSig = base64url(
    crypto.createHmac('sha256', SESSION_SECRET).update(data).digest()
  )
  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSig))) {
    throw new Error('Invalid signature')
  }
  const payload = JSON.parse(base64urlDecode(bodyB64).toString())
  if (payload.exp && Date.now() >= payload.exp * 1000) {
    throw new Error('Token expired')
  }
  return payload
}

export function createSession(metadata?: { ipAddress?: string; userAgent?: string }): string {
  const sessionId = crypto.randomBytes(16).toString('hex')
  const now = Date.now()
  
  sessions.set(sessionId, {
    createdAt: now,
    lastActivity: now,
    ipAddress: metadata?.ipAddress,
    userAgent: metadata?.userAgent,
    loginAttempts: 1
  })
  
  const token = sign({ 
    sessionId, 
    exp: Math.floor(Date.now() / 1000) + (SESSION_DURATION / 1000)
  })
  
  return token
}

export function validateSession(token: string): boolean {
  try {
    const payload = verify(token) as { sessionId: string }
    const session = sessions.get(payload.sessionId)
    
    if (!session) {
      console.warn(`[Session] Validation failed: session not found for ID ${payload.sessionId}`)
      return false
    }
    
    // Update last activity
    session.lastActivity = Date.now()
    
    return true
  } catch (error) {
    console.error('[Session] Validation error:', error instanceof Error ? error.message : 'Unknown error')
    return false
  }
}

export function revokeSession(token: string): void {
  try {
    const payload = verify(token) as { sessionId: string }
    const deleted = sessions.delete(payload.sessionId)
    if (deleted) {
      console.log(`[Session] Revoked session ${payload.sessionId}`)
    }
  } catch (error) {
    console.warn('[Session] Failed to revoke session:', error instanceof Error ? error.message : 'Invalid token')
  }
}

// Helper functions for session management
export function getSessionCount(): number {
  return sessions.size
}

export function getSessionStats(): { total: number; active: number; expired: number } {
  const now = Date.now()
  let active = 0
  let expired = 0
  
  for (const [, data] of sessions.entries()) {
    if (now - data.createdAt > SESSION_DURATION) {
      expired++
    } else {
      active++
    }
  }
  
  return { total: sessions.size, active, expired }
}

export function clearAllSessions(): void {
  const count = sessions.size
  sessions.clear()
  console.log(`[Session] Cleared all ${count} sessions`)
}
