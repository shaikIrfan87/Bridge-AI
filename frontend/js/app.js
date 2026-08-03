/**
 * Main Application Logic
 * Upload handling, AI integration, modal controls
 */

// Global state and config
let API_BASE_URL = 'http://localhost:19440/api/v1';

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Dynamic API URL detection
    API_BASE_URL = window.location.origin + '/api/v1';
    
    // Check for dev setup (Frontend on 3000 or similar)
    if (window.location.port !== '19440' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
        API_BASE_URL = 'http://localhost:19440/api/v1';
    }

    console.log('App Initialized. API Base:', API_BASE_URL);

    // Elements
    const modal = document.getElementById('assessment-modal');
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const closeModalBtn = document.getElementById('close-modal');
    const uploadResumeBtn = document.getElementById('upload-resume-btn');
    const startAssessmentBtn = document.getElementById('start-assessment-btn');
    const uploadProgress = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    if (!modal) {
        console.error('Fatal: assessment-modal not found');
        return;
    }

    // Attach core listeners
    uploadResumeBtn?.addEventListener('click', openModal);
    startAssessmentBtn?.addEventListener('click', openModal);
    closeModalBtn?.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.classList.contains('modal-backdrop')) {
            closeModal();
        }
    });

    uploadArea?.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop
    uploadArea?.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea?.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea?.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFileUpload(files[0]);
    });

    fileInput?.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files.length > 0) handleFileUpload(files[0]);
    });

    // Health monitoring
    startConnectionMonitoring();

    // Export functions to window for dynamic HTML onclicks
    window.closeModal = closeModal;
    window.openModal = openModal;
});

// --- Modal Helper Functions ---

function setModalWide(isWide) {
    const modalContent = document.querySelector('.modal-content');
    if (!modalContent) return;
    modalContent.classList.toggle('modal-wide', isWide);
}

function openModal() {
    const modal = document.getElementById('assessment-modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        setModalWide(false);
    }
}

window.showCountdownLoader = function(title, subtitle, estimatedSeconds) {
    const mc = document.querySelector('.modal-content');
    if (!mc) return;
    
    if (window._waitTimer) clearInterval(window._waitTimer);
    
    mc.innerHTML = `
        <div class="loader-container">
            <div class="pulse-loader" style="color:var(--accent-primary)">&#x26A1;</div>
            <h2>${escapeHtml(title)}</h2>
            <p style="color:var(--text-secondary);margin-top:10px;">${escapeHtml(subtitle)}</p>
            
            <div style="margin-top:25px; font-size:1.1rem; color:var(--text-secondary);">
                Estimated time remaining: 
                <span id="wait-countdown" style="font-weight:bold; color:var(--accent-cyan); font-variant-numeric: tabular-nums;">${estimatedSeconds}s</span>
            </div>
            
            <div style="width: 70%; max-width: 300px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; margin: 15px auto; overflow: hidden;">
                <div id="wait-progress" style="width: 0%; height: 100%; background: var(--accent-cyan); transition: width 1s linear;"></div>
            </div>
            <p style="font-size:0.8rem;opacity:0.6;margin-top:15px;">Please don't close this window.</p>
        </div>
    `;
    
    let timeLeft = estimatedSeconds;
    const timerEl = document.getElementById('wait-countdown');
    const progEl = document.getElementById('wait-progress');
    
    window._waitTimer = setInterval(() => {
        timeLeft--;
        if (timeLeft < 0) timeLeft = 0;
        
        if (timerEl) timerEl.textContent = timeLeft + 's';
        if (progEl) {
            let pct = ((estimatedSeconds - timeLeft) / estimatedSeconds) * 100;
            progEl.style.width = Math.min(100, Math.max(0, pct)) + '%';
        }
        
        if (timeLeft <= 0) clearInterval(window._waitTimer);
    }, 1000);
};

window.triggerCriticalFailure = function(reason) {
    if (window._waitTimer) clearInterval(window._waitTimer);
    if (quizState.timer) clearInterval(quizState.timer);
    deactivateIntegrityGuard();
    
    const mc = document.querySelector('.modal-content');
    if (mc) {
        setModalWide(true);
        mc.innerHTML = `
            <div class="loader-container">
                <div style="font-size: 3.5rem; margin-bottom: 20px;">⚠️</div>
                <h2 style="color: #ff4757;">Process Interrupted</h2>
                <p style="color:var(--text-secondary); margin-top:10px;">${escapeHtml(reason || 'An unexpected error occurred.')}</p>
                <div style="margin-top:25px; font-weight:bold; color:var(--accent-cyan); font-size:1.1rem;">
                    Returning to the start step...
                </div>
            </div>
        `;
    }
    
    localStorage.clear();
    sessionStorage.clear();
    
    setTimeout(() => {
        closeModal();
        showError("Process failed. Please restart from the beginning.");
    }, 4000);
};

function closeModal() {
    const modal = document.getElementById('assessment-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        if (window._waitTimer) clearInterval(window._waitTimer);
        resetUploadArea();
        setModalWide(false);
    }
}

function resetUploadArea() {
    const uploadArea = document.getElementById('upload-area');
    const uploadProgress = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    if (uploadArea) uploadArea.classList.remove('hidden');
    if (uploadProgress) uploadProgress.classList.add('hidden');
    if (progressFill) progressFill.style.width = '0%';
    if (progressText) {
        progressText.textContent = 'Uploading...';
        progressText.style.color = '';
    }
}

// --- Upload Logic ---

async function handleFileUpload(file) {
    const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|docx)$/i)) {
        showError('Invalid file type. Please upload PDF or DOCX.');
        return;
    }

    if (file.size > maxSize) {
        showError(`File too large. Maximum size is 10MB.`);
        return;
    }

    const uploadArea = document.getElementById('upload-area');
    const uploadProgress = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    // CLEAR OLD SESSION DATA ON NEW UPLOAD
    sessionStorage.clear();
    
    if (uploadArea) uploadArea.classList.add('hidden');
    if (uploadProgress) uploadProgress.classList.remove('hidden');

    try {
        const formData = new FormData();
        formData.append('file', file);

        if (progressFill) progressFill.style.width = '10%';
        if (progressText) progressText.textContent = 'Uploading... 10%';

        const response = await fetch(`${API_BASE_URL}/upload-resume`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
            throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();
        if (progressFill) progressFill.style.width = '100%';
        if (progressText) {
            progressText.textContent = 'Upload complete!';
            progressText.style.color = 'var(--accent-cyan)';
        }

        setTimeout(() => handleUploadSuccess(data), 800);
    } catch (error) {
        console.error('Upload error:', error);
        showError(error.message || 'Upload failed. Please try again.');
        resetUploadArea();
    }
}

async function handleUploadSuccess(data) {
    if (data.session_id) {
        sessionStorage.setItem('session_id', data.session_id);
    }
    if (data.file_info?.filename) sessionStorage.setItem('uploaded_filename', data.file_info.filename);

    const progressText = document.getElementById('progress-text');
    if (progressText) {
        progressText.textContent = `✓ ${data.file_info?.original_filename || 'Resume'} uploaded successfully!`;
        progressText.style.color = 'var(--accent-cyan)';
    }
    
    showSuccess(data.message || 'Resume uploaded successfully! Acquiring session token...');

    if (data.file_info?.filename) {
        setTimeout(() => analyzeResume(data.file_info.filename), 1000);
    }
}

/**
 * Request authentication token after resume upload
 * Token is required for all subsequent API calls
 */
async function requestAuthToken(sessionId) {
    try {
        console.log('🔐 Requesting authentication token...');
        await authManager.requestSessionToken(sessionId);
        console.log('✓ Authentication token acquired');
        showSuccess('✓ Your session is now secure');
    } catch (error) {
        console.error('Token request failed:', error);
        showError(`Security warning: ${error.message}`);
    }
}

// --- Notifications ---

function showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 242, 254, 0.4);
        z-index: 1000; animation: fadeInDown 0.3s ease; max-width: 400px;
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'fadeInUp 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        z-index: 1000; animation: fadeInDown 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'fadeInUp 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// --- Connection Monitoring ---

let connectionAttempts = 0;
const MAX_CONNECTION_ATTEMPTS = 3;

async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            showConnectionStatus(true, data);
            connectionAttempts = 0;
            return true;
        }
        throw new Error(`HTTP ${response.status}`);
    } catch (error) {
        connectionAttempts++;
        if (connectionAttempts < MAX_CONNECTION_ATTEMPTS) {
            setTimeout(checkApiHealth, 2000);
        } else {
            showConnectionStatus(false, error);
        }
        return false;
    }
}

function showConnectionStatus(connected, data) {
    const existing = document.querySelector('.connection-badge');
    if (existing) existing.remove();

    if (connected) return; // SILENCE SUCCESS: Don't show badge if everything is OK

    const badge = document.createElement('div');
    badge.className = 'connection-badge';
    badge.style.cssText = `
        position: fixed; top: 80px; right: 20px; padding: 10px 20px;
        border-radius: 30px; font-size: 0.85rem; font-weight: 600; z-index: 999;
        display: flex; align-items: center; gap: 8px; animation: fadeInDown 0.5s ease;
        cursor: pointer; transition: transform 0.2s;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
        color: white;
    `;

    badge.innerHTML = `<span style="width: 8px; height: 8px; background: white; border-radius: 50%;"></span>Backend Disconnected`;

    badge.addEventListener('click', () => {
        if (!connected) { connectionAttempts = 0; checkApiHealth(); }
    });

    document.body.appendChild(badge);
}

function startConnectionMonitoring() {
    checkApiHealth();
    setInterval(checkApiHealth, 30000);
}

// --- Global Assessment State ---
let quizState = {
    currentQuestion: 0, answers: {}, quizData: null, timer: null, timeLeft: 0, evaluationResult: null
};

// --- Security & Proctoring ---

function activateIntegrityGuard() {
    const filename = sessionStorage.getItem('uploaded_filename');
    if (!filename) return;

    window.onblur = async () => {
        console.warn('INTEGRITY VIOLATION: Tab switched or window blurred.');
        await triggerIntegrityFailure('Tab Switch / Window Inactive');
    };
    
    document.onvisibilitychange = async () => {
        if (document.visibilityState === 'hidden') {
            await triggerIntegrityFailure('Tab Hidden');
        }
    };
}

function deactivateIntegrityGuard() {
    window.onblur = null;
    document.onvisibilitychange = null;
}

async function triggerIntegrityFailure(reason) {
    deactivateIntegrityGuard();
    const filename = sessionStorage.getItem('uploaded_filename');
    if (!filename) return;

    try {
        await fetch(`${API_BASE_URL}/record-cheat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
    } catch (e) {}

    // Force Exit & Show Error
    if (quizState.timer) clearInterval(quizState.timer);
    
    const mc = document.querySelector('.modal-content');
    mc.innerHTML = `
        <div class="loader-container" style="color: #ff4757;">
            <div style="font-size: 3rem; margin-bottom: 20px;">⚠️</div>
            <h2 style="color: #ff4757;">ASSESSMENT TERMINATED</h2>
            <p><strong>REASON:</strong> ${reason}</p>
            <p style="margin-top:20px; color:var(--text-secondary);">An integrity violation has been recorded. This session is now locked.</p>
            <button class="btn btn-primary" style="margin-top:30px; background:#ff4757;" onclick="location.reload()">Return to Safety</button>
        </div>`;
    
    showError("Integrity Violation: Assessment Terminated Automatically.");
}

// Ensure guard is active during assessments
async function startQuiz(filename) {
    if (!filename) { showError('Session lost. Please upload resume again.'); return; }
    activateIntegrityGuard(); // LOCK DOWN ACTIVATED
    setModalWide(true);
    window.showCountdownLoader(
        'Generating Your Interview Questions...',
        'Gemini is crafting questions from your actual work experience & projects.',
        15
    );

    try {
        const body = { filename };
        if (window._forceRegenQuiz) { body.force_regenerate = true; window._forceRegenQuiz = false; }

        const response = await fetch(`${API_BASE_URL}/generate-quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error('Quiz generation failed');
        const data = await response.json();

        quizState.quizData = data.quiz;
        quizState.currentQuestion = 0;
        quizState.answers = {};
        quizState.timeLeft = (data.quiz.estimated_time_minutes || 45) * 60;
        startTimer();
        renderQuestion();
    } catch (error) {
        window.triggerCriticalFailure('Failed to generate quiz: ' + error.message);
    }
}

function startTimer() {
    if (quizState.timer) clearInterval(quizState.timer);
    quizState.timer = setInterval(() => {
        quizState.timeLeft--;
        const mins = Math.floor(quizState.timeLeft / 60);
        const secs = quizState.timeLeft % 60;
        const timerEl = document.getElementById('quiz-timer');
        if (timerEl) {
            timerEl.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>${mins}:${String(secs).padStart(2, '0')}`;
        }
        if (quizState.timeLeft <= 0) finishQuiz(true);
    }, 1000);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function getQTypeBadgeHtml(qtype) {
    const slug = (qtype || 'Technical').toLowerCase().replace(/[\s/]+/g, '-');
    return `<span class="qtype-badge qtype-${slug}">${escapeHtml(qtype || 'Technical')}</span>`;
}

function renderQuestion() {
    setModalWide(true);
    const question = quizState.quizData.questions[quizState.currentQuestion];
    const total = quizState.quizData.questions.length;
    const mc = document.querySelector('.modal-content');
    const progressPct = Math.round((quizState.currentQuestion / total) * 100);
    const isLast = quizState.currentQuestion === total - 1;
    const qId = String(question.id);
    const savedAnswer = quizState.answers[qId] || '';
    const hasSaved = savedAnswer.trim() !== '';

    mc.innerHTML = `
        <div class="qz-progress-track"><div class="qz-progress-fill" style="width:${progressPct}%"></div></div>
        <div class="qz-header">
            <div class="qz-meta">
                <span class="qz-badge">${quizState.currentQuestion + 1}<span class="qz-badge-sep">/</span>${total}</span>
                <span class="qz-label">${escapeHtml(question.topic || 'Interview')}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <button class="regen-btn" id="regen-quiz-btn">New Questions</button>
                <div class="qz-timer" id="quiz-timer"><span>--:--</span></div>
                <button class="qz-exit-btn" onclick="exitQuiz()">Exit</button>
            </div>
        </div>

        <div class="qz-question-card">
            ${getQTypeBadgeHtml(question.question_type)}
            <div class="qz-q-number">Q${quizState.currentQuestion + 1} &middot; ${escapeHtml(question.difficulty || 'Medium')}</div>
            <p class="qz-q-text">${escapeHtml(question.text)}</p>
        </div>

        <div class="qz-answer-zone">
            <textarea id="answer-text" class="qz-textarea" placeholder="Your answer...">${escapeHtml(savedAnswer)}</textarea>
        </div>

        <div class="qz-footer">
            <div class="qz-step-dots">
                ${Array.from({ length: total }, (_, i) => `<span class="qz-dot ${i < quizState.currentQuestion ? 'done' : i === quizState.currentQuestion ? 'active' : ''}"></span>`).join('')}
            </div>
            ${isLast
            ? `<button class="btn btn-primary" id="finish-btn" ${hasSaved ? '' : 'disabled'}>Finish</button>`
            : `<button class="btn btn-primary" id="next-btn" ${hasSaved ? '' : 'disabled'}>Next</button>`
        }
        </div>`;

    document.getElementById('regen-quiz-btn')?.addEventListener('click', () => {
        window._forceRegenQuiz = true;
        startQuiz(sessionStorage.getItem('uploaded_filename'));
    });

    document.getElementById('next-btn')?.addEventListener('click', () => { quizState.currentQuestion++; renderQuestion(); });
    document.getElementById('finish-btn')?.addEventListener('click', () => finishQuiz());
    
    const textarea = document.getElementById('answer-text');
    textarea.focus();
    textarea.addEventListener('input', () => {
        quizState.answers[qId] = textarea.value;
        const btn = document.getElementById('next-btn') || document.getElementById('finish-btn');
        if (btn) btn.disabled = textarea.value.trim() === '';
    });
}

function exitQuiz() {
    deactivateIntegrityGuard(); // UNLOCK ON EXIT
    if (quizState.timer) clearInterval(quizState.timer);
    closeModal();
}

async function finishQuiz(autoSubmit = false) {
    if (quizState.timer) clearInterval(quizState.timer);
    const mc = document.querySelector('.modal-content');
    
    // FAST UI: Instantly proceed without waiting for evaluation
    mc.innerHTML = `<div class="loader-container"><h2>✓ Round 1 Recorded!</h2><p>Your technical answers are being securely saved. Preparing your Coding Round...</p></div>`;

    const filename = sessionStorage.getItem('uploaded_filename');
    try {
        const resp = await fetch(`${API_BASE_URL}/evaluate-quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quiz_id: filename, answers: quizState.answers })
        });
        
        // Even if evaluation is deferred, we save the raw answers for the report
        sessionStorage.setItem('quiz_questions_json', JSON.stringify(quizState.quizData.questions));
        sessionStorage.setItem('quiz_answers_json', JSON.stringify(quizState.answers));

        deactivateIntegrityGuard(); // SUCCESSFUL FINISH
        // Use advanced coding IDE from coding-ide.js
        setTimeout(() => startCodingChallenge(), 1500);
    } catch (e) {
        window.triggerCriticalFailure('Submission failed: ' + e.message);
    }
}

// Coding functions are delegated to coding-ide.js
// The advanced IDE provides Monaco editor-based coding challenges
// See coding-ide.js for implementation

// --- Final Report Logic ---

async function generateFinalReport() {
    const filename = sessionStorage.getItem('uploaded_filename');
    const mc = document.querySelector('.modal-content');
    
    // Professional Loader for Unified Analysis
    window.showCountdownLoader(
        'Finalizing Your Assessment...',
        'Our AI is performing a deep-dive audit of your Technical Quiz and Coding solutions.',
        25
    );

    try {
        const response = await fetch(`${API_BASE_URL}/generate-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const data = await response.json();
        
        if (data.success && data.report) {
            renderReport(data.report);
        } else {
            throw new Error(data.message || 'Report generation failed');
        }
    } catch (e) {
        window.triggerCriticalFailure('Report generation failed: ' + e.message);
    }
}

function renderReport(report) {
    const mc = document.querySelector('.modal-content');
    setModalWide(true);
    
    const v = report.recommendation || {};
    const verdictClass = (v.verdict || 'Neutral').toLowerCase();
    
    // Build score breakdown section
    const scoreBreakdown = `
        ${report.quiz_score !== undefined ? `<div class="score-item"><span>Technical Quiz:</span> <strong>${report.quiz_score}/100</strong></div>` : ''}
        ${report.coding_score !== undefined ? `<div class="score-item"><span>Coding Challenges:</span> <strong>${report.coding_score}/100</strong></div>` : ''}
    `;
    
    // Build detailed quiz answers section
    let detailedQuizHtml = '';
    if (report.detailed_quiz_answers && report.detailed_quiz_answers.length > 0) {
        const quizAnswersHtml = report.detailed_quiz_answers.map((ans, idx) => `
            <div class="quiz-answer-item">
                <div class="answer-header">
                    <div class="answer-question-number">Question ${idx + 1}</div>
                    <div class="answer-score-badge" style="background: ${ans.score >= 80 ? '#4CAF50' : ans.score >= 60 ? '#FF9800' : '#f44336'};">
                        Score: ${ans.score}/100
                    </div>
                </div>
                
                <div class="answer-question-text">
                    <strong>Q:</strong> ${escapeHtml(ans.question_text)}
                </div>
                
                <div class="answer-section">
                    <div class="answer-label">Topic:</div>
                    <span class="badge">${escapeHtml(ans.topic)}</span>
                    <span class="badge" style="margin-left: 4px;">${escapeHtml(ans.difficulty)}</span>
                </div>
                
                <div class="answer-section">
                    <div class="answer-label">Your Answer:</div>
                    <div class="answer-content user-answer">
                        ${escapeHtml(ans.user_answer || '(No answer provided)')}
                    </div>
                </div>
                
                <div class="answer-section">
                    <div class="answer-label">What the answer should include:</div>
                    <div class="answer-content correct-answer">
                        ${escapeHtml(ans.correct_answer_guide)}
                    </div>
                </div>
                
                <div class="answer-section">
                    <div class="answer-label">Key Points You Covered:</div>
                    <div class="keywords-list">
                        ${ans.matched_keywords && ans.matched_keywords.length > 0 
                            ? ans.matched_keywords.map(kw => `<span class="keyword matched">✓ ${escapeHtml(kw)}</span>`).join('')
                            : '<span style="color: var(--text-secondary);">None identified</span>'
                        }
                    </div>
                </div>
                
                <div class="answer-section">
                    <div class="answer-label">Important concepts you missed:</div>
                    <div class="keywords-list">
                        ${ans.missing_keywords && ans.missing_keywords.length > 0
                            ? ans.missing_keywords.map(kw => `<span class="keyword missing">✗ ${escapeHtml(kw)}</span>`).join('')
                            : '<span style="color: var(--text-secondary);">None - great job!</span>'
                        }
                    </div>
                </div>
                
                <div class="answer-section">
                    <div class="answer-label">Feedback & Suggestions:</div>
                    <div class="feedback-content">
                        ${escapeHtml(ans.feedback)}
                    </div>
                </div>
            </div>
        `).join('');
        
        detailedQuizHtml = `
            <div class="report-section">
                <h3>Detailed Quiz Review</h3>
                <p style="color: var(--text-secondary); margin-bottom: 16px;">Review your answers question by question to understand what you did well and where to improve.</p>
                ${quizAnswersHtml}
            </div>
        `;
    }
    
    // Build skills and gaps
    const skillGapsHtml = report.skill_gaps && report.skill_gaps.length > 0 
        ? report.skill_gaps.map(gap => `
            <div class="skill-gap-item">
                <div class="gap-skill-name">${escapeHtml(gap.skill)}</div>
                <div class="gap-status ${gap.status.toLowerCase().replace(' ', '-')}">${escapeHtml(gap.status)}</div>
                <div class="gap-analysis">${escapeHtml(gap.gap_analysis)}</div>
            </div>
        `).join('')
        : '<div style="color: var(--text-secondary);">No skill gaps identified.</div>';
    
    // Build recommendation details
    const prosCons = `
        ${v.pros && v.pros.length > 0 ? `
            <div class="pros-section">
                <h4>Strengths</h4>
                <ul>${v.pros.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>
            </div>
        ` : ''}
        ${v.cons && v.cons.length > 0 ? `
            <div class="cons-section">
                <h4>Areas for Improvement</h4>
                <ul>${v.cons.map(c => `<li>${escapeHtml(c)}</li>`).join('')}</ul>
            </div>
        ` : ''}
        ${v.learning_path && v.learning_path.length > 0 ? `
            <div class="learning-path-section">
                <h4>Recommended Learning Path</h4>
                <ul>${v.learning_path.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
            </div>
        ` : ''}
    `;
    
    mc.innerHTML = `
        <div class="modal-header">
            <h2>Hiring Assessment: ${escapeHtml(report.candidate_name)}</h2>
            <div class="report-verdict verdict-${verdictClass}">${escapeHtml(v.verdict || 'Review Required')}</div>
        </div>
        
        <div class="modal-body" style="overflow-y: auto; max-height: 70vh; padding: 20px;">
            <div class="report-dashboard">
                <div class="report-score-card">
                    <div class="score-main">${report.overall_score}</div>
                    <div class="score-label">Overall Match</div>
                </div>
                
                <div class="report-details">
                    <div class="detail-section">
                        <h3>Score Breakdown</h3>
                        ${scoreBreakdown}
                    </div>
                    <div class="detail-section">
                        <h3>Summary</h3>
                        <p>${escapeHtml(report.summary)}</p>
                    </div>
                    <div class="detail-section">
                        <h3>Key Recommendation</h3>
                        <p>${escapeHtml(v.justification || v.summary || 'Review the detailed assessment above.')}</p>
                    </div>
                </div>
            </div>
            
            ${detailedQuizHtml}
            
            ${report.skill_gaps && report.skill_gaps.length > 0 ? `
                <div class="report-section">
                    <h3>Skill Assessment</h3>
                    ${skillGapsHtml}
                </div>
            ` : ''}
            
            <div class="report-section">
                <h3>Candidate Profile</h3>
                <div class="profile-rating">
                    <div class="rating-item">
                        <span>Technical Rating:</span>
                        <strong>${escapeHtml(report.technical_rating)}</strong>
                    </div>
                    <div class="rating-item">
                        <span>Credibility Status:</span>
                        <strong>${escapeHtml(report.credibility_status)}</strong>
                    </div>
                </div>
            </div>
            
            <div class="report-section">
                <h3>Assessment Details</h3>
                ${prosCons}
            </div>
        </div>
        
        <div class="modal-footer" style="margin-top:20px; text-align:right; padding: 20px; border-top: 1px solid var(--border-color);">
            <button class="btn btn-secondary" onclick="window.print()">Print Report</button>
            <button class="btn btn-primary" onclick="closeModal()">Finish Session</button>
        </div>`;
        
    // Add CSS styles for the detailed report
    if (!document.getElementById('report-styles')) {
        const style = document.createElement('style');
        style.id = 'report-styles';
        style.textContent = `
            .report-section {
                margin-top: 24px;
                padding-top: 24px;
                border-top: 1px solid var(--border-color);
            }
            
            .report-section h3 {
                margin-bottom: 16px;
                color: var(--text-primary);
            }
            
            .quiz-answer-item {
                background: var(--bg-secondary);
                border-left: 4px solid #2196F3;
                padding: 16px;
                margin-bottom: 16px;
                border-radius: 4px;
            }
            
            .answer-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }
            
            .answer-question-number {
                font-weight: 600;
                color: var(--text-primary);
            }
            
            .answer-score-badge {
                padding: 4px 12px;
                border-radius: 12px;
                color: white;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            .answer-question-text {
                font-size: 0.95rem;
                margin-bottom: 12px;
                color: var(--text-primary);
                line-height: 1.5;
            }
            
            .answer-section {
                margin-top: 12px;
            }
            
            .answer-label {
                font-weight: 600;
                font-size: 0.9rem;
                margin-bottom: 6px;
                color: var(--text-primary);
            }
            
            .answer-content {
                background: var(--bg-primary);
                padding: 10px;
                border-radius: 3px;
                font-size: 0.9rem;
                line-height: 1.5;
                overflow-x: auto;
                color: var(--text-secondary);
            }
            
            .answer-content.user-answer {
                border-left: 3px solid #2196F3;
            }
            
            .answer-content.correct-answer {
                border-left: 3px solid #4CAF50;
            }
            
            .keywords-list {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }
            
            .keyword {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            .keyword.matched {
                background: rgba(76, 175, 80, 0.2);
                color: #2e7d32;
            }
            
            .keyword.missing {
                background: rgba(244, 67, 54, 0.2);
                color: #c62828;
            }
            
            .feedback-content {
                background: var(--bg-primary);
                padding: 12px;
                border-radius: 3px;
                font-size: 0.9rem;
                line-height: 1.6;
                color: var(--text-secondary);
                border-left: 3px solid #FF9800;
            }
            
            .badge {
                display: inline-block;
                padding: 2px 8px;
                background: var(--accent-color);
                color: white;
                border-radius: 12px;
                font-size: 0.8rem;
            }
            
            .skill-gap-item {
                background: var(--bg-secondary);
                padding: 12px;
                margin-bottom: 12px;
                border-radius: 4px;
                border-left: 4px solid #FF9800;
            }
            
            .gap-skill-name {
                font-weight: 600;
                margin-bottom: 6px;
                color: var(--text-primary);
            }
            
            .gap-status {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.8rem;
                font-weight: 500;
                margin-bottom: 6px;
            }
            
            .gap-status.verified {
                background: rgba(76, 175, 80, 0.2);
                color: #2e7d32;
            }
            
            .gap-status.partially-verified {
                background: rgba(255, 152, 0, 0.2);
                color: #e65100;
            }
            
            .gap-status.flagged {
                background: rgba(244, 67, 54, 0.2);
                color: #c62828;
            }
            
            .gap-status.not-tested {
                background: rgba(158, 158, 158, 0.2);
                color: #424242;
            }
            
            .gap-analysis {
                font-size: 0.9rem;
                color: var(--text-secondary);
                line-height: 1.5;
            }
            
            .profile-rating {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 12px;
            }
            
            .rating-item {
                background: var(--bg-secondary);
                padding: 12px;
                border-radius: 4px;
            }
            
            .rating-item span {
                display: block;
                font-size: 0.9rem;
                color: var(--text-secondary);
                margin-bottom: 6px;
            }
            
            .rating-item strong {
                font-size: 1.1rem;
                color: var(--text-primary);
            }
            
            .pros-section h4,
            .cons-section h4,
            .learning-path-section h4 {
                margin: 12px 0 8px 0;
                color: var(--text-primary);
                font-size: 0.95rem;
            }
            
            .pros-section ul,
            .cons-section ul,
            .learning-path-section ul {
                margin: 0;
                padding-left: 20px;
            }
            
            .pros-section li,
            .cons-section li,
            .learning-path-section li {
                margin-bottom: 6px;
                font-size: 0.9rem;
                color: var(--text-secondary);
                line-height: 1.4;
            }
            
            .score-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid var(--border-color);
                color: var(--text-secondary);
            }
            
            .score-item:last-child {
                border-bottom: none;
            }
            
            .score-item strong {
                color: var(--text-primary);
            }
        `;
        document.head.appendChild(style);
    }
}

// --- Analysis Logic ---

async function analyzeResume(filename) {
    window.showCountdownLoader(
        'Analyzing Resume...',
        'Extracting core skills and mapping technological profile.',
        15
    );
    try {
        const response = await fetch(`${API_BASE_URL}/analyze-resume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const data = await response.json();
        showAnalysisResults(data.profile);
    } catch (e) {
        window.triggerCriticalFailure('Analysis failed: ' + e.message);
    }
}

function showAnalysisResults(profile) {
    const mc = document.querySelector('.modal-content');
    mc.innerHTML = `
        <div class="modal-header"><h2>Profile: ${escapeHtml(profile.full_name)}</h2></div>
        <div class="profile-info">${escapeHtml(profile.summary)}</div>
        <button class="btn btn-primary" id="confirm-skills-btn">Start Quiz</button>`;
    
    document.getElementById('confirm-skills-btn').addEventListener('click', () => {
        startQuiz(sessionStorage.getItem('uploaded_filename'));
    });
}
