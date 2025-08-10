/**
 * Simple logger utility for security events and debugging
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogEntry {
  timestamp: string
  level: LogLevel
  message: string
  context?: any
}

class Logger {
  private isDevelopment = process.env.NODE_ENV !== 'production'
  
  private formatMessage(level: LogLevel, message: string, context?: any): string {
    const timestamp = new Date().toISOString()
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`
    
    if (context) {
      return `${prefix} ${message} ${JSON.stringify(context)}`
    }
    return `${prefix} ${message}`
  }
  
  debug(message: string, context?: any): void {
    if (this.isDevelopment) {
      console.debug(this.formatMessage('debug', message, context))
    }
  }
  
  info(message: string, context?: any): void {
    console.info(this.formatMessage('info', message, context))
  }
  
  warn(message: string, context?: any): void {
    console.warn(this.formatMessage('warn', message, context))
  }
  
  error(message: string, context?: any): void {
    console.error(this.formatMessage('error', message, context))
  }
  
  // Security-specific logging methods
  authAttempt(success: boolean, context?: { ip?: string; userAgent?: string; reason?: string }): void {
    const level = success ? 'info' : 'warn'
    const message = success ? 'Authentication successful' : 'Authentication failed'
    this[level](`[AUTH] ${message}`, context)
  }
  
  sessionEvent(event: 'created' | 'validated' | 'revoked' | 'expired', sessionId?: string): void {
    this.info(`[SESSION] Session ${event}`, sessionId ? { sessionId } : undefined)
  }
  
  securityAlert(message: string, context?: any): void {
    this.error(`[SECURITY] ${message}`, context)
  }
}

// Export singleton instance
export const logger = new Logger()