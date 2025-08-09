import { NextResponse } from 'next/server';

export async function GET() {
  // Basic health check
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
  };

  // Check if we can reach the backend API
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8987';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`${backendUrl}/health`, {
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    health['backend'] = {
      status: response.ok ? 'connected' : 'error',
      statusCode: response.status,
    };
  } catch (error) {
    health['backend'] = {
      status: 'disconnected',
      error: error.message,
    };
  }

  return NextResponse.json(health, { status: 200 });
}