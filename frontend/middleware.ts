import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Allow access to login page
  if (pathname === '/admin/login') {
    return NextResponse.next()
  }
  
  // Check for admin session cookie
  const adminSession = request.cookies.get('admin-session')
  
  // Protect admin routes
  if (pathname.startsWith('/admin')) {
    if (!adminSession) {
      // Redirect to login page if not authenticated
      const loginUrl = new URL('/admin/login', request.url)
      loginUrl.searchParams.set('from', pathname)
      return NextResponse.redirect(loginUrl)
    }
    
    // TODO: In production, validate the session token against a store
    // For now, we just check if the cookie exists
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: '/admin/:path*'
}