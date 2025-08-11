"""
Project mapping and management functionality.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .db_core import execute_query, execute_batch, DatabaseOperationError

# Configure logging
logger = logging.getLogger(__name__)

class ProjectMappingError(Exception):
    """Custom exception for project mapping errors"""
    pass

def create_project_tables():
    """
    Create project-related database tables if they don't exist.
    
    Creates:
    - project_mappings_v2: Store project mappings
    - mapping_audit_log_v2: Track changes to mappings
    """
    try:
        # Create project_mappings_v2 table
        execute_query("""
            CREATE TABLE IF NOT EXISTS project_mappings_v2 (
                id SERIAL PRIMARY KEY,
                project_key VARCHAR(255) UNIQUE NOT NULL,
                location_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                auto_discovered BOOLEAN DEFAULT false,
                approved BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(255),
                approved_by VARCHAR(255),
                metadata JSONB
            );

            CREATE INDEX IF NOT EXISTS idx_project_mappings_v2_key 
            ON project_mappings_v2(project_key);
            
            CREATE INDEX IF NOT EXISTS idx_project_mappings_v2_active 
            ON project_mappings_v2(is_active);
        """)

        # Create mapping_audit_log_v2 table
        execute_query("""
            CREATE TABLE IF NOT EXISTS mapping_audit_log_v2 (
                id SERIAL PRIMARY KEY,
                project_key VARCHAR(255) NOT NULL,
                action VARCHAR(50) NOT NULL,
                old_value JSONB,
                new_value JSONB,
                performed_by VARCHAR(255),
                performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        logger.info("Project tables created successfully")
        
    except DatabaseOperationError as e:
        logger.error(f"Failed to create project tables: {e}")
        raise ProjectMappingError(f"Table creation failed: {e}")

def get_project_mapping(project_key: str) -> Optional[Dict]:
    """
    Get mapping for a project key.
    
    Args:
        project_key: Project identifier
        
    Returns:
        Dict containing project mapping or None if not found
    """
    try:
        result = execute_query("""
            SELECT project_key, location_name, is_active, approved, 
                   auto_discovered, created_at, updated_at, metadata
            FROM project_mappings_v2
            WHERE project_key = %s
        """, (project_key,), fetch=True)
        
        if result:
            return dict(zip([
                'project_key', 'location_name', 'is_active', 'approved',
                'auto_discovered', 'created_at', 'updated_at', 'metadata'
            ], result[0]))
        return None
        
    except DatabaseOperationError as e:
        logger.error(f"Error getting project mapping: {e}")
        raise ProjectMappingError(f"Failed to get project mapping: {e}")

def add_project_mapping(
    project_key: str,
    location_name: str,
    created_by: Optional[str] = None,
    auto_discovered: bool = False,
    metadata: Optional[Dict] = None
) -> bool:
    """
    Add new project mapping.
    
    Args:
        project_key: Project identifier
        location_name: Location name for the project
        created_by: Username of creator
        auto_discovered: Whether project was auto-discovered
        metadata: Additional project metadata
        
    Returns:
        bool: True if mapping was added successfully
    """
    try:
        # Get existing mapping for audit log
        old_value = None
        result = execute_query(
            "SELECT location_name, metadata FROM project_mappings_v2 WHERE project_key = %s",
            (project_key,),
            fetch=True
        )
        if result:
            old_value = {'location_name': result[0][0], 'metadata': result[0][1]}
        
        # Insert new mapping
        result = execute_query("""
            INSERT INTO project_mappings_v2 
            (project_key, location_name, auto_discovered, approved, created_by, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_key) DO NOTHING
            RETURNING id
        """, (
            project_key, location_name, auto_discovered, not auto_discovered,
            created_by, json.dumps(metadata) if metadata else None
        ), fetch=True)
        
        if result:
            # Log the addition
            execute_query("""
                INSERT INTO mapping_audit_log_v2 
                (project_key, action, old_value, new_value, performed_by)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                project_key,
                'CREATE',
                json.dumps(old_value) if old_value else None,
                json.dumps({
                    'location_name': location_name,
                    'metadata': metadata
                }),
                created_by
            ))
            
            return True
        return False
        
    except DatabaseOperationError as e:
        logger.error(f"Error adding project mapping: {e}")
        raise ProjectMappingError(f"Failed to add project mapping: {e}")

def update_project_mapping(
    project_key: str,
    location_name: str,
    approved: bool = False,
    approved_by: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> bool:
    """
    Update existing project mapping.
    
    Args:
        project_key: Project identifier
        location_name: New location name
        approved: Whether mapping is approved
        approved_by: Username of approver
        metadata: Updated metadata
        
    Returns:
        bool: True if mapping was updated successfully
    """
    try:
        # Get existing mapping for audit log
        old_value = None
        result = execute_query(
            "SELECT location_name, metadata FROM project_mappings_v2 WHERE project_key = %s",
            (project_key,),
            fetch=True
        )
        if result:
            old_value = {'location_name': result[0][0], 'metadata': result[0][1]}
        
        # Update mapping
        result = execute_query("""
            UPDATE project_mappings_v2
            SET location_name = %s,
                approved = %s,
                approved_by = CASE WHEN %s THEN %s ELSE approved_by END,
                metadata = COALESCE(%s, metadata),
                updated_at = CURRENT_TIMESTAMP
            WHERE project_key = %s
            RETURNING id
        """, (
            location_name,
            approved,
            approved,
            approved_by,
            json.dumps(metadata) if metadata else None,
            project_key
        ), fetch=True)
        
        if result:
            # Log the update
            execute_query("""
                INSERT INTO mapping_audit_log_v2 
                (project_key, action, old_value, new_value, performed_by)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                project_key,
                'UPDATE',
                json.dumps(old_value) if old_value else None,
                json.dumps({
                    'location_name': location_name,
                    'metadata': metadata,
                    'approved': approved
                }),
                approved_by if approved else None
            ))
            
            return True
        return False
        
    except DatabaseOperationError as e:
        logger.error(f"Error updating project mapping: {e}")
        raise ProjectMappingError(f"Failed to update project mapping: {e}")

def get_all_project_mappings(include_inactive: bool = False) -> List[Dict]:
    """
    Get all project mappings.
    
    Args:
        include_inactive: Whether to include inactive projects
        
    Returns:
        List of project mapping dictionaries
    """
    try:
        query = """
            SELECT project_key, location_name, is_active, approved,
                   auto_discovered, created_at, updated_at, metadata
            FROM project_mappings_v2
        """
        if not include_inactive:
            query += " WHERE is_active = true"
        query += " ORDER BY created_at DESC"
        
        result = execute_query(query, fetch=True)
        
        columns = [
            'project_key', 'location_name', 'is_active', 'approved',
            'auto_discovered', 'created_at', 'updated_at', 'metadata'
        ]
        return [dict(zip(columns, row)) for row in result] if result else []
        
    except DatabaseOperationError as e:
        logger.error(f"Error getting all project mappings: {e}")
        raise ProjectMappingError(f"Failed to get project mappings: {e}")

def get_project_stats(project_key: str) -> Dict:
    """
    Get statistics for a specific project.
    
    Args:
        project_key: Project identifier
        
    Returns:
        Dict containing project statistics
    """
    try:
        result = execute_query("""
            SELECT 
                COUNT(*) as total_issues,
                MAX(last_updated) as last_sync,
                COUNT(CASE WHEN closed IS NOT NULL THEN 1 END) as closed_issues,
                COUNT(CASE WHEN status = 'In Progress' THEN 1 END) as in_progress
            FROM jira_issues_v2 
            WHERE project_name = %s
        """, (project_key,), fetch=True)
        
        if result:
            return dict(zip(
                ['total_issues', 'last_sync', 'closed_issues', 'in_progress'],
                result[0]
            ))
        return {}
        
    except DatabaseOperationError as e:
        logger.error(f"Error fetching stats for project {project_key}: {e}")
        raise ProjectMappingError(f"Failed to get project stats: {e}")