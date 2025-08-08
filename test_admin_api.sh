#!/bin/bash

# Test admin API endpoints

echo "Testing admin API with configured key..."

# Test field mappings endpoint
echo -e "\n1. Testing GET /api/admin/config/field-mappings"
curl -X GET http://localhost:8987/api/admin/config/field-mappings \
  -H "X-Admin-Key: jira-admin-key-2024" \
  -H "Content-Type: application/json" | jq .

# Test sync config endpoint  
echo -e "\n\n2. Testing GET /api/admin/config/sync"
curl -X GET http://localhost:8987/api/admin/config/sync \
  -H "X-Admin-Key: jira-admin-key-2024" \
  -H "Content-Type: application/json" | jq .

# Test backups endpoint
echo -e "\n\n3. Testing GET /api/admin/config/backups"
curl -X GET http://localhost:8987/api/admin/config/backups \
  -H "X-Admin-Key: jira-admin-key-2024" \
  -H "Content-Type: application/json" | jq .