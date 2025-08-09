"""
Configuration API routes
"""
from fastapi import APIRouter, HTTPException
import logging
import json
import os
from pathlib import Path

from models.schemas import SyncConfig, SyncResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Config file path
CONFIG_FILE = Path(__file__).parent.parent.parent.parent / "config" / "sync_config.json"


@router.get("/sync", response_model=SyncConfig)
async def get_sync_config():
    """Get current sync configuration"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return SyncConfig(
                    interval_minutes=data.get('interval_minutes', 2),
                    enabled=data.get('enabled', True)
                )
        else:
            # Return default config
            return SyncConfig(interval_minutes=2, enabled=True)
    except Exception as e:
        logger.error(f"Failed to get sync config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sync", response_model=SyncResponse)
async def update_sync_config(config: SyncConfig):
    """Update sync configuration"""
    try:
        # Ensure config directory exists
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                'interval_minutes': config.interval_minutes,
                'enabled': config.enabled
            }, f, indent=2)
        
        return SyncResponse(
            success=True,
            message=f"Sync configuration updated successfully"
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