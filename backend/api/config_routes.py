"""
Configuration API routes
"""
from fastapi import APIRouter, HTTPException
import logging
import json
from pathlib import Path

from ..models.schemas import SyncConfig, SyncResponse
from ..core.db.db_config import get_configuration, save_configuration

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sync", response_model=SyncConfig)
async def get_sync_config():
    """Get current sync configuration from database"""
    try:
        config = get_configuration('sync', 'scheduler')
        if config and config.get('value'):
            data = config['value']
            return SyncConfig(
                interval_minutes=data.get('interval_minutes', 5),
                enabled=data.get('enabled', True)
            )
        else:
            # Return default config
            return SyncConfig(interval_minutes=5, enabled=True)
    except Exception as e:
        logger.error(f"Failed to get sync config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sync", response_model=SyncResponse)
async def update_sync_config(config: SyncConfig):
    """Update sync configuration in database"""
    try:
        # Save to database
        config_data = {
            'interval_minutes': config.interval_minutes,
            'enabled': config.enabled
        }
        
        save_configuration(
            config_type='sync',
            config_key='scheduler',
            config_value=config_data,
            user='api'
        )
        
        return SyncResponse(
            success=True,
            message="Sync configuration updated successfully in database"
        )
    except Exception as e:
        logger.error(f"Failed to update sync config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/field-mappings")
async def get_field_mappings():
    """Get JIRA field mappings configuration"""
    try:
        mappings_file = Path(__file__).parent.parent.parent.parent / "config" / "field_mappings.json"
        if mappings_file.exists():
            with open(mappings_file, 'r') as f:
                return json.load(f)
        else:
            return {"error": "Field mappings not found"}
    except Exception as e:
        logger.error(f"Failed to get field mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
