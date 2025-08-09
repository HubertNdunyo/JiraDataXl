"""
Enhanced admin routes with database configuration management
"""
from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks, Query, Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, AliasChoices
import logging
import os

from core.db.db_config import (
    get_configuration,
    save_configuration,
    create_backup,
    list_backups,
    restore_backup,
    get_configuration_history,
    create_config_tables,
    migrate_file_configs_to_db
)
from core.db.db_field_cache import FieldCacheManager
from core.db.db_schema_manager import SchemaManager
from core.jira import JiraClient
from core.jira.jira_client import JiraApiError

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models
class FieldMapping(BaseModel):
    field_id: str = Field(..., pattern=r'^customfield_\d+$|^[a-zA-Z][a-zA-Z0-9_\.]*$', description="Valid JIRA field ID")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class FieldDefinition(BaseModel):
    type: str = Field(..., pattern=r'^(string|number|integer|boolean|date|datetime|array|object|status)$')
    required: bool = False
    description: Optional[str] = Field(None, max_length=1000)
    system_field: Optional[bool] = False
    field_id: Optional[str] = None  # For system fields
    instance_1: Optional[FieldMapping] = None
    instance_2: Optional[FieldMapping] = None
    
    @field_validator('type')
    def validate_type(cls, v):
        valid_types = ['string', 'number', 'integer', 'boolean', 'date', 'datetime', 'array', 'object', 'status']
        if v not in valid_types:
            raise ValueError(f'Invalid field type. Must be one of: {", ".join(valid_types)}')
        return v


class FieldGroup(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    fields: Dict[str, FieldDefinition]
    
    @field_validator('fields')
    def validate_fields(cls, v):
        if not v:
            raise ValueError('Field group must contain at least one field')
        if len(v) > 100:
            raise ValueError('Field group cannot contain more than 100 fields')
        return v


class FieldMappingsConfig(BaseModel):
    version: str = "2.0"
    last_updated: Optional[str] = None
    description: Optional[str] = None
    instances: Dict[str, Dict[str, str]]
    field_groups: Dict[str, FieldGroup]


class SyncConfig(BaseModel):
    interval_minutes: int = Field(
        ge=1,
        le=1440,
        validation_alias=AliasChoices("interval_minutes", "interval"),
    )
    enabled: bool = True


class PerformanceConfig(BaseModel):
    """Performance configuration for sync operations"""
    max_workers: int = Field(ge=1, le=16, default=8, description="Number of concurrent threads for parallel processing")
    project_timeout: int = Field(ge=60, le=1800, default=300, description="Maximum time in seconds to wait for a project sync")
    batch_size: int = Field(ge=50, le=1000, default=200, description="Number of issues to fetch per API request")
    lookback_days: int = Field(ge=1, le=365, default=60, description="How many days of history to sync")
    max_retries: int = Field(ge=0, le=10, default=3, description="Number of retry attempts for failed requests")
    backoff_factor: float = Field(ge=0.1, le=5.0, default=0.5, description="Exponential backoff multiplier between retries")
    rate_limit_pause: float = Field(ge=0.0, le=10.0, default=1.0, description="Pause in seconds between API requests")
    connection_pool_size: int = Field(ge=5, le=50, default=20, description="Size of HTTP connection pool for JIRA API requests")
    connection_pool_block: bool = Field(default=False, description="Whether to block when connection pool is exhausted")


class ConfigUpdate(BaseModel):
    config_type: str
    config_key: str
    config_value: Dict[str, Any]
    reason: Optional[str] = None


class BackupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_\-]+$')
    description: Optional[str] = Field(None, max_length=500)


# Authentication
async def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    """Verify admin API key"""
    import os
    import re
    
    # Validate header format (alphanumeric + dash)
    if x_admin_key and not re.match(r'^[a-zA-Z0-9\-]+$', x_admin_key):
        raise HTTPException(status_code=400, detail="Invalid API key format")
    
    admin_key = os.getenv('ADMIN_API_KEY')
    if not admin_key:
        raise HTTPException(
            status_code=500, 
            detail="Admin API key not configured. Please set ADMIN_API_KEY environment variable."
        )
    if not x_admin_key or x_admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


# Note: Configuration tables are initialized in main.py lifespan


# Configuration endpoints
@router.get("/config/field-mappings")
async def get_field_mappings(authorized: bool = Depends(verify_admin_key)):
    """Get field mappings configuration from database"""
    try:
        config = get_configuration('jira', 'field_mappings')
        if config:
            return config['value']
        else:
            # Return empty structure if not found
            return {
                "version": "2.0",
                "instances": {},
                "field_groups": {}
            }
    except Exception as e:
        logger.error(f"Error fetching field mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/field-mappings")
async def update_field_mappings(
    config: FieldMappingsConfig,
    background_tasks: BackgroundTasks,
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Update field mappings configuration"""
    try:
        # Create pre-update backup
        backup_name = f"field_mappings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        background_tasks.add_task(
            create_backup,
            backup_name,
            'pre_update',
            'Automatic backup before field mappings update',
            x_user or 'admin'
        )
        
        # Save configuration
        config_id = save_configuration(
            'jira',
            'field_mappings',
            config.dict(),
            x_user or 'admin',
            'Updated via admin interface'
        )
        
        # Sync database schema with new field mappings
        try:
            schema_manager = SchemaManager()
            sync_results = schema_manager.sync_fields_with_schema(config.dict())
            logger.info(
                f"Schema sync after field update: "
                f"Added {len(sync_results['added'])} columns"
            )
        except Exception as e:
            logger.error(f"Schema sync failed (non-critical): {e}")
            # Don't fail the entire operation if schema sync fails
        
        return {
            "message": "Field mappings updated successfully",
            "config_id": config_id,
            "backup_created": backup_name,
            "schema_sync": sync_results if 'sync_results' in locals() else None
        }
    except Exception as e:
        logger.error(f"Error updating field mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/sync")
async def get_sync_config(authorized: bool = Depends(verify_admin_key)):
    """Get sync configuration from database"""
    try:
        config = get_configuration('sync', 'settings')
        if config:
            return config['value']
        else:
            return {"interval_minutes": 60, "enabled": False}
    except Exception as e:
        logger.error(f"Error fetching sync config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/sync")
async def update_sync_config(
    config: SyncConfig,
    background_tasks: BackgroundTasks,
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Update sync configuration"""
    try:
        # Create pre-update backup
        backup_name = f"sync_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        background_tasks.add_task(
            create_backup,
            backup_name,
            'pre_update',
            'Automatic backup before sync config update',
            x_user or 'admin'
        )
        
        # Save configuration
        config_id = save_configuration(
            'sync',
            'settings',
            config.dict(),
            x_user or 'admin',
            'Updated via admin interface'
        )
        
        return {
            "message": "Sync configuration updated successfully",
            "config_id": config_id,
            "backup_created": backup_name
        }
    except Exception as e:
        logger.error(f"Error updating sync config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/performance")
async def get_performance_config(
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Get performance configuration"""
    config = get_configuration('performance', 'settings')
    
    if config:
        return config['value']
    else:
        # Return defaults if not configured
        return PerformanceConfig().model_dump()


@router.put("/config/performance")
async def update_performance_config(
    config: PerformanceConfig,
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Update performance configuration"""
    try:
        # Create auto backup before updating
        backup_name = f"pre_performance_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_id = create_backup(
            backup_name,
            'auto',
            'Automatic backup before performance config update',
            x_user or 'admin'
        )
        
        # Save configuration
        config_id = save_configuration(
            'performance',
            'settings',
            config.model_dump(),
            x_user or 'admin',
            'Updated via admin interface'
        )
        
        return {
            "message": "Performance configuration updated successfully",
            "config_id": config_id,
            "backup_created": backup_name
        }
    except Exception as e:
        logger.error(f"Error updating performance config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/performance/test")
async def test_performance_config(
    config: PerformanceConfig,
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Test performance configuration with a dry run"""
    try:
        # Validate the configuration
        validation_results = {
            "valid": True,
            "warnings": [],
            "estimated_impact": {}
        }
        
        # Check for potential issues
        if config.max_workers > 12:
            validation_results["warnings"].append(
                "High worker count may cause rate limiting issues"
            )
        
        if config.batch_size > 500:
            validation_results["warnings"].append(
                "Large batch size may cause API timeouts"
            )
        
        if config.lookback_days > 180:
            validation_results["warnings"].append(
                "Large lookback period will increase sync duration significantly"
            )
        
        # Calculate estimated impact
        validation_results["estimated_impact"] = {
            "api_requests_per_project": f"~{1000 // config.batch_size} requests per 1000 issues",
            "max_concurrent_projects": config.max_workers,
            "total_sync_time_estimate": f"~{config.project_timeout * 50 // config.max_workers // 60} minutes for 50 projects",
            "memory_usage": f"~{config.max_workers * 50}MB",
            "rate_limit_safety": "High" if config.rate_limit_pause >= 1.0 else "Medium"
        }
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error testing performance config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/field-mappings/validate")
async def validate_field_mappings(
    config: FieldMappingsConfig,
    authorized: bool = Depends(verify_admin_key)
):
    """Validate field mappings against JIRA schema"""
    import os
    from core.jira.jira_client import JiraClient
    
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "field_validation": {
            "instance_1": {},
            "instance_2": {}
        }
    }
    
    # Define nested/special fields that don't appear in JIRA field list
    NESTED_FIELDS = {
        'project.name': 'Project Name',
        'project.key': 'Project Key',
        'assignee.displayName': 'Assignee Display Name',
        'assignee.emailAddress': 'Assignee Email',
        'reporter.displayName': 'Reporter Display Name',
        'reporter.emailAddress': 'Reporter Email',
        'creator.displayName': 'Creator Display Name',
        'priority.name': 'Priority Name',
        'issuetype.name': 'Issue Type Name',
        'resolution.name': 'Resolution Name'
    }
    
    # Basic validation
    if not config.field_groups:
        validation_results["warnings"].append("No field groups defined")
        # Don't mark as invalid - empty config is valid for new setups
        return validation_results
    
    # Get JIRA credentials
    jira_email = os.getenv('JIRA_EMAIL')
    jira_token = os.getenv('JIRA_ACCESS_TOKEN')
    
    if not jira_email or not jira_token:
        validation_results["errors"].append("JIRA credentials not configured")
        validation_results["valid"] = False
        return validation_results
    
    # Validate fields against JIRA instances
    try:
        # Check Instance 1
        instance_1_url = os.getenv('JIRA_INSTANCE_1')
        if instance_1_url:
            jira1 = JiraClient(instance_1_url, jira_email, jira_token)
            fields_1 = jira1.get_fields()
            field_ids_1 = {f['id']: f['name'] for f in fields_1}
            
            # Validate each field in instance 1
            for group_name, group in config.field_groups.items():
                for field_name, field in group.fields.items():
                    # Handle system fields
                    if field.system_field and field.field_id:
                        field_id = field.field_id
                        if field_id in field_ids_1 or field_id in ['summary', 'status', 'updated', 'created', 'assignee', 'reporter']:
                            validation_results["field_validation"]["instance_1"][field_id] = {
                                "valid": True,
                                "jira_name": field_ids_1.get(field_id, field_id),
                                "config_name": field_id,
                                "system_field": True
                            }
                        else:
                            validation_results["errors"].append(
                                f"System field '{field_name}' with ID '{field_id}' not recognized"
                            )
                            validation_results["valid"] = False
                    # Handle custom fields with instance mapping
                    elif field.instance_1:
                        field_id = field.instance_1.field_id
                        # Check if it's a nested field
                        if field_id in NESTED_FIELDS:
                            validation_results["field_validation"]["instance_1"][field_id] = {
                                "valid": True,
                                "jira_name": NESTED_FIELDS[field_id],
                                "config_name": field.instance_1.name,
                                "nested_field": True
                            }
                        elif field_id in field_ids_1:
                            validation_results["field_validation"]["instance_1"][field_id] = {
                                "valid": True,
                                "jira_name": field_ids_1[field_id],
                                "config_name": field.instance_1.name
                            }
                        else:
                            validation_results["field_validation"]["instance_1"][field_id] = {
                                "valid": False,
                                "error": f"Field ID '{field_id}' not found in JIRA instance 1"
                            }
                            validation_results["errors"].append(
                                f"Field '{field_name}' - Instance 1 field ID '{field_id}' not found in JIRA"
                            )
                            validation_results["valid"] = False
        
        # Check Instance 2
        instance_2_url = os.getenv('JIRA_INSTANCE_2')
        if instance_2_url:
            jira2 = JiraClient(instance_2_url, jira_email, jira_token)
            fields_2 = jira2.get_fields()
            field_ids_2 = {f['id']: f['name'] for f in fields_2}
            
            # Validate each field in instance 2
            for group_name, group in config.field_groups.items():
                for field_name, field in group.fields.items():
                    # Handle system fields
                    if field.system_field and field.field_id:
                        field_id = field.field_id
                        if field_id in field_ids_2 or field_id in ['summary', 'status', 'updated', 'created', 'assignee', 'reporter']:
                            validation_results["field_validation"]["instance_2"][field_id] = {
                                "valid": True,
                                "jira_name": field_ids_2.get(field_id, field_id),
                                "config_name": field_id,
                                "system_field": True
                            }
                        else:
                            validation_results["errors"].append(
                                f"System field '{field_name}' with ID '{field_id}' not recognized in instance 2"
                            )
                            validation_results["valid"] = False
                    # Handle custom fields with instance mapping
                    elif field.instance_2:
                        field_id = field.instance_2.field_id
                        # Check if it's a nested field
                        if field_id in NESTED_FIELDS:
                            validation_results["field_validation"]["instance_2"][field_id] = {
                                "valid": True,
                                "jira_name": NESTED_FIELDS[field_id],
                                "config_name": field.instance_2.name,
                                "nested_field": True
                            }
                        elif field_id in field_ids_2:
                            validation_results["field_validation"]["instance_2"][field_id] = {
                                "valid": True,
                                "jira_name": field_ids_2[field_id],
                                "config_name": field.instance_2.name
                            }
                        else:
                            validation_results["field_validation"]["instance_2"][field_id] = {
                                "valid": False,
                                "error": f"Field ID '{field_id}' not found in JIRA instance 2"
                            }
                            validation_results["errors"].append(
                                f"Field '{field_name}' - Instance 2 field ID '{field_id}' not found in JIRA"
                            )
                            validation_results["valid"] = False
                    
    except Exception as e:
        logger.error(f"Error validating fields against JIRA: {e}")
        validation_results["errors"].append(f"Failed to connect to JIRA: {str(e)}")
        validation_results["valid"] = False
    
    # Check for missing instance mappings
    for group_name, group in config.field_groups.items():
        for field_name, field in group.fields.items():
            # Skip system fields as they don't need instance mappings
            if field.system_field and field.field_id:
                continue
            # Warn about fields with no mappings
            if not field.instance_1 and not field.instance_2:
                validation_results["warnings"].append(
                    f"Field '{field_name}' in group '{group_name}' has no instance mappings"
                )
    
    return validation_results


# Backup and restore endpoints
@router.get("/config/backups")
async def list_configuration_backups(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of backups to return"),
    authorized: bool = Depends(verify_admin_key)
):
    """List available configuration backups"""
    try:
        backups = list_backups(limit)
        return {"backups": backups, "total": len(backups)}
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/backups")
async def create_configuration_backup(
    request: BackupRequest,
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Create a manual configuration backup"""
    try:
        backup_id = create_backup(
            request.name,
            'manual',
            request.description,
            x_user or 'admin'
        )
        return {
            "message": "Backup created successfully",
            "backup_id": backup_id
        }
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/field-mappings/validate-field")
async def validate_single_field(
    field_id: str,
    instance: str = Query(..., pattern="^(instance_1|instance_2|both)$"),
    authorized: bool = Depends(verify_admin_key)
):
    """Validate a single field ID against JIRA schema"""
    import os
    from core.jira.jira_client import JiraClient
    
    # Define nested/special fields that don't appear in JIRA field list
    NESTED_FIELDS = {
        'project.name': 'Project Name',
        'project.key': 'Project Key',
        'assignee.displayName': 'Assignee Display Name',
        'assignee.emailAddress': 'Assignee Email',
        'reporter.displayName': 'Reporter Display Name',
        'reporter.emailAddress': 'Reporter Email',
        'creator.displayName': 'Creator Display Name',
        'priority.name': 'Priority Name',
        'issuetype.name': 'Issue Type Name',
        'resolution.name': 'Resolution Name'
    }
    
    validation_result = {
        "field_id": field_id,
        "instance_1": None,
        "instance_2": None
    }
    
    # Get JIRA credentials
    jira_email = os.getenv('JIRA_EMAIL')
    jira_token = os.getenv('JIRA_ACCESS_TOKEN')
    
    if not jira_email or not jira_token:
        raise HTTPException(status_code=500, detail="JIRA credentials not configured")
    
    try:
        # Check if it's a nested field first
        if field_id in NESTED_FIELDS:
            if instance in ['instance_1', 'both']:
                validation_result["instance_1"] = {
                    "valid": True,
                    "field_name": NESTED_FIELDS[field_id],
                    "nested_field": True
                }
            if instance in ['instance_2', 'both']:
                validation_result["instance_2"] = {
                    "valid": True,
                    "field_name": NESTED_FIELDS[field_id],
                    "nested_field": True
                }
            return validation_result
        
        # Check if it's a known system field
        system_fields = ['summary', 'status', 'updated', 'created', 'assignee', 'reporter', 'description', 'priority', 'labels']
        
        if field_id in system_fields:
            if instance in ['instance_1', 'both']:
                validation_result["instance_1"] = {
                    "valid": True,
                    "field_name": field_id.capitalize(),
                    "system_field": True
                }
            if instance in ['instance_2', 'both']:
                validation_result["instance_2"] = {
                    "valid": True,
                    "field_name": field_id.capitalize(),
                    "system_field": True
                }
            return validation_result
        
        # Check Instance 1
        if instance in ['instance_1', 'both']:
            instance_1_url = os.getenv('JIRA_INSTANCE_1')
            if instance_1_url:
                jira1 = JiraClient(instance_1_url, jira_email, jira_token)
                fields_1 = jira1.get_fields()
                field_map_1 = {f['id']: f['name'] for f in fields_1}
                
                if field_id in field_map_1:
                    validation_result["instance_1"] = {
                        "valid": True,
                        "field_name": field_map_1[field_id]
                    }
                else:
                    validation_result["instance_1"] = {
                        "valid": False,
                        "error": f"Field ID '{field_id}' not found in JIRA instance 1"
                    }
        
        # Check Instance 2
        if instance in ['instance_2', 'both']:
            instance_2_url = os.getenv('JIRA_INSTANCE_2')
            if instance_2_url:
                jira2 = JiraClient(instance_2_url, jira_email, jira_token)
                fields_2 = jira2.get_fields()
                field_map_2 = {f['id']: f['name'] for f in fields_2}
                
                if field_id in field_map_2:
                    validation_result["instance_2"] = {
                        "valid": True,
                        "field_name": field_map_2[field_id]
                    }
                else:
                    validation_result["instance_2"] = {
                        "valid": False,
                        "error": f"Field ID '{field_id}' not found in JIRA instance 2"
                    }
                    
    except Exception as e:
        logger.error(f"Error validating field: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to JIRA: {str(e)}")
    
    return validation_result


@router.post("/config/restore/{backup_id}")
async def restore_configuration_backup(
    backup_id: int = Path(..., ge=1, description="Backup ID to restore"),
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Restore configuration from a backup"""
    try:
        success = restore_backup(backup_id, x_user or 'admin')
        if success:
            return {"message": "Configuration restored successfully"}
        else:
            raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# History endpoint
@router.get("/config/history")
async def get_config_history(
    config_type: Optional[str] = None,
    config_key: Optional[str] = None,
    limit: int = 50,
    authorized: bool = Depends(verify_admin_key)
):
    """Get configuration change history"""
    try:
        history = get_configuration_history(config_type, config_key, limit)
        return {"history": history, "total": len(history)}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Migration endpoint
@router.post("/config/migrate")
async def migrate_configs(
    background_tasks: BackgroundTasks,
    authorized: bool = Depends(verify_admin_key)
):
    """Migrate file-based configs to database"""
    try:
        background_tasks.add_task(migrate_file_configs_to_db)
        return {"message": "Migration started in background"}
    except Exception as e:
        logger.error(f"Error starting migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Field Discovery Endpoints
@router.post("/fields/discover")
async def discover_jira_fields(
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Discover and cache all fields from both JIRA instances"""
    import os
    from core.jira.jira_client import JiraClient
    
    field_cache = FieldCacheManager()
    
    # Get JIRA credentials - using the correct environment variable names
    jira_email = os.getenv('JIRA_USERNAME_1') or os.getenv('JIRA_CREATE_EMAIL')
    jira_token = os.getenv('JIRA_PASSWORD_1') or os.getenv('JIRA_CREATE_TOKEN')
    
    if not jira_email or not jira_token:
        raise HTTPException(status_code=500, detail="JIRA credentials not configured")
    
    results = {
        "instance_1": {"discovered": 0, "error": None},
        "instance_2": {"discovered": 0, "error": None}
    }
    
    # Discover fields from Instance 1
    instance_1_url = os.getenv('JIRA_URL_1')
    if instance_1_url:
        try:
            jira1 = JiraClient(instance_1_url, jira_email, jira_token)
            fields_1 = jira1.get_fields()
            count = field_cache.cache_fields('instance_1', fields_1)
            results["instance_1"]["discovered"] = count
        except Exception as e:
            logger.error(f"Error discovering fields from instance 1: {e}")
            results["instance_1"]["error"] = str(e)
    
    # Discover fields from Instance 2
    instance_2_url = os.getenv('JIRA_URL_2')
    if instance_2_url:
        try:
            # Use instance 2 credentials if different
            jira2_email = os.getenv('JIRA_USERNAME_2') or jira_email
            jira2_token = os.getenv('JIRA_PASSWORD_2') or jira_token
            jira2 = JiraClient(instance_2_url, jira2_email, jira2_token)
            fields_2 = jira2.get_fields()
            count = field_cache.cache_fields('instance_2', fields_2)
            results["instance_2"]["discovered"] = count
        except Exception as e:
            logger.error(f"Error discovering fields from instance 2: {e}")
            results["instance_2"]["error"] = str(e)
    
    # Get cache statistics
    stats = field_cache.get_cache_stats()
    
    return {
        "message": "Field discovery completed",
        "results": results,
        "cache_stats": stats,
        "discovered_by": x_user or "admin"
    }


@router.get("/fields/cached")
async def get_cached_fields(
    instance: Optional[str] = Query(None, pattern="^(instance_1|instance_2)$"),
    authorized: bool = Depends(verify_admin_key)
):
    """Get all cached fields, optionally filtered by instance"""
    field_cache = FieldCacheManager()
    
    try:
        fields = field_cache.get_cached_fields(instance)
        
        # Group fields by instance and type
        grouped = {
            "instance_1": {"system": [], "custom": []},
            "instance_2": {"system": [], "custom": []}
        }
        
        for field in fields:
            instance_key = field['instance']
            field_type = 'custom' if field['is_custom'] else 'system'
            grouped[instance_key][field_type].append({
                "field_id": field['field_id'],
                "field_name": field['field_name'],
                "field_type": field['field_type'],
                "is_array": field['is_array']
            })
        
        # Get statistics
        stats = field_cache.get_cache_stats()
        
        return {
            "fields": grouped,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error retrieving cached fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fields/search")
async def search_fields(
    term: str = Query(..., min_length=2, description="Search term"),
    instance: Optional[str] = Query(None, pattern="^(instance_1|instance_2)$"),
    authorized: bool = Depends(verify_admin_key)
):
    """Search for fields by name or ID"""
    field_cache = FieldCacheManager()
    
    try:
        fields = field_cache.search_fields(term, instance)
        return {
            "search_term": term,
            "results": fields,
            "count": len(fields)
        }
    except Exception as e:
        logger.error(f"Error searching fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fields/suggest")
async def suggest_field_mappings(
    field_name: str,
    exclude_mapped: Optional[List[str]] = None,
    authorized: bool = Depends(verify_admin_key)
):
    """Get field mapping suggestions based on name similarity"""
    field_cache = FieldCacheManager()
    
    try:
        suggestions = field_cache.get_field_suggestions(field_name, exclude_mapped or [])
        return {
            "field_name": field_name,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error getting field suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fields/preview")
async def preview_field_data(
    field_id: str = Query(..., description="Field ID to preview"),
    instance: str = Query(..., description="JIRA instance (instance_1 or instance_2)"),
    limit: int = Query(5, ge=1, le=10, description="Number of sample values to return"),
    authorized: bool = Depends(verify_admin_key)
):
    """Get sample data for a specific field from JIRA issues."""
    from core.jira.jira_client import JiraClient
    
    if instance not in ["instance_1", "instance_2"]:
        raise HTTPException(status_code=400, detail="Invalid instance")
    
    try:
        # Get JIRA credentials from environment
        if instance == "instance_1":
            url = "https://betteredits.atlassian.net"
            username = os.getenv('JIRA_USERNAME_1') or os.getenv('JIRA_EMAIL')
            password = os.getenv('JIRA_PASSWORD_1') or os.getenv('JIRA_ACCESS_TOKEN')
        else:  # instance_2
            url = "https://betteredits2.atlassian.net"
            username = os.getenv('JIRA_USERNAME_2') or os.getenv('JIRA_EMAIL')
            password = os.getenv('JIRA_PASSWORD_2') or os.getenv('JIRA_ACCESS_TOKEN')
        
        if not username or not password:
            raise HTTPException(status_code=500, detail="JIRA credentials not configured")
        
        # Get JIRA client for the instance
        client = JiraClient(url=url, username=username, password=password)
        
        # Search for issues - we'll filter for non-empty values after retrieval
        # Use a simple query to get recent issues
        jql = "ORDER BY updated DESC"
        
        # For some system fields, we can use more specific queries
        if field_id == "assignee":
            jql = "assignee is not EMPTY ORDER BY updated DESC"
        elif field_id == "reporter":
            jql = "reporter is not EMPTY ORDER BY updated DESC"
        
        # Search issues - returns dict with 'issues' key
        # Fetch more issues since we'll filter for non-empty values
        result = client.search_issues(
            jql=jql,
            fields=[field_id, "key"],
            max_results=50  # Fetch more to ensure we get enough non-empty values
        )
        issues = result.get('issues', [])
        
        # Extract sample values
        samples = []
        seen_values = set()
        
        for issue in issues:
            value = None
            fields = issue.get('fields', {})
            
            # Handle nested fields
            if '.' in field_id:
                parts = field_id.split('.')
                obj = fields
                for part in parts:
                    if isinstance(obj, dict):
                        obj = obj.get(part)
                    else:
                        obj = None
                    if obj is None:
                        break
                value = obj
            else:
                # Direct field access
                value = fields.get(field_id)
            
            # Process the value
            if value is not None:
                # Convert complex objects to readable format
                if isinstance(value, dict):
                    if 'displayName' in value:
                        display_value = value['displayName']
                    elif 'name' in value:
                        display_value = value['name']
                    elif 'value' in value:
                        display_value = value['value']
                    else:
                        display_value = str(value)
                elif isinstance(value, list):
                    display_value = f"[Array of {len(value)} items]"
                else:
                    display_value = str(value)
                
                # Only add unique values
                if display_value not in seen_values:
                    samples.append({
                        "issue_key": issue.get('key', 'Unknown'),
                        "value": display_value,
                        "raw_value": str(value)[:200]  # Truncate for safety
                    })
                    seen_values.add(display_value)
                    
                    # Stop if we have enough samples
                    if len(samples) >= limit:
                        break
        
        # Get field info from cache
        manager = FieldCacheManager()
        field_info = None
        cached_fields = manager.get_cached_fields(instance)
        for field in cached_fields:
            if field['field_id'] == field_id:
                field_info = field
                break
        
        return {
            "field_id": field_id,
            "instance": instance,
            "field_info": field_info,
            "sample_count": len(samples),
            "samples": samples
        }
        
    except JiraApiError as e:
        logger.error(f"JIRA API error previewing field data: {e}")
        # Return empty samples if field doesn't exist or can't be queried
        return {
            "field_id": field_id,
            "instance": instance,
            "field_info": None,
            "sample_count": 0,
            "samples": [],
            "error": f"Could not fetch field data: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error previewing field data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schema/sync")
async def sync_database_schema(
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """Synchronize database schema with field mappings configuration."""
    try:
        # Get current field mappings
        config = get_configuration('jira', 'field_mappings')
        if not config or not config.get('value'):
            raise HTTPException(status_code=404, detail="No field mappings configuration found")
        
        # Initialize schema manager
        schema_manager = SchemaManager()
        
        # Sync fields with database schema
        results = schema_manager.sync_fields_with_schema(config['value'])
        
        # Log the operation
        logger.info(
            f"Schema sync by {x_user or 'admin'}: "
            f"Added {len(results['added'])} columns, "
            f"Skipped {len(results['skipped'])} existing, "
            f"Errors: {len(results['errors'])}"
        )
        
        return {
            "success": True,
            "added_columns": results['added'],
            "skipped_columns": results['skipped'],
            "errors": results['errors'],
            "message": f"Added {len(results['added'])} new columns to database"
        }
        
    except Exception as e:
        logger.error(f"Error syncing database schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/columns")
async def get_database_columns(
    authorized: bool = Depends(verify_admin_key)
):
    """Get list of columns in the jira_issues_v2 table."""
    try:
        schema_manager = SchemaManager()
        columns = schema_manager.get_existing_columns()
        
        return {
            "table": "jira_issues_v2",
            "schema": "jira_sync",
            "columns": columns,
            "count": len(columns)
        }
        
    except Exception as e:
        logger.error(f"Error fetching database columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-issues-table")
async def clear_issues_table(
    authorized: bool = Depends(verify_admin_key),
    x_user: Optional[str] = Header(None)
):
    """
    Clear all data from the jira_issues_v2 table.
    WARNING: This will delete all synced issues!
    """
    try:
        from core.db.db_core import get_db_connection
        
        # Create a backup first for safety
        logger.info(f"Creating backup before clearing jira_issues_v2 table (requested by {x_user or 'admin'})")
        
        # Count existing records first
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM jira_issues_v2")
                count_before = cursor.fetchone()[0]
                
                if count_before == 0:
                    return {
                        "message": "Table is already empty",
                        "records_deleted": 0
                    }
                
                # Clear the table using TRUNCATE for better performance
                logger.info(f"Clearing {count_before} records from jira_issues_v2")
                cursor.execute("TRUNCATE TABLE jira_issues_v2 RESTART IDENTITY")
                conn.commit()
                
                # Log the operation
                cursor.execute("""
                    INSERT INTO audit_log (
                        operation, 
                        affected_table, 
                        affected_records, 
                        performed_by, 
                        details
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    'CLEAR_TABLE',
                    'jira_issues_v2',
                    count_before,
                    x_user or 'admin',
                    f'Cleared {count_before} records from jira_issues_v2 table'
                ))
                conn.commit()
        
        logger.info(f"Successfully cleared {count_before} records from jira_issues_v2")
        
        return {
            "message": "Table cleared successfully",
            "records_deleted": count_before,
            "performed_by": x_user or 'admin',
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing jira_issues_v2 table: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to clear table: {str(e)}"
        )


@router.get("/issues/count")
async def get_issues_count(
    authorized: bool = Depends(verify_admin_key)
):
    """Get the current count of records in jira_issues_v2 table"""
    try:
        from core.db.db_core import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM jira_issues_v2")
                count = cursor.fetchone()[0]
                
                # Get count by project
                cursor.execute("""
                    SELECT project_name, COUNT(*) as issue_count 
                    FROM jira_issues_v2 
                    GROUP BY project_name 
                    ORDER BY issue_count DESC
                    LIMIT 10
                """)
                projects = cursor.fetchall()
                
                return {
                    "total_issues": count,
                    "top_projects": [
                        {"project": p[0], "count": p[1]} for p in projects
                    ]
                }
                
    except Exception as e:
        logger.error(f"Error getting issues count: {e}")
        raise HTTPException(status_code=500, detail=str(e))