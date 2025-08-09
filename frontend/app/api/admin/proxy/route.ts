import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

// Use BACKEND_URL for server-side requests (Docker internal network)
// Falls back to NEXT_PUBLIC_API_URL for local development
const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8987'
const ADMIN_API_KEY = process.env.ADMIN_API_KEY || ''

// Proxy admin requests to backend with proper authentication
export async function handleAdminRequest(
  request: NextRequest,
  method: string
) {
  try {
    // Check if user has a valid session
    const cookieStore = cookies()
    const sessionToken = cookieStore.get('admin-session')

    if (!sessionToken) {
      return NextResponse.json(
        { error: 'Unauthorized - Please login' },
        { status: 401 }
      )
    }

    if (!ADMIN_API_KEY) {
      return NextResponse.json(
        { error: 'Admin API key not configured' },
        { status: 500 }
      )
    }

    // Get the path from the URL
    const url = new URL(request.url)
    const path = url.searchParams.get('path') || ''

    // Build backend URL
    const backendUrl = `${BACKEND_URL}${path}${url.search.replace('?path=' + encodeURIComponent(path), '')}`

    // Get request body for POST/PUT requests
    let body = undefined
    if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
      try {
        body = await request.json()
      } catch {
        // No body or not JSON
      }
    }

    // Forward request to backend with admin key
    const response = await fetch(backendUrl, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Key': ADMIN_API_KEY,
      },
      body: body ? JSON.stringify(body) : undefined,
    })

    const data = await response.json()

    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Admin proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to process admin request' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  return handleAdminRequest(request, 'GET')
}

export async function POST(request: NextRequest) {
  return handleAdminRequest(request, 'POST')
}

export async function PUT(request: NextRequest) {
  return handleAdminRequest(request, 'PUT')
}

export async function PATCH(request: NextRequest) {
  return handleAdminRequest(request, 'PATCH')
}

export async function DELETE(request: NextRequest) {
  return handleAdminRequest(request, 'DELETE')
}