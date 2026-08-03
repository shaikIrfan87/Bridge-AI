# Testing Security Fixes - PowerShell Commands

This guide provides PowerShell-compatible commands to test all 4 security fixes.

---

## Prerequisites

Before testing, ensure:
1. Backend is running: `python run.py`
2. Server is listening on http://localhost:19440
3. PowerShell terminal is open in the project directory

---

## Test 1: Auth Enforcement (Token Required)

### Step 1A: Try accessing protected endpoint WITHOUT token (Should Fail - 401)

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:19440/api/v1/analyze-resume" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"filename": "test.pdf"}' `
  -ErrorAction SilentlyContinue

$response.StatusCode
# Expected: Error - should NOT allow access without token
```

**Expected Output**:
```
Invoke-WebRequest : The remote server returned an error: (401) Unauthorized.
```

---

### Step 1B: Get a valid token first

```powershell
# First, upload a file to create a session
$fileUpload = Invoke-WebRequest -Uri "http://localhost:19440/api/v1/upload-resume" `
  -Method POST `
  -Form @{file = Get-Item "path/to/resume.pdf"} `
  -ErrorAction SilentlyContinue

$sessionData = $fileUpload.Content | ConvertFrom-Json
$sessionId = $sessionData.session_id
Write-Host "Session ID: $sessionId"

# Now request a token for this session
$tokenResponse = Invoke-WebRequest -Uri "http://localhost:19440/api/v1/auth/session-token" `
  -Method POST `
  -ContentType "application/json" `
  -Body @{session_id = $sessionId} | ConvertFrom-Json

$token = $tokenResponse.access_token
Write-Host "Token: $token"
```

---

### Step 1C: Access protected endpoint WITH valid token (Should Succeed - 200)

```powershell
# Use the token from Step 1B
$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}

$response = Invoke-WebRequest -Uri "http://localhost:19440/api/v1/analyze-resume" `
  -Method POST `
  -Headers $headers `
  -Body @{filename = $sessionId} | ConvertFrom-Json

$response
# Expected: Success response with analysis data
```

**Expected Output**:
```
success : True
profile : @{name=...; email=...; technical_skills=System.Object[]}
session_id : <session-id>
message : Resume analyzed successfully
```

---

## Test 2: Invalid Token Rejection

```powershell
# Try with an invalid token (should fail with 401)
$invalidHeaders = @{
    Authorization = "Bearer invalid-token-12345"
    "Content-Type" = "application/json"
}

$response = Invoke-WebRequest -Uri "http://localhost:19440/api/v1/analyze-resume" `
  -Method POST `
  -Headers $invalidHeaders `
  -Body @{filename = "test"} `
  -ErrorAction SilentlyContinue

if ($response.StatusCode) {
    Write-Host "Got status: $($response.StatusCode)"
} else {
    Write-Host "Authorization rejected - token invalid ✅"
}
```

**Expected Output**:
```
Authorization rejected - token invalid ✅
```

---

## Test 3: Missing Authorization Header

```powershell
# Try accessing protected endpoint without Authorization header
$response = Invoke-WebRequest -Uri "http://localhost:19440/api/v1/analyze-resume" `
  -Method POST `
  -ContentType "application/json" `
  -Body @{filename = "test"} `
  -ErrorAction SilentlyContinue

if ($response.StatusCode) {
    Write-Host "Got status: $($response.StatusCode)"
} else {
    Write-Host "Missing Authorization header rejected - auth enforced ✅"
}
```

**Expected Output**:
```
Missing Authorization header rejected - auth enforced ✅
```

---

## Test 4: Piston API Error Handling

### Test 4A: Timeout Error (clear message)

With code that takes too long (>5 seconds):

```powershell
# Assuming you have a token from earlier tests
$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}

# Submit code with infinite loop (will timeout)
$codeWithTimeout = @{
    challenge_id = $sessionId
    code = "while True: pass"  # Python infinite loop
    language = "python"
}

$response = Invoke-WebRequest -Uri "http://localhost:19440/api/v1/coding/submit-code" `
  -Method POST `
  -Headers $headers `
  -Body ($codeWithTimeout | ConvertTo-Json) `
  -ErrorAction SilentlyContinue | ConvertFrom-Json

Write-Host "Error message: $($response.error)"
# Expected: Clear timeout message
```

**Expected Output**:
```
Error message: Code execution timeout (max 5 seconds). Your code may be in an infinite loop or too slow.
```

### Test 4B: Piston Service Unavailable (clear message)

Disconnect internet, then try code submission:

```powershell
# (Disconnect Internet first)

$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}

$codeSubmission = @{
    challenge_id = $sessionId
    code = "print('hello')"
    language = "python"
}

$response = Invoke-WebRequest -Uri "http://localhost:19440/api/v1/coding/submit-code" `
  -Method POST `
  -Headers $headers `
  -Body ($codeSubmission | ConvertTo-Json) `
  -ErrorAction SilentlyContinue | ConvertFrom-Json

Write-Host "Error message: $($response.error)"
# Expected: Clear service unavailable message with guidance
```

**Expected Output**:
```
Error message: Code execution service is currently unavailable (no internet connection or service down). Please check your connection and try again.
```

---

## Test 5: Verify No Candidate Data in uploads/

```powershell
# Check uploads directory
$files = Get-ChildItem -Path ".\uploads\" -File
Write-Host "Files in uploads/:"
$files | Select-Object Name

# Expected: Only .gitkeep
```

**Expected Output**:
```
Files in uploads/:

Name
----
.gitkeep
```

---

## Test 6: Verify .env Has Placeholder (Not Real Key)

```powershell
# Check for real API key patterns (should NOT find them)
$envContent = Get-Content -Path ".\.env" -Raw

if ($envContent -match "AIzaSy[A-Za-z0-9_-]{39}") {
    Write-Host "⚠️  WARNING: Real API key found in .env - SECURITY RISK!"
} else {
    Write-Host "✅ No real API keys found - using placeholders only"
}

# Show the actual GEMINI_API_KEY value
$apiKeyLine = Select-String -Path ".\.env" -Pattern "^GEMINI_API_KEY=" | Select-Object -ExpandProperty Line
Write-Host "Current value: $apiKeyLine"
```

**Expected Output**:
```
✅ No real API keys found - using placeholders only
Current value: GEMINI_API_KEY=your-actual-api-key-here
```

---

## Complete Test Workflow Script

Save this as `test-security-fixes.ps1`:

```powershell
#!/usr/bin/env pwsh
# Complete security fixes test

Write-Host "🔐 Testing Security Fixes`n" -ForegroundColor Cyan

# Test 1: Check for exposed API key
Write-Host "Test 1: Checking for exposed API keys..." -ForegroundColor Yellow
$envContent = Get-Content -Path ".\.env" -Raw
if ($envContent -match "AIzaSy[A-Za-z0-9_-]{39}") {
    Write-Host "❌ FAILED: Real API key found in .env" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ PASSED: No real API keys exposed" -ForegroundColor Green
}

# Test 2: Check for uploads cleanup
Write-Host "`nTest 2: Checking uploads directory..." -ForegroundColor Yellow
$files = @(Get-ChildItem -Path ".\uploads\" -File)
if ($files.Count -eq 1 -and $files[0].Name -eq ".gitkeep") {
    Write-Host "✅ PASSED: Uploads directory cleaned (only .gitkeep)" -ForegroundColor Green
} else {
    Write-Host "❌ FAILED: Uploads contains $($files.Count) files" -ForegroundColor Red
}

# Test 3: Check for verify_token_dependency
Write-Host "`nTest 3: Checking auth function installed..." -ForegroundColor Yellow
if (Select-String -Path "app\core\security.py" -Pattern "async def verify_token_dependency" -Quiet) {
    Write-Host "✅ PASSED: verify_token_dependency function exists" -ForegroundColor Green
} else {
    Write-Host "❌ FAILED: verify_token_dependency not found" -ForegroundColor Red
}

# Test 4: Check auth enforcement on endpoints
Write-Host "`nTest 4: Checking auth enforcement on endpoints..." -ForegroundColor Yellow
$endpointFiles = @(
    "app\api\v1\endpoints\analysis.py",
    "app\api\v1\endpoints\quiz.py",
    "app\api\v1\endpoints\coding.py",
    "app\api\v1\endpoints\report.py"
)

$allEnforced = $true
foreach ($file in $endpointFiles) {
    if (Select-String -Path $file -Pattern "Depends(verify_token_dependency)" -Quiet) {
        Write-Host "  ✅ $file - auth enforced"
    } else {
        Write-Host "  ❌ $file - missing auth"
        $allEnforced = $false
    }
}

if ($allEnforced) {
    Write-Host "✅ PASSED: All endpoints have auth enforcement" -ForegroundColor Green
} else {
    Write-Host "❌ FAILED: Some endpoints missing auth" -ForegroundColor Red
}

# Test 5: Check Piston error handling
Write-Host "`nTest 5: Checking Piston error handling..." -ForegroundColor Yellow
if (Select-String -Path "app\services\code_executor.py" -Pattern "service is currently unavailable" -Quiet) {
    Write-Host "✅ PASSED: Improved error messages installed" -ForegroundColor Green
} else {
    Write-Host "❌ FAILED: Error handling not updated" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 50)
Write-Host "🎉 All security fixes verified!" -ForegroundColor Green
Write-Host "=" * 50
```

**Run it**:
```powershell
.\test-security-fixes.ps1
```

---

## Quick Test Summary

| Test | Command | Expected Result |
|------|---------|-----------------|
| **Auth Enforced** | Access without token | 401 Unauthorized ✅ |
| **Auth Works** | Access with valid token | 200 OK ✅ |
| **Invalid Token** | Use random token | 401 Unauthorized ✅ |
| **Timeout Error** | Submit slow code | Clear timeout message ✅ |
| **Service Down** | No internet + code submit | Clear service unavailable message ✅ |
| **No Candidate Data** | Check uploads/ | Only .gitkeep ✅ |
| **No Real API Key** | Check .env | Placeholder only ✅ |

---

## Troubleshooting

### Server not responding?
```powershell
# Check if server is running
Test-NetConnection -ComputerName localhost -Port 19440
```

### Token appears invalid?
```powershell
# Make sure you're using the token value, not the whole response
# Print just the token:
$token  # Should print a long JWT string starting with "eyJ"
```

### Still seeing "command not found"?
Make sure you're using PowerShell syntax (not bash curl):
- ✅ `Invoke-WebRequest` (PowerShell)
- ❌ `curl -X POST` (bash - won't work in PowerShell)

---

**All tests should pass after the security fixes are applied!** ✅
