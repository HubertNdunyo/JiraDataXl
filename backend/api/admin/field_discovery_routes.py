"""
Field discovery and caching routes for admin API
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, List
import logging
import os

from core.db.db_field_cache import FieldCacheManager
from core.jira import JiraClient
from core.jira.jira_client import JiraApiError

logger = logging.getLogger(__name__)
router = APIRouter()


# Import the admin key verification dependency
from ..admin_routes_v2 import verify_admin_key


@router.post("/discover")
async def discover_fields(authorized: bool = Depends(verify_admin_key)):
    """
    Discover and cache fields from both JIRA instances.
    This fetches all available fields and stores them for later use.
    """
    try:
        cache_manager = FieldCacheManager()
        results = {}
        
        # Process Instance 1
        instance_1_url = os.getenv('JIRA_URL_1')
        instance_1_username = os.getenv('JIRA_USERNAME_1')
        instance_1_password = os.getenv('JIRA_PASSWORD_1')
        
        if instance_1_url and instance_1_username and instance_1_password:
            try:
                client_1 = JiraClient(instance_1_url, instance_1_username, instance_1_password)
                fields_1 = client_1.get_fields()
                cache_manager.cache_fields('instance_1', fields_1)
                results['instance_1'] = {'discovered': len(fields_1), 'status': 'success'}
            except Exception as e:
                logger.error(f"Failed to discover fields from instance 1: {e}")
                results['instance_1'] = {'error': str(e), 'status': 'failed'}
        
        # Process Instance 2
        instance_2_url = os.getenv('JIRA_URL_2')
        instance_2_username = os.getenv('JIRA_USERNAME_2')
        instance_2_password = os.getenv('JIRA_PASSWORD_2')
        
        if instance_2_url and instance_2_username and instance_2_password:
            try:
                client_2 = JiraClient(instance_2_url, instance_2_username, instance_2_password)
                fields_2 = client_2.get_fields()
                cache_manager.cache_fields('instance_2', fields_2)
                results['instance_2'] = {'discovered': len(fields_2), 'status': 'success'}
            except Exception as e:
                logger.error(f"Failed to discover fields from instance 2: {e}")
                results['instance_2'] = {'error': str(e), 'status': 'failed'}
        
        # Get cache statistics
        stats = cache_manager.get_cache_stats()
        
        return {
            'success': True,
            'results': results,
            'cache_stats': stats,
            'message': 'Field discovery completed'
        }
        
    except Exception as e:
        logger.error(f"Field discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cached")
async def get_cached_fields(
    instance: Optional[str] = Query(None, pattern='^(instance_1|instance_2)$'),
    authorized: bool = Depends(verify_admin_key)
):
    """Get cached fields for one or both instances"""
    try:
        cache_manager = FieldCacheManager()
        
        if instance:
            fields = cache_manager.get_cached_fields(instance)
            return {
                instance: fields,
                'count': len(fields)
            }
        else:
            # Get fields for both instances
            fields_1 = cache_manager.get_cached_fields('instance_1')
            fields_2 = cache_manager.get_cached_fields('instance_2')
            
            return {
                'instance_1': {
                    'fields': fields_1,
                    'count': len(fields_1)
                },
                'instance_2': {
                    'fields': fields_2,
                    'count': len(fields_2)
                },
                'cache_stats': cache_manager.get_cache_stats()
            }
    except Exception as e:
        logger.error(f"Failed to get cached fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_fields(
    term: str = Query(..., min_length=2),
    instance: Optional[str] = Query(None, pattern='^(instance_1|instance_2)$'),
    authorized: bool = Depends(verify_admin_key)
):
    """Search for fields by name or ID"""
    try:
        cache_manager = FieldCacheManager()
        results = cache_manager.search_fields(term, instance)
        
        return {
            'search_term': term,
            'results': results,
            'count': len(results)
        }
    except Exception as e:
        logger.error(f"Field search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def suggest_field_mapping(
    field_name: str = Query(..., min_length=1),
    source_instance: str = Query(..., pattern='^(instance_1|instance_2)$'),
    authorized: bool = Depends(verify_admin_key)
):
    """Get field mapping suggestions based on field name"""
    try:
        cache_manager = FieldCacheManager()
        target_instance = 'instance_2' if source_instance == 'instance_1' else 'instance_1'
        
        suggestions = cache_manager.suggest_field_mapping(field_name, source_instance, target_instance)
        
        return {
            'field_name': field_name,
            'source_instance': source_instance,
            'target_instance': target_instance,
            'suggestions': suggestions
        }
    except Exception as e:
        logger.error(f"Failed to suggest field mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_field_data(
    field_id: str = Query(..., min_length=1),
    instance: str = Query(..., pattern='^(instance_1|instance_2)$'),
    limit: int = Query(5, ge=1, le=10),
    authorized: bool = Depends(verify_admin_key)
):
    """Preview sample data for a specific field"""
    try:
        # Get JIRA credentials
        url = os.getenv(f'JIRA_URL_{instance[-1]}')
        username = os.getenv(f'JIRA_USERNAME_{instance[-1]}')
        password = os.getenv(f'JIRA_PASSWORD_{instance[-1]}')
        
        if not all([url, username, password]):
            raise HTTPException(
                status_code=400,
                detail=f"Missing JIRA credentials for {instance}"
            )
        
        # Create JIRA client
        client = JiraClient(url, username, password)
        
        # Build JQL to get recent issues
        jql = "project is not empty ORDER BY updated DESC"
        
        try:
            # Fetch recent issues
            issues = client.search_issues(jql, max_results=limit, fields=[field_id])
            
            # Extract field values
            preview_data = []
            for issue in issues:
                field_value = issue.get('fields', {}).get(field_id)
                if field_value is not None:
                    preview_data.append({
                        'issue_key': issue.get('key'),
                        'value': field_value
                    })
            
            # Get field info from cache
            cache_manager = FieldCacheManager()
            field_info = cache_manager.get_field_info(instance, field_id)
            
            return {
                'field_id': field_id,
                'field_info': field_info,
                'instance': instance,
                'preview_data': preview_data,
                'sample_count': len(preview_data)
            }
            
        except JiraApiError as e:
            logger.error(f"JIRA API error during field preview: {e}")
            raise HTTPException(status_code=400, detail=f"JIRA API error: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview field data: {e}")
        raise HTTPException(status_code=500, detail=str(e))