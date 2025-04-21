# Project File Structure

```
dataappV3/
├── config/
│   └── field_mappings.json     # Field mapping configuration
├── core/
│   ├── config/
│   │   ├── app_config.py       # Application configuration and constants
│   │   └── logging_config.py   # Centralized logging configuration
│   ├── db/
│   │   ├── constants.py        # Database constants and column definitions
│   │   ├── db_audit.py        # Audit logging functionality
│   │   ├── db_core.py         # Core database operations
│   │   ├── db_issues.py       # Issue-related database operations
│   │   └── db_projects.py     # Project-related database operations
│   ├── jira/
│   │   ├── field_processor.py # Field processing and validation
│   │   ├── jira_client.py     # JIRA API client
│   │   └── jira_issues.py     # Issue fetching and processing
│   └── sync/
│       ├── status_manager.py  # Status management
│       └── sync_manager.py    # Sync process coordination
├── monitoring/
│   └── metrics.py             # System monitoring and metrics
├── utils/
│   ├── scripts/
│   │   └── maintenance/
│   │       └── clear_jira_data.py  # Database maintenance
│   └── tests/
│       ├── analyze_data_volume.py  # Data volume analysis
│       ├── check_specific_issue.py # Issue verification
│       ├── full_sync_test.py       # Full sync testing
│       └── scan_project_issues.py  # Project scanning
├── main.py                    # Main application entry point
├── setup.py                   # Database initialization
└── web_app.py                # Web interface and API endpoints
```

## Key Components

1. **Configuration (`config/`)**
   - Centralized configuration files
   - Field mappings and application settings

2. **Core (`core/`)**
   - Main application logic organized by functionality
   - Modular design with clear separation of concerns

3. **Database (`core/db/`)**
   - Centralized database operations
   - Consistent column definitions
   - Audit logging and tracking

4. **JIRA Integration (`core/jira/`)**
   - Field processing and validation
   - API client with rate limiting
   - Issue fetching and processing

5. **Sync Management (`core/sync/`)**
   - Sync process coordination
   - Status tracking and management

6. **Monitoring (`monitoring/`)**
   - System metrics collection
   - Performance monitoring

7. **Utilities (`utils/`)**
   - Maintenance scripts
   - Testing utilities
   - Analysis tools