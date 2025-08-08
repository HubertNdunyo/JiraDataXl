# JIRA Sync Dashboard

A modern web application for monitoring and managing JIRA synchronization operations with a Next.js frontend and FastAPI backend.

## Features

- **Real-time Dashboard**: Monitor sync status, progress, and system health
- **Sync Control**: Start/stop synchronization operations manually
- **Configuration**: Set sync intervals and enable/disable automatic sync
- **History View**: Browse past synchronization operations
- **Modern UI**: Built with Next.js, TypeScript, Tailwind CSS, and shadcn/ui

## Tech Stack

### Frontend
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Lucide React icons

### Backend
- FastAPI (Python)
- PostgreSQL database
- Real JIRA integration
- High-performance sync engine

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- PostgreSQL database
- `.env` file with required environment variables

## Quick Start

### Backend Setup

```bash
cd backend
./run.sh
```

The backend will be available at http://localhost:8987

### Frontend Setup

```bash
cd frontend
./run.sh
```

The frontend will be available at http://localhost:5648

## Remote Access

The application is configured for network access:
- Frontend: `http://YOUR_IP:5648`
- Backend API: `http://YOUR_IP:8987`
- API Docs: `http://YOUR_IP:8987/docs`

## Project Structure

```
jiraData/
├── frontend/               # Next.js frontend application
├── backend/                # FastAPI backend application
├── core/                   # Core business logic
├── config/                 # Configuration files
├── database/               # Database scripts
├── docs/                   # Documentation
├── tests/                  # Test files
├── samples/                # Sample data
├── analysis/               # Analysis outputs
├── logs/                   # Application logs
├── utils/                  # Utility scripts
├── archive/                # Legacy Flask application
└── FUTURE_FEATURES.md      # Roadmap
```

## Documentation

See the `docs/` directory for detailed documentation:
- [Setup and Configuration](docs/SETUP_AND_CONFIGURATION.md)
- [Technical Architecture](docs/TECHNICAL.md)
- [Field Guide](docs/FIELD_GUIDE.md)
- [Security Recommendations](docs/SECURITY_FIXES.md)

## License

This project is part of the DataAppV3 system.