"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class SyncStatus(str, Enum):
    """Sync operation status"""
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SyncConfig(BaseModel):
    """Sync configuration"""
    interval_minutes: int = Field(ge=1, le=1440, description="Sync interval in minutes")
    enabled: bool = Field(default=True, description="Whether automatic sync is enabled")
    
    model_config = ConfigDict(from_attributes=True)


class SyncStartRequest(BaseModel):
    """Request to start sync"""
    force: bool = Field(default=False, description="Force sync even if one is running")


class SyncResponse(BaseModel):
    """Generic sync operation response"""
    success: bool
    message: str
    sync_id: Optional[str] = None


class SyncProgress(BaseModel):
    """Current sync progress"""
    status: SyncStatus
    current_project: int = 0
    total_projects: int = 0
    current_issues: int = 0
    total_issues: int = 0
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SyncStatistics(BaseModel):
    """Sync operation statistics"""
    sync_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    total_projects: int
    successful_projects: int
    failed_projects: int
    total_issues: int
    issues_per_second: Optional[float] = None
    status: SyncStatus
    error_message: Optional[str] = None


class SystemStatus(BaseModel):
    """Overall system status"""
    sync_status: SyncStatus
    sync_progress: Optional[SyncProgress] = None
    last_sync: Optional[SyncStatistics] = None
    next_sync_time: Optional[datetime] = None
    database_connected: bool
    jira_instances_connected: Dict[str, bool]
    system_health: str


class IssueSearchRequest(BaseModel):
    """Request to search for issues"""
    issue_key: str = Field(..., description="JIRA issue key (e.g., PROJ-123)")


class JiraField(BaseModel):
    """JIRA field information"""
    field_id: str
    field_name: str
    field_type: str
    value: Any
    instance: str


class JiraIssue(BaseModel):
    """JIRA issue details"""
    issue_key: str
    summary: str
    status: str
    issue_type: str
    created: datetime
    updated: datetime
    project_key: str
    instance: str
    fields: List[JiraField]
    url: str


class SyncHistoryFilter(BaseModel):
    """Filter options for sync history"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[SyncStatus] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SyncHistoryResponse(BaseModel):
    """Sync history response"""
    total: int
    items: List[SyncStatistics]
    has_more: bool


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)