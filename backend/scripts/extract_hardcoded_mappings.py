#!/usr/bin/env python3
"""
Extract all hardcoded field mappings from jira_issues.py
This script documents the current legacy field extraction logic.
"""

import json
import re
from pathlib import Path

def extract_hardcoded_mappings():
    """Extract all hardcoded field references from jira_issues.py"""
    
    # Read the jira_issues.py file
    jira_issues_path = Path(__file__).parent.parent / "core" / "jira" / "jira_issues.py"
    
    with open(jira_issues_path, 'r') as f:
        content = f.read()
    
    # Extract all customfield references
    customfield_pattern = r"customfield_\d+"
    customfields = re.findall(customfield_pattern, content)
    
    # Manual mapping based on code analysis
    hardcoded_mappings = {
        "field_groups": {
            "Legacy Core Fields": {
                "description": "Fields extracted from hardcoded jira_issues.py",
                "fields": {
                    # Basic fields (system fields)
                    "issue_key": {
                        "type": "string",
                        "system_field": True,
                        "field_path": "key",
                        "description": "JIRA Issue Key"
                    },
                    "summary": {
                        "type": "string", 
                        "system_field": True,
                        "field_path": "fields.summary",
                        "description": "Issue Summary"
                    },
                    "status": {
                        "type": "string",
                        "system_field": True,
                        "field_path": "fields.status.name",
                        "description": "Issue Status"
                    },
                    "project_name": {
                        "type": "string",
                        "system_field": True,
                        "field_path": "fields.project.key",
                        "description": "Project Key"
                    },
                    "last_updated": {
                        "type": "datetime",
                        "system_field": True,
                        "field_path": "fields.updated",
                        "description": "Last Updated Timestamp"
                    },
                    
                    # Order fields (line 210)
                    "ndpu_order_number": {
                        "type": "string",
                        "line": 210,
                        "instance_1": {"field_id": "customfield_10501"},
                        "instance_2": {"field_id": "customfield_10501"},  # Assumed same
                        "description": "NDPU Order Number"
                    },
                    
                    # Raw photos (lines 212-215)
                    "ndpu_raw_photos": {
                        "type": "integer",
                        "line": "212-215",
                        "instance_1": {"field_id": "customfield_12581"},
                        "instance_2": {"field_id": "customfield_12602"},
                        "description": "Number of Raw Photos",
                        "notes": "Tries multiple field IDs"
                    },
                    
                    # Dropbox links (lines 218-219)
                    "dropbox_raw_link": {
                        "type": "string",
                        "line": 218,
                        "instance_1": {"field_id": "customfield_10713"},
                        "instance_2": {"field_id": "customfield_10713"},
                        "description": "Dropbox Raw Media Link"
                    },
                    "dropbox_edited_link": {
                        "type": "string",
                        "line": 219,
                        "instance_1": {"field_id": "customfield_10714"},
                        "instance_2": {"field_id": "customfield_10714"},
                        "description": "Dropbox Edited Media Link"
                    },
                    
                    # Delivery fields (lines 222-224)
                    "same_day_delivery": {
                        "type": "boolean",
                        "line": "222-224",
                        "instance_1": {"field_id": "customfield_12661"},
                        "instance_2": {"field_id": "customfield_12661"},
                        "description": "Same Day Delivery Flag",
                        "notes": "Extracts from dict value"
                    },
                    
                    # Editing fields (lines 226-227)
                    "escalated_editing": {
                        "type": "boolean",
                        "line": 226,
                        "instance_1": {"field_id": "customfield_11712"},
                        "instance_2": {"field_id": "customfield_11712"},
                        "description": "Escalated Editing Flag"
                    },
                    "edited_media_revision_notes": {
                        "type": "string",
                        "line": 227,
                        "instance_1": {"field_id": "customfield_10716"},
                        "instance_2": {"field_id": "customfield_10716"},
                        "description": "Revision Notes"
                    },
                    
                    # Team field (lines 230-234)
                    "ndpu_editing_team": {
                        "type": "string",
                        "line": "230-234",
                        "instance_1": {"field_id": "customfield_12644"},
                        "instance_2": {"field_id": "customfield_12648"},
                        "description": "Editing Team",
                        "notes": "Tries multiple field IDs"
                    },
                    
                    # Service field (lines 237-240)
                    "ndpu_service": {
                        "type": "string",
                        "line": "237-240",
                        "instance_1": {"field_id": "customfield_11104"},
                        "instance_2": {"field_id": "customfield_11700"},
                        "description": "Service Type",
                        "notes": "Falls back to second field"
                    },
                    
                    # Client fields (lines 243-245)
                    "ndpu_client_name": {
                        "type": "string",
                        "line": 243,
                        "instance_1": {"field_id": "customfield_10600"},
                        "instance_2": {"field_id": "customfield_10600"},
                        "description": "Client Name"
                    },
                    "ndpu_client_email": {
                        "type": "string",
                        "line": 244,
                        "instance_1": {"field_id": "customfield_10601"},
                        "instance_2": {"field_id": "customfield_10601"},
                        "description": "Client Email"
                    },
                    "ndpu_listing_address": {
                        "type": "string",
                        "line": 245,
                        "instance_1": {"field_id": "customfield_10603"},
                        "instance_2": {"field_id": "customfield_10603"},
                        "description": "Listing Address"
                    },
                    
                    # Comments and notes (lines 247-248)
                    "ndpu_comments": {
                        "type": "string",
                        "line": 247,
                        "instance_1": {"field_id": "customfield_10612"},
                        "instance_2": {"field_id": "customfield_10612"},
                        "description": "Comments"
                    },
                    "ndpu_editor_notes": {
                        "type": "string",
                        "line": 248,
                        "instance_1": {"field_id": "customfield_11601"},
                        "instance_2": {"field_id": "customfield_11601"},
                        "description": "Editor Notes"
                    },
                    
                    # Combined instruction fields (lines 251-263)
                    "ndpu_access_instructions": {
                        "type": "string",
                        "line": "251-256",
                        "instance_1": {"field_ids": ["customfield_10700", "customfield_12594", "customfield_12611"]},
                        "instance_2": {"field_ids": ["customfield_10700", "customfield_12594", "customfield_12611"]},
                        "description": "Access Instructions",
                        "notes": "Combines multiple fields with space"
                    },
                    "ndpu_special_instructions": {
                        "type": "string",
                        "line": "258-263",
                        "instance_1": {"field_ids": ["customfield_11100", "customfield_12595", "customfield_12612"]},
                        "instance_2": {"field_ids": ["customfield_11100", "customfield_12595", "customfield_12612"]},
                        "description": "Special Instructions",
                        "notes": "Combines multiple fields with space"
                    },
                    
                    # Workflow timestamps (from transitions, lines 281-289)
                    "scheduled": {
                        "type": "datetime",
                        "source": "transitions",
                        "description": "Scheduled Timestamp"
                    },
                    "acknowledged": {
                        "type": "datetime",
                        "source": "transitions",
                        "description": "Acknowledged Timestamp"
                    },
                    "at_listing": {
                        "type": "datetime",
                        "source": "transitions",
                        "description": "At Listing Timestamp"
                    },
                    "shoot_complete": {
                        "type": "datetime",
                        "source": "transitions",
                        "description": "Shoot Complete Timestamp"
                    },
                    "uploaded": {
                        "type": "datetime",
                        "source": "transitions",
                        "description": "Uploaded Timestamp"
                    },
                    "edit_start": {
                        "type": "datetime",
                        "source": "transitions",
                        "description": "Edit Start Timestamp"
                    },
                    "final_review": {
                        "type": "datetime",
                        "source": "transitions",
                        "description": "Final Review Timestamp"
                    },
                    "closed": {
                        "type": "datetime",
                        "source": "transitions",
                        "description": "Closed Timestamp"
                    },
                    
                    # Location name (line 292, uses project mapping)
                    "location_name": {
                        "type": "string",
                        "source": "project_mapping",
                        "description": "Location Name",
                        "notes": "Derived from project name"
                    }
                }
            }
        }
    }
    
    # Save to file
    output_path = Path(__file__).parent.parent / "config" / "legacy_field_mappings.json"
    with open(output_path, 'w') as f:
        json.dump(hardcoded_mappings, f, indent=2)
    
    print(f"✅ Extracted hardcoded mappings saved to: {output_path}")
    
    # Generate summary
    print("\n📊 Summary of Hardcoded Field Mappings:")
    print("=" * 50)
    
    fields = hardcoded_mappings["field_groups"]["Legacy Core Fields"]["fields"]
    
    # Count by type
    type_counts = {}
    for field, config in fields.items():
        field_type = config.get("type", "unknown")
        type_counts[field_type] = type_counts.get(field_type, 0) + 1
    
    print("\nField Types:")
    for field_type, count in sorted(type_counts.items()):
        print(f"  - {field_type}: {count} fields")
    
    # List unique custom fields
    all_customfields = set()
    for field, config in fields.items():
        if "instance_1" in config:
            if "field_id" in config["instance_1"]:
                if config["instance_1"]["field_id"].startswith("customfield"):
                    all_customfields.add(config["instance_1"]["field_id"])
            elif "field_ids" in config["instance_1"]:
                for fid in config["instance_1"]["field_ids"]:
                    if fid.startswith("customfield"):
                        all_customfields.add(fid)
        
        if "instance_2" in config:
            if "field_id" in config["instance_2"]:
                if config["instance_2"]["field_id"].startswith("customfield"):
                    all_customfields.add(config["instance_2"]["field_id"])
            elif "field_ids" in config["instance_2"]:
                for fid in config["instance_2"]["field_ids"]:
                    if fid.startswith("customfield"):
                        all_customfields.add(fid)
    
    print(f"\nUnique Custom Fields Referenced: {len(all_customfields)}")
    for cf in sorted(all_customfields):
        print(f"  - {cf}")
    
    # Fields with special handling
    special_fields = []
    for field, config in fields.items():
        if "notes" in config:
            special_fields.append(f"{field}: {config['notes']}")
    
    if special_fields:
        print("\nFields with Special Handling:")
        for sf in special_fields:
            print(f"  - {sf}")
    
    print("\n✅ Analysis complete!")
    return hardcoded_mappings

if __name__ == "__main__":
    extract_hardcoded_mappings()