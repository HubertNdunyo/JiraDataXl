# Jira Data Sync Application

A robust application for synchronizing and storing Jira issue data with a focus on reliability and data integrity.

## Overview

This application synchronizes data from multiple Jira instances, storing the complete raw data for maximum flexibility and future-proofing. Instead of transforming and mapping fields during sync, we store the complete Jira response and handle transformations at query time.

## Features

- Complete Jira data synchronization
- Raw data storage in JSONB format
- Efficient batch processing
- Comprehensive sync logging with timestamped files
- Detailed performance metrics
- Error tracking and recovery
- Flexible status handling without hardcoding
- Support for combined fields
- Full project discovery without filtering

## Architecture

The application follows a modular and maintainable architecture:

1. **Core Components**
   - Centralized configuration management
   - Unified logging system
   - Standardized database operations
   - Configuration-driven field processing

2. **Data Management**
   - Raw Jira data in JSONB format
   - Centralized column definitions
   - Consistent field mapping
   - Efficient batch processing

3. **Sync Process**
   - Regular sync every 2 minutes
   - Multi-instance coordination
   - Intelligent rate limiting
   - Robust error handling

4. **Monitoring**
   - Real-time sync status
   - Performance metrics
   - Resource utilization
   - Comprehensive logging

For detailed documentation, see:
- [Technical Documentation](TECHNICAL.md)
- [File Structure](FILE_STRUCTURE.md)

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Jira API access
- Environment variables configured

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dataappV3
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application:
   - Copy configuration templates:
     ```bash
     cp .env.example .env
     cp config/field_mappings.example.json config/field_mappings.json
     ```
   - Edit `.env` with your database and JIRA credentials
   - Update `field_mappings.json` with your field configuration

4. Initialize the system:
```bash
# Initialize database
python setup.py

# Verify configuration
python utils/tests/check_specific_issue.py TEST-1
```

## Configuration

1. **Environment Variables** (in `.env`):
```bash
# Database Configuration
DB_NAME=jira_data
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# JIRA Credentials
JIRA_USERNAME_1=your_username
JIRA_PASSWORD_1=your_password
JIRA_USERNAME_2=your_username
JIRA_PASSWORD_2=your_password
```

2. **Field Mappings** (in `config/field_mappings.json`):
```json
{
  "field_groups": {
    "order_details": {
      "fields": {
        "order_number": {
          "type": "string",
          "required": true,
          "instance_1": {
            "field_id": "customfield_10501"
          }
        }
      }
    }
  }
}
```

## Usage

1. Start the sync service:
```bash
python app.py
```

2. Monitor sync status:
```bash
# View sync logs
tail -f logs/sync.log

# Check database status
python utils/tests/analyze_data_volume.py
```

## Development

1. Set up development environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run tests:
```bash
python -m pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is proprietary and confidential.

## Support

For support, please contact the development team.
