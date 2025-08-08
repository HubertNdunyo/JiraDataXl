#!/bin/bash
# Frontend startup script with custom port

echo "Starting JIRA Sync Dashboard Frontend..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start Next.js on custom port and all interfaces
PORT=5648 npm run dev -- -H 0.0.0.0