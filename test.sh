#!/bin/bash
# Test script for Smart Bookmark Manager
# Run this after docker-compose up to verify all components

set -e

API_BASE="http://localhost:8000"
FRONTEND_BASE="http://localhost:80"
PASS=0
FAIL=0

echo "========================================="
echo "Smart Bookmark Manager - Component Tests"
echo "========================================="
echo ""

# Test 1: Backend Health Check
echo -n "Test 1: Backend health check... "
if curl -sf "$API_BASE/health" > /dev/null; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL"
    FAIL=$((FAIL + 1))
fi

# Test 2: Frontend accessible
echo -n "Test 2: Frontend accessible... "
if curl -sf "$FRONTEND_BASE" > /dev/null; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL"
    FAIL=$((FAIL + 1))
fi

# Test 3: Register user
echo -n "Test 3: Register new user... "
REGISTER_RESPONSE=$(curl -sf -X POST "$API_BASE/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}' \
    -o /tmp/register_response.json 2>&1) || true

if [ -f /tmp/register_response.json ] && grep -q "id" /tmp/register_response.json; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $REGISTER_RESPONSE)"
    FAIL=$((FAIL + 1))
fi

# Test 4: Login
echo -n "Test 4: Login with registered user... "
LOGIN_RESPONSE=$(curl -sf -X POST "$API_BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"testpass123"}' \
    -o /tmp/login_response.json 2>&1) || true

TOKEN=""
if [ -f /tmp/login_response.json ] && grep -q "access_token" /tmp/login_response.json; then
    TOKEN=$(grep -o '"access_token":"[^"]*"' /tmp/login_response.json | cut -d'"' -f4)
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL (Response: $LOGIN_RESPONSE)"
    FAIL=$((FAIL + 1))
fi

# Test 5: List bookmarks (empty)
echo -n "Test 5: List bookmarks (empty)... "
if [ -n "$TOKEN" ]; then
    BOOKMARKS_RESPONSE=$(curl -sf "$API_BASE/bookmarks" \
        -H "Authorization: Bearer $TOKEN" \
        -o /tmp/bookmarks_response.json 2>&1) || true
    if [ -f /tmp/bookmarks_response.json ]; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL"
        FAIL=$((FAIL + 1))
    fi
else
    echo "SKIP (no token)"
fi

# Summary
echo ""
echo "========================================="
echo "Results: $PASS passed, $FAIL failed"
echo "========================================="

# Cleanup
rm -f /tmp/register_response.json /tmp/login_response.json /tmp/bookmarks_response.json

if [ $FAIL -gt 0 ]; then
    exit 1
fi
