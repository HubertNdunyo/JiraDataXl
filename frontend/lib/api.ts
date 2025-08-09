// API configuration utility

export const getApiUrl = () => {
  // In browser, use relative URLs to go through Next.js proxy
  if (typeof window !== 'undefined') {
    return ''  // Empty string means use relative URLs
  }
  
  // Server-side: use backend container name in Docker
  if (process.env.BACKEND_URL) {
    return process.env.BACKEND_URL
  }
  
  // Fallback
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8987'
}

export const apiUrl = getApiUrl()