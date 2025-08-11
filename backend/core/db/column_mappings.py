"""
Column name mappings between database columns and field mapping keys
"""

# Map database column names to field mapping keys
COLUMN_TO_FIELD_MAPPING = {
    # Order details
    'ndpu_order_number': 'order_number',
    'ndpu_raw_photos': 'raw_photos',
    
    # Media links
    'dropbox_raw_link': 'dropbox_raw',
    'dropbox_edited_link': 'dropbox_edited',
    'ndpu_dropbox_raw': 'dropbox_raw',
    'ndpu_dropbox_edited': 'dropbox_edited',
    'ndpu_raw_media_folder': 'raw_media_folder',
    'ndpu_edited_media_folder': 'edited_media_folder',
    
    # Delivery options
    'same_day_delivery': 'same_day_delivery',
    'escalated_editing': 'escalated_editing',
    'ndpu_same_day_delivery': 'same_day_delivery',
    'ndpu_escalated_editing': 'escalated_editing',
    
    # Notes and revision
    'edited_media_revision_notes': 'edited_media_revision_notes',
    'ndpu_edited_media_revision_notes': 'edited_media_revision_notes',
    'ndpu_editing_revision_notes': 'editing_revision_notes',
    'ndpu_platform_escalation_notes': 'platform_escalation_notes',
    
    # Editing details
    'ndpu_editing_team': 'editing_team',
    'ndpu_editor_notes': 'editor_notes',
    
    # Service info
    'ndpu_service': 'service_type',
    'ndpu_service_type': 'service_type',
    
    # Client info
    'ndpu_client_name': 'client_name',
    'ndpu_client_email': 'client_email',
    
    # Location info
    'location_name': 'location_name',
    'ndpu_listing_address': 'listing_address',
    
    # Instructions
    'ndpu_comments': 'comments',
    'ndpu_access_instructions': 'access_instructions',
    'ndpu_special_instructions': 'special_instructions',
    
    # Timestamps (from transitions)
    'scheduled': 'scheduled',
    'acknowledged': 'acknowledged',
    'at_listing': 'at_listing',
    'shoot_complete': 'shoot_complete',
    'uploaded': 'uploaded',
    'edit_start': 'edit_start',
    'final_review': 'final_review',
    'closed': 'closed',
    'ndpu_at_listing_timestamp': 'at_listing',
    'ndpu_shoot_complete_timestamp': 'shoot_complete',
    'ndpu_uploaded_timestamp': 'uploaded',
    'ndpu_start_edit_timestamp': 'edit_start',
    'ndpu_mp_ready_timestamp': 'final_review',
    'ndpu_final_review_timestamp': 'final_review',
    'ndpu_closed_timestamp': 'closed',
    
    # System fields
    'summary': 'summary',
    'status': 'status',
    'updated': 'updated'
}

def get_field_key_for_column(column_name: str) -> str:
    """
    Get the field mapping key for a database column name.
    
    Args:
        column_name: Database column name
    
    Returns:
        Field mapping key to look up in configuration
    """
    return COLUMN_TO_FIELD_MAPPING.get(column_name, column_name)