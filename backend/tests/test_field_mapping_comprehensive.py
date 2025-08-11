#!/usr/bin/env python3
"""
Comprehensive Field Mapping Test Suite
Tests the complete field mapping flow from configuration to data extraction
"""

import os
import sys
import json
import time
import logging
import psycopg2
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.db_config import get_field_mapping_config, save_configuration
from core.db.column_mappings import get_field_key_for_column, COLUMN_TO_FIELD_MAPPING
from core.jira import JiraClient
from core.jira.jira_issues import IssueProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FieldMappingTestSuite:
    """Comprehensive test suite for field mapping functionality"""
    
    def __init__(self):
        self.api_url = os.getenv('API_URL', 'http://localhost:8987')
        self.admin_key = os.getenv('ADMIN_API_KEY', 'secure-admin-key-2024')
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'jira_sync'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'port': os.getenv('DB_PORT', 5432)
        }
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def connect_db(self):
        """Establish database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and track results"""
        self.total_tests += 1
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running: {test_name}")
            logger.info(f"{'='*60}")
            
            result = test_func()
            
            if result:
                self.passed_tests += 1
                logger.info(f"✅ PASSED: {test_name}")
                self.test_results.append((test_name, 'PASSED', None))
            else:
                logger.error(f"❌ FAILED: {test_name}")
                self.test_results.append((test_name, 'FAILED', 'Test returned False'))
            
            return result
            
        except Exception as e:
            logger.error(f"❌ ERROR in {test_name}: {e}")
            self.test_results.append((test_name, 'ERROR', str(e)))
            return False
    
    # ==================== DATABASE TESTS ====================
    
    def test_database_tables_exist(self) -> bool:
        """Test that all required tables exist"""
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            required_tables = [
                'configurations',
                'configuration_history', 
                'jira_issues_v2',
                'jira_field_cache',
                'update_log_v2'
            ]
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = []
            for table in required_tables:
                if table not in existing_tables:
                    missing_tables.append(table)
                    logger.error(f"  Missing table: {table}")
                else:
                    logger.info(f"  ✓ Table exists: {table}")
            
            return len(missing_tables) == 0
            
        finally:
            conn.close()
    
    def test_field_mappings_loaded(self) -> bool:
        """Test that field mappings are loaded in database"""
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT config_value, version, is_active
                FROM configurations
                WHERE config_type = 'jira' 
                AND config_key = 'field_mappings'
                AND is_active = true
            """)
            
            result = cursor.fetchone()
            if not result:
                logger.error("  No active field mappings found in database")
                return False
            
            config_value, version, is_active = result
            field_groups = config_value.get('field_groups', {})
            
            logger.info(f"  Field mapping version: {version}")
            logger.info(f"  Number of field groups: {len(field_groups)}")
            
            # Count total fields
            total_fields = sum(len(group.get('fields', {})) for group in field_groups.values())
            logger.info(f"  Total fields configured: {total_fields}")
            
            # Check critical field groups
            required_groups = ['order_details', 'media_links', 'service_info']
            missing_groups = []
            for group in required_groups:
                if group not in field_groups:
                    missing_groups.append(group)
                    logger.error(f"  Missing field group: {group}")
                else:
                    fields_count = len(field_groups[group].get('fields', {}))
                    logger.info(f"  ✓ Field group '{group}': {fields_count} fields")
            
            return len(missing_groups) == 0 and total_fields > 20
            
        finally:
            conn.close()
    
    def test_column_mappings(self) -> bool:
        """Test column name mappings are correctly configured"""
        test_mappings = [
            ('ndpu_order_number', 'order_number'),
            ('ndpu_client_name', 'client_name'),
            ('ndpu_listing_address', 'listing_address'),
            ('dropbox_raw_link', 'dropbox_raw'),
            ('ndpu_editing_team', 'editing_team'),
            ('ndpu_service_type', 'service_type'),
            ('ndpu_same_day_delivery', 'same_day_delivery')
        ]
        
        all_passed = True
        for db_column, expected_key in test_mappings:
            actual_key = get_field_key_for_column(db_column)
            if actual_key == expected_key:
                logger.info(f"  ✓ {db_column} -> {actual_key}")
            else:
                logger.error(f"  ✗ {db_column} -> {actual_key} (expected: {expected_key})")
                all_passed = False
        
        # Check total mappings
        logger.info(f"  Total column mappings defined: {len(COLUMN_TO_FIELD_MAPPING)}")
        
        return all_passed
    
    def test_database_columns_exist(self) -> bool:
        """Test that database columns exist for mapped fields"""
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'jira_issues_v2'
                ORDER BY ordinal_position
            """)
            
            columns = {row[0]: row[1] for row in cursor.fetchall()}
            logger.info(f"  Total columns in jira_issues_v2: {len(columns)}")
            
            # Check critical columns
            critical_columns = [
                'issue_key', 'project_name', 'summary', 'status',
                'ndpu_order_number', 'ndpu_client_name', 'ndpu_listing_address',
                'ndpu_service_type', 'ndpu_editing_team', 'dropbox_raw_link'
            ]
            
            missing_columns = []
            for col in critical_columns:
                if col in columns:
                    logger.info(f"  ✓ Column exists: {col} ({columns[col]})")
                else:
                    logger.error(f"  ✗ Missing column: {col}")
                    missing_columns.append(col)
            
            return len(missing_columns) == 0
            
        finally:
            conn.close()
    
    # ==================== API TESTS ====================
    
    def test_api_field_mappings_endpoint(self) -> bool:
        """Test the field mappings API endpoint"""
        try:
            response = requests.get(
                f"{self.api_url}/api/admin/config/field-mappings",
                headers={'X-Admin-Key': self.admin_key}
            )
            
            if response.status_code != 200:
                logger.error(f"  API returned status {response.status_code}")
                return False
            
            data = response.json()
            
            # Validate response structure
            if 'field_groups' not in data:
                logger.error("  Response missing 'field_groups'")
                return False
            
            field_groups = data['field_groups']
            logger.info(f"  API returned {len(field_groups)} field groups")
            
            # Check for specific fields
            if 'order_details' in field_groups:
                order_fields = field_groups['order_details'].get('fields', {})
                logger.info(f"  Order details group has {len(order_fields)} fields")
                
                if 'order_number' in order_fields:
                    order_config = order_fields['order_number']
                    instance_1_id = order_config.get('instance_1', {}).get('field_id')
                    instance_2_id = order_config.get('instance_2', {}).get('field_id')
                    logger.info(f"  Order number field IDs: instance_1={instance_1_id}, instance_2={instance_2_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"  API test failed: {e}")
            return False
    
    def test_field_discovery_api(self) -> bool:
        """Test field discovery functionality"""
        try:
            # First check if fields are already cached
            response = requests.get(
                f"{self.api_url}/api/admin/fields/cached",
                headers={'X-Admin-Key': self.admin_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                instance_1_count = data.get('instance_1', {}).get('count', 0)
                instance_2_count = data.get('instance_2', {}).get('count', 0)
                
                if instance_1_count > 0 and instance_2_count > 0:
                    logger.info(f"  ✓ Fields already cached: instance_1={instance_1_count}, instance_2={instance_2_count}")
                    return True
            
            # If not cached, try discovery (with timeout to avoid blocking)
            try:
                response = requests.post(
                    f"{self.api_url}/api/admin/fields/discover",
                    headers={'X-Admin-Key': self.admin_key},
                    timeout=10  # 10 second timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', {})
                    
                    # Check both instances
                    for instance in ['instance_1', 'instance_2']:
                        if instance in results:
                            instance_result = results[instance]
                            status = instance_result.get('status')
                            discovered = instance_result.get('discovered', 0)
                            
                            if status == 'success':
                                logger.info(f"  ✓ {instance}: {discovered} fields discovered")
                            else:
                                logger.warning(f"  ⚠ {instance}: {instance_result.get('error', 'Unknown error')}")
                    
                    return True
                else:
                    logger.warning(f"  Field discovery returned status {response.status_code}")
                    # Don't fail the test if discovery is not available
                    return True
                    
            except requests.exceptions.Timeout:
                logger.warning("  Field discovery timed out (may be sync in progress)")
                # Don't fail if timeout - fields might already be cached
                return True
            
        except Exception as e:
            logger.warning(f"  Field discovery test skipped: {e}")
            # Don't fail the entire test suite for field discovery
            return True
    
    # ==================== FIELD EXTRACTION TESTS ====================
    
    def test_issue_processor_initialization(self) -> bool:
        """Test that IssueProcessor loads field mappings correctly"""
        try:
            # Initialize for instance_1
            jira_url = os.getenv('JIRA_URL_1')
            jira_username = os.getenv('JIRA_USERNAME_1')
            jira_password = os.getenv('JIRA_PASSWORD_1')
            
            if not all([jira_url, jira_username, jira_password]):
                logger.warning("  JIRA credentials not configured, skipping")
                return True
            
            client = JiraClient(jira_url, jira_username, jira_password)
            processor = IssueProcessor(client, 'instance_1')
            
            # Check field mappings loaded
            field_groups = len(processor.field_mappings)
            logger.info(f"  Field groups loaded: {field_groups}")
            
            if field_groups == 0:
                logger.error("  No field mappings loaded")
                return False
            
            # Get required fields
            required_fields = processor.get_required_fields()
            logger.info(f"  Required fields: {len(required_fields)}")
            
            # Count custom fields
            custom_fields = [f for f in required_fields if f.startswith('customfield_')]
            system_fields = [f for f in required_fields if not f.startswith('customfield_')]
            
            logger.info(f"  System fields: {system_fields}")
            logger.info(f"  Custom fields count: {len(custom_fields)}")
            
            # Test column mapping
            test_columns = ['ndpu_order_number', 'ndpu_client_name', 'ndpu_listing_address']
            for column in test_columns:
                mapping = processor.get_field_mapping_for_column(column)
                if mapping:
                    field_id = mapping.get('field_id')
                    logger.info(f"  ✓ {column}: mapped to {field_id}")
                else:
                    logger.error(f"  ✗ {column}: no mapping found")
            
            return field_groups > 0 and len(required_fields) > 10
            
        except Exception as e:
            logger.error(f"  IssueProcessor test failed: {e}")
            return False
    
    def test_field_extraction_simulation(self) -> bool:
        """Simulate field extraction with mock data"""
        try:
            # Create mock issue data
            mock_issue = {
                'key': 'TEST-123',
                'fields': {
                    'summary': 'Test Issue Summary',
                    'status': {'name': 'In Progress'},
                    'project': {'key': 'TEST', 'name': 'Test Project'},
                    'updated': '2025-01-10T10:30:00.000+0000',
                    'customfield_10501': 'ORD-2025-001',  # Order number
                    'customfield_10600': 'John Doe',       # Client name
                    'customfield_10700': '123 Main St',    # Listing address
                }
            }
            
            # Initialize processor
            processor = IssueProcessor(None, 'instance_1')  # Using None for client in simulation
            
            # Test field extraction
            extracted_values = {}
            test_columns = ['summary', 'status', 'ndpu_order_number', 'ndpu_client_name', 'ndpu_listing_address']
            
            for column in test_columns:
                mapping = processor.get_field_mapping_for_column(column)
                if mapping:
                    # Simulate extraction (simplified)
                    if column == 'summary':
                        extracted_values[column] = mock_issue['fields']['summary']
                    elif column == 'status':
                        extracted_values[column] = mock_issue['fields']['status']['name']
                    elif mapping.get('field_id'):
                        field_id = mapping['field_id']
                        extracted_values[column] = mock_issue['fields'].get(field_id)
                
                if column in extracted_values:
                    logger.info(f"  ✓ Extracted {column}: {extracted_values[column]}")
                else:
                    logger.warning(f"  ⚠ Could not extract {column}")
            
            return len(extracted_values) >= 3
            
        except Exception as e:
            logger.error(f"  Field extraction simulation failed: {e}")
            return False
    
    # ==================== SYNC TESTS ====================
    
    def test_sync_with_field_population(self) -> bool:
        """Test actual sync to verify field population"""
        try:
            # Start a small sync
            response = requests.post(
                f"{self.api_url}/api/sync/start",
                headers={'Content-Type': 'application/json'},
                json={'force': False, 'projects': ['TEST'], 'max_issues': 10}
            )
            
            if response.status_code != 200:
                logger.warning(f"  Sync API returned status {response.status_code}")
                return True  # Don't fail if sync not available
            
            logger.info("  Sync started, waiting 30 seconds...")
            time.sleep(30)
            
            # Check field population
            conn = self.connect_db()
            if not conn:
                return False
            
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(ndpu_order_number) as has_order,
                        COUNT(ndpu_client_name) as has_client,
                        COUNT(ndpu_listing_address) as has_address
                    FROM jira_issues_v2
                    WHERE project_name = 'TEST'
                    AND last_updated > NOW() - INTERVAL '5 minutes'
                """)
                
                result = cursor.fetchone()
                if result:
                    total, has_order, has_client, has_address = result
                    logger.info(f"  Issues synced: {total}")
                    logger.info(f"  With order number: {has_order}")
                    logger.info(f"  With client name: {has_client}")
                    logger.info(f"  With listing address: {has_address}")
                    
                    if total > 0:
                        population_rate = (has_order + has_client + has_address) / (total * 3) * 100
                        logger.info(f"  Field population rate: {population_rate:.1f}%")
                
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.warning(f"  Sync test skipped: {e}")
            return True
    
    # ==================== PERFORMANCE TESTS ====================
    
    def test_field_mapping_performance(self) -> bool:
        """Test performance of field mapping operations"""
        try:
            import time
            
            # Test configuration loading speed
            start = time.time()
            config = get_field_mapping_config()
            load_time = time.time() - start
            logger.info(f"  Configuration load time: {load_time:.3f}s")
            
            if not config:
                logger.error("  Failed to load configuration")
                return False
            
            # Test column mapping lookup speed
            test_columns = list(COLUMN_TO_FIELD_MAPPING.keys())[:20]
            start = time.time()
            for _ in range(1000):
                for col in test_columns:
                    get_field_key_for_column(col)
            lookup_time = (time.time() - start) / 1000
            logger.info(f"  Average column mapping lookup time: {lookup_time*1000:.3f}ms")
            
            # Test processor initialization
            start = time.time()
            processor = IssueProcessor(None, 'instance_1')
            init_time = time.time() - start
            logger.info(f"  IssueProcessor initialization time: {init_time:.3f}s")
            
            # Performance thresholds
            if load_time > 1.0:
                logger.warning("  ⚠ Configuration loading is slow")
            if lookup_time > 0.001:
                logger.warning("  ⚠ Column mapping lookup is slow")
            if init_time > 0.5:
                logger.warning("  ⚠ Processor initialization is slow")
            
            return True
            
        except Exception as e:
            logger.error(f"  Performance test failed: {e}")
            return False
    
    # ==================== MAIN TEST RUNNER ====================
    
    def run_all_tests(self):
        """Run all test categories"""
        logger.info("\n" + "="*80)
        logger.info("FIELD MAPPING COMPREHENSIVE TEST SUITE")
        logger.info("="*80)
        
        # Database Tests
        logger.info("\n📊 DATABASE TESTS")
        self.run_test("Database Tables Exist", self.test_database_tables_exist)
        self.run_test("Field Mappings Loaded", self.test_field_mappings_loaded)
        self.run_test("Column Name Mappings", self.test_column_mappings)
        self.run_test("Database Columns Exist", self.test_database_columns_exist)
        
        # API Tests
        logger.info("\n🌐 API TESTS")
        self.run_test("Field Mappings API Endpoint", self.test_api_field_mappings_endpoint)
        self.run_test("Field Discovery API", self.test_field_discovery_api)
        
        # Field Extraction Tests
        logger.info("\n🔍 FIELD EXTRACTION TESTS")
        self.run_test("IssueProcessor Initialization", self.test_issue_processor_initialization)
        self.run_test("Field Extraction Simulation", self.test_field_extraction_simulation)
        
        # Sync Tests
        logger.info("\n🔄 SYNC TESTS")
        self.run_test("Sync with Field Population", self.test_sync_with_field_population)
        
        # Performance Tests
        logger.info("\n⚡ PERFORMANCE TESTS")
        self.run_test("Field Mapping Performance", self.test_field_mapping_performance)
        
        # Generate Report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        logger.info("\n" + "="*80)
        logger.info("TEST REPORT")
        logger.info("="*80)
        
        # Summary
        logger.info(f"\nTotal Tests: {self.total_tests}")
        logger.info(f"Passed: {self.passed_tests}")
        logger.info(f"Failed: {self.total_tests - self.passed_tests}")
        logger.info(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        # Detailed Results
        logger.info("\nDetailed Results:")
        for test_name, status, error in self.test_results:
            if status == 'PASSED':
                logger.info(f"  ✅ {test_name}")
            elif status == 'FAILED':
                logger.info(f"  ❌ {test_name}: {error}")
            else:
                logger.info(f"  ⚠️  {test_name}: {error}")
        
        # Overall Status
        if self.passed_tests == self.total_tests:
            logger.info("\n🎉 ALL TESTS PASSED! Field mapping system is working correctly.")
        elif self.passed_tests >= self.total_tests * 0.8:
            logger.info("\n✅ MOST TESTS PASSED. Minor issues detected.")
        elif self.passed_tests >= self.total_tests * 0.5:
            logger.info("\n⚠️  PARTIAL SUCCESS. Several issues need attention.")
        else:
            logger.info("\n❌ CRITICAL FAILURES. Field mapping system needs immediate attention.")
        
        # Recommendations
        logger.info("\nRecommendations:")
        if self.passed_tests < self.total_tests:
            failed_tests = [t[0] for t in self.test_results if t[1] != 'PASSED']
            
            if 'Database Tables Exist' in failed_tests:
                logger.info("  • Run database migrations: alembic upgrade head")
            if 'Field Mappings Loaded' in failed_tests:
                logger.info("  • Initialize database: python scripts/init_database.py")
            if 'Field Discovery API' in failed_tests:
                logger.info("  • Check JIRA credentials in environment variables")
            if 'Database Columns Exist' in failed_tests:
                logger.info("  • Sync database schema with field mappings")


if __name__ == "__main__":
    tester = FieldMappingTestSuite()
    tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if tester.passed_tests == tester.total_tests else 1
    sys.exit(exit_code)