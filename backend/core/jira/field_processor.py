"""
Field processing and validation functionality.
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from dateutil import parser

# Configure logging
logger = logging.getLogger(__name__)

# Mapping of transition names to accepted status values
STATUS_MAPPING = {
    "scheduled": [
        "scheduled",
        "Scheduled",
    ],
    "acknowledged": [
        "acknowledged",
        "ACKNOWLEDGED",
        "Acknowledged",
        "ack",
        "acknowledged by agent",
    ],
    "at_listing": [
        "at listing",
        "At Listing",
        "AT LISTING",
        "listing",
        "at_listing",
    ],
    "shoot_complete": [
        "shoot complete",
        "Shoot Complete",
        "SHOOT COMPLETE",
        "shooting complete",
        "shoot_complete",
    ],
    "uploaded": [
        "uploaded",
        "Uploaded",
        "UPLOADED",
        "upload complete",
        "upload_complete",
    ],
    "edit_start": [
        "edit start",
        "Edit Start",
        "Edit",
        "EDIT",
        "editing started",
        "edit_start",
    ],
    "final_review": [
        "final review",
        "Final Review",
        "Managing Partner Ready",
        "final_review",
        "pending review",
    ],
    "escalated_editing": [
        "escalated editing",
        "Escalated Editing",
    ],
    "closed": [
        "closed",
        "Closed",
        "CLOSED",
        "Complete",
        "Done",
        "complete",
        "completed",
        "done",
    ],
}

class FieldProcessingError(Exception):
    """Exception for field processing errors"""
    pass

class FieldProcessor:
    """
    Handles field mapping, validation, and transformation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize field processor.
        
        Args:
            config_path: Path to field mapping configuration file
        """
        self.config_path = config_path
        self.config = self._load_config(config_path) if config_path else {}
        self.field_cache: Dict[str, Dict] = {}

    def _load_config(self, config_path: str) -> Dict:
        """
        Load field mapping configuration.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dict containing field configuration
            
        Raises:
            FieldProcessingError: If config loading fails
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load field configuration: {e}")
            raise FieldProcessingError(f"Config loading failed: {e}")

    def get_field_mapping(
        self,
        field_name: str,
        instance_type: str
    ) -> Optional[Dict]:
        """
        Get field mapping for an instance.
        
        Args:
            field_name: Field name to look up
            instance_type: Type of JIRA instance
            
        Returns:
            Dict containing field mapping or None if not found
        """
        cache_key = f"{instance_type}:{field_name}"
        
        if cache_key in self.field_cache:
            return self.field_cache[cache_key]
            
        mapping = None
        for group in self.config.get('field_groups', {}).values():
            for field, config in group.get('fields', {}).items():
                if field == field_name:
                    instance_config = config.get(instance_type)
                    if instance_config:
                        mapping = {
                            'field_id': instance_config['field_id'],
                            'type': config.get('type', 'string'),
                            'required': config.get('required', False),
                            'combine': config.get('combine', False)
                        }
                        break
        
        self.field_cache[cache_key] = mapping
        return mapping

    def sanitize_value(
        self,
        value: Any,
        data_type: str,
        field_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        Sanitize and validate field value.
        
        Args:
            value: Value to sanitize
            data_type: Expected data type
            field_name: Field name for logging
            
        Returns:
            Sanitized value or None if invalid
        """
        if value is None:
            return None

        try:
            if data_type == 'string':
                return str(value).strip() if value else None
                
            elif data_type == 'integer':
                if isinstance(value, (int, float)):
                    return int(value)
                if isinstance(value, str):
                    # Handle common non-numeric cases
                    if value.lower() in ('zip', 'none', 'n/a', '-'):
                        return None
                    # Try to extract first number from string
                    import re
                    match = re.search(r'\d+', value)
                    if match:
                        return int(match.group())
                    return None
                return None
                
            elif data_type == 'float':
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    return float(value.replace(',', ''))
                return None
                
            elif data_type == 'boolean':
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    # Only convert known boolean string values
                    val = value.lower().strip()
                    if val in {'yes', 'true', '1', 'y', 'on'}:
                        return True
                    if val in {'no', 'false', '0', 'n', 'off'}:
                        return False
                    # If string doesn't match known boolean values, return None
                    return None
                if isinstance(value, (int, float)):
                    return bool(value)
                # For any other type, return None to avoid incorrect conversions
                return None
                
            elif data_type == 'datetime':
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    return parser.parse(value)
                return None
                
            elif data_type == 'json':
                if isinstance(value, (dict, list)):
                    return value
                if isinstance(value, str):
                    return json.loads(value)
                return None
                
            return value
            
        except Exception as e:
            logger.debug(
                f"Sanitization error for {field_name or 'unknown field'} "
                f"({data_type}): {value} - {e}"
            )
            return None

    def process_field(
        self,
        field_name: str,
        raw_value: Any,
        instance_type: str
    ) -> Optional[Any]:
        """
        Process a field value using its configuration.
        
        Args:
            field_name: Name of the field
            raw_value: Raw field value
            instance_type: Type of JIRA instance
            
        Returns:
            Processed field value or None if invalid
        """
        mapping = self.get_field_mapping(field_name, instance_type)
        if not mapping:
            return None
            
        value = self.sanitize_value(
            raw_value,
            mapping['type'],
            field_name
        )
        
        if mapping['required'] and value is None:
            logger.warning(
                f"Required field {field_name} has null value: {raw_value}"
            )
            
        return value

    def extract_field_value(
        self,
        fields: Dict[str, Any],
        field_id: Union[str, list],
        default: Any = None
    ) -> Any:
        """
        Extract a value from JIRA issue fields.
        
        Args:
            fields: Dictionary of issue fields
            field_id: Field identifier or list of identifiers for combined fields
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        try:
            # Handle combined fields
            if isinstance(field_id, list):
                values = []
                for fid in field_id:
                    val = self.extract_field_value(fields, fid)
                    if val:
                        values.append(str(val))
                return ' '.join(values) if values else default

            # Handle nested fields
            if '.' in str(field_id):
                parts = field_id.split('.')
                value = fields
                for part in parts:
                    if value is None:
                        return default
                    value = value.get(part)
                return value if value is not None else default

            return fields.get(field_id, default)
        except (AttributeError, KeyError) as e:
            logger.debug(f"Field {field_id} not found: {e}")
            return default

    def validate_required_fields(
        self,
        fields: Dict[str, Any],
        instance_type: str
    ) -> bool:
        """
        Validate all required fields are present.
        
        Args:
            fields: Dictionary of field values
            instance_type: Type of JIRA instance
            
        Returns:
            bool: True if all required fields are valid
        """
        for group in self.config.get('field_groups', {}).values():
            for field_name, config in group.get('fields', {}).items():
                if config.get('required'):
                    mapping = self.get_field_mapping(field_name, instance_type)
                    if not mapping:
                        continue
                        
                    value = self.extract_field_value(
                        fields,
                        mapping['field_id']
                    )
                    if self.sanitize_value(
                        value,
                        mapping['type'],
                        field_name
                    ) is None:
                        logger.warning(
                            f"Required field {field_name} is invalid: {value}"
                        )
                        return False
                        
        return True

    def get_field_type(
        self,
        field_name: str,
        instance_type: str
    ) -> Optional[str]:
        """
        Get the type of a field.
        
        Args:
            field_name: Name of the field
            instance_type: Type of JIRA instance
            
        Returns:
            Field type string or None if not found
        """
        mapping = self.get_field_mapping(field_name, instance_type)
        return mapping['type'] if mapping else None

    def process_issue_transitions(
        self,
        issue_key: str,
        changelog: Dict[str, Any]
    ) -> Dict[str, Optional[datetime]]:
        """
        Process issue status transitions from changelog.
        
        Args:
            issue_key: JIRA issue key
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
                created_date = self.sanitize_value(
                    history.get('created'),
                    'datetime',
                    'transition_date'
                )
                if not created_date:
                    continue
                
                for item in history.get('items', []):
                    if item.get('field') == 'status':
                        to_status = item.get('toString', '').strip()
                        # Check against mapped statuses (case-insensitive)
                        for transition_key, valid_statuses in STATUS_MAPPING.items():
                            if to_status in valid_statuses:
                                if transitions[transition_key] is None or created_date > transitions[transition_key]:
                                    transitions[transition_key] = created_date
                                break

        except Exception as e:
            logger.error(f"Error processing transitions for {issue_key}: {e}")
        
        return transitions
