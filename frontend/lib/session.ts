import crypto from 'crypto'

const SESSION_SECRET = process.env.SESSION_SECRET || 'dev-session-secret'

interface SessionData {
  createdAt: number
}

const sessions = new Map<string, SessionData>()

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

export function createSession(): string {
  const sessionId = crypto.randomBytes(16).toString('hex')
  sessions.set(sessionId, { createdAt: Date.now() })
  const token = sign({ sessionId, exp: Math.floor(Date.now() / 1000) + 60 * 60 * 24 })
  return token
}

export function validateSession(token: string): boolean {
  try {
    const payload = verify(token) as { sessionId: string }
    return sessions.has(payload.sessionId)
  } catch {
    return false
  }
}

export function revokeSession(token: string): void {
  try {
    const payload = verify(token) as { sessionId: string }
    sessions.delete(payload.sessionId)
  } catch {
    // Invalid token, nothing to revoke
  }
}
