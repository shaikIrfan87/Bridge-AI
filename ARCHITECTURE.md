# 🏗️ System Architecture

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
    ┌──────┐      ┌──────┐   ┌──────┐         ┌──────┐
    │ HTML │      │  CSS │   │ JS   │         │ API  │
    │ /    │      │ /css │   │ /js  │         │ Endpoints│
    └──────┘      └──────┘   └──────┘         └──────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    │              │              │
                                    ▼              ▼              ▼
                              ┌─────────┐   ┌──────────┐   ┌─────────┐
                              │ Health  │   │Connection│   │  CORS   │
                              │  /api/  │   │   Test   │   │  Test   │
                              │  v1/    │   │  /api/v1/│   │ /api/v1/│
                              │ health  │   │connection│   │test-cors│
                              └─────────┘   └──────────┘   └─────────┘
```

## 🔄 Request Flow

### Frontend Page Request
```
Browser Request (/)
    │
    ▼
FastAPI Root Handler
    │
    ▼
FileResponse(frontend/index.html)
    │
    ▼
Browser Renders HTML
    │
    ├─► Loads CSS (/css/*)
    ├─► Loads JS (/js/*)
    └─► Three.js Background Starts
```

### API Request Flow
```
Frontend JavaScript
    │
    ▼
fetch('http://localhost:19440/api/v1/health')
    │
    ▼
CORS Middleware Check
    │
    ▼
API Router (/api/v1)
    │
    ▼
Health Endpoint Handler
    │
    ▼
JSON Response
    │
    ▼
Frontend Receives Data
    │
    ▼
Update UI (Connection Badge)
```

### Upload Flow (Future - CHUNK 1.2)
```
User Drag & Drop File
    │
    ▼
JavaScript File Validation
    │
    ▼
FormData Creation
    │
    ▼
POST /api/v1/upload-resume
    │
    ▼
FastAPI Upload Handler
    │
    ▼
File Storage
    │
    ▼
Return Assessment ID
    │
    ▼
Navigate to Quiz
```

## 📡 Connection Monitoring

### Real-time Health Checks
```
Page Load
    │
    ▼
startConnectionMonitoring()
    │
    ├─► Initial Check (500ms delay)
    │   └─► checkApiHealth()
    │           │
    │           ├─► Success → Show "Connected" Badge
    │           └─► Failure → Retry (3x, 2s delay)
    │
    └─► Periodic Check (Every 30s)
            └─► checkApiHealth()
```

### Badge Update Flow
```
API Response
    │
    ▼
showConnectionStatus(connected, data)
    │
    ├─► Remove Old Badge
    ├─► Create New Badge
    ├─► Apply Styles
    │   ├─► Connected: Cyan Gradient + Pulse
    │   └─► Disconnected: Pink Gradient
    ├─► Add Event Listeners
    │   ├─► Click → Retry/Open Test
    │   └─► Hover → Transform
    └─► Append to Body
```

## 🗂️ File Organization

```
ttt/
├── app/                          # Backend
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── health.py     # Health check
│   │       │   └── connection.py # Connection test
│   │       └── router.py         # Route aggregation
│   ├── core/
│   │   └── config.py            # Settings
│   └── main.py                  # FastAPI app + static mounting
│
├── frontend/                     # Frontend
│   ├── index.html               # Main landing page
│   ├── test-connection.html     # Connection test page
│   ├── css/
│   │   ├── reset.css
│   │   ├── design-system.css
│   │   ├── components.css
│   │   └── pages.css
│   └── js/
│       ├── three-background.js  # 3D particles
│       ├── animations.js        # Scroll effects
│       └── app.js               # Main logic + monitoring
│
├── .env                         # Environment config
├── requirements.txt             # Python dependencies
├── run.py                       # Server launcher
├── README.md                    # Main documentation
├── CONNECTION_STATUS.md         # Connection details
└── ARCHITECTURE.md              # This file
```

## 🎯 Design Patterns

### Backend Patterns
- **Factory Pattern:** `create_application()` in main.py
- **Router Pattern:** Modular endpoint organization
- **Middleware Pattern:** CORS configuration
- **Settings Pattern:** Pydantic-based config

### Frontend Patterns
- **Module Pattern:** Self-contained JavaScript
- **Observer Pattern:** Event listeners
- **Retry Pattern:** Connection failure handling
- **State Management:** Connection status tracking

## 🔐 Security Layers

```
Request
    │
    ▼
1. CORS Middleware
    │ (Check Origin)
    ▼
2. Route Validation
    │ (Match Path)
    ▼
3. Endpoint Handler
    │ (Process Request)
    ▼
4. Response
```

## 📊 Data Flow

### Frontend → Backend
```javascript
// JavaScript
const response = await fetch(`${API_BASE_URL}/health`);
                        ↓
                   HTTP Request
                        ↓
                   Python FastAPI
```

### Backend → Frontend
```python
# Python
return {"status": "healthy"}
           ↓
      JSON Response
           ↓
    JavaScript Object
```

## 🚀 Performance Optimizations

### Static File Serving
- Direct file serving via FastAPI StaticFiles
- Proper MIME types
- Browser caching enabled

### API Response
- Async/await pattern
- Minimal processing
- JSON serialization optimized

### Frontend
- CSS/JS loaded in parallel
- Three.js optimized rendering
- Debounced animations
- Efficient DOM updates

---

**This architecture provides a solid, scalable foundation for all future chunks!** 🎉
