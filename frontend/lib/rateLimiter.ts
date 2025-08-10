/**
 * Rate limiter for preventing brute force attacks
 */

import { logger } from './logger'

interface RateLimitEntry {
  count: number
  resetAt: number
  blocked: boolean
}

class RateLimiter {
  private attempts = new Map<string, RateLimitEntry>()
  private readonly maxAttempts: number
  private readonly windowMs: number
  private readonly blockDurationMs: number
  
  constructor(options?: {
    maxAttempts?: number
    windowMs?: number
    blockDurationMs?: number
  }) {
    this.maxAttempts = options?.maxAttempts || 5
    this.windowMs = options?.windowMs || 15 * 60 * 1000 // 15 minutes
    this.blockDurationMs = options?.blockDurationMs || 60 * 60 * 1000 // 1 hour block
    
    // Clean up old entries every 5 minutes
    if (typeof setInterval !== 'undefined') {
      setInterval(() => this.cleanup(), 5 * 60 * 1000)
    }
  }
  
  /**
   * Check if an identifier (IP address) is rate limited
   * @returns true if the request should be allowed, false if blocked
   */
  checkLimit(identifier: string): boolean {
    const now = Date.now()
    const entry = this.attempts.get(identifier)
    
    // No previous attempts
    if (!entry) {
      this.attempts.set(identifier, {
        count: 1,
        resetAt: now + this.windowMs,
        blocked: false
      })
      return true
    }
    
    // Check if blocked
    if (entry.blocked && now < entry.resetAt) {
      logger.securityAlert('Rate limit: Blocked request', { 
        identifier, 
        remainingBlockTime: entry.resetAt - now 
      })
      return false
    }
    
    // Reset if window expired
    if (now > entry.resetAt) {
      entry.count = 1
      entry.resetAt = now + this.windowMs
      entry.blocked = false
      return true
    }
    
    // Increment attempt count
    entry.count++
    
    // Check if should be blocked
    if (entry.count > this.maxAttempts) {
      entry.blocked = true
      entry.resetAt = now + this.blockDurationMs
      logger.securityAlert('Rate limit: Blocking identifier due to too many attempts', {
        identifier,
        attempts: entry.count,
        blockDuration: this.blockDurationMs
      })
      return false
    }
    
    // Log warning if getting close to limit
    if (entry.count === this.maxAttempts - 1) {
      logger.warn('Rate limit: Approaching limit', {
        identifier,
        attempts: entry.count,
        maxAttempts: this.maxAttempts
      })
    }
    
    return true
  }
  
  /**
   * Reset limits for a specific identifier (e.g., after successful login)
   */
  reset(identifier: string): void {
    this.attempts.delete(identifier)
    logger.debug('Rate limit: Reset for identifier', { identifier })
  }
  
  /**
   * Clean up expired entries to prevent memory leak
   */
  private cleanup(): void {
    const now = Date.now()
    let cleaned = 0
    
    for (const [identifier, entry] of this.attempts.entries()) {
      if (now > entry.resetAt) {
        this.attempts.delete(identifier)
        cleaned++
      }
    }
    
    if (cleaned > 0) {
      logger.debug('Rate limit: Cleaned up expired entries', { count: cleaned })
    }
  }
  
  /**
   * Get current status for monitoring
   */
  getStatus(): { totalEntries: number; blockedEntries: number } {
    let blockedEntries = 0
    const now = Date.now()
    
    for (const entry of this.attempts.values()) {
      if (entry.blocked && now < entry.resetAt) {
        blockedEntries++
      }
    }
    
    return {
      totalEntries: this.attempts.size,
      blockedEntries
    }
  }
}

// Export singleton instance for login attempts
export const loginRateLimiter = new RateLimiter({
  maxAttempts: 5,
  windowMs: 15 * 60 * 1000, // 15 minutes
  blockDurationMs: 60 * 60 * 1000 // 1 hour
})

// Export class for custom rate limiters
export { RateLimiter }