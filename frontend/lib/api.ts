// API configuration utility

export const getApiUrl = () => {
  // Use environment variable if available
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  
  // For security, backend only listens on localhost
  // All API calls should go through localhost, even when frontend is accessed via IP
  return 'http://localhost:8987'
}

export const apiUrl = getApiUrl()