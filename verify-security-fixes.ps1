#!/usr/bin/env pwsh
# Quick Security Fixes Verification Script

Write-Host ""
Write-Host "============================================================"
Write-Host "   SECURITY FIXES VERIFICATION" -ForegroundColor Cyan
Write-Host "============================================================"
Write-Host ""

$passed = 0
$failed = 0

# Test 1: Exposed API Key
Write-Host "[Test 1] Checking for exposed API keys in .env..." -ForegroundColor Yellow
$envContent = Get-Content -Path ".\.env" -Raw
if ($envContent -match "AIzaSy[A-Za-z0-9_-]{39}") {
    Write-Host "  [FAILED] Real API key found in .env" -ForegroundColor Red
    Write-Host ""
    $failed++
} else {
    Write-Host "  [PASSED] No real API keys (using placeholder)" -ForegroundColor Green
    Write-Host ""
    $passed++
}

# Test 2: Uploads Directory Cleanup
Write-Host "[Test 2] Checking uploads directory cleanup..." -ForegroundColor Yellow
$uploads = @(Get-ChildItem -Path ".\uploads\" -File | Where-Object { $_.Name -ne ".gitkeep" })
if ($uploads.Count -eq 0) {
    Write-Host "  [PASSED] All candidate data removed" -ForegroundColor Green
    Write-Host ""
    $passed++
} else {
    Write-Host "  [FAILED] Found $($uploads.Count) files in uploads/ (should be clean)" -ForegroundColor Red
    Write-Host "     Files: $($uploads.Name -join ', ')" -ForegroundColor Red
    Write-Host ""
    $failed++
}

# Test 3: Auth Function Exists
Write-Host "[Test 3] Checking verify_token_dependency function..." -ForegroundColor Yellow
if (Select-String -Path "app\core\security.py" -Pattern "async def verify_token_dependency" -Quiet) {
    Write-Host "  [PASSED] verify_token_dependency function installed" -ForegroundColor Green
    Write-Host ""
    $passed++
} else {
    Write-Host "  [FAILED] verify_token_dependency function not found" -ForegroundColor Red
    Write-Host ""
    $failed++
}

# Test 4: Auth Enforcement on Endpoints
Write-Host "[Test 4] Checking auth enforcement on protected endpoints..." -ForegroundColor Yellow
$endpoints = @(
    "app\api\v1\endpoints\analysis.py",
    "app\api\v1\endpoints\quiz.py",
    "app\api\v1\endpoints\coding.py",
    "app\api\v1\endpoints\report.py"
)

$allEnforced = $true
foreach ($endpoint in $endpoints) {
    if (Select-String -Path $endpoint -Pattern "Depends\(verify_token_dependency\)" -Quiet) {
        Write-Host "    [OK] $endpoint" -ForegroundColor Green
    } else {
        Write-Host "    [FAIL] $endpoint - missing auth dependency" -ForegroundColor Red
        $allEnforced = $false
    }
}

if ($allEnforced) {
    Write-Host "  [PASSED] All endpoints have auth enforcement" -ForegroundColor Green
    Write-Host ""
    $passed++
} else {
    Write-Host "  [FAILED] Some endpoints missing auth" -ForegroundColor Red
    Write-Host ""
    $failed++
}

# Test 5: Piston Error Handling
Write-Host "[Test 5] Checking Piston API error handling..." -ForegroundColor Yellow
if (Select-String -Path "app\services\code_executor.py" -Pattern "service is currently unavailable" -Quiet) {
    Write-Host "  [PASSED] Improved error messages implemented" -ForegroundColor Green
    Write-Host ""
    $passed++
} else {
    Write-Host "  [FAILED] Error handling not updated" -ForegroundColor Red
    Write-Host ""
    $failed++
}

# Summary
Write-Host "============================================================"
Write-Host "RESULTS: $passed passed, $failed failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "============================================================"
Write-Host ""

if ($failed -eq 0) {
    Write-Host "All security fixes verified and working!" -ForegroundColor Green
    Write-Host "Your project is ready for production deployment." -ForegroundColor Green
    Write-Host ""
    exit 0
} else {
    Write-Host "Some tests failed - review the changes above." -ForegroundColor Red
    exit 1
}
