# JIRA Fields Analysis

## Primary JIRA (https://betteredits.atlassian.net)

### System Fields

| Field ID | Name | Type |
| --- | --- | --- |
| versions | Affects versions | array |
| assignee | Assignee | user |
| attachment | Attachment | array |
| comment | Comment | comments-page |
| components | Components | array |
| created | Created | datetime |
| creator | Creator | user |
| description | Description | string |
| duedate | Due date | date |
| environment | Environment | string |
| fixVersions | Fix versions | array |
| thumbnail | Images |  |
| issuetype | Issue Type | issuetype |
| issuekey | Key |  |
| labels | Labels | array |
| lastViewed | Last Viewed | datetime |
| issuelinks | Linked Issues | array |
| worklog | Log Work | array |
| timeoriginalestimate | Original estimate | number |
| parent | Parent |  |
| priority | Priority | priority |
| progress | Progress | progress |
| project | Project | project |
| timeestimate | Remaining Estimate | number |
| reporter | Reporter | user |
| resolution | Resolution | resolution |
| resolutiondate | Resolved | datetime |
| issuerestriction | Restrict to | issuerestriction |
| security | Security Level | securitylevel |
| status | Status | status |
| statusCategory | Status Category |  |
| statuscategorychangedate | Status Category Changed | datetime |
| subtasks | Sub-tasks | array |
| summary | Summary | string |
| timespent | Time Spent | number |
| timetracking | Time tracking | timetracking |
| updated | Updated | datetime |
| votes | Votes | votes |
| watches | Watchers | watches |
| workratio | Work Ratio | number |
| aggregatetimeoriginalestimate | Σ Original Estimate | number |
| aggregateprogress | Σ Progress | progress |
| aggregatetimeestimate | Σ Remaining Estimate | number |
| aggregatetimespent | Σ Time Spent | number |

### Custom Fields

| Field ID | Name | Type |
| --- | --- | --- |
| customfield_11401 | Address Google Map Link | string |
| customfield_11402 | Address test link | string |
| customfield_12670 | Affected services | array |
| customfield_10016 | Approvals | sd-approvals |
| customfield_12669 | Approver groups | array |
| customfield_10027 | Approvers | array |
| customfield_10403 | Attachment Links | string |
| customfield_10613 | Branch | string |
| customfield_12629 | CAB | array |
| customfield_12679 | Category | option |
| customfield_12105 | Change completion date | datetime |
| customfield_12628 | Change managers | array |
| customfield_12103 | Change reason | option |
| customfield_12102 | Change risk | option |
| customfield_12104 | Change start date | datetime |
| customfield_12101 | Change type | option |
| customfield_10023 | Customer Request Type | sd-customerrequesttype |
| customfield_12691 | Design | array |
| customfield_10100 | Development | any |
| customfield_10712 | Editing Team | option |
| customfield_10101 | Email Sent? | option |
| customfield_10020 | Epic Color | string |
| customfield_10017 | Epic Link | any |
| customfield_10019 | Epic Name | string |
| customfield_10018 | Epic Status | option |
| customfield_12544 | Field Tester | string |
| customfield_12576 | Flagged | array |
| customfield_12696 | Goals | array |
| customfield_10032 | Image File Name | string |
| customfield_12100 | Impact | option |
| customfield_12630 | Investigation reason | option |
| customfield_12672 | Is Matterport? | option |
| customfield_12635 | Issue color | string |
| customfield_12677 | Locked forms | number |
| customfield_12671 | Matterport Space ID | string |
| customfield_10404 | NDP201 - Processed Client Invoice List | string |
| customfield_10406 | NDP201 - Total line items | number |
| customfield_10402 | NDP201-GR | string |
| customfield_10400 | NDP201-LS | string |
| customfield_10401 | NDP201-SEMI | string |
| customfield_10408 | NDP201-Task Notes | string |
| customfield_10407 | NDP201-Task Rating | number |
| customfield_10405 | NDP201-Total Invoices | number |
| customfield_11501 | NDPE - Editing Revision Notes | string |
| customfield_12602 | NDPE Actual Editor | option |
| customfield_12614 | NDPE Actual QCE | option |
| customfield_12615 | NDPE Actual QTL | option |
| customfield_12621 | NDPE Actual Uploader | option |
| customfield_12574 | NDPE Additional Photos | string |
| customfield_11710 | NDPE Alignment/Composition | option |
| customfield_12547 | NDPE Blurred/focus issues | number |
| customfield_11704 | NDPE Brightness & Contrast | option |
| customfield_12512 | NDPE Color Consistency | number |
| customfield_12517 | NDPE Day to Dusk | number |
| customfield_12612 | NDPE Distribution Details | string |
| customfield_12515 | NDPE Dusty Lens/Dusty Sensor/Lens Hood | number |
| customfield_12665 | NDPE Edited Square Footage | string |
| customfield_12607 | NDPE Editing Deduction Note | string |
| customfield_12589 | NDPE Editing End Timestamp | datetime |
| customfield_12604 | NDPE Editing Minutes Deduction | number |
| customfield_12588 | NDPE Editing Start Timestamp | datetime |
| customfield_11300 | NDPE Editing Type | string |
| customfield_11500 | NDPE Editor | user |
| customfield_11707 | NDPE Exposure Accuracy | option |
| customfield_12681 | NDPE Focus | option |
| customfield_12513 | NDPE Foggy or Hazy or Ghosted Images | number |
| customfield_11708 | NDPE LCA (Purple Fringing) | option |
| customfield_12572 | NDPE Late Add Photos | number |
| customfield_11705 | NDPE Lens Clarity/Distortion | option |
| customfield_11709 | NDPE Lens Flare | option |
| customfield_12511 | NDPE Lens Flare & Light Orbs | number |
| customfield_11711 | NDPE Lighting | option |
| customfield_12524 | NDPE Listing Description | number |
| customfield_12685 | NDPE Missing Photos | option |
| customfield_12613 | NDPE New Editor | option |
| customfield_11702 | NDPE Noise | option |
| customfield_12616 | NDPE Number of Edited Rework Files | number |
| customfield_12617 | NDPE Number of QCE Edited Files | number |
| customfield_12610 | NDPE Number of images for rework | number |
| customfield_12683 | NDPE Object Removal | option |
| customfield_12516 | NDPE Object Removal | number |
| customfield_12545 | NDPE Object Replacement | number |
| customfield_12684 | NDPE Photo Compression & Size Format | option |
| customfield_12647 | NDPE Premium Edit | option |
| customfield_12649 | NDPE Premium Edit Notes | string |
| customfield_12651 | NDPE Premium Edit Type | array |
| customfield_12648 | NDPE Premium Edit Type | option-with-child |
| customfield_12609 | NDPE QCE Deduction Notes | string |
| customfield_12606 | NDPE QCE Minutes Deduction | number |
| customfield_12608 | NDPE QTL Deduction Notes | string |
| customfield_12605 | NDPE QTL Minutes Deduction | number |
| customfield_12526 | NDPE Rating Notes | string |
| customfield_11703 | NDPE Sharpness | option |
| customfield_12618 | NDPE Ticket Ready | string |
| customfield_12611 | NDPE Turn Over Notes | string |
| customfield_12518 | NDPE Twilight Conversion | number |
| customfield_12514 | NDPE Unusable Exposures | number |
| customfield_12620 | NDPE Uploader Checklist | array |
| customfield_11706 | NDPE Vignetting | option |
| customfield_12523 | NDPE Virtual Staging | number |
| customfield_12682 | NDPE Window Pull | option |
| customfield_12686 | NDPE Wrong Photos | option |
| customfield_10900 | NDPEA - Editor 01 | user |
| customfield_10906 | NDPEA - Editor 01 Assigned Photo Count | number |
| customfield_10903 | NDPEA - Editor 01 Assigned Photos | string |
| customfield_11001 | NDPEA - Editor 01 Revision Notes | string |
| customfield_11003 | NDPEA - Editor 01 Revision Notes | string |
| customfield_10901 | NDPEA - Editor 02 | user |
| customfield_10907 | NDPEA - Editor 02 Assigned Photo Count | number |
| customfield_10904 | NDPEA - Editor 02 Assigned Photos | string |
| customfield_11002 | NDPEA - Editor 02 Revision Notes | string |
| customfield_10902 | NDPEA - Editor 03 | user |
| customfield_10908 | NDPEA - Editor 03 Assigned Photo Count | number |
| customfield_10905 | NDPEA - Editor 03 Assigned Photos | string |
| customfield_11000 | NDPEA - Re-edit | array |
| customfield_12652 | NDPEE Number of Additional Photos | number |
| customfield_12653 | NDPEE Number of Edited Files | number |
| customfield_12600 | NDPTE Actual Floor Plan | option |
| customfield_12597 | NDPTE Actual Photo Editor 01 | option |
| customfield_12598 | NDPTE Actual Photo Editor 02 | option |
| customfield_12599 | NDPTE Actual Photo Editor 03 | option |
| customfield_12601 | NDPTE Actual Video Editor | option |
| customfield_12400 | NDPTE Consolidate Comments | string |
| customfield_11302 | NDPTE Floor Plan Editor | user |
| customfield_12006 | NDPTE Folder Name | string |
| customfield_11200 | NDPTE Location | string |
| customfield_12622 | NDPTE Number of Blended Images | number |
| customfield_11303 | NDPTE Photo Editor 01 | user |
| customfield_12003 | NDPTE Photo Editor 01 Scope | string |
| customfield_12001 | NDPTE Photo Editor 02 | user |
| customfield_12004 | NDPTE Photo Editor 02 Scope | string |
| customfield_12002 | NDPTE Photo Editor 03 | user |
| customfield_12005 | NDPTE Photo Editor 03 Scope | string |
| customfield_11800 | NDPTE QA Manager | user |
| customfield_11600 | NDPTE Raw and Edited File Location | string |
| customfield_11801 | NDPTE Upload Manager | user |
| customfield_11301 | NDPTE Video Editor | user |
| customfield_12660 | NDPU 3D Matterport Option | string |
| customfield_10703 | NDPU 3D Model | string |
| customfield_12594 | NDPU Access Instructions | string |
| customfield_10700 | NDPU Access Instructions | string |
| customfield_12687 | NDPU Acknowledged Timestamp | datetime |
| customfield_12666 | NDPU Aerial Link | string |
| customfield_10701 | NDPU Aerial Photos | string |
| customfield_11102 | NDPU Aerial Video | string |
| customfield_11103 | NDPU Aerial Video + Photos | string |
| customfield_11900 | NDPU Appointment Number | string |
| customfield_12584 | NDPU At Listing Timestamp | datetime |
| customfield_10614 | NDPU Booking Date | date |
| customfield_10500 | NDPU Booking Details | string |
| customfield_12658 | NDPU Booking Key | string |
| customfield_12000 | NDPU Booking Status | string |
| customfield_12659 | NDPU Branch | string |
| customfield_10604 | NDPU City State Zip | string |
| customfield_10602 | NDPU Client Cell No. | string |
| customfield_10600 | NDPU Client Name | string |
| customfield_10601 | NDPU Client email | string |
| customfield_12690 | NDPU Closed Timestamp | datetime |
| customfield_11101 | NDPU Combination | string |
| customfield_10612 | NDPU Comments | string |
| customfield_12655 | NDPU Direct Send Link | string |
| customfield_10714 | NDPU Edited Media Folder Link | string |
| customfield_12636 | NDPU Edited Media Library | string |
| customfield_10716 | NDPU Edited Media Revision Notes | string |
| customfield_12644 | NDPU Editing Team | string |
| customfield_12689 | NDPU Final Review Timestamp | datetime |
| customfield_10704 | NDPU Floor Plan | string |
| customfield_12543 | NDPU Folder Created | string |
| customfield_12646 | NDPU Google Map Link | string |
| customfield_11400 | NDPU Google Map Link | string |
| customfield_10705 | NDPU Ground Level | string |
| customfield_12674 | NDPU Home Measurement Flag | array |
| customfield_10603 | NDPU Listing Address | string |
| customfield_12641 | NDPU MP Payment | string |
| customfield_12587 | NDPU MP Ready Timestamp | datetime |
| customfield_12579 | NDPU Managing Partner Mobile | string |
| customfield_12637 | NDPU Media Delivery Link | string |
| customfield_10707 | NDPU Media Pro | user |
| customfield_12522 | NDPU Media Pro Cost $$ | number |
| customfield_12510 | NDPU Media Pro Cost Detail | string |
| customfield_11602 | NDPU Media Pro Mileage | number |
| customfield_12642 | NDPU MediaPro ID | string |
| customfield_11601 | NDPU Notes for Editor | string |
| customfield_12520 | NDPU Number of Edited Files | number |
| customfield_12698 | NDPU Number of Expected Output | string |
| customfield_12581 | NDPU Number of Raw Photos | string |
| customfield_12519 | NDPU Number of Upload Files | number |
| customfield_10501 | NDPU Order Number | string |
| customfield_12662 | NDPU Order Ready | string |
| customfield_12638 | NDPU Photo Pack Type | string |
| customfield_12645 | NDPU PhotoUp Link | string |
| customfield_12664 | NDPU Premium Edit Cost | string |
| customfield_12663 | NDPU Premium Edit Description | string |
| customfield_10713 | NDPU Raw Media Folder Link | string |
| customfield_12640 | NDPU Reimbursement | string |
| customfield_12688 | NDPU RelaHQ Upload Link | string |
| customfield_12521 | NDPU Return Home Miles | number |
| customfield_12661 | NDPU Reviewed | option |
| customfield_12639 | NDPU SKU Number | string |
| customfield_12573 | NDPU Same Day Delivery | string |
| customfield_11104 | NDPU Service | string |
| customfield_11700 | NDPU Service Add-ons | string |
| customfield_12583 | NDPU Shoot Complete Timestamp | datetime |
| customfield_12200 | NDPU Shoot Date | date |
| customfield_11105 | NDPU Shoot Date | string |
| customfield_10711 | NDPU Shoot Start Time  | string |
| customfield_12654 | NDPU Skip Editing | string |
| customfield_12595 | NDPU Special Instructions | string |
| customfield_11100 | NDPU Special Instructions | string |
| customfield_10610 | NDPU Square Footage | string |
| customfield_12586 | NDPU Start Edit Timestamp | datetime |
| customfield_12667 | NDPU Supplementary Links | string |
| customfield_10702 | NDPU Twilights | string |
| customfield_12585 | NDPU Uploaded Timestamp | datetime |
| customfield_12580 | NDPU User Role | string |
| customfield_12650 | NPDE Premium Edit Type | array |
| customfield_12675 | Open forms | number |
| customfield_12626 | Operational categorization | option-with-child |
| customfield_10200 | Organizations | array |
| customfield_11712 | Overall | number |
| customfield_12540 | PES - Aerial Details | string |
| customfield_12542 | PES - Edited Media Link | string |
| customfield_12538 | PES - Listing Address | string |
| customfield_12537 | PES - Number of Upload Photos | number |
| customfield_12541 | PES - Raw Media Link | string |
| customfield_12539 | PES - Twilight Details | string |
| customfield_10002 | Parent Link | any |
| customfield_12624 | Pending reason | option |
| customfield_12625 | Product categorization | option-with-child |
| customfield_12693 | Project overview key | string |
| customfield_12694 | Project overview status | string |
| customfield_10022 | Rank | any |
| customfield_12577 | Request language | sd-request-lang |
| customfield_10024 | Request participants | array |
| customfield_12673 | Responders | array |
| customfield_12631 | Root cause | string |
| customfield_10025 | Satisfaction | sd-feedback |
| customfield_10026 | Satisfaction date | datetime |
| customfield_12695 | Sentiment | array |
| customfield_12627 | Source | option |
| customfield_10021 | Sprint | array |
| customfield_12590 | Start date | date |
| customfield_12619 | Story point estimate | number |
| customfield_12676 | Submitted forms | number |
| customfield_12657 | Target end | date |
| customfield_12656 | Target start | date |
| customfield_10300 | Team | team |
| customfield_12300 | Test 01 | option |
| customfield_10800 | Test Cascading | option-with-child |
| customfield_12634 | Time to approve normal change | sd-servicelevelagreement |
| customfield_12633 | Time to close after resolution | sd-servicelevelagreement |
| customfield_10029 | Time to first response | sd-servicelevelagreement |
| customfield_10028 | Time to resolution | sd-servicelevelagreement |
| customfield_12678 | Total forms | number |
| customfield_12623 | Urgency | option |
| customfield_12692 | Vulnerability | any |
| customfield_12668 | Work category | string |
| customfield_12632 | Workaround | string |
| customfield_10000 | [CHART] Date of First Response | datetime |
| customfield_10001 | [CHART] Time in Status | any |
| customfield_12643 | webhook_token | string |

## Secondary JIRA (https://betteredits2.atlassian.net)

### System Fields

| Field ID | Name | Type |
| --- | --- | --- |
| versions | Affects versions | array |
| assignee | Assignee | user |
| attachment | Attachment | array |
| comment | Comment | comments-page |
| components | Components | array |
| created | Created | datetime |
| creator | Creator | user |
| description | Description | string |
| duedate | Due date | date |
| environment | Environment | string |
| fixVersions | Fix versions | array |
| thumbnail | Images |  |
| issuetype | Issue Type | issuetype |
| issuekey | Key |  |
| labels | Labels | array |
| lastViewed | Last Viewed | datetime |
| issuelinks | Linked Issues | array |
| worklog | Log Work | array |
| timeoriginalestimate | Original estimate | number |
| parent | Parent |  |
| priority | Priority | priority |
| progress | Progress | progress |
| project | Project | project |
| timeestimate | Remaining Estimate | number |
| reporter | Reporter | user |
| resolution | Resolution | resolution |
| resolutiondate | Resolved | datetime |
| issuerestriction | Restrict to | issuerestriction |
| security | Security Level | securitylevel |
| status | Status | status |
| statusCategory | Status Category |  |
| statuscategorychangedate | Status Category Changed | datetime |
| subtasks | Sub-tasks | array |
| summary | Summary | string |
| timespent | Time Spent | number |
| timetracking | Time tracking | timetracking |
| updated | Updated | datetime |
| votes | Votes | votes |
| watches | Watchers | watches |
| workratio | Work Ratio | number |
| aggregatetimeoriginalestimate | Σ Original Estimate | number |
| aggregateprogress | Σ Progress | progress |
| aggregatetimeestimate | Σ Remaining Estimate | number |
| aggregatetimespent | Σ Time Spent | number |

### Custom Fields

| Field ID | Name | Type |
| --- | --- | --- |
| customfield_11401 | Address Google Map Link | string |
| customfield_11402 | Address test link | string |
| customfield_12675 | Affected services | array |
| customfield_10016 | Approvals | sd-approvals |
| customfield_10027 | Approvers | array |
| customfield_10403 | Attachment Links | string |
| customfield_10613 | Branch | string |
| customfield_12683 | Category | option |
| customfield_12105 | Change completion date | datetime |
| customfield_12103 | Change reason | option |
| customfield_12102 | Change risk | option |
| customfield_12104 | Change start date | datetime |
| customfield_12101 | Change type | option |
| customfield_10023 | Customer Request Type | sd-customerrequesttype |
| customfield_12727 | Date of hire | date |
| customfield_12717 | Date of hire | date |
| customfield_12726 | Department | string |
| customfield_12716 | Department | string |
| customfield_12707 | Design | array |
| customfield_10100 | Development | any |
| customfield_10712 | Editing Team | option |
| customfield_10101 | Email Sent? | option |
| customfield_10020 | Epic Color | string |
| customfield_10017 | Epic Link | any |
| customfield_12600 | Epic Link | any |
| customfield_10019 | Epic Name | string |
| customfield_10018 | Epic Status | option |
| customfield_12544 | Field Tester | string |
| customfield_12576 | Flagged | array |
| customfield_12710 | Goals | array |
| customfield_12724 | Hiring manager | string |
| customfield_12714 | Hiring manager | string |
| customfield_10032 | Image File Name | string |
| customfield_12100 | Impact | option |
| customfield_12639 | Issue color | string |
| customfield_12725 | Job role | string |
| customfield_12715 | Job role | string |
| customfield_12728 | Location | string |
| customfield_12718 | Location | string |
| customfield_12679 | Locked forms | number |
| customfield_12668 | NDP Platform Escalation Notes | string |
| customfield_12666 | NDP Platform Link | string |
| customfield_10404 | NDP201 - Processed Client Invoice List | string |
| customfield_10406 | NDP201 - Total line items | number |
| customfield_10402 | NDP201-GR | string |
| customfield_10400 | NDP201-LS | string |
| customfield_10401 | NDP201-SEMI | string |
| customfield_10408 | NDP201-Task Notes | string |
| customfield_10407 | NDP201-Task Rating | number |
| customfield_10405 | NDP201-Total Invoices | number |
| customfield_11501 | NDPE - Editing Revision Notes | string |
| customfield_12618 | NDPE Actual Editor | option |
| customfield_12621 | NDPE Actual QCE | option |
| customfield_12622 | NDPE Actual QTL | option |
| customfield_12637 | NDPE Actual Uploader | option |
| customfield_12574 | NDPE Additional Photos | string |
| customfield_11710 | NDPE Alignment/Composition | option |
| customfield_12547 | NDPE Blurred/focus issues | number |
| customfield_11704 | NDPE Brightness & Contrast | option |
| customfield_12512 | NDPE Color Consistency | number |
| customfield_12517 | NDPE Day to Dusk | number |
| customfield_12623 | NDPE Distribution Details | string |
| customfield_12515 | NDPE Dusty Lens/Dusty Sensor/Lens Hood | number |
| customfield_12665 | NDPE Edited Square Footage | string |
| customfield_12624 | NDPE Editing Deduction Note | string |
| customfield_12604 | NDPE Editing End Timestamp | datetime |
| customfield_12625 | NDPE Editing Minutes Deduction | number |
| customfield_12603 | NDPE Editing Start Timestamp | datetime |
| customfield_11300 | NDPE Editing Type | string |
| customfield_11500 | NDPE Editor | user |
| customfield_11707 | NDPE Exposure Accuracy | option |
| customfield_12695 | NDPE Focus | option |
| customfield_12513 | NDPE Foggy or Hazy or Ghosted Images | number |
| customfield_11708 | NDPE LCA (Purple Fringing) | option |
| customfield_12572 | NDPE Late Add Photos | number |
| customfield_11705 | NDPE Lens Clarity/Distortion | option |
| customfield_11709 | NDPE Lens Flare | option |
| customfield_12511 | NDPE Lens Flare & Light Orbs | number |
| customfield_11711 | NDPE Lighting | option |
| customfield_12524 | NDPE Listing Description | number |
| customfield_12693 | NDPE Missing Photos | option |
| customfield_12619 | NDPE New Editor | option |
| customfield_11702 | NDPE Noise | option |
| customfield_12626 | NDPE Number of Edited Rework Files | number |
| customfield_12628 | NDPE Number of QCE Edited Files | number |
| customfield_12627 | NDPE Number of images for rework | number |
| customfield_12697 | NDPE Object Removal | option |
| customfield_12516 | NDPE Object Removal | number |
| customfield_12545 | NDPE Object Replacement | number |
| customfield_12698 | NDPE Photo Compression & Size Format | option |
| customfield_12651 | NDPE Premium Edit | option |
| customfield_12652 | NDPE Premium Edit Notes | string |
| customfield_12653 | NDPE Premium Edit Type | option-with-child |
| customfield_12629 | NDPE QCE Deduction Notes | string |
| customfield_12630 | NDPE QCE Minutes Deduction | number |
| customfield_12631 | NDPE QTL Deduction Notes | string |
| customfield_12632 | NDPE QTL Minutes Deduction | number |
| customfield_12526 | NDPE Rating Notes | string |
| customfield_11703 | NDPE Sharpness | option |
| customfield_12633 | NDPE Ticket Ready | string |
| customfield_12634 | NDPE Turn Over Notes | string |
| customfield_12518 | NDPE Twilight Conversion | number |
| customfield_12514 | NDPE Unusable Exposures | number |
| customfield_12636 | NDPE Uploader Checklist | array |
| customfield_11706 | NDPE Vignetting | option |
| customfield_12523 | NDPE Virtual Staging | number |
| customfield_12696 | NDPE Window Pull | option |
| customfield_12694 | NDPE Wrong Photos | option |
| customfield_10900 | NDPEA - Editor 01 | user |
| customfield_10906 | NDPEA - Editor 01 Assigned Photo Count | number |
| customfield_10903 | NDPEA - Editor 01 Assigned Photos | string |
| customfield_11001 | NDPEA - Editor 01 Revision Notes | string |
| customfield_11003 | NDPEA - Editor 01 Revision Notes | string |
| customfield_10901 | NDPEA - Editor 02 | user |
| customfield_10907 | NDPEA - Editor 02 Assigned Photo Count | number |
| customfield_10904 | NDPEA - Editor 02 Assigned Photos | string |
| customfield_11002 | NDPEA - Editor 02 Revision Notes | string |
| customfield_10902 | NDPEA - Editor 03 | user |
| customfield_10908 | NDPEA - Editor 03 Assigned Photo Count | number |
| customfield_10905 | NDPEA - Editor 03 Assigned Photos | string |
| customfield_11000 | NDPEA - Re-edit | array |
| customfield_12654 | NDPEE Number of Additional Photos | number |
| customfield_12655 | NDPEE Number of Edited Files | number |
| customfield_12617 | NDPTE Actual Floor Plan | option |
| customfield_12613 | NDPTE Actual Photo Editor 01 | option |
| customfield_12614 | NDPTE Actual Photo Editor 02 | option |
| customfield_12615 | NDPTE Actual Photo Editor 03 | option |
| customfield_12616 | NDPTE Actual Video Editor | option |
| customfield_12400 | NDPTE Consolidate Comments | string |
| customfield_11302 | NDPTE Floor Plan Editor | user |
| customfield_12006 | NDPTE Folder Name | string |
| customfield_11200 | NDPTE Location | string |
| customfield_12638 | NDPTE Number of Blended Images | number |
| customfield_11303 | NDPTE Photo Editor 01 | user |
| customfield_12003 | NDPTE Photo Editor 01 Scope | string |
| customfield_12001 | NDPTE Photo Editor 02 | user |
| customfield_12004 | NDPTE Photo Editor 02 Scope | string |
| customfield_12002 | NDPTE Photo Editor 03 | user |
| customfield_12005 | NDPTE Photo Editor 03 Scope | string |
| customfield_11800 | NDPTE QA Manager | user |
| customfield_11600 | NDPTE Raw and Edited File Location | string |
| customfield_11801 | NDPTE Upload Manager | user |
| customfield_11301 | NDPTE Video Editor | user |
| customfield_12660 | NDPU 3D Matterport Option | string |
| customfield_10703 | NDPU 3D Model | string |
| customfield_10700 | NDPU Access Instructions | string |
| customfield_12611 | NDPU Access Instructions | string |
| customfield_12699 | NDPU Acknowledged Timestamp | datetime |
| customfield_10701 | NDPU Aerial Photos | string |
| customfield_11102 | NDPU Aerial Video | string |
| customfield_11103 | NDPU Aerial Video + Photos | string |
| customfield_11900 | NDPU Appointment Number | string |
| customfield_12609 | NDPU At Listing Timestamp | datetime |
| customfield_10614 | NDPU Booking Date | date |
| customfield_10500 | NDPU Booking Details | string |
| customfield_12670 | NDPU Booking Key | string |
| customfield_12000 | NDPU Booking Status | string |
| customfield_12671 | NDPU Branch | string |
| customfield_10604 | NDPU City State Zip | string |
| customfield_10602 | NDPU Client Cell No. | string |
| customfield_10600 | NDPU Client Name | string |
| customfield_10601 | NDPU Client email | string |
| customfield_12704 | NDPU Closed Timestamp | datetime |
| customfield_11101 | NDPU Combination | string |
| customfield_10612 | NDPU Comments | string |
| customfield_12657 | NDPU Direct Send Link | string |
| customfield_10714 | NDPU Edited Media Folder Link | string |
| customfield_12640 | NDPU Edited Media Library | string |
| customfield_10716 | NDPU Edited Media Revision Notes | string |
| customfield_12648 | NDPU Editing Team | string |
| customfield_12703 | NDPU Final Review Timestamp | datetime |
| customfield_10704 | NDPU Floor Plan | string |
| customfield_12543 | NDPU Folder Created | string |
| customfield_12650 | NDPU Google Map Link | string |
| customfield_11400 | NDPU Google Map Link | string |
| customfield_10705 | NDPU Ground Level | string |
| customfield_12676 | NDPU Home Measurement Flag | array |
| customfield_10603 | NDPU Listing Address | string |
| customfield_12645 | NDPU MP Payment | string |
| customfield_12610 | NDPU MP Ready Timestamp | datetime |
| customfield_12702 | NDPU MP Square Footage | number |
| customfield_12579 | NDPU Managing Partner Mobile | string |
| customfield_12641 | NDPU Media Delivery Link | string |
| customfield_10707 | NDPU Media Pro | user |
| customfield_12522 | NDPU Media Pro Cost $$ | number |
| customfield_12510 | NDPU Media Pro Cost Detail | string |
| customfield_11602 | NDPU Media Pro Mileage | number |
| customfield_12646 | NDPU MediaPro ID | string |
| customfield_11601 | NDPU Notes for Editor | string |
| customfield_12635 | NDPU Number of Edited Files | number |
| customfield_12713 | NDPU Number of Expected Output | string |
| customfield_12602 | NDPU Number of Raw Photos | string |
| customfield_12519 | NDPU Number of Upload Files | number |
| customfield_10501 | NDPU Order Number | string |
| customfield_12662 | NDPU Order Ready | string |
| customfield_12643 | NDPU Photo Pack Type | string |
| customfield_12649 | NDPU PhotoUp Link | string |
| customfield_12664 | NDPU Premium Edit Cost | string |
| customfield_12663 | NDPU Premium Edit Description | string |
| customfield_10713 | NDPU Raw Media Folder Link | string |
| customfield_12644 | NDPU Reimbursement | string |
| customfield_12700 | NDPU RelaHQ Upload Link | string |
| customfield_12521 | NDPU Return Home Miles | number |
| customfield_12661 | NDPU Reviewed | option |
| customfield_12642 | NDPU SKU Number | string |
| customfield_12573 | NDPU Same Day Delivery | string |
| customfield_11104 | NDPU Service | string |
| customfield_11700 | NDPU Service Add-ons | string |
| customfield_12606 | NDPU Shoot Complete Timestamp | datetime |
| customfield_12200 | NDPU Shoot Date | date |
| customfield_11105 | NDPU Shoot Date | string |
| customfield_10711 | NDPU Shoot Start Time  | string |
| customfield_12656 | NDPU Skip Editing | string |
| customfield_11100 | NDPU Special Instructions | string |
| customfield_12612 | NDPU Special Instructions | string |
| customfield_10610 | NDPU Square Footage | string |
| customfield_12607 | NDPU Start Edit Timestamp | datetime |
| customfield_12667 | NDPU Supplementary Links | string |
| customfield_10702 | NDPU Twilights | string |
| customfield_12608 | NDPU Uploaded Timestamp | datetime |
| customfield_12601 | NDPU User Role | string |
| customfield_12677 | Open forms | number |
| customfield_10200 | Organizations | array |
| customfield_11712 | Overall | number |
| customfield_12540 | PES - Aerial Details | string |
| customfield_12542 | PES - Edited Media Link | string |
| customfield_12538 | PES - Listing Address | string |
| customfield_12537 | PES - Number of Upload Photos | number |
| customfield_12541 | PES - Raw Media Link | string |
| customfield_12539 | PES - Twilight Details | string |
| customfield_10002 | Parent Link | any |
| customfield_12705 | Project overview key | string |
| customfield_12706 | Project overview status | string |
| customfield_10022 | Rank | any |
| customfield_12577 | Request language | sd-request-lang |
| customfield_10024 | Request participants | array |
| customfield_10025 | Satisfaction | sd-feedback |
| customfield_10026 | Satisfaction date | datetime |
| customfield_12709 | Sentiment | array |
| customfield_10021 | Sprint | array |
| customfield_12605 | Start date | date |
| customfield_12620 | Story point estimate | number |
| customfield_12678 | Submitted forms | number |
| customfield_12659 | Target end | date |
| customfield_12658 | Target start | date |
| customfield_10300 | Team | team |
| customfield_12300 | Test 01 | option |
| customfield_10800 | Test Cascading | option-with-child |
| customfield_10029 | Time to first response | sd-servicelevelagreement |
| customfield_10028 | Time to resolution | sd-servicelevelagreement |
| customfield_12680 | Total forms | number |
| customfield_12708 | Vulnerability | any |
| customfield_10000 | [CHART] Date of First Response | datetime |
| customfield_10001 | [CHART] Time in Status | any |
| customfield_12647 | webhook_token | string |

