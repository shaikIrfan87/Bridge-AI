/**
 * Authentication Module for Frontend
 * Handles JWT token management, token refresh, and secure API calls
 * Uses sessionStorage for token (more secure than localStorage)
 */

class AuthManager {
    constructor() {
        this.API_BASE_URL = this.getApiBaseUrl();
        this.TOKEN_KEY = 'access_token';
        this.SESSION_ID_KEY = 'session_id';
        this.EXPIRY_KEY = 'token_expiry';
    }

    /**
     * Detect API base URL (supports both dev and production)
     */
    getApiBaseUrl() {
        if (window.location.port !== '19440' && 
            (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
            return 'http://localhost:19440/api/v1';
        }
        return window.location.origin + '/api/v1';
    }

    /**
     * Request session token after file upload
     * @param {string} sessionId - Session ID from upload response
     * @returns {Promise<{access_token, expires_in}>} Token data
     */
    async requestSessionToken(sessionId) {
        try {
            const response = await fetch(`${this.API_BASE_URL}/auth/session-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || 'Failed to get session token');
            }

            const data = await response.json();
            
            // Store token and session info
            this.setToken(data.access_token, data.expires_in);
            sessionStorage.setItem(this.SESSION_ID_KEY, sessionId);

            console.log('✓ Session token acquired, valid for', data.expires_in, 'seconds');
            return data;
        } catch (error) {
            console.error('Token request failed:', error);
            throw error;
        }
    }

    /**
     * Store token with expiry time
     * @param {string} token - JWT access token
     * @param {number} expiresIn - Expiration time in seconds
     */
    setToken(token, expiresIn) {
        sessionStorage.setItem(this.TOKEN_KEY, token);
        const expiryTime = Date.now() + (expiresIn * 1000);
        sessionStorage.setItem(this.EXPIRY_KEY, expiryTime);
    }

    /**
     * Get current access token
     * @returns {string|null} Access token or null if expired/missing
     */
    getToken() {
        const token = sessionStorage.getItem(this.TOKEN_KEY);
        const expiry = sessionStorage.getItem(this.EXPIRY_KEY);

        if (!token || !expiry) return null;

        // Check if token is expired (with 1 minute buffer before actual expiry)
        const bufferTime = 60000; // 1 minute
        if (Date.now() > parseInt(expiry) - bufferTime) {
            console.warn('⚠ Token expired, clearing storage');
            this.clearToken();
            return null;
        }

        return token;
    }

    /**
     * Check if token exists and is valid
     * @returns {boolean} True if valid token exists
     */
    hasValidToken() {
        return !!this.getToken();
    }

    /**
     * Get remaining token validity in seconds
     * @returns {number} Seconds remaining, or 0 if no token
     */
    getTokenExpiresInSeconds() {
        const expiry = sessionStorage.getItem(this.EXPIRY_KEY);
        if (!expiry) return 0;

        const remaining = (parseInt(expiry) - Date.now()) / 1000;
        return Math.max(0, remaining);
    }

    /**
     * Verify token with server
     * @returns {Promise<boolean>} True if token is valid
     */
    async verifyToken() {
        const token = this.getToken();
        if (!token) return false;

        try {
            const response = await fetch(`${this.API_BASE_URL}/auth/verify-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token })
            });

            if (response.ok) {
                const data = await response.json();
                return data.valid === true;
            }
            return false;
        } catch (error) {
            console.error('Token verification failed:', error);
            return false;
        }
    }

    /**
     * Logout and invalidate token
     * @returns {Promise<boolean>} Success status
     */
    async logout() {
        const token = this.getToken();
        
        try {
            if (token) {
                // Notify server to invalidate token
                await fetch(`${this.API_BASE_URL}/auth/invalidate-token`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ token })
                }).catch(err => {
                    console.warn('Could not notify server of logout:', err);
                });
            }

            // Clear local storage
            this.clearToken();
            sessionStorage.removeItem(this.SESSION_ID_KEY);
            console.log('✓ Logged out successfully');
            return true;
        } catch (error) {
            console.error('Logout failed:', error);
            this.clearToken();
            return false;
        }
    }

    /**
     * Clear token from storage
     */
    clearToken() {
        sessionStorage.removeItem(this.TOKEN_KEY);
        sessionStorage.removeItem(this.EXPIRY_KEY);
    }

    /**
     * Make authenticated API call (automatically includes token)
     * @param {string} endpoint - API endpoint (e.g., /analysis/123)
     * @param {object} options - Fetch options
     * @returns {Promise<Response>} API response
     */
    async authenticatedFetch(endpoint, options = {}) {
        const token = this.getToken();

        if (!token) {
            throw new Error('No valid authentication token. Please upload resume first.');
        }

        const headers = options.headers || {};
        headers['Authorization'] = `Bearer ${token}`;

        return fetch(`${this.API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });
    }

    /**
     * Make authenticated GET request
     * @param {string} endpoint - API endpoint
     * @returns {Promise<object>} Response JSON
     */
    async get(endpoint) {
        const response = await this.authenticatedFetch(endpoint);
        
        if (!response.ok) {
            if (response.status === 401) {
                this.clearToken();
                throw new Error('Authentication expired. Please upload resume again.');
            }
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `API error: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Make authenticated POST request
     * @param {string} endpoint - API endpoint
     * @param {object} data - Request body
     * @returns {Promise<object>} Response JSON
     */
    async post(endpoint, data) {
        const response = await this.authenticatedFetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            if (response.status === 401) {
                this.clearToken();
                throw new Error('Authentication expired. Please upload resume again.');
            }
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `API error: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Display token status in UI
     */
    displayTokenStatus() {
        const expiresIn = this.getTokenExpiresInSeconds();
        const minutes = Math.floor(expiresIn / 60);
        
        if (minutes <= 5) {
            console.warn(`⚠ Token expires in ${minutes} minutes`);
            return this.showTokenWarning(minutes);
        }
        return null;
    }

    /**
     * Show token expiry warning in UI
     */
    showTokenWarning(minutesRemaining) {
        const warningElement = document.getElementById('token-warning');
        if (warningElement) {
            warningElement.innerHTML = `⏱ Session expires in ${minutesRemaining} minutes. Submit your answers before expiry.`;
            warningElement.classList.remove('hidden');
        }
    }

    /**
     * Hide token warning
     */
    hideTokenWarning() {
        const warningElement = document.getElementById('token-warning');
        if (warningElement) {
            warningElement.classList.add('hidden');
        }
    }

    /**
     * Start periodic token status monitoring
     * Checks every 30 seconds if token is about to expire
     */
    startTokenMonitoring() {
        setInterval(() => {
            if (this.hasValidToken()) {
                this.displayTokenStatus();
            }
        }, 30000); // Check every 30 seconds
    }
}

// Create global auth manager instance
const authManager = new AuthManager();

// Auto-start token monitoring when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        authManager.startTokenMonitoring();
    });
} else {
    authManager.startTokenMonitoring();
}
