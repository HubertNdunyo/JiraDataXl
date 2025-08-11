#!/bin/bash

# Quick Field Mapping Test Script
# Run this to quickly verify field mapping functionality

echo "======================================================================"
echo "FIELD MAPPING QUICK TEST SUITE"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL=${API_URL:-"http://localhost:8987"}
ADMIN_API_KEY=${ADMIN_API_KEY:-"secure-admin-key-2024"}
DB_HOST=${DB_HOST:-"localhost"}
DB_NAME=${DB_NAME:-"jira_sync"}
DB_USER=${DB_USER:-"postgres"}
DB_PASSWORD=${DB_PASSWORD:-"postgres"}

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Test function
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Test $TESTS_RUN: $test_name... "
    
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

echo "🔍 Testing Environment Setup"
echo "=============================="
echo "API URL: $API_URL"
echo "Database: $DB_NAME@$DB_HOST"
echo ""

# Test 1: Database connectivity
echo "📊 DATABASE TESTS"
echo "-----------------"
run_test "Database connection" \
    "PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c 'SELECT 1' 2>/dev/null"

# Test 2: Check tables exist
run_test "Required tables exist" \
    "PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('configurations', 'jira_issues_v2', 'jira_field_cache')\" 2>/dev/null | grep -q '3'"

# Test 3: Field mappings loaded
run_test "Field mappings configured" \
    "PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c \"SELECT COUNT(*) FROM configurations WHERE config_type='jira' AND config_key='field_mappings' AND is_active=true\" 2>/dev/null | grep -q '1'"

# Test 4: Check column mappings
echo ""
echo "🗺️ COLUMN MAPPING TESTS"
echo "------------------------"
echo "Checking critical column mappings..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'jira_issues_v2' 
AND column_name LIKE 'ndpu_%'
ORDER BY column_name
LIMIT 10
" 2>/dev/null | while read col; do
    if [ ! -z "$col" ]; then
        echo "  • Found column: $col"
    fi
done

# Test 5: API endpoint test
echo ""
echo "🌐 API TESTS"
echo "------------"
run_test "Field mappings API endpoint" \
    "curl -s -H 'X-Admin-Key: $ADMIN_API_KEY' $API_URL/api/admin/config/field-mappings | grep -q 'field_groups'"

# Test 6: Check field population
echo ""
echo "📈 FIELD POPULATION STATISTICS"
echo "------------------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
SELECT 
    'Total Issues: ' || COUNT(*) as metric
FROM jira_issues_v2
UNION ALL
SELECT 
    'With Order Number: ' || COUNT(ndpu_order_number)
FROM jira_issues_v2
WHERE ndpu_order_number IS NOT NULL
UNION ALL
SELECT 
    'With Client Name: ' || COUNT(ndpu_client_name)
FROM jira_issues_v2
WHERE ndpu_client_name IS NOT NULL
UNION ALL
SELECT 
    'With Listing Address: ' || COUNT(ndpu_listing_address)
FROM jira_issues_v2
WHERE ndpu_listing_address IS NOT NULL
" 2>/dev/null | while read stat; do
    if [ ! -z "$stat" ]; then
        echo "  $stat"
    fi
done

# Test 7: Recent sync activity
echo ""
echo "🔄 RECENT SYNC ACTIVITY"
echo "-----------------------"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
SELECT 
    project_name || ': ' || status || ' (' || 
    to_char(timestamp, 'YYYY-MM-DD HH24:MI') || ')' as activity
FROM update_logs
ORDER BY timestamp DESC
LIMIT 5
" 2>/dev/null | while read activity; do
    if [ ! -z "$activity" ]; then
        echo "  • $activity"
    fi
done

# Final report
echo ""
echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo "Tests Run: $TESTS_RUN"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $((TESTS_RUN - TESTS_PASSED))"

if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "✨ Field mapping system is configured correctly."
    exit 0
else
    echo -e "${YELLOW}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Recommendations:"
    echo "1. Check database connectivity and credentials"
    echo "2. Run: docker exec jira-sync-backend python scripts/init_database.py"
    echo "3. Verify JIRA credentials are set in environment"
    echo "4. Check logs: docker logs jira-sync-backend"
    exit 1
fi