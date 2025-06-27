#!/usr/bin/env python3
"""Test the sync history API endpoints"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:3545"

def test_sync_history():
    """Test the sync history endpoint"""
    print("Testing /api/sync/history endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sync/history")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total syncs: {data.get('total', 0)}")
            print(f"Current page: {data.get('page', 1)}")
            print(f"Has next page: {data.get('has_next', False)}")
            
            syncs = data.get('syncs', [])
            print(f"\nFound {len(syncs)} sync records:")
            
            for i, sync in enumerate(syncs[:5]):  # Show first 5
                print(f"\n{i+1}. Project: {sync.get('project_key', 'N/A')}")
                print(f"   Status: {sync.get('status', 'Unknown')}")
                print(f"   Duration: {sync.get('duration', 0):.2f}s")
                print(f"   Records: {sync.get('records_processed', 0)}")
                print(f"   Time: {sync.get('last_update_time', 'N/A')}")
                if sync.get('error_message'):
                    print(f"   Error: {sync['error_message'][:100]}...")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_sync_stats():
    """Test the sync stats endpoint"""
    print("\n\nTesting /api/sync/stats endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sync/stats?days=7")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"\nStats for last {stats.get('period_days', 7)} days:")
            print(f"Total syncs: {stats.get('total_syncs', 0)}")
            print(f"Successful: {stats.get('successful_syncs', 0)}")
            print(f"Failed: {stats.get('failed_syncs', 0)}")
            print(f"Empty: {stats.get('empty_syncs', 0)}")
            print(f"Success rate: {stats.get('success_rate', 0):.1f}%")
            print(f"Average duration: {stats.get('average_duration', 0):.2f}s")
            
            print(f"\nToday's stats:")
            today = stats.get('today', {})
            print(f"Total: {today.get('total', 0)}")
            print(f"Successful: {today.get('successful', 0)}")
            
            print(f"\nSyncs by day:")
            syncs_by_day = stats.get('syncs_by_day', {})
            for day, count in sorted(syncs_by_day.items()):
                print(f"  {day}: {count} syncs")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Testing Sync History API Endpoints")
    print("=" * 40)
    test_sync_history()
    test_sync_stats()