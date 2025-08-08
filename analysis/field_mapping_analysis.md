# JIRA Custom Field Mapping Analysis

## Overview
This document analyzes the custom field mappings between two JIRA instances:
- **Instance 1**: betteredits.atlassian.net (sampledata1.md)
- **Instance 2**: betteredits2.atlassian.net (sampledata2.md)

## Key Custom Fields Comparison

### NDPU Editing Team
- **Instance 1**: customfield_12644
- **Instance 2**: customfield_12648
- **Field Type**: textfield
- **Sample Value**: "EDUPlus"

### NDPU Number of Raw Photos
- **Instance 1**: customfield_12581
- **Instance 2**: customfield_12602
- **Field Type**: textfield
- **Sample Values**: "50" (Instance 1), "7" (Instance 2)

### NDPU Raw Media Folder Link
- **Instance 1**: customfield_10713
- **Instance 2**: customfield_10713
- **Field Type**: textfield
- **Note**: Same field ID in both instances

### NDPU Edited Media Folder Link
- **Instance 1**: customfield_10714
- **Instance 2**: customfield_10714
- **Field Type**: textfield
- **Note**: Same field ID in both instances

### Client Information Fields

#### NDPU Client Name
- **Instance 1**: customfield_10600
- **Instance 2**: customfield_10600
- **Field Type**: textfield
- **Note**: Same field ID in both instances

#### NDPU Client email
- **Instance 1**: customfield_10601
- **Instance 2**: customfield_10601
- **Field Type**: textfield
- **Note**: Same field ID in both instances

#### NDPU Client Cell No.
- **Instance 1**: customfield_10602
- **Instance 2**: customfield_10602
- **Field Type**: textfield
- **Note**: Same field ID in both instances

### Service Details

#### NDPU Service
- **Instance 1**: customfield_11104
- **Instance 2**: customfield_11104
- **Field Type**: textfield
- **Sample Values**: "Photo Package" (Instance 1), "Aerial Photos" (Instance 2)
- **Note**: Same field ID in both instances

#### NDPU Order Number
- **Instance 1**: customfield_10501
- **Instance 2**: customfield_10501
- **Field Type**: textfield
- **Note**: Same field ID in both instances

### Timestamp Fields

#### NDPU At Listing Timestamp
- **Instance 1**: customfield_12584
- **Instance 2**: customfield_12609
- **Field Type**: datetime

#### NDPU Shoot Complete Timestamp
- **Instance 1**: customfield_12583
- **Instance 2**: customfield_12606
- **Field Type**: datetime

#### NDPU Uploaded Timestamp
- **Instance 1**: customfield_12585
- **Instance 2**: customfield_12608
- **Field Type**: datetime

#### NDPU Start Edit Timestamp
- **Instance 1**: customfield_12586
- **Instance 2**: customfield_12607
- **Field Type**: datetime

#### NDPU MP Ready Timestamp
- **Instance 1**: customfield_12587
- **Instance 2**: customfield_12610
- **Field Type**: datetime

#### NDPU Final Review Timestamp
- **Instance 1**: customfield_12689
- **Instance 2**: customfield_12703
- **Field Type**: datetime

#### NDPU Closed Timestamp
- **Instance 1**: customfield_12690
- **Instance 2**: customfield_12704
- **Field Type**: datetime

### Other Important Fields

#### NDPU Access Instructions
- **Instance 1**: customfield_12594
- **Instance 2**: customfield_12611
- **Field Type**: textarea

#### NDPU MediaPro ID
- **Instance 1**: customfield_12642
- **Instance 2**: customfield_12646
- **Field Type**: textfield

#### NDPU Google Map Link (URL type)
- **Instance 1**: customfield_12646
- **Instance 2**: customfield_12650
- **Field Type**: url

#### NDPU RelaHQ Upload Link
- **Instance 1**: customfield_12688
- **Instance 2**: customfield_12700
- **Field Type**: url

#### NDPU Number of Expected Output
- **Instance 1**: customfield_12698
- **Instance 2**: customfield_12713
- **Field Type**: textfield

#### webhook_token
- **Instance 1**: customfield_12643
- **Instance 2**: customfield_12647
- **Field Type**: textfield

## Fields Only in Instance 2

#### NDPU Special Instructions
- **Instance 2**: customfield_12612
- **Field Type**: textarea
- **Note**: This field doesn't appear in Instance 1

#### NDPU Reviewed
- **Instance 2**: customfield_12661
- **Field Type**: select
- **Note**: This field doesn't appear in Instance 1

## Common Fields (Same ID in Both Instances)
- customfield_10016: Approvals
- customfield_10100: Development
- customfield_10404: NDP201 - Processed Client Invoice List
- customfield_11600: NDPTE Raw and Edited File Location
- customfield_11900: NDPU Appointment Number
- customfield_10614: NDPU Booking Date
- customfield_10600: NDPU Client Name
- customfield_10601: NDPU Client email
- customfield_10602: NDPU Client Cell No.
- customfield_10714: NDPU Edited Media Folder Link
- customfield_10716: NDPU Edited Media Revision Notes (only in Instance 1)
- customfield_12543: NDPU Folder Created
- customfield_11400: NDPU Google Map Link (textfield type)
- customfield_10603: NDPU Listing Address
- customfield_10707: NDPU Media Pro
- customfield_11602: NDPU Media Pro Mileage
- customfield_11601: NDPU Notes for Editor
- customfield_10501: NDPU Order Number
- customfield_10713: NDPU Raw Media Folder Link
- customfield_12521: NDPU Return Home Miles (only in Instance 1)
- customfield_12573: NDPU Same Day Delivery
- customfield_11104: NDPU Service
- customfield_12200: NDPU Shoot Date
- customfield_10711: NDPU Shoot Start Time
- customfield_10610: NDPU Square Footage
- customfield_10200: Organizations
- customfield_12540: PES - Aerial Details
- customfield_12542: PES - Edited Media Link
- customfield_12541: PES - Raw Media Link
- customfield_10022: Rank
- customfield_10021: Sprint
- customfield_10001: [CHART] Time in Status

## Summary of Required Mappings

The following fields need to be mapped between instances:

1. **NDPU Editing Team**: 12644 → 12648
2. **NDPU Number of Raw Photos**: 12581 → 12602
3. **NDPU At Listing Timestamp**: 12584 → 12609
4. **NDPU Shoot Complete Timestamp**: 12583 → 12606
5. **NDPU Uploaded Timestamp**: 12585 → 12608
6. **NDPU Start Edit Timestamp**: 12586 → 12607
7. **NDPU MP Ready Timestamp**: 12587 → 12610
8. **NDPU Final Review Timestamp**: 12689 → 12703
9. **NDPU Closed Timestamp**: 12690 → 12704
10. **NDPU Access Instructions**: 12594 → 12611
11. **NDPU MediaPro ID**: 12642 → 12646
12. **NDPU Google Map Link (URL)**: 12646 → 12650
13. **NDPU RelaHQ Upload Link**: 12688 → 12700
14. **NDPU Number of Expected Output**: 12698 → 12713
15. **webhook_token**: 12643 → 12647