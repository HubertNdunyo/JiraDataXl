"""
Database constants and shared configurations.
"""

# Column definitions for the issues table
# Column order must match create_tables.sql exactly
ISSUE_COLUMNS = [
    'issue_key',                  # 1
    'summary',                    # 2
    'status',                     # 3
    'ndpu_order_number',          # 4
    'ndpu_raw_photos',           # 5
    'dropbox_raw_link',          # 6
    'dropbox_edited_link',       # 7
    'same_day_delivery',         # 8
    'escalated_editing',         # 9
    'edited_media_revision_notes', # 10
    'ndpu_editing_team',         # 11
    'scheduled',                 # 12
    'acknowledged',              # 13
    'at_listing',               # 14
    'shoot_complete',           # 15
    'uploaded',                 # 16
    'edit_start',              # 17
    'final_review',            # 18
    'closed',                  # 19
    'ndpu_service',            # 20
    'project_name',            # 21
    'last_updated',            # 22
    'location_name',           # 23
    'ndpu_client_name',        # 24
    'ndpu_client_email',       # 25
    'ndpu_comments',           # 26
    'ndpu_editor_notes',       # 27
    'ndpu_access_instructions', # 28
    'ndpu_special_instructions' # 29
]