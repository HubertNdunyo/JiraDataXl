"""
Admin routes for configuration management
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import json
import os
from datetime import datetime
import shutil
from models.schemas import SyncConfig

router = APIRouter()

# Simple API key authentication
async def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    """Verify admin API key"""
    admin_key = os.getenv('ADMIN_API_KEY', 'default-admin-key-change-me')
    if not x_admin_key or x_admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@router.get("/config/field-mappings")
async def get_field_mappings(authorized: bool = Depends(verify_admin_key)):
    """Get current field mappings configuration"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '../../config/field_mappings.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/sync")
async def get_sync_config(authorized: bool = Depends(verify_admin_key)):
    """Get current sync configuration"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '../../config/sync_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config/sync")
async def update_sync_config(
    config: SyncConfig,
    authorized: bool = Depends(verify_admin_key)
):
    """Update sync configuration (MVP: only interval)"""
    try:
        # Validate interval
        if config.interval < 1 or config.interval > 1440:
            raise HTTPException(
                status_code=400, 
                detail="Interval must be between 1 and 1440 minutes"
            )
        
        # Load current config
        config_path = os.path.join(os.path.dirname(__file__), '../../config/sync_config.json')
        with open(config_path, 'r') as f:
            current_config = json.load(f)
        
        # Update only allowed fields
        current_config['interval'] = config.interval
        if hasattr(config, 'enabled') and config.enabled is not None:
            current_config['enabled'] = config.enabled
        
        # Backup before writing
        backup_dir = os.path.join(os.path.dirname(config_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(
            backup_dir,
            f"sync_config.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )
        shutil.copy2(config_path, backup_path)
        
        # Write updated config
        with open(config_path, 'w') as f:
            json.dump(current_config, f, indent=2)
        
        return {
            "message": "Sync configuration updated",
            "config": current_config,
            "backup": backup_path
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))