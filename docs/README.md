# JIRA Sync Dashboard Documentation

Welcome to the comprehensive documentation for the JIRA Sync Dashboard project. This documentation is organized into categories for easy navigation.

## 📚 Documentation Structure

### 🏗️ [Architecture](./architecture/)
Technical architecture and system design documentation.

- **[SYNC_ARCHITECTURE.md](./architecture/SYNC_ARCHITECTURE.md)** - Complete sync architecture explanation including field mapping design, database strategy, and data flow
- **[FIELD_MAPPING_MIGRATION_PLAN.md](./architecture/FIELD_MAPPING_MIGRATION_PLAN.md)** - Detailed migration plan from hardcoded to dynamic field mapping system

### 📖 [Guides](./guides/)
How-to guides and configuration documentation.

- **[DYNAMIC_FIELD_SYNC_GUIDE.md](./guides/DYNAMIC_FIELD_SYNC_GUIDE.md)** - Complete guide to the dynamic field sync system (current implementation)
- **[FIELD_MAPPING_GUIDE.md](./guides/FIELD_MAPPING_GUIDE.md)** - How to configure and manage field mappings
- **[CORE_FIELDS_README.md](./guides/CORE_FIELDS_README.md)** - Documentation of all 25 core business fields
- **[ADDING_NEW_FIELDS_GUIDE.md](./guides/ADDING_NEW_FIELDS_GUIDE.md)** - Step-by-step guide for adding new fields to sync
- **[AUTOMATED_SYNC_GUIDE.md](./guides/AUTOMATED_SYNC_GUIDE.md)** - Configure and manage automated synchronization
- **[AI_AGENT_GUIDE.md](./guides/AI_AGENT_GUIDE.md)** - AI agent integration and usage guide

### 🐳 [Deployment](./deployment/)
Docker and deployment related documentation.

- **[DOCKER_README.md](./deployment/DOCKER_README.md)** - Docker setup and deployment guide
- **[DOCKER_IMPLEMENTATION_REPORT.md](./deployment/DOCKER_IMPLEMENTATION_REPORT.md)** - Detailed Docker implementation report with all configurations

### 🧪 [Testing](./testing/)
Testing guides and test script documentation.

- **[INUA_TESTING_README.md](./testing/INUA_TESTING_README.md)** - INUA interface testing documentation
- **[TEST_SCRIPTS_README.md](./testing/TEST_SCRIPTS_README.md)** - Guide to all test scripts and utilities

### 📝 [Changelog](./changelog/)
Project history and version documentation.

- **[CHANGELOG.md](./changelog/CHANGELOG.md)** - Complete project changelog with all updates and improvements

### 🔌 [Integrations](./integrations/)
External system integrations and workflows.

- **[JIRA_INTEGRATION_GUIDE.md](./integrations/JIRA_INTEGRATION_GUIDE.md)** - JIRA API integration details
- **[INUA_WORKFLOW_GUIDE.md](./integrations/INUA_WORKFLOW_GUIDE.md)** - INUA workflow integration

### ⚙️ [Operations](./operations/)
Operational procedures and system reference.

- **[OPERATIONAL_GUIDE.md](./operations/OPERATIONAL_GUIDE.md)** - Day-to-day operational procedures
- **[SYSTEM_REFERENCE.md](./operations/SYSTEM_REFERENCE.md)** - Complete system reference and specifications

### 🎯 [Features](./features/)
Feature implementations and future roadmap.

- **[ADMIN_INTERFACE_IMPLEMENTATION.md](./features/ADMIN_INTERFACE_IMPLEMENTATION.md)** - Admin interface implementation details
- **[SYNC_HISTORY_IMPLEMENTATION.md](./features/SYNC_HISTORY_IMPLEMENTATION.md)** - Sync history feature documentation
- **[FEATURE_TEST_RESULTS.md](./features/FEATURE_TEST_RESULTS.md)** - Feature testing results and reports
- **[FUTURE_FEATURES.md](./features/FUTURE_FEATURES.md)** - Planned features and development roadmap

---

## Quick Links

### For Developers
- [System Architecture](./architecture/SYNC_ARCHITECTURE.md) - Start here to understand the system
- [Dynamic Field Sync Guide](./guides/DYNAMIC_FIELD_SYNC_GUIDE.md) - Current implementation details
- [Docker Setup](./deployment/DOCKER_README.md) - Local development setup

### For System Administrators
- [Field Mapping Configuration](./guides/FIELD_MAPPING_GUIDE.md) - Configure field mappings
- [Core Fields Reference](./guides/CORE_FIELDS_README.md) - Available business fields
- [Deployment Guide](./deployment/DOCKER_README.md) - Production deployment

### For Testing
- [Test Scripts Guide](./testing/TEST_SCRIPTS_README.md) - Available test utilities
- [INUA Testing](./testing/INUA_TESTING_README.md) - Integration testing

---

## Key Features Documentation

### 1. Dynamic Field Mapping System
The system now uses a fully dynamic, database-driven field mapping system. No more hardcoded field IDs!
- **Learn More**: [Dynamic Field Sync Guide](./guides/DYNAMIC_FIELD_SYNC_GUIDE.md)

### 2. Field Mapping Dashboard
Web-based UI for managing field mappings without code changes.
- **Learn More**: [Field Mapping Guide](./guides/FIELD_MAPPING_GUIDE.md)

### 3. Docker Deployment
Complete containerized deployment with PostgreSQL, Redis, Backend, and Frontend.
- **Learn More**: [Docker README](./deployment/DOCKER_README.md)

### 4. Clear Data Feature
Ability to clear synced data for testing field mappings.
- **Location**: Main dashboard → Sync Control → Clear Data button

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- JIRA API credentials for two instances
- PostgreSQL (included in Docker setup)
- Redis (included in Docker setup)

### Quick Start
1. Clone the repository
2. Set up environment variables (see `.env.example`)
3. Run Docker Compose: `docker-compose -f docker-compose.dev.yml up`
4. Access the dashboard at http://localhost:5648
5. Configure field mappings via the admin panel

### Key URLs
- **Main Dashboard**: http://localhost:5648/
- **Field Mappings**: http://localhost:5648/admin/field-mappings
- **Sync History**: http://localhost:5648/history
- **API Documentation**: http://localhost:8987/docs (FastAPI)

---

## Project Structure

```
dataApp/
├── docs/                    # All documentation
│   ├── architecture/       # System design docs
│   ├── guides/            # How-to guides
│   ├── deployment/        # Docker & deployment
│   ├── testing/           # Test documentation
│   └── changelog/         # Version history
├── backend/               # FastAPI backend
│   ├── api/              # API endpoints
│   ├── core/             # Core business logic
│   ├── migrations/       # Database migrations
│   └── scripts/          # Utility scripts
├── frontend/              # Next.js frontend
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   └── lib/              # Utilities
├── docker/               # Docker configurations
└── jira_utilities/       # JIRA-specific utilities
```

---

## Recent Updates (January 2025)

### Major Changes
1. **Dynamic Field Sync System** - Complete removal of hardcoded field mappings
2. **Database-Driven Configuration** - All field mappings stored in PostgreSQL
3. **Clear Data Feature** - New button to clear synced data for testing
4. **Improved Documentation** - Consolidated and organized documentation

### Latest Features
- ✅ Dynamic field extraction from database configuration
- ✅ Field Mapping Wizard UI
- ✅ Clear table functionality with confirmation dialog
- ✅ Support for different field IDs per JIRA instance
- ✅ Automatic type conversion and validation

---

## Support and Contribution

### Reporting Issues
Please report issues with detailed information including:
- Error messages
- Steps to reproduce
- Expected vs actual behavior
- Environment details

### Contributing
1. Review the [Architecture Documentation](./architecture/SYNC_ARCHITECTURE.md)
2. Follow the existing code patterns
3. Add tests for new features
4. Update relevant documentation

---

## License and Credits

This project synchronizes JIRA data between instances using a configurable field mapping system.

**Last Updated**: January 9, 2025
**Version**: 2.0.0 (Dynamic Field Sync)