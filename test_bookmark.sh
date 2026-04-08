#!/bin/bash
# Test script to verify bookmark creation with the provided URL

BASE_URL="http://localhost:8000"
TEST_URL="https://azbyka.ru/garden/15-prostyh-idej-dlya-ogoroda-kak-uvelichit-urozhaj/"

echo "================================================================================"
echo "Testing Bookmark Creation Flow"
echo "================================================================================"

# Step 1: Register a test user
echo ""
echo "[1/4] Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "username": "testuser"
  }')

echo "Register response: $REGISTER_RESPONSE"

# Step 2: Login
echo ""
echo "[2/4] Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }')

echo "Login response: $LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "✗ Failed to get access token"
  exit 1
fi

echo "✓ Got access token"

# Step 3: Create bookmark
echo ""
echo "[3/4] Creating bookmark for URL: $TEST_URL"
echo "This will call the LLM with coder-model..."
BOOKMARK_RESPONSE=$(curl -s -X POST "$BASE_URL/api/bookmarks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"url\": \"$TEST_URL\"}")

echo "Bookmark response: $BOOKMARK_RESPONSE"

# Check if response contains required fields
if echo "$BOOKMARK_RESPONSE" | grep -q '"title"'; then
  echo "✓ Bookmark created successfully"
  
  # Extract and display bookmark details
  TITLE=$(echo $BOOKMARK_RESPONSE | grep -o '"title":"[^"]*' | cut -d'"' -f4)
  SUMMARY=$(echo $BOOKMARK_RESPONSE | grep -o '"summary":"[^"]*' | cut -d'"' -f4)
  TAGS=$(echo $BOOKMARK_RESPONSE | grep -o '"tags":\[[^]]*\]' | head -1)
  CATEGORIES=$(echo $BOOKMARK_RESPONSE | grep -o '"categories":\[[^]]*\]' | head -1)
  
  echo ""
  echo "Bookmark Details:"
  echo "  Title: $TITLE"
  echo "  Summary: $SUMMARY"
  echo "  Tags: $TAGS"
  echo "  Categories: $CATEGORIES"
else
  echo "✗ Failed to create bookmark"
  echo "Response: $BOOKMARK_RESPONSE"
  exit 1
fi

# Step 4: List bookmarks
echo ""
echo "[4/4] Listing bookmarks..."
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/api/bookmarks" \
  -H "Authorization: Bearer $TOKEN")

echo "List response: $LIST_RESPONSE"

if echo "$LIST_RESPONSE" | grep -q '"title"'; then
  echo "✓ Bookmarks listed successfully"
else
  echo "✗ Failed to list bookmarks"
  exit 1
fi

echo ""
echo "================================================================================"
echo "✓ ALL TESTS PASSED!"
echo "================================================================================"
