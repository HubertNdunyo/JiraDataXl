// Admin API helper functions
// These functions proxy admin requests through our API routes
// which handle authentication server-side

export async function adminFetch(path: string, options: RequestInit = {}) {
  // Use the proxy endpoint instead of direct backend calls
  const proxyUrl = `/api/admin/proxy?path=${encodeURIComponent(path)}`
  
  const response = await fetch(proxyUrl, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (response.status === 401) {
    // Redirect to login if unauthorized
    window.location.href = '/admin/login'
    throw new Error('Unauthorized')
  }

  return response
}

export async function checkAdminAuth(): Promise<boolean> {
  try {
    const response = await fetch('/api/admin/auth')
    const data = await response.json()
    return data.authenticated === true
  } catch {
    return false
  }
}

export async function adminLogin(password: string): Promise<boolean> {
  try {
    const response = await fetch('/api/admin/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ password }),
    })

    return response.ok
  } catch {
    return false
  }
}

export async function adminLogout(): Promise<void> {
  try {
    await fetch('/api/admin/auth', {
      method: 'DELETE',
    })
  } catch {
    // Ignore errors on logout
  }
}