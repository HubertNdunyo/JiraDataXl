#!/usr/bin/env python3
"""
Test script for INUA Testing interface API endpoints
"""
import requests
import json
import time
from datetime import datetime

def test_inua_api():
    """Test the INUA testing API endpoints"""
    base_url = "http://localhost:8987/api/admin/inua-test"
    
    print("\n" + "="*60)
    print("Testing INUA Interface API")
    print("="*60)
    
    # Test 1: Get workflow info
    print("\n1. Testing workflow info endpoint...")
    try:
        response = requests.get(f"{base_url}/workflow-info")
        if response.status_code == 200:
            print("✅ Workflow info retrieved successfully")
            workflow = response.json()
            print(f"   - {len(workflow['workflow'])} workflow steps found")
            print(f"   - {len(workflow['field_info'])} field definitions found")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 2: Create issue
    print("\n2. Testing issue creation...")
    issue_key = None
    try:
        test_summary = f"API Test - {datetime.now().strftime('%H:%M:%S')}"
        response = requests.post(
            f"{base_url}/create-issue",
            json={"summary": test_summary}
        )
        if response.status_code == 200:
            data = response.json()
            issue_key = data['key']
            print(f"✅ Issue created: {issue_key}")
            print(f"   - Status: {data['status']}")
            print(f"   - Transitions: {len(data['transitions'])}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 3: Get issue details
    if issue_key:
        print(f"\n3. Testing get issue details for {issue_key}...")
        try:
            response = requests.get(f"{base_url}/issue/{issue_key}")
            if response.status_code == 200:
                print("✅ Issue details retrieved")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # Test 4: Transition issue
    if issue_key:
        print(f"\n4. Testing issue transition...")
        try:
            response = requests.post(
                f"{base_url}/transition",
                json={
                    "issue_key": issue_key,
                    "target_status": "ACKNOWLEDGED",
                    "comment": "Test transition via API"
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print(f"✅ Transition successful: {data['message']}")
                else:
                    print(f"❌ Transition failed: {data['message']}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # Test 5: Delete issue
    if issue_key:
        print(f"\n5. Testing issue deletion...")
        time.sleep(1)  # Brief pause
        try:
            response = requests.delete(f"{base_url}/issue/{issue_key}")
            if response.status_code == 200:
                print(f"✅ Issue {issue_key} deleted")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("API tests completed")
    print("="*60)

if __name__ == "__main__":
    print("\n🧪 Testing INUA Interface API...")
    print("Make sure the FastAPI backend is running on port 8987")
    
    try:
        # Check if backend is running
        response = requests.get("http://localhost:8987/health")
        if response.status_code == 200:
            print("✅ Backend is running")
            test_inua_api()
        else:
            print("❌ Backend health check failed")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend on localhost:8987")
        print("Please start the backend with: cd backend && python main.py")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")