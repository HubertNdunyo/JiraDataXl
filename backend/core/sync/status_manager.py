"""
Status transition and workflow management.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from ..db import log_operation

# Configure logging
logger = logging.getLogger(__name__)

class StatusError(Exception):
    """Exception for status-related errors"""
    pass

class StatusManager:
    """
    Manages status transitions and workflow validation.
    """
    
    def __init__(self):
        """Initialize status manager."""
        # Status mapping for timestamp extraction
        self.status_mapping = {
            'acknowledged': {
                'acknowledged', 'ack', 'acknowledged by agent',
                'acknowledged', 'ACKNOWLEDGED'
            },
            'at_listing': {
                'at listing', 'listing', 'at_listing', 'At Listing'
            },
            'shoot_complete': {
                'shoot complete', 'shooting complete',
                'shoot_complete', 'Shoot Complete'
            },
            'uploaded': {
                'uploaded', 'upload complete',
                'upload_complete', 'Uploaded'
            },
            'edit_start': {
                'edit start', 'editing started',
                'edit_start', 'Edit'
            },
            'final_review': {
                'final review', 'final_review',
                'pending review', 'Final Review',
                'Managing Partner Ready'
            },
            'escalated_editing': {
                'escalated editing', 'Escalated Editing'
            },
            'closed': {
                'closed', 'complete', 'completed',
                'done', 'Closed'
            }
        }

    def process_transitions(
        self,
        issue_key: str,
        changelog: Dict[str, Any]
    ) -> Dict[str, Optional[datetime]]:
        """
        Process status transitions from changelog.
        
        Args:
            issue_key: Issue identifier
            changelog: Issue changelog data
            
        Returns:
            Dict mapping transition names to timestamps
        """
        transitions = {
            "scheduled": None,
            "acknowledged": None,
            "at_listing": None,
            "shoot_complete": None,
            "uploaded": None,
            "edit_start": None,
            "final_review": None,
            "escalated_editing": None,
            "closed": None
        }
        
        try:
            if not changelog:
                return transitions

            for history in changelog.get('histories', []):
                created = history.get('created')
                if not created:
                    continue
                    
                created_date = datetime.fromisoformat(
                    created.replace('Z', '+00:00')
                )
                
                for item in history.get('items', []):
                    if item.get('field') == 'status':
                        to_status = item.get('toString', '').strip()
                        
                        # Check against mapped statuses
                        for transition_key, valid_statuses in self.status_mapping.items():
                            if to_status.lower() in {s.lower() for s in valid_statuses}:
                                if (transitions[transition_key] is None or
                                    created_date > transitions[transition_key]):
                                    transitions[transition_key] = created_date
                                    
                                    # Log transition
                                    log_operation(
                                        'STATUS_CHANGE',
                                        'ISSUE',
                                        issue_key,
                                        details={
                                            'status': to_status,
                                            'transition_type': transition_key,
                                            'timestamp': created_date.isoformat()
                                        }
                                    )
                                break

        except Exception as e:
            logger.error(f"Error processing transitions for {issue_key}: {e}")
            
        return transitions

    def get_current_status(
        self,
        transitions: Dict[str, Optional[datetime]]
    ) -> Optional[str]:
        """
        Get the current status based on transitions.
        
        Args:
            transitions: Dict of transitions and their timestamps
            
        Returns:
            Current status or None if no transitions
        """
        latest_status = None
        latest_time = None
        
        for status, timestamp in transitions.items():
            if timestamp and (latest_time is None or timestamp > latest_time):
                latest_status = status
                latest_time = timestamp
                
        return latest_status

    def get_time_in_status(
        self,
        transitions: Dict[str, Optional[datetime]],
        status: str
    ) -> Optional[float]:
        """
        Calculate time spent in a specific status.
        
        Args:
            transitions: Dict of transitions and their timestamps
            status: Status to calculate time for
            
        Returns:
            Time in seconds or None if status not found
        """
        if status not in transitions or transitions[status] is None:
            return None
            
        start_time = transitions[status]
        
        # Find the next transition after this status
        next_time = None
        for s, t in transitions.items():
            if (t and t > start_time and
                (next_time is None or t < next_time)):
                next_time = t
                
        if next_time:
            return (next_time - start_time).total_seconds()
            
        # If no next transition, calculate time until now
        return (datetime.now() - start_time).total_seconds()