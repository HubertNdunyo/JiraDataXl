import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Allow access to login page and auth API
  if (pathname === '/admin/login' || pathname === '/api/admin/auth') {
    return NextResponse.next()
  }
  
  // Check for admin session cookie
  const adminSession = request.cookies.get('admin-session')
  
  // Protect admin routes and admin API routes (except the proxy which handles its own auth)
  if (pathname.startsWith('/admin') || 
      (pathname.startsWith('/api/') && 
       (pathname.startsWith('/api/scheduler') || pathname.startsWith('/api/admin')))) {
    
    if (!adminSession) {
      // For API routes, return 401
      if (pathname.startsWith('/api/')) {
        return NextResponse.json(
          { error: 'Unauthorized - Please login' },
          { status: 401 }
        )
      }
      
      // For page routes, redirect to login
      const loginUrl = new URL('/admin/login', request.url)
      loginUrl.searchParams.set('from', pathname)
      return NextResponse.redirect(loginUrl)
    }
    
    // The actual session validation happens in the API route handlers
    // Middleware just checks for cookie presence to avoid edge runtime limitations
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: ['/admin/:path*', '/api/admin/:path*', '/api/scheduler/:path*']
}