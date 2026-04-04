# Test script for Smart Bookmark Manager (PowerShell)
# Run this after docker-compose up to verify all components

$API_BASE = "http://localhost:8000"
$FRONTEND_BASE = "http://localhost:80"
$PASS = 0
$FAIL = 0

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Smart Bookmark Manager - Component Tests" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Backend Health Check
Write-Host -NoNewline "Test 1: Backend health check... "
try {
    $response = Invoke-WebRequest -Uri "$API_BASE/health" -Method Get -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "PASS" -ForegroundColor Green
        $PASS++
    }
} catch {
    Write-Host "FAIL" -ForegroundColor Red
    $FAIL++
}

# Test 2: Frontend accessible
Write-Host -NoNewline "Test 2: Frontend accessible... "
try {
    $response = Invoke-WebRequest -Uri "$FRONTEND_BASE" -Method Get -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "PASS" -ForegroundColor Green
        $PASS++
    }
} catch {
    Write-Host "FAIL" -ForegroundColor Red
    $FAIL++
}

# Test 3: Register user
Write-Host -NoNewline "Test 3: Register new user... "
try {
    $body = @{email="test@example.com"; username="testuser"; password="testpass123"} | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$API_BASE/auth/register" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "PASS" -ForegroundColor Green
        $PASS++
        $registerData = $response.Content | ConvertFrom-Json
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "PASS (already exists)" -ForegroundColor Yellow
        $PASS++
    } else {
        Write-Host "FAIL" -ForegroundColor Red
        $FAIL++
    }
}

# Test 4: Login
Write-Host -NoNewline "Test 4: Login with registered user... "
$TOKEN = ""
try {
    $body = @{email="test@example.com"; password="testpass123"} | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$API_BASE/auth/login" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $loginData = $response.Content | ConvertFrom-Json
        $TOKEN = $loginData.access_token
        Write-Host "PASS" -ForegroundColor Green
        $PASS++
    }
} catch {
    Write-Host "FAIL" -ForegroundColor Red
    $FAIL++
}

# Test 5: List bookmarks (empty)
Write-Host -NoNewline "Test 5: List bookmarks (empty)... "
if ($TOKEN) {
    try {
        $headers = @{Authorization = "Bearer $TOKEN"}
        $response = Invoke-WebRequest -Uri "$API_BASE/bookmarks" -Method Get -Headers $headers -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "PASS" -ForegroundColor Green
            $PASS++
        }
    } catch {
        Write-Host "FAIL" -ForegroundColor Red
        $FAIL++
    }
} else {
    Write-Host "SKIP (no token)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Results: $PASS passed, $FAIL failed" -ForegroundColor $(if ($FAIL -eq 0) {"Green"} else {"Red"})
Write-Host "=========================================" -ForegroundColor Cyan

if ($FAIL -gt 0) {
    exit 1
}
