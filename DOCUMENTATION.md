# Complete Documentation - Skill Assessment System

**Version**: 2.0 (Production Ready)  
**Last Updated**: 2026-04-07

---

## Table of Contents
1. [Quick Start Guide](#quick-start-guide)
2. [System Architecture](#system-architecture)
3. [Security Implementation](#security-implementation)
4. [Deployment & Setup](#deployment--setup)
5. [API Reference](#api-reference)
6. [Troubleshooting](#troubleshooting)
7. [Frontend Guide](#frontend-guide)

---

## Quick Start Guide

### Prerequisites
- Python 3.9+
- pip package manager
- Modern web browser

### Step 1: Install Dependencies
```bash
cd c:\Users\ijgam\Downloads\res\res
pip install -r requirements.txt
```

**Expected Output**:
```
Successfully installed fastapi-0.109.0 uvicorn-0.27.0 PyJWT-2.8.1 ...
```

### Step 2: Configure Environment

Copy `.env.example` to `.env` and update values:
```bash
copy .env.example .env
```

Edit `.env` with your actual values:
1. **Get Gemini API key** from https://aistudio.google.com/apikey
2. **Generate SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Paste values into `.env`**:
   ```bash
   API_DEBUG=False
   SECRET_KEY=<your-generated-key>
   GEMINI_API_KEY=<your-api-key>
   ```

### Step 3: Start the Server
```bash
python run.py
```

**Expected Output**:
```
[2026-04-07 10:00:00] INFO: ClinXAI Self-Healing Engine initializing...
[2026-04-07 10:00:01] INFO: Database Synchronized.
[2026-04-07 10:00:02] INFO: Uvicorn running on http://0.0.0.0:19440
[2026-04-07 10:00:02] INFO: Press CTRL+C to quit
```

### Step 4: Access the Application

**Frontend Application**:
- Main App: http://localhost:19440
- Connection Test: http://localhost:19440/test-connection.html

**API Documentation**:
- Swagger UI: http://localhost:19440/docs
- ReDoc: http://localhost:19440/redoc

**API Endpoints**:
- Health Check: http://localhost:19440/api/v1/health
- Connection Test: http://localhost:19440/api/v1/connection-test
- CORS Test: http://localhost:19440/api/v1/test-cors

---

## System Architecture

### High-Level Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                         PORT 19440                              │
│                    FastAPI Application                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │   Static Files    │       │     API v1        │
    │   (Frontend)      │       │   (Backend)       │
    └───────────────────┘       └───────────────────┘
                │                           │
        ┌───────┴────────┐         ┌────────┴────────┐
        │                │         │                 │
        ▼                ▼         ▼                 ▼
    ┌──────┐      ┌──────┐   ┌──────┐         ┌──────────┐
    │ HTML │      │  CSS │   │ JS   │         │ API      │
    │ /    │      │ /css │   │ /js  │         │ Endpoints│
    └──────┘      └──────┘   └──────┘         └──────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    │              │              │
                                    ▼              ▼              ▼
                              ┌──────────┐  ┌──────────┐  ┌──────────┐
                              │  Upload  │  │ Analysis │  │   Quiz   │
                              │  Resume  │  │  Engine  │  │ Generator│
                              └──────────┘  └──────────┘  └──────────┘
                                    │              │              │
                              ┌─────┴──────┬──────┴─────┬─────┴─────┐
                              │            │            │           │
                              ▼            ▼            ▼           ▼
                        ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐
                        │ Gemini   │ │ Database │ │ Piston   │ │ Report │
                        │ API      │ │ (SQLite) │ │ API      │ │Generator│
                        └──────────┘ └──────────┘ └──────────┘ └────────┘
```

### Request Flow

#### Authentication Flow
```
User uploads resume
    ↓
system_id created and stored in database
    ↓
POST /api/v1/auth/session-token with session_id
    ↓
JWT access token generated (valid for 30 minutes)
    ↓
token stored in sessionStorage (client side)
    ↓
all subsequent API calls include: Authorization: Bearer <token>
    ↓
token validated against SessionToken database table
    ↓
access granted/denied based on token validity
```

#### Resume Analysis Flow
```
Upload Resume (PDF/DOCX)
    ↓
Extract text using pypdf/python-docx
    ↓
Send to Gemini API for skill extraction
    ↓
Parse response into structured format
    ↓
Store in database
    ↓
Return skills to frontend
```

#### Code Execution Flow
```
User submits code solution
    ↓
code sent to /api/v1/coding/execute endpoint
    ↓
code forwarded to Piston API (sandboxed)
    ↓
test cases executed in isolated environment
    ↓
results returned (pass/fail, output, errors)
    ↓
no local code execution - completely safe
```

### Project Structure
```
res/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/       # API endpoint handlers
│   │       │   ├── auth.py      # Authentication endpoints
│   │       │   ├── upload.py    # File upload
│   │       │   ├── analysis.py  # Resume analysis
│   │       │   ├── quiz.py      # Quiz generation
│   │       │   ├── coding.py    # Code challenges
│   │       │   └── report.py    # Report generation
│   │       └── router.py        # Route aggregation
│   ├── core/
│   │   ├── config.py            # Settings & environment
│   │   ├── database.py          # Database models
│   │   ├── security.py          # JWT, password hashing
│   │   ├── ai.py                # Gemini integration
│   │   └── prompts.py           # AI prompt templates
│   ├── models/
│   │   ├── auth.py              # Auth data models
│   │   ├── upload.py            # File models
│   │   ├── quiz.py              # Quiz models
│   │   └── ...
│   ├── services/
│   │   ├── analysis.py          # Resume analysis service
│   │   ├── quiz_generator.py    # Quiz generation
│   │   ├── code_executor.py     # Piston API integration
│   │   └── report_generator.py  # Report generation
│   ├── utils/
│   │   ├── file_handler.py      # File storage management
│   │   └── text_extractor.py    # PDF/DOCX text extraction
│   └── main.py                  # FastAPI app factory
├── frontend/
│   ├── index.html               # Main app
│   ├── test-connection.html     # Connection test
│   ├── css/
│   │   ├── reset.css
│   │   ├── design-system.css
│   │   ├── components.css
│   │   └── pages.css
│   └── js/
│       ├── three-background.js  # 3D animations
│       ├── animations.js        # UI animations
│       ├── auth.js              # Token management
│       └── app.js               # Main app logic
├── .env                         # Environment variables (not in git)
├── .env.example                 # Template
├── requirements.txt             # Dependencies
├── run.py                       # Server launcher
├── app.db                       # SQLite database
└── uploads/                     # User uploads storage
```

---

## Security Implementation

### Critical Issues Fixed

#### Issue #1: Exposed API Key ✅
**Problem**: Real Gemini API key was exposed in distributed files.
**Solution**: 
- `.env` now contains placeholder values only
- `.gitignore` prevents `.env` from version control
- Setup instructions guide users to add real keys

#### Issue #2: No Authentication ✅
**Problem**: Anyone with a UUID could access any candidate's data.
**Solution**:
- JWT authentication system implemented
- Access tokens expire after 30 minutes
- Database tracks token validity
- All protected endpoints require Authorization header

**How Authentication Works**:
```
1. User uploads resume → session_id created
2. Call /api/v1/auth/session-token?session_id=xyz
3. Get back access_token (valid for 30 minutes)
4. Include in all requests: Authorization: Bearer <token>
5. Token validated against database on each request
```

**Protected Endpoints**:
- `/api/v1/analysis/*` - Resume analysis
- `/api/v1/quiz/*` - Quiz management
- `/api/v1/coding/*` - Code submissions
- `/api/v1/report/*` - Report generation

#### Issue #3: No Code Execution Sandbox ✅
**Problem**: Gemini was "pretending" to run code, not actually executing it.
**Solution**:
- Integrated Piston API for real code execution
- Code runs in isolated Docker containers
- No local code execution (completely safe)
- Supports: Python, JavaScript, Java, Go, Rust, C++, C
- Timeout protection: 5 seconds default
- Output limiting: 5000 characters

#### Issue #4: Fragile Session Design ✅
**Problem**: Sessions tied to files, broke on server restart.
**Solution**:
- Database-backed sessions
- Token lifecycle tracking
- Activity logging (last_accessed_at)
- Session locking after completion

#### Issue #5: Missing Authentication Frontend ✅
**Problem**: Frontend had no token management.
**Solution**:
- Auth manager handles token lifecycle
- Tokens stored in sessionStorage (secure)
- Automatic refresh on expiration
- Token warning before expiry

#### Issue #6: Missing Imports ✅
**Problem**: ImportError on startup.
**Solution**:
- All modules created and verified
- No circular dependencies
- Proper module structure

### Deployment Checklist

Before deploying to production:

- [ ] Generated new `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Generated Gemini API key from https://aistudio.google.com/apikey
- [ ] Updated `.env` with production values
- [ ] Set `API_DEBUG=False`
- [ ] Set `API_RELOAD=False`
- [ ] Set `ALLOWED_ORIGINS` to your domain
- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Tested authentication workflow
- [ ] Tested code execution sandbox
- [ ] Tested token expiration
- [ ] Setup HTTPS with SSL certificate
- [ ] Configured rate limiting
- [ ] Setup database backups
- [ ] Configured logging and monitoring

---

## Deployment & Setup

### Environment Variables

Required variables in `.env`:

```bash
# FastAPI Configuration
API_PORT=19440                    # Server port
API_HOST=0.0.0.0                 # Server host
API_DEBUG=False                   # Disable debug mode for production
API_RELOAD=False                  # Disable auto-reload for production

# Security
SECRET_KEY=<your-generated-key>   # For JWT signing
JWT_ALGORITHM=HS256              # Algorithm for JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30   # Token expiration
REFRESH_TOKEN_EXPIRE_DAYS=7      # Refresh token expiration

# API Keys
GEMINI_API_KEY=<your-api-key>    # Google Gemini API key

# CORS & Origins
ALLOWED_ORIGINS=["http://localhost:19440", "https://yourdomain.com"]

# Database
DATABASE_URL=sqlite:///./app.db  # SQLite (default)

# Code Execution
CODE_TIMEOUT_SECONDS=5            # Maximum code execution time
MAX_CODE_OUTPUT_LENGTH=5000       # Maximum output length

# File Upload
MAX_UPLOAD_SIZE_MB=10             # Maximum file size in MB
UPLOAD_DIR=uploads                # Directory for uploads
```

### Installation Steps

1. **Clone/Download the project**
   ```bash
   cd c:\Users\ijgam\Downloads\res\res
   ```

2. **Create Python virtual environment (recommended)**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment**
   ```bash
   # Copy template
   copy .env.example .env
   
   # Add your real API keys and settings
   ```

5. **Initialize database**
   ```bash
   # Database is created automatically on first run
   # Or explicitly:
   python -c "from app.core.database import init_db; init_db()"
   ```

6. **Start server**
   ```bash
   python run.py
   ```

### Production Deployment

#### Using Gunicorn + Nginx

```bash
# Install production WSGI server
pip install gunicorn

# Start with Gunicorn (4 workers, auto-reload disabled)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:19440
```

#### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:19440"]
```

#### Using Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:19440;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## API Reference

### Health Check
```bash
GET /api/v1/health

Response:
{
  "status": "healthy",
  "app_name": "Skill Assessment System",
  "version": "1.0.0"
}
```

### Authentication Endpoints

#### Generate Session Token
```bash
POST /api/v1/auth/session-token

Request:
{
  "session_id": "uuid-string"
}

Response:
{
  "access_token": "eyJ...",
  "expires_in": 1800,
  "token_type": "bearer"
}
```

#### Verify Token
```bash
POST /api/v1/auth/verify-token

Request:
{
  "token": "eyJ..."
}

Response:
{
  "valid": true,
  "session_id": "uuid"
}
```

#### Invalidate Token (Logout)
```bash
POST /api/v1/auth/invalidate-token

Request:
{
  "token": "eyJ..."
}

Response:
{
  "success": true,
  "message": "Token invalidated"
}
```

### File Upload
```bash
POST /api/v1/upload-resume

Request:
multipart/form-data with file field

Response:
{
  "session_id": "uuid",
  "filename": "resume.pdf",
  "size_bytes": 102400
}
```

### Resume Analysis
```bash
POST /api/v1/analyze-resume

Authorization: Bearer <token>

Request:
{
  "filename": "session-id"
}

Response:
{
  "profile": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "technical_skills": ["Python", "FastAPI", "React"],
  "experience_years": 5
}
```

### Generate Quiz
```bash
POST /api/v1/generate-quiz

Authorization: Bearer <token>

Request:
{
  "filename": "session-id"
}

Response:
{
  "quiz": {
    "questions": [
      {
        "id": 1,
        "question": "What is FastAPI?",
        "options": ["A", "B", "C", "D"],
        "difficulty": "medium"
      }
    ]
  }
}
```

### Execute Code
```bash
POST /api/v1/coding/execute

Authorization: Bearer <token>

Request:
{
  "code": "print('Hello')",
  "language": "python",
  "test_cases": [
    {"input": "", "expected_output": "Hello"}
  ]
}

Response:
{
  "success": true,
  "output": "Hello",
  "test_results": [
    {"passed": true, "message": "Test case 1 passed"}
  ],
  "execution_time_ms": 50
}
```

---

## Troubleshooting

### Issue: "Port 19440 already in use"
```bash
# Find process using port
netstat -ano | findstr :19440

# Kill process (Windows)
taskkill /PID <PID> /F

# Or change port in .env
API_PORT=19441
```

### Issue: "API key missing" or "Gemini API not responding"
```bash
# Check .env configuration
type .env

# Verify GEMINI_API_KEY is set
# Get new key: https://aistudio.google.com/apikey

# Restart server
# Press Ctrl+C, then: python run.py
```

### Issue: "Database locked" error
```bash
# SQLite constraint with concurrent access
# Restart the server - auto-recovery enabled
# For production: consider PostgreSQL

# Check WAL files
dir *.db-*
```

### Issue: "Token expired" after upload
```bash
# By design - tokens expire after 30 minutes
# This is secure and intentional
# Re-upload resume for new token
# Or: POST /api/v1/auth/session-token
```

### Issue: Code execution fails
```bash
# Check Piston API status: https://emkc.org/api/v2/piston/runtimes
# If down: fallback to local execution (less secure)
# Try different language or simpler code
```

### Issue: Frontend shows "Backend not connected"
```bash
# Check CORS configuration in .env
# Verify ALLOWED_ORIGINS includes frontend URL
# Check browser console for error details
# Verify backend is running on correct port
```

### Issue: File upload fails
```bash
# Check upload directory permissions
# Verify disk space available
# Check MAX_UPLOAD_SIZE_MB in .env
# File size limit: 10 MB default
```

---

## Frontend Guide

### Features
- **Three.js 3D Background**: Animated particle system with geometric shapes
- **Glassmorphism Design**: Modern frosted glass effects
- **Resume Upload**: Drag-and-drop file upload
- **Authentication**: Session-based token management
- **Quiz Interface**: Dynamic question display
- **Coding Editor**: Code submission interface
- **Results Display**: Assessment report generation

### Components
- **Navbar** - Sticky navigation with glassmorphism
- **Hero Section** - Interactive landing with floating cards
- **How It Works** - 5-step process visualization
- **Features Grid** - System capabilities showcase
- **Upload Modal** - Drag and drop interface
- **Footer** - Site navigation

### Interactions
- 🖱️ Mouse-reactive 3D background
- 📜 Scroll-triggered animations
- 📤 Drag & drop file upload
- ⌨️ Keyboard shortcuts:
  - `Ctrl/Cmd + K` - Open connection test
  - `Escape` - Close modals
- 🎯 Smooth scroll navigation

### File Structure
```
frontend/
├── index.html              # Main landing/app page
├── test-connection.html    # API connectivity test
├── css/
│   ├── reset.css          # CSS reset
│   ├── design-system.css  # Colors, typography
│   ├── components.css     # UI components
│   └── pages.css          # Page layouts
└── js/
    ├── three-background.js # 3D particle system
    ├── animations.js      # UI animations
    ├── auth.js            # Token management
    └── app.js             # Main app logic
```

### Design System
```css
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
--accent-primary: hsl(250, 70%, 65%);
--accent-cyan: hsl(185, 100%, 60%);
```

### API Integration
Frontend connects to: `http://localhost:19440/api/v1`

Implemented endpoints:
- ✅ Health check
- ✅ Authentication/tokens
- ✅ File upload
- ✅ Resume analysis
- ✅ Quiz generation
- ✅ Code execution
- ✅ Report generation

### Token Management
Handled in `frontend/js/auth.js`:
- Request token after upload
- Store in sessionStorage (30-minute expiration)
- Include in all API requests
- Auto-refresh on expiration
- Display warning before expiry
- Logout invalidates token

---

## Performance Monitoring

### View Logs
```bash
# All logs appear in terminal where python run.py runs
# Look for [INFO], [WARNING], [ERROR] prefixes
```

### Check Database
```bash
# Install SQLite viewer
pip install sqlite-web

# SQLite database location
c:\Users\ijgam\Downloads\res\res\app.db
```

### Monitor API Health
```bash
# Every request to health endpoint
curl http://localhost:19440/api/v1/health --silent

# Continuous monitoring
while($true) {
    curl http://localhost:19440/api/v1/health --silent
    Start-Sleep -Seconds 5
}
```

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Piston API Documentation](https://github.com/engineer-man/piston)
- [OWASP Top 10 Security Issues](https://owasp.org/www-project-top-ten/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

---

**Status**: ✅ Production Ready  
**Last Updated**: 2026-04-07  
**Version**: 2.0 (Security Enhanced)

For questions or issues, refer to troubleshooting section above.
