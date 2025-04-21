"""
Application configuration and constants.

This module provides a clear overview of the project's structure, component relationships,
and configuration constants used throughout the application.
"""

# Project structure documentation
PROJECT_STRUCTURE = {
    'core': {
        'app.py': 'Core application logic and component initialization',
        'config/': 'Configuration and constants',
        'db/': 'Database operations and models',
        'jira/': 'JIRA API client and field processing',
        'sync/': 'Synchronization management'
    },
    'monitoring': {
        'metrics.py': 'System monitoring and metrics collection'
    },
    'tests': {
        'test_db/': 'Database operation tests',
        'test_jira/': 'JIRA client tests',
        'test_sync/': 'Sync functionality tests'
    },
    'utils': {
        'scripts/': 'Maintenance and migration scripts',
        'tests/': 'Integration test scripts'
    }
}

# Component dependencies
COMPONENT_DEPENDENCIES = {
    'web_app.py': ['core.app', 'monitoring.metrics'],
    'main.py': ['core.app'],
    'core.jira.jira_issues': ['core.jira.field_processor'],
    'core.db.db_core': ['monitoring.metrics']
}

# Database schema documentation
DATABASE_SCHEMA = {
    'jira_issues_v2': {
        'issue_key': 'VARCHAR(255) PRIMARY KEY',
        'summary': 'TEXT',
        'status': 'VARCHAR(255)',
        'ndpu_order_number': 'VARCHAR(255)',
        'ndpu_raw_photos': 'INTEGER',
        'dropbox_raw_link': 'TEXT',
        'dropbox_edited_link': 'TEXT',
        'same_day_delivery': 'BOOLEAN',
        'escalated_editing': 'BOOLEAN',
        'edited_media_revision_notes': 'TEXT',
        'ndpu_editing_team': 'VARCHAR(255)',
        # Status timestamps
        'scheduled': 'TIMESTAMP',
        'acknowledged': 'TIMESTAMP',
        'at_listing': 'TIMESTAMP',
        'shoot_complete': 'TIMESTAMP',
        'uploaded': 'TIMESTAMP',
        'edit_start': 'TIMESTAMP',
        'final_review': 'TIMESTAMP',
        'escalated_editing_timestamp': 'TIMESTAMP',
        'closed': 'TIMESTAMP',
        # Service and client info
        'ndpu_service': 'VARCHAR(255)',
        'project_name': 'TEXT',
        'location_name': 'TEXT',
        'ndpu_client_name': 'TEXT',
        'ndpu_client_email': 'TEXT',
        # Notes and instructions
        'ndpu_comments': 'TEXT',
        'ndpu_editor_notes': 'TEXT',
        'ndp_platform_escalation_notes': 'TEXT',
        'ndpe_editing_revision_notes': 'TEXT',
        'ndpu_access_instructions': 'TEXT',
        'ndpu_special_instructions': 'TEXT',
        'last_updated': 'TIMESTAMP'
    }
}

# API endpoints documentation
API_ENDPOINTS = {
    'GET /api/status': 'Current sync status and metrics',
    'POST /api/interval': 'Set sync interval',
    'POST /api/sync/start': 'Start sync process',
    'POST /api/sync/stop': 'Stop sync process',
    'POST /api/sync/force': 'Force immediate sync'
}

# Required environment variables
REQUIRED_ENV_VARS = {
    'Database': [
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'DB_HOST',
        'DB_PORT'
    ],
    'Jira Instance 1': [
        'JIRA_USERNAME_1',
        'JIRA_PASSWORD_1'
    ],
    'Jira Instance 2': [
        'JIRA_USERNAME_2',
        'JIRA_PASSWORD_2'
    ]
}

# Performance settings
PERFORMANCE_SETTINGS = {
    'MAX_WORKERS': 8,
    'PROJECT_TIMEOUT': 300,  # seconds
    'BATCH_SIZE': 500,
    'MAX_RETRIES': 3,
    'BACKOFF_FACTOR': 0.5,
    'RATE_LIMIT_PAUSE': 1,  # seconds
    'DEFAULT_SYNC_INTERVAL': 5  # minutes
}

# Excluded projects (staging, testing, and internal projects)
EXCLUDED_PROJECTS = {'NDPS', 'JBR', 'TP', 'IT', 'NDPDEV', 'NDPS02', 'GTP', 'TL1'}