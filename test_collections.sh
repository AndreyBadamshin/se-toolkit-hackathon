#!/bin/bash
# Test script for collections and bookmark-to-collection functionality
# Run this after docker-compose up to verify all components

set -e

API_BASE="http://localhost:8000"
PASS=0
FAIL=0
TOKEN=""

echo "========================================="
echo "Collections & Bookmarks Integration Tests"
echo "========================================="
echo ""

# Helper function to extract JSON value
extract_json() {
    local key=$1
    local file=$2
    grep -o "\"${key}\":[^,}]*" "$file" | head -1 | cut -d':' -f2 | tr -d '"' | tr -d ' '
}

# Test 1: Backend Health Check
echo -n "Test 1: Backend health check... "
if curl -sf "$API_BASE/health" > /dev/null; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL"
    FAIL=$((FAIL + 1))
    exit 1
fi

# Test 2: Register user
echo -n "Test 2: Register new user... "
REGISTER_RESPONSE=$(curl -sf -X POST "$API_BASE/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"test_collections@example.com","username":"testcollections","password":"testpass123"}' \
    -o /tmp/register_response.json 2>&1) || true

if [ -f /tmp/register_response.json ] && grep -q "id" /tmp/register_response.json; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $(cat /tmp/register_response.json 2>/dev/null || echo 'No response'))"
    FAIL=$((FAIL + 1))
fi

# Test 3: Login
echo -n "Test 3: Login with registered user... "
LOGIN_RESPONSE=$(curl -sf -X POST "$API_BASE/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"test_collections@example.com","password":"testpass123"}' \
    -o /tmp/login_response.json 2>&1) || true

if [ -f /tmp/login_response.json ] && grep -q "access_token" /tmp/login_response.json; then
    TOKEN=$(python3 -c "import json; data=json.load(open('/tmp/login_response.json')); print(data['access_token'])" 2>/dev/null || \
            grep -o '"access_token":"[^"]*"' /tmp/login_response.json | cut -d'"' -f4)
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $(cat /tmp/login_response.json 2>/dev/null || echo 'No response'))"
    FAIL=$((FAIL + 1))
fi

if [ -z "$TOKEN" ]; then
    echo "Cannot continue without authentication token"
    exit 1
fi

# Test 4: Create first collection
echo -n "Test 4: Create first collection... "
COLLECTION1_RESPONSE=$(curl -sf -X POST "$API_BASE/api/collections" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"name":"Work","color":"#FF5733"}' \
    -o /tmp/collection1_response.json 2>&1) || true

COLLECTION1_ID=""
if [ -f /tmp/collection1_response.json ] && grep -q "id" /tmp/collection1_response.json; then
    COLLECTION1_ID=$(extract_json "id" /tmp/collection1_response.json)
    echo "PASS (Collection ID: $COLLECTION1_ID)"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $(cat /tmp/collection1_response.json 2>/dev/null || echo 'No response'))"
    FAIL=$((FAIL + 1))
fi

# Test 5: Create second collection
echo -n "Test 5: Create second collection... "
COLLECTION2_RESPONSE=$(curl -sf -X POST "$API_BASE/api/collections" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"name":"Personal","color":"#33FF57"}' \
    -o /tmp/collection2_response.json 2>&1) || true

COLLECTION2_ID=""
if [ -f /tmp/collection2_response.json ] && grep -q "id" /tmp/collection2_response.json; then
    COLLECTION2_ID=$(extract_json "id" /tmp/collection2_response.json)
    echo "PASS (Collection ID: $COLLECTION2_ID)"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $(cat /tmp/collection2_response.json 2>/dev/null || echo 'No response'))"
    FAIL=$((FAIL + 1))
fi

# Test 6: List collections
echo -n "Test 6: List all collections... "
LIST_RESPONSE=$(curl -sf "$API_BASE/api/collections" \
    -H "Authorization: Bearer $TOKEN" \
    -o /tmp/list_collections.json 2>&1) || true

if [ -f /tmp/list_collections.json ] && grep -q "Work" /tmp/list_collections.json && grep -q "Personal" /tmp/list_collections.json; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $(cat /tmp/list_collections.json 2>/dev/null || echo 'No response'))"
    FAIL=$((FAIL + 1))
fi

# Test 7: Create a bookmark
echo -n "Test 7: Create a bookmark... "
BOOKMARK_RESPONSE=$(curl -sf -X POST "$API_BASE/api/bookmarks" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"url":"https://example.com"}' \
    -o /tmp/bookmark_response.json 2>&1) || true

BOOKMARK_ID=""
if [ -f /tmp/bookmark_response.json ] && grep -q "id" /tmp/bookmark_response.json; then
    BOOKMARK_ID=$(extract_json "id" /tmp/bookmark_response.json)
    echo "PASS (Bookmark ID: $BOOKMARK_ID)"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $(cat /tmp/bookmark_response.json 2>/dev/null || echo 'No response'))"
    FAIL=$((FAIL + 1))
fi

# Test 8: Add bookmark to first collection
echo -n "Test 8: Add bookmark to first collection... "
if [ -n "$BOOKMARK_ID" ] && [ -n "$COLLECTION1_ID" ]; then
    ADD_RESPONSE=$(curl -sf -X POST "$API_BASE/api/collections/${COLLECTION1_ID}/bookmarks/${BOOKMARK_ID}" \
        -H "Authorization: Bearer $TOKEN" \
        -o /tmp/add_bookmark_response.json 2>&1) || true
    
    if [ -f /tmp/add_bookmark_response.json ] && grep -q "message" /tmp/add_bookmark_response.json; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (Response: $(cat /tmp/add_bookmark_response.json 2>/dev/null || echo 'No response'))"
        FAIL=$((FAIL + 1))
    fi
else
    echo "SKIP (missing bookmark or collection ID)"
fi

# Test 9: Add bookmark to second collection
echo -n "Test 9: Add bookmark to second collection... "
if [ -n "$BOOKMARK_ID" ] && [ -n "$COLLECTION2_ID" ]; then
    ADD_RESPONSE=$(curl -sf -X POST "$API_BASE/api/collections/${COLLECTION2_ID}/bookmarks/${BOOKMARK_ID}" \
        -H "Authorization: Bearer $TOKEN" \
        -o /tmp/add_bookmark2_response.json 2>&1) || true
    
    if [ -f /tmp/add_bookmark2_response.json ] && grep -q "message" /tmp/add_bookmark2_response.json; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (Response: $(cat /tmp/add_bookmark2_response.json 2>/dev/null || echo 'No response'))"
        FAIL=$((FAIL + 1))
    fi
else
    echo "SKIP (missing bookmark or collection ID)"
fi

# Test 10: Get bookmarks in first collection
echo -n "Test 10: Get bookmarks in first collection... "
if [ -n "$COLLECTION1_ID" ]; then
    GET_RESPONSE=$(curl -sf "$API_BASE/api/collections/${COLLECTION1_ID}/bookmarks" \
        -H "Authorization: Bearer $TOKEN" \
        -o /tmp/get_collection_bookmarks.json 2>&1) || true
    
    if [ -f /tmp/get_collection_bookmarks.json ] && [ "$(cat /tmp/get_collection_bookmarks.json)" != "[]" ]; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (Response: $(cat /tmp/get_collection_bookmarks.json 2>/dev/null || echo 'No response'))"
        FAIL=$((FAIL + 1))
    fi
else
    echo "SKIP (missing collection ID)"
fi

# Test 11: Verify bookmark still exists after collection operations
echo -n "Test 11: Verify bookmark still exists... "
if [ -n "$BOOKMARK_ID" ]; then
    VERIFY_RESPONSE=$(curl -sf "$API_BASE/api/bookmarks/${BOOKMARK_ID}" \
        -H "Authorization: Bearer $TOKEN" \
        -o /tmp/verify_bookmark.json 2>&1) || true
    
    if [ -f /tmp/verify_bookmark.json ] && grep -q "id" /tmp/verify_bookmark.json; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (Response: $(cat /tmp/verify_bookmark.json 2>/dev/null || echo 'No response'))"
        FAIL=$((FAIL + 1))
    fi
else
    echo "SKIP (missing bookmark ID)"
fi

# Test 12: Delete first collection
echo -n "Test 12: Delete first collection... "
if [ -n "$COLLECTION1_ID" ]; then
    DELETE_RESPONSE=$(curl -sf -X DELETE "$API_BASE/api/collections/${COLLECTION1_ID}" \
        -H "Authorization: Bearer $TOKEN" \
        -o /tmp/delete_collection.json \
        -w "%{http_code}" 2>&1) || true
    
    if echo "$DELETE_RESPONSE" | grep -q "204"; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (HTTP Status: $DELETE_RESPONSE)"
        FAIL=$((FAIL + 1))
    fi
else
    echo "SKIP (missing collection ID)"
fi

# Test 13: Verify bookmark still exists after collection deletion
echo -n "Test 13: Verify bookmark still exists after collection deletion... "
if [ -n "$BOOKMARK_ID" ]; then
    VERIFY_RESPONSE=$(curl -sf "$API_BASE/api/bookmarks/${BOOKMARK_ID}" \
        -H "Authorization: Bearer $TOKEN" \
        -o /tmp/verify_bookmark_after_delete.json 2>&1) || true
    
    if [ -f /tmp/verify_bookmark_after_delete.json ] && grep -q "id" /tmp/verify_bookmark_after_delete.json; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (Response: $(cat /tmp/verify_bookmark_after_delete.json 2>/dev/null || echo 'No response'))"
        FAIL=$((FAIL + 1))
    fi
else
    echo "SKIP (missing bookmark ID)"
fi

# Test 14: Verify second collection still exists
echo -n "Test 14: Verify second collection still exists... "
if [ -n "$COLLECTION2_ID" ]; then
    VERIFY_COL_RESPONSE=$(curl -sf "$API_BASE/api/collections/${COLLECTION2_ID}" \
        -H "Authorization: Bearer $TOKEN" \
        -o /tmp/verify_collection.json 2>&1) || true
    
    if [ -f /tmp/verify_collection.json ] && grep -q "Personal" /tmp/verify_collection.json; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL (Response: $(cat /tmp/verify_collection.json 2>/dev/null || echo 'No response'))"
        FAIL=$((FAIL + 1))
    fi
else
    echo "SKIP (missing collection ID)"
fi

# Test 15: List remaining collections
echo -n "Test 15: List remaining collections... "
LIST_FINAL=$(curl -sf "$API_BASE/api/collections" \
    -H "Authorization: Bearer $TOKEN" \
    -o /tmp/list_collections_final.json 2>&1) || true

if [ -f /tmp/list_collections_final.json ] && grep -q "Personal" /tmp/list_collections_final.json && ! grep -q "Work" /tmp/list_collections_final.json; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $(cat /tmp/list_collections_final.json 2>/dev/null || echo 'No response'))"
    FAIL=$((FAIL + 1))
fi

# Summary
echo ""
echo "========================================="
echo "Results: $PASS passed, $FAIL failed"
echo "========================================="

# Cleanup
rm -f /tmp/register_response.json /tmp/login_response.json \
      /tmp/collection1_response.json /tmp/collection2_response.json \
      /tmp/list_collections.json /tmp/bookmark_response.json \
      /tmp/add_bookmark_response.json /tmp/add_bookmark2_response.json \
      /tmp/get_collection_bookmarks.json /tmp/verify_bookmark.json \
      /tmp/delete_collection.json /tmp/verify_bookmark_after_delete.json \
      /tmp/verify_collection.json /tmp/list_collections_final.json

if [ $FAIL -gt 0 ]; then
    exit 1
fi

exit 0
