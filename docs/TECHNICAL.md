# Technical Documentation

## Architecture Overview

### Core Components

1. **Configuration Management**
   - `core/config/app_config.py`: Application configuration and constants
   - `core/config/logging_config.py`: Centralized logging configuration
   - `config/field_mappings.json`: Field mapping configuration

2. **Database Layer (`core/db/`)**
   - `constants.py`: Centralized column definitions
   - `db_core.py`: Core database operations
   - `db_issues.py`: Issue-related operations
   - `db_projects.py`: Project management
   - `db_audit.py`: Audit logging

3. **JIRA Integration (`core/jira/`)**
   - `jira_client.py`: API client with rate limiting
   - `field_processor.py`: Centralized field processing
   - `jira_issues.py`: Issue fetching and processing
   - Consistent error handling
   - Configuration-driven field mapping

4. **Sync Management (`core/sync/`)**
   - `sync_manager.py`: Process coordination
   - `status_manager.py`: Status tracking
   - Multi-instance support
   - Performance optimization
   - Error recovery

5. **Web Interface (`web_app.py`)**
   - Flask-based API
   - Background scheduling
   - Real-time monitoring
   - Configuration management

6. **Monitoring (`monitoring/`)**
   - `metrics.py`: System metrics
   - Resource tracking
   - Performance monitoring
   - Error logging

## API Reference

### Jira Integration

#### `get_projects(jira_instance)`
- **Purpose**: Fetches all projects from a Jira instance
- **Parameters**:
  ```python
  jira_instance: Dict[str, str] = {
      'url': str,      # Jira instance URL
      'username': str, # Authentication username
      'password': str  # Authentication password
  }
  ```
- **Returns**: List[Dict] - Project information
- **Error Handling**: HTTP and request exceptions

#### `fetch_jira_issues(jira_instance, project_key, instance_type, max_results=100)`
- **Purpose**: Fetches and processes issues from a project
- **Parameters**:
  ```python
  jira_instance: Dict[str, str]  # Instance configuration
  project_key: str               # Project identifier
  instance_type: str            # Instance type identifier
  max_results: int = 100        # Results per request
  ```
- **Returns**: List[tuple] - Processed issue data
- **Features**:
  - Pagination handling
  - Rate limiting
  - Retry logic
  - Data validation

### Database Operations

#### `batch_insert_issues(issues_data, batch_size=500)`
- **Purpose**: Efficient batch insertion/update of issues
- **Parameters**:
  ```python
  issues_data: List[tuple]    # Issue data tuples
  batch_size: int = 500      # Batch size for processing
  ```
- **Returns**: int - Number of processed records
- **Features**:
  - Transaction management
  - Error handling per batch
  - Performance metrics
  - Data integrity checks

#### `create_or_alter_tables()`
- **Purpose**: Database schema management
- **Features**:
  - Table creation
  - Schema updates
  - Index management
  - Constraint handling

### Data Processing

The application uses a centralized field processing system through the `FieldProcessor` class with support for combined fields and flexible status handling:

#### Status Processing
- Raw status strings stored directly from Jira
- Status transition timestamps tracked:
  * scheduled
  * acknowledged
  * at_listing
  * shoot_complete
  * uploaded
  * edit_start
  * final_review
  * escalated_editing
  * closed
- Status history maintained through changelog processing
- No hardcoded status mappings

#### Combined Fields Support
- Multiple source fields can be combined into a single target field
- Example combined fields:
  * NDPU Access Instructions (customfield_10700, customfield_12594, customfield_12611)
  * NDPU Special Instructions (customfield_11100, customfield_12595, customfield_12612)
- Values concatenated with proper spacing
- Null handling for missing fields

#### Field Configuration
- Field mappings defined in `config/field_mappings.json`
- Support for multiple JIRA instances
- Type validation and conversion
- Required field enforcement

#### Field Processing Features
- Nested field access with dot notation
- Combined field support
- Type-safe value extraction
- Configurable default values
- Caching for field mappings

Example configuration:
```json
{
  "field_groups": {
    "order_details": {
      "fields": {
        "order_number": {
          "type": "string",
          "required": true,
          "instance_1": {
            "field_id": "customfield_10501",
            "name": "NDPU Order Number"
          }
        }
      }
    }
  }
}
```

Usage in code:
```python
field_processor = FieldProcessor(config_path)
value = field_processor.extract_field_value(fields, field_id)
```

### Error Handling Strategy

#### Retry Logic
```python
retry_strategy = Retry(
    total=MAX_RETRIES,
    backoff_factor=BACKOFF_FACTOR,
    status_forcelist=[429, 500, 502, 503, 504]
)
```

#### Transaction Management
```python
@contextmanager
def get_db_connection():
    try:
        conn = connect()
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### Performance Optimization

#### Batch Processing
```python
def batch_insert_issues(issues_data: List[tuple], batch_size: int = 500) -> int:
    total_processed = 0
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for i in range(0, len(issues_data), batch_size):
                batch = issues_data[i:i + batch_size]
                try:
                    execute_batch(cursor, query, batch)
                    conn.commit()
                    total_processed += len(batch)
                except:
                    conn.rollback()
                    continue
    
    return total_processed
```

#### Concurrent Processing
```python
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [
        executor.submit(process_project, project)
        for project in projects
    ]
```

### Monitoring Implementation

#### Performance Metrics
```python
def log_performance_metrics(
    start_time: datetime,
    total_issues: int,
    successful_projects: int
):
    duration = (datetime.now() - start_time).total_seconds()
    metrics = {
        'duration': duration,
        'issues_rate': total_issues / duration if duration > 0 else 0,
        'projects_rate': (successful_projects * 60) / duration if duration > 0 else 0
    }
    log_metrics(metrics)
```

#### Database Monitoring
```python
def monitor_database():
    with get_db_connection() as conn:
        size = get_database_size(conn)
        tables = get_table_stats(conn)
        log_database_metrics(size, tables)
```

### Security Considerations

1. **Credential Management**
   - Environment variables
   - Secure connection handling
   - Password encryption

2. **Error Message Sanitization**
   - Remove sensitive information
   - Structured error logging
   - Secure error handling

### Testing Strategy

1. **Unit Tests**
   - Component isolation
   - Mock external services
   - Error case validation

2. **Integration Tests**
   - End-to-end workflows
   - Database integration
   - API integration

3. **Performance Tests**
   - Load testing
   - Memory usage
   - Database performance

### Deployment Considerations

1. **Environment Setup**
   - Python runtime
   - Database configuration
   - Network access
   - Resource allocation

2. **Monitoring Setup**
   - Log aggregation
   - Metric collection
   - Alert configuration
   - Performance tracking

3. **Maintenance**
   - Log rotation
   - Database maintenance
   - Backup strategy
   - Update procedures
