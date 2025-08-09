# Field Mapping System Migration Plan
## From Hardcoded to Configuration-Based Field Extraction

### Executive Summary
This document outlines a careful, phased approach to migrate the JIRA sync system from hardcoded field mappings to a dynamic, configuration-based system. The migration will be done incrementally with multiple safeguards to ensure zero data loss and maintain system stability.

---

## Current State Analysis

### Legacy System (Previously Used - Now Migrated)
- **Location**: `/backend/core/jira/jira_issues.py` (now fully refactored)
- **Method**: Previously used hardcoded custom field IDs directly in code
- **Fields**: 30 fields defined in `ISSUE_COLUMNS`
- **Data**: Successfully synced 25,743 issues
- **Risk**: Low (proven stable in production)

### New System (Partially Implemented)
- **Location**: Field Mappings Dashboard + Database Configuration
- **Method**: Dynamic field mapping via `configurations` table
- **Fields**: Only 4 fields currently configured
- **Components Built**:
  - Field discovery and caching system
  - Field mapping wizard UI
  - Database configuration storage
  - Field processor with type validation
- **Risk**: Untested with full production load

---

## Migration Phases

### Phase 1: Preparation and Safety Measures (Week 1)

#### 1.1 Create Full System Backup
```bash
# Database backup
pg_dump -U postgres -d jira_sync > backup_before_migration_$(date +%Y%m%d).sql

# Configuration backup
cp -r backend/config backend/config.backup.$(date +%Y%m%d)
cp backend/core/jira/jira_issues.py backend/core/jira/jira_issues.py.backup
```

#### 1.2 Document Current Hardcoded Mappings
Create a comprehensive inventory of all hardcoded field mappings:
- Extract all customfield_* references from jira_issues.py
- Map each to its business purpose
- Identify which fields work for both instances
- Document any field combining logic

#### 1.3 Create Migration Configuration
Generate a complete field mapping configuration from the hardcoded values:
```json
{
  "field_groups": {
    "Migrated Core Fields": {
      "fields": {
        "ndpu_order_number": {
          "instance_1": {"field_id": "customfield_10501"},
          "instance_2": {"field_id": "customfield_10501"}
        }
        // ... all other fields
      }
    }
  }
}
```

---

### Phase 2: Parallel Implementation (Week 2)

#### 2.1 Create New Field Extraction Method
Create `jira_issues_v2.py` that:
- Reads field mappings from database configuration
- Falls back to hardcoded values if configuration missing
- Logs any discrepancies between methods

```python
class ConfigurableIssueProcessor:
    def __init__(self, use_legacy_fallback=True):
        self.config = self.load_configuration()
        self.legacy_fallback = use_legacy_fallback
    
    def extract_field(self, fields, field_name, instance_type):
        # Try configuration first
        mapping = self.get_field_mapping(field_name, instance_type)
        if mapping:
            return self.extract_by_config(fields, mapping)
        
        # Fall back to legacy if enabled
        if self.legacy_fallback:
            return self.extract_legacy(fields, field_name)
        
        return None
```

#### 2.2 Implement Comparison Mode
Add a comparison mode that:
- Runs both extraction methods in parallel
- Compares results field by field
- Logs any differences
- Uses legacy values for actual storage

#### 2.3 Create Field Mapping Validator
Build a validation tool that:
- Verifies all required fields have mappings
- Checks field type compatibility
- Validates both instances have necessary fields
- Reports missing or incorrect mappings

---

### Phase 3: Testing and Validation (Week 3)

#### 3.1 Unit Testing
- Test field extraction for all 30 fields
- Test type conversions and sanitization
- Test fallback mechanisms
- Test error handling

#### 3.2 Integration Testing
- Test with sample of 100 issues from each project
- Verify data consistency
- Compare with existing database records
- Test both JIRA instances

#### 3.3 Performance Testing
- Measure extraction speed (legacy vs new)
- Test with full project load
- Monitor memory usage
- Verify caching effectiveness

#### 3.4 Data Validation
```sql
-- Create validation queries
SELECT 
    COUNT(*) as total,
    COUNT(ndpu_order_number) as with_order,
    COUNT(DISTINCT project_name) as projects
FROM jira_issues_v2_test
```

---

### Phase 4: Gradual Rollout (Week 4)

#### 4.1 Shadow Mode (Days 1-3)
- Enable new system in shadow mode
- Continue using legacy for actual sync
- Log all differences to monitoring table
- Review discrepancy reports daily

```python
# Configuration flag
FIELD_EXTRACTION_MODE = "shadow"  # legacy | shadow | hybrid | new
```

#### 4.2 Hybrid Mode (Days 4-5)
- Use new system for non-critical fields
- Keep legacy for critical fields (order_number, status, etc.)
- Monitor error rates
- Validate data quality

#### 4.3 Canary Deployment (Days 6-7)
- Enable new system for 1-2 small projects
- Monitor closely for issues
- Compare sync results with historical data
- Rollback if any anomalies detected

---

### Phase 5: Full Migration (Week 5)

#### 5.1 Final Configuration Load
```python
# Load all field mappings into database
python scripts/load_field_mappings.py --source legacy --validate
```

#### 5.2 Switch to New System
- Update configuration flag to "new"
- Disable legacy fallback
- Monitor first full sync cycle
- Keep legacy code available for emergency rollback

#### 5.3 Validation Checkpoints
- [ ] All 30 fields extracting correctly
- [ ] Both instances working
- [ ] No data loss or corruption
- [ ] Performance within acceptable range
- [ ] Error rate < 0.1%

---

## Implementation Details

### Configuration Structure
```python
# New configuration-based extraction
def process_issue_configurable(self, issue, project_key, instance_type):
    config = self.get_active_configuration()
    field_mappings = config.get('field_groups', {})
    
    record = []
    for column in ISSUE_COLUMNS:
        mapping = self.find_mapping_for_column(column, field_mappings, instance_type)
        value = self.extract_and_validate(issue['fields'], mapping)
        record.append(value)
    
    return tuple(record)
```

### Rollback Procedure
```bash
# Immediate rollback steps
1. Update FIELD_EXTRACTION_MODE = "legacy"
2. Restart sync service
3. Verify sync functioning
4. Investigate issues
5. Restore from backup if needed
```

### Monitoring Queries
```sql
-- Monitor extraction success rate
CREATE TABLE field_extraction_metrics (
    sync_id VARCHAR(255),
    extraction_mode VARCHAR(50),
    field_name VARCHAR(100),
    success_count INTEGER,
    failure_count INTEGER,
    mismatch_count INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Daily validation
SELECT 
    field_name,
    SUM(success_count) as successes,
    SUM(failure_count) as failures,
    ROUND(100.0 * SUM(success_count) / 
          (SUM(success_count) + SUM(failure_count)), 2) as success_rate
FROM field_extraction_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY field_name
ORDER BY success_rate ASC;
```

---

## Risk Mitigation

### High-Risk Areas
1. **Field ID Changes**: Custom field IDs might differ between instances
   - **Mitigation**: Complete field discovery before migration
   
2. **Type Mismatches**: Field types might not match expected format
   - **Mitigation**: Comprehensive type validation and sanitization
   
3. **Missing Fields**: Some fields might not exist in Instance 2
   - **Mitigation**: Graceful handling of missing fields
   
4. **Performance Degradation**: Dynamic lookup might be slower
   - **Mitigation**: Implement caching layer

### Rollback Triggers
Immediate rollback if:
- Error rate > 1%
- Sync duration increases > 50%
- Data corruption detected
- Missing critical fields (order_number, status)
- Database constraint violations

---

## Success Criteria

### Technical Metrics
- [ ] 100% field coverage (all 30 fields)
- [ ] < 0.1% error rate
- [ ] < 10% performance degradation
- [ ] Zero data loss
- [ ] Both instances fully functional

### Business Metrics
- [ ] No disruption to daily syncs
- [ ] All historical data preserved
- [ ] Field mappings editable via UI
- [ ] New fields easily addable

---

## Timeline

| Week | Phase | Key Activities | Checkpoint |
|------|-------|---------------|------------|
| 1 | Preparation | Backup, Documentation, Config Creation | Config file ready |
| 2 | Implementation | New extraction method, Comparison mode | Code complete |
| 3 | Testing | Unit, Integration, Performance tests | All tests passing |
| 4 | Rollout | Shadow → Hybrid → Canary | No critical issues |
| 5 | Migration | Full switch, Validation, Cleanup | Migration complete |

---

## Post-Migration Tasks

1. **Remove Legacy Code** (Week 6)
   - Archive jira_issues.py.backup
   - Remove hardcoded field references
   - Update documentation

2. **Optimize Configuration** (Week 7)
   - Review field usage statistics
   - Remove unused fields
   - Optimize database queries

3. **Enable Advanced Features** (Week 8)
   - Field transformation rules
   - Conditional mappings
   - Multi-instance field sync

---

## Appendix A: Critical Files to Modify

1. `/backend/core/jira/jira_issues.py` - Main extraction logic
2. `/backend/core/sync/sync_manager.py` - Sync orchestration
3. `/backend/core/db/constants.py` - Column definitions
4. `/backend/core/jira/field_processor.py` - Field processing
5. `/backend/config/core_field_mappings.json` - Configuration template

---

## Appendix B: Emergency Contacts

- Database Admin: [Contact]
- System Owner: [Contact]
- On-Call Engineer: [Contact]

---

## Appendix C: Validation Checklist

### Pre-Migration
- [ ] Full database backup completed
- [ ] All hardcoded fields documented
- [ ] Configuration file validated
- [ ] Test environment ready
- [ ] Rollback procedure tested

### During Migration
- [ ] Shadow mode metrics acceptable
- [ ] Hybrid mode stable
- [ ] Canary projects successful
- [ ] No data anomalies detected
- [ ] Performance within limits

### Post-Migration
- [ ] All fields syncing correctly
- [ ] Both instances operational
- [ ] UI configuration working
- [ ] Documentation updated
- [ ] Legacy code archived

---

*Document Version: 1.0*
*Created: 2025-01-09*
*Last Updated: 2025-01-09*
*Status: DRAFT - Pending Review*