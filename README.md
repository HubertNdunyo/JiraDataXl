# JIRA Sync Dashboard

A high-performance web application for monitoring and managing JIRA synchronization operations with a Next.js frontend and FastAPI backend.

## 📚 Documentation

**All documentation has been organized in the [`docs/`](./docs/) folder.**

- 📖 **[Documentation Index](./docs/README.md)** - Start here for comprehensive documentation
- 🏗️ **[Architecture](./docs/architecture/)** - System design and technical architecture
- 📝 **[Guides](./docs/guides/)** - How-to guides and configuration instructions
- 🐳 **[Deployment](./docs/deployment/)** - Docker and deployment documentation
- 🧪 **[Testing](./docs/testing/)** - Testing guides and utilities

## 🚀 Features

- **Real-time Dashboard**: Monitor sync status, progress, and system health
- **High Performance**: 500 issues/second throughput, syncing 45,000+ issues in ~90 seconds
- **Sync Control**: Start/stop synchronization operations manually or scheduled
- **Configuration Management**: Set sync intervals and enable/disable automatic sync
- **History & Analytics**: Browse past synchronization operations with detailed metrics
- **Advanced Field Mapping System**:
  - Automatic field discovery from JIRA instances (530+ fields supported)
  - Interactive mapping wizard with guided and manual modes
  - Real-time field search with autocomplete
  - Automatic database schema synchronization
  - Visual field type indicators and validation
- **Modern UI**: Built with Next.js 14, TypeScript, Tailwind CSS, and shadcn/ui
- **Docker Support**: Fully containerized with development and production configurations

## Tech Stack

### Frontend
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Lucide React icons

### Backend
- FastAPI (Python 3.8+)
- PostgreSQL database with Alembic migrations
- Redis caching for performance optimization
- Real JIRA API integration
- High-performance sync engine (272 issues/sec)
- Comprehensive error handling and logging

## ⚠️ BREAKING CHANGES (January 2025)

### Enhanced Security: Admin Authentication Required
Admin pages now implement secure server-side authentication. All sensitive API keys are handled server-side only.

#### Security Improvements:
- ✅ **No hardcoded API keys in frontend code** - All removed
- ✅ **Server-side authentication** - API keys stored only in environment variables
- ✅ **Secure proxy pattern** - Admin requests proxied through `/api/admin/proxy`
- ✅ **Session-based access** - HTTP-only cookies for admin sessions
- ✅ **Automatic redirects** - Unauthorized users redirected to login

#### Setup:
1. **Configure Environment Variables**:
   ```bash
   # Backend (.env)
   ADMIN_API_KEY=secure-admin-key-2024
   
   # Frontend (.env.local)
   BACKEND_URL=http://backend:8987  # For Docker internal network
   ADMIN_API_KEY=secure-admin-key-2024  # Must match backend
   SESSION_SECRET=dev-session-secret-change-in-production-32chars
   ```

2. **Access Admin Panel**:
   - Navigate to `/admin/login`
   - Enter the admin password
   - Session persists across page refreshes

3. **Security Architecture**:
   - Frontend uses `adminFetch()` helper for all admin API calls
   - Proxy endpoint validates session and adds API key server-side
   - No sensitive credentials exposed to client-side code

See [Migration Guide](./docs/guides/ADMIN_AUTH_MIGRATION.md) for details.

## Prerequisites

- Docker and Docker Compose (recommended)
- OR:
  - Node.js 18+ and npm
  - Python 3.8+
  - PostgreSQL database
  - Redis server
- `.env` file with required environment variables (see `.env.example`)

## Quick Start

### 🐳 Docker Setup (Recommended)

#### Development Environment
```bash
# Start all services with hot-reload
docker-compose -f docker-compose.dev.yml up

# Or use the install script
./install-docker.sh
```

#### Production Environment
```bash
# Start optimized production containers
docker-compose -f docker-compose.prod.yml up -d
```

Services:
- Frontend: http://localhost:5648
- Backend API: http://localhost:8987
- API Documentation: http://localhost:8987/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Manual Setup

#### Backend
```bash
cd backend
./run.sh
```

#### Frontend
```bash
cd frontend
./run.sh
```

## Remote Access

The application is configured for network access:
- Frontend: `http://YOUR_IP:5648`
- Backend API: `http://YOUR_IP:8987`
- API Docs: `http://YOUR_IP:8987/docs`

## Project Structure

```
dataApp/
├── frontend/               # Next.js 14 frontend application
│   ├── app/               # App router pages
│   ├── components/        # UI components
│   └── lib/              # Utilities and API client
├── backend/               # FastAPI backend application
│   ├── api/              # API endpoints
│   ├── core/             # Business logic
│   │   ├── db/          # Database operations
│   │   ├── cache/       # Redis caching
│   │   └── sync/        # Sync engine
│   ├── alembic/         # Database migrations
│   └── main.py          # Application entry point
├── docker/               # Docker configurations
├── jira_utilities/       # JIRA utility modules (optional)
├── docs/                # Documentation
├── logs/                # Application logs
├── archive/             # Legacy Flask application
├── docker-compose.*.yml # Docker Compose configs
├── CHANGELOG.md         # Version history
└── FUTURE_FEATURES.md   # Roadmap
```

## 📚 Documentation

See the `docs/` directory for detailed documentation:
- [Setup and Configuration](docs/SETUP_AND_CONFIGURATION.md)
- [Technical Architecture](docs/TECHNICAL.md)
- [Field Guide](docs/FIELD_GUIDE.md)
- [Security Recommendations](docs/SECURITY_FIXES.md)
- [Docker Implementation](DOCKER_README.md)
- [Changelog](CHANGELOG.md)

## ⚡ Performance

- **Sync Speed**: 500 issues/second throughput
- **Full Sync Time**: ~90 seconds for 45,000+ issues
- **Parallel Processing**: 10 concurrent workers across 97 projects
- **Batch Size**: 400 issues per API request (optimized)
- **Cache Performance**: Redis caching with smart TTL
- **Response Times**: Sub-millisecond for cached operations
- **Database**: Optimized with indexes on key columns (issue_key, summary, status, etc.)
- **Performance Tuning**: Admin UI for real-time performance configuration
- **Monitoring**: Built-in performance metrics and sync statistics

## 🔄 Recent Updates (January 2025)

### Security & Architecture Improvements
- **Admin Authentication**: Removed hard-coded API keys, implemented secure login
- **Dynamic JIRA Instances**: Support for unlimited JIRA instances (not just 2)
- **Database Configuration**: All config now in PostgreSQL (no JSON files)
- **Repository Pattern**: Clean separation of data access and business logic
- **Python Package Structure**: Proper imports without sys.path hacks
- **Next.js Layouts**: Proper nested layouts implementation

See [Changelog](./docs/changelog/CHANGELOG.md) for complete details.

## 🔄 Previous Updates (2025-08-08)

### Field Mapping System
- ✅ Implemented automatic field discovery (530+ fields from both instances)
- ✅ Created interactive field mapping wizard
- ✅ Fixed environment variable configuration for JIRA credentials
- ✅ Added unique constraints for field caching
- ✅ Fixed infinite loop issues in field search component
- ✅ Implemented automatic database schema synchronization

### Infrastructure & Performance
- ✅ Fixed all database schema mismatches
- ✅ Added performance metrics tracking
- ✅ Implemented Alembic migrations
- ✅ Added frontend health checks
- ✅ Organized project structure
- ✅ Full Docker containerization

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## 🛠️ Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL is running on port 5432
   - Check database credentials in `.env`
   - Run migrations: `cd backend && alembic upgrade head`

2. **Redis Connection Errors**
   - Ensure Redis is running on port 6379
   - Check Redis configuration in `.env`

3. **JIRA API Errors**
   - Verify JIRA credentials and instance URLs
   - Check API rate limits
   - Ensure network connectivity to JIRA instances

4. **Docker Issues**
   - Ensure Docker daemon is running
   - Check port availability (5648, 8987, 5432, 6379)
   - Review container logs: `docker-compose logs [service]`

## 🚀 Next Steps

- [ ] Add comprehensive test suite
- [ ] Implement CI/CD pipeline
- [ ] Add monitoring stack (Prometheus + Grafana)
- [ ] Enhance error handling
- [ ] Add user authentication
- [ ] Implement webhook support

## License

This project is part of the DataAppV3 system.