#!/bin/bash
set -e

SUFFIX=$RANDOM
USER="user$SUFFIX"
EMAIL="user$SUFFIX@example.com"
PASS="password123"

echo "User: $USER"

# Register
echo "Registering..."
REG_RESP=$(curl -s -X POST "http://localhost:8000/api/v1/register" \
     -H "Content-Type: application/json" \
     -d "{\"email\":\"$EMAIL\", \"password\":\"$PASS\", \"full_name\":\"Test User\", \"username\":\"$USER\"}")
echo "Reg Resp: $REG_RESP"

# Login
echo "Logging in..."
TOKEN_JSON=$(curl -s -X POST "http://localhost:8000/api/v1/login/access-token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=$USER&password=$PASS")
     
TOKEN=$(echo $TOKEN_JSON | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
    echo "Login failed: $TOKEN_JSON"
    exit 1
fi
echo "Token obtained."

# Get Route
echo "Getting routes..."
ROUTES_JSON=$(curl -s -X GET "http://localhost:8000/api/v1/routes/" -H "Authorization: Bearer $TOKEN")
ROUTE_ID=$(echo $ROUTES_JSON | python3 -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")
echo "Route ID: $ROUTE_ID"

# Start Route
echo "Starting route..."
curl -v -X POST "http://localhost:8000/api/v1/progress/" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d "{\"route_id\": $ROUTE_ID, \"status\": \"started\"}"

# List Progress
echo "Listing progress..."
curl -s -X GET "http://localhost:8000/api/v1/progress/" \
     -H "Authorization: Bearer $TOKEN"
