/**
 * Advanced Coding IDE with Monaco Editor
 * Professional code editor with syntax highlighting, multiple languages, and test execution
 */

let monacoEditor = null;
let codingEditorState = {
    challenges: [],
    currentChallengeIndex: 0,
    filename: null,
    language: 'python',
    codeByChallenge: {},
    editorInstance: null,
    testResults: {},
    isSubmitting: false,
    skippedChallenges: {},
    listenersAttached: false
};

// Initialize Monaco Editor
function initMonacoEditor(code = '') {
    require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });
    
    require(['vs/editor/editor.main'], () => {
        const container = document.getElementById('monaco-editor-container');
        if (!container) return;

        monacoEditor = monaco.editor.create(container, {
            value: code,
            language: getMonacoLanguage(codingEditorState.language),
            theme: 'vs-dark',
            fontSize: 14,
            fontFamily: "'JetBrains Mono', monospace",
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            formatOnPaste: true,
            formatOnType: true,
            tabSize: 4,
            wordWrap: 'on',
            lineNumbers: 'on',
            folding: true,
            bracketPairColorization: true,
            padding: { top: 16 }
        });

        // Update code state on input
        monacoEditor.onDidChangeModelContent(() => {
            codingEditorState.codeByChallenge[codingEditorState.currentChallengeIndex] = monacoEditor.getValue();
        });
    });
}

function getMonacoLanguage(lang) {
    const langMap = {
        'python': 'python',
        'javascript': 'javascript',
        'java': 'java',
        'cpp': 'cpp',
        'c++': 'cpp'
    };
    return langMap[lang] || 'python';
}

function switchLanguage(newLanguage) {
    if (!monacoEditor) return;

    // Save current code
    codingEditorState.codeByChallenge[codingEditorState.currentChallengeIndex] = monacoEditor.getValue();
    codingEditorState.language = newLanguage;

    // Get starter code for new language
    const challenge = codingEditorState.challenges[codingEditorState.currentChallengeIndex];
    const starterCode = challenge.starter_code_by_language?.[newLanguage] || '';

    // Update editor language and code
    const model = monacoEditor.getModel();
    monaco.editor.setModelLanguage(model, getMonacoLanguage(newLanguage));
    monacoEditor.setValue(starterCode);

    // Update language selector
    document.getElementById('language-select').value = newLanguage;
}

function resetCode() {
    if (!monacoEditor) return;

    const challenge = codingEditorState.challenges[codingEditorState.currentChallengeIndex];
    const starterCode = challenge.starter_code_by_language?.[codingEditorState.language] || '';
    monacoEditor.setValue(starterCode);
    
    showSuccess('Code reset to starter template');
}

async function renderCodingChallengeAdvanced() {
    const challenge = codingEditorState.challenges[codingEditorState.currentChallengeIndex];
    if (!challenge) return;

    const mc = document.querySelector('.modal-content');
    const totalChallenges = codingEditorState.challenges.length;
    const currentNum = codingEditorState.currentChallengeIndex + 1;

    mc.innerHTML = `
        <div class="ide-container">
            <!-- Header -->
            <div class="ide-header">
                <div class="ide-title">
                    <h3 class="ide-challenge-name">${escapeHtml(challenge.title || 'Coding Challenge')}</h3>
                    <span class="ide-difficulty difficulty-${(challenge.difficulty || 'medium').toLowerCase()}">
                        ${escapeHtml(challenge.difficulty || 'Medium')}
                    </span>
                </div>
                <div class="ide-progress">
                    <span class="progress-badge">${currentNum} / ${totalChallenges}</span>
                </div>
                
                <div class="ide-controls">
                    <select id="language-select" class="language-selector">
                        <option value="python" ${codingEditorState.language === 'python' ? 'selected' : ''}>Python</option>
                        <option value="javascript" ${codingEditorState.language === 'javascript' ? 'selected' : ''}>JavaScript</option>
                        <option value="java" ${codingEditorState.language === 'java' ? 'selected' : ''}>Java</option>
                        <option value="cpp" ${codingEditorState.language === 'cpp' ? 'selected' : ''}>C++</option>
                    </select>
                    <button class="reset-code-btn" data-action="reset" title="Reset to starter code">
                        Reset
                    </button>
                    <button class="reset-code-btn" data-action="skip" style="cursor: pointer; text-decoration: none;">Skip</button>
                </div>
            </div>

            <!-- Main Body -->
            <div class="ide-body">
                <!-- Problem Panel (Left) -->
                <div class="problem-panel">
                    <div class="problem-panel-header">
                        <h3>Problem Statement</h3>
                    </div>
                    <div class="problem-content">
                        <div class="problem-description">
                            <h3>Challenge</h3>
                            <p>${escapeHtml(challenge.problem_statement || '')}</p>
                        </div>

                        ${challenge.examples ? `
                            <div class="test-cases-panel">
                                <h3>Examples</h3>
                                ${challenge.examples.map((ex, i) => `
                                    <div class="test-case-item">
                                        <div class="test-case-label">Example ${i + 1}</div>
                                        <div class="test-case-input"><strong>Input:</strong> ${escapeHtml(ex.input || '')}</div>
                                        <div class="test-case-output"><strong>Output:</strong> ${escapeHtml(ex.output || '')}</div>
                                        ${ex.explanation ? `<div style="margin-top: 6px; color: var(--text-secondary);"><strong>Explanation:</strong> ${escapeHtml(ex.explanation)}</div>` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}

                        ${challenge.constraints ? `
                            <div class="constraints-section">
                                <h4>Constraints</h4>
                                <p>${escapeHtml(challenge.constraints)}</p>
                            </div>
                        ` : ''}
                    </div>
                </div>

                <!-- Editor Panel (Right) -->
                <div class="editor-panel">
                    <!-- Code Editor -->
                    <div class="editor-top">
                        <div class="editor-wrapper">
                            <div id="monaco-editor-container" class="monaco-editor-container"></div>
                        </div>
                        <div class="editor-stats">
                            <div class="editor-stat">
                                <span class="editor-stat-label">Language:</span>
                                <span class="editor-stat-value" id="lang-display">python</span>
                            </div>
                            <div class="editor-stat">
                                <span class="editor-stat-label">Characters:</span>
                                <span class="editor-stat-value" id="char-count">0</span>
                            </div>
                            <div class="editor-stat">
                                <span class="editor-stat-label">Lines:</span>
                                <span class="editor-stat-value" id="line-count">0</span>
                            </div>
                        </div>
                    </div>

                    <!-- Footer with Console & Results -->
                    <div class="editor-footer">
                        <!-- Console Output -->
                        <div class="console-panel">
                            <div class="panel-header">
                                <h4>Console Output</h4>
                                <button class="panel-clear-btn" data-action="clear">Clear</button>
                            </div>
                            <div id="console-output" class="console-output">
                                <span class="console-empty">Output will appear here...</span>
                            </div>
                        </div>

                        <!-- Test Results -->
                        <div class="test-results-panel">
                            <div class="panel-header">
                                <h4>Test Results</h4>
                            </div>
                            <div id="test-results-area" class="test-results">
                                <div class="console-empty" style="padding: 12px; text-align: center;">
                                    Run code to see results
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Submission Buttons -->
                    <div class="submission-panel">
                        <button class="submit-btn" id="submit-code-btn" ${codingEditorState.isSubmitting ? 'disabled' : ''}>
                            <span id="submit-text">Submit Code</span>
                        </button>
                        <button class="skip-btn" data-action="skip">Skip Challenge</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Initialize Monaco Editor after DOM is rendered
    const challengeCode = codingEditorState.codeByChallenge[codingEditorState.currentChallengeIndex] ||
        challenge.starter_code_by_language?.[codingEditorState.language] || '';
    
    setTimeout(() => {
        try {
            initMonacoEditor(challengeCode);
            updateCodeStats();
            attachEventListeners();
        } catch (error) {
            console.error('Error initializing editor:', error);
            showError('Failed to initialize coding editor');
        }
    }, 100);
}

// Attach event listeners to dynamically created elements
function attachEventListeners() {
    try {
        // Remove old listeners by cloning elements (removes all event listeners)
        const skipButtons = document.querySelectorAll('[data-action="skip"]');
        skipButtons.forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
        });

        // Re-attach listeners to fresh elements
        document.querySelectorAll('[data-action="skip"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                skipChallenge();
            }, { once: false });
        });

        // Submit button
        const submitBtn = document.getElementById('submit-code-btn');
        if (submitBtn) {
            // Clone and replace to remove old listeners
            const newSubmitBtn = submitBtn.cloneNode(true);
            submitBtn.parentNode.replaceChild(newSubmitBtn, submitBtn);
            newSubmitBtn.addEventListener('click', (e) => {
                e.preventDefault();
                submitCodeAdvanced();
            });
        }

        // Language selector
        const langSelect = document.getElementById('language-select');
        if (langSelect) {
            const newLangSelect = langSelect.cloneNode(true);
            langSelect.parentNode.replaceChild(newLangSelect, langSelect);
            newLangSelect.addEventListener('change', (e) => {
                switchLanguage(e.target.value);
            });
        }

        // Reset button
        const resetBtn = document.querySelector('[data-action="reset"]');
        if (resetBtn) {
            const newResetBtn = resetBtn.cloneNode(true);
            resetBtn.parentNode.replaceChild(newResetBtn, resetBtn);
            newResetBtn.addEventListener('click', (e) => {
                e.preventDefault();
                resetCode();
            });
        }

        // Clear console button
        const clearBtn = document.querySelector('[data-action="clear"]');
        if (clearBtn) {
            const newClearBtn = clearBtn.cloneNode(true);
            clearBtn.parentNode.replaceChild(newClearBtn, clearBtn);
            newClearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                clearConsole();
            });
        }
    } catch (error) {
        console.error('Error attaching event listeners:', error);
    }
}

function updateCodeStats() {
    if (!monacoEditor) return;

    const code = monacoEditor.getValue();
    const charCount = code.length;
    const lineCount = code.split('\n').length;

    // Update new stat display format
    const charEl = document.getElementById('char-count');
    const lineEl = document.getElementById('line-count');
    const langEl = document.getElementById('lang-display');

    if (charEl) charEl.textContent = charCount;
    if (lineEl) lineEl.textContent = lineCount;
    if (langEl) langEl.textContent = codingEditorState.language;
}

function clearConsole() {
    const console = document.getElementById('console-output');
    if (console) {
        console.innerHTML = '<span class="console-empty">Cleared</span>';
    }
}

function addConsoleOutput(text, type = 'info') {
    const console = document.getElementById('console-output');
    if (!console) return;

    // Remove empty placeholder
    if (console.querySelector('.console-empty')) {
        console.innerHTML = '';
    }

    const line = document.createElement('div');
    line.className = `output-${type}`;
    line.textContent = text;
    console.appendChild(line);
    console.scrollTop = console.scrollHeight;
}

async function submitCodeAdvanced() {
    if (codingEditorState.isSubmitting || !monacoEditor) {
        showError('Already submitting or editor not ready');
        return;
    }

    const code = monacoEditor.getValue();
    
    if (!code || code.trim().length === 0) {
        addConsoleOutput('✗ Please write some code before submitting', 'error');
        return;
    }

    codingEditorState.isSubmitting = true;
    const submitBtn = document.getElementById('submit-code-btn');
    const submitText = submitBtn ? document.getElementById('submit-text') : null;
    
    if (submitBtn) {
        submitBtn.disabled = true;
        if (submitText) submitText.textContent = 'Submitting...';
    }

    const challenge = codingEditorState.challenges[codingEditorState.currentChallengeIndex];
    if (!challenge) {
        addConsoleOutput('✗ Challenge not loaded', 'error');
        codingEditorState.isSubmitting = false;
        return;
    }

    addConsoleOutput(`Submitting ${codingEditorState.language} code...`, 'info');

    try {
        const response = await fetch(`${API_BASE_URL}/submit-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                challenge_id: codingEditorState.filename,
                challenge_index: codingEditorState.currentChallengeIndex,
                code,
                language: codingEditorState.language,
                skipped: false  // Not skipped - user submitted code
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Server error' }));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        if (!result) throw new Error('No response from server');

        displayTestResults(result);
        
        if (result.success) {
            addConsoleOutput(`✓ All tests passed!`, 'success');
            if (result.feedback) {
                addConsoleOutput(`Feedback: ${result.feedback}`, 'info');
            }
            sessionStorage.setItem(`coding_test_result_${codingEditorState.currentChallengeIndex}`, JSON.stringify(result));
            
            setTimeout(() => {
                try {
                    if (codingEditorState.currentChallengeIndex < codingEditorState.challenges.length - 1) {
                        codingEditorState.currentChallengeIndex++;
                        codingEditorState.language = 'python';
                        renderCodingChallengeAdvanced();
                    } else {
                        finishCodingRoundAdvanced();
                    }
                } catch (err) {
                    console.error('Error loading next challenge:', err);
                    showError('Failed to load next challenge');
                }
            }, 2000);
        } else {
            const failMessage = result.feedback ? `${result.feedback}` : 'Some tests failed';
            addConsoleOutput(`✗ ${failMessage}`, 'error');
            
            if (result.passed_test_cases !== undefined && result.total_test_cases !== undefined) {
                addConsoleOutput(`Passed: ${result.passed_test_cases}/${result.total_test_cases}`, 'warning');
            }
            
            if (submitBtn) {
                submitBtn.disabled = false;
                if (submitText) submitText.textContent = 'Submit Code';
            }
        }
    } catch (error) {
        console.error('Submission error:', error);
        addConsoleOutput(`✗ Error: ${error.message}`, 'error');
        if (submitBtn) {
            submitBtn.disabled = false;
            if (submitText) submitText.textContent = 'Submit Code';
        }
        showError('Submission failed: ' + error.message);
    } finally {
        codingEditorState.isSubmitting = false;
    }
}

function displayTestResults(result) {
    const resultsArea = document.getElementById('test-results-area');
    if (!resultsArea) {
        console.warn('Test results area not found');
        return;
    }

    try {
        // Handle both test_cases and test_results field names for compatibility
        const testCases = result.test_cases || result.test_results || [];
        const totalTests = result.total_test_cases || testCases.length || 0;
        const passedTests = result.passed_test_cases !== undefined ? result.passed_test_cases : (testCases.filter(tc => tc.passed).length || 0);
        
        // If no test cases to display, show summary
        if (testCases.length === 0) {
            resultsArea.innerHTML = `
                <div class="test-result-item ${result.success ? 'pass' : 'fail'}">
                    <div class="result-status ${result.success ? 'pass' : 'fail'}">
                        ${result.success ? '✓ Accepted' : '✗ Wrong Answer'}
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 8px;">
                        ${result.feedback || 'Check your solution'}
                    </div>
                    ${totalTests > 0 ? `<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 6px;">Passed: ${passedTests}/${totalTests}</div>` : ''}
                    ${result.time_complexity ? `<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">Complexity: ${result.time_complexity}</div>` : ''}
                </div>
            `;
            return;
        }

        // Display detailed test results
        const overallHtml = `
            <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
                <div style="font-size: 0.9rem; font-weight: 500; color: var(--text-primary);">Overall: ${passedTests}/${totalTests} passed</div>
                ${result.score !== undefined ? `<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">Score: ${result.score}/100</div>` : ''}
            </div>
        `;

        const testCasesHtml = testCases.map((tc, i) => `
            <div class="test-result-item ${tc.passed ? 'pass' : 'fail'}">
                <div class="result-status ${tc.passed ? 'pass' : 'fail'}">
                    Test ${i + 1}: ${tc.passed ? '✓ Passed' : '✗ Failed'}
                </div>
                ${!tc.passed ? `
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 6px;">
                        Expected: ${tc.expected_output ? escapeHtml(String(tc.expected_output).slice(0, 50)) : 'N/A'}
                        <br>Got: ${tc.actual_output ? escapeHtml(String(tc.actual_output).slice(0, 50)) : 'N/A'}
                        ${tc.explanation ? `<br><span style="color: var(--text-tertiary);">${escapeHtml(String(tc.explanation).slice(0, 100))}</span>` : ''}
                    </div>
                ` : ''}
                ${tc.execution_time ? `<div class="result-time">${tc.execution_time}ms</div>` : ''}
            </div>
        `).join('');

        resultsArea.innerHTML = overallHtml + testCasesHtml;
        
        // Add feedback if available
        if (result.feedback && !result.success) {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.style.cssText = 'margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-color); font-size: 0.85rem; color: var(--text-secondary);';
            feedbackDiv.innerHTML = `<strong>Feedback:</strong> ${escapeHtml(result.feedback)}`;
            resultsArea.appendChild(feedbackDiv);
        }
    } catch (error) {
        console.error('Error displaying test results:', error);
        resultsArea.innerHTML = `<div style="color: var(--text-secondary);">Error displaying results: ${escapeHtml(error.message)}</div>`;
    }
}

async function skipChallenge() {
    try {
        if (!codingEditorState.challenges || codingEditorState.challenges.length === 0) {
            showError('No challenges available');
            return;
        }

        const currentIndex = codingEditorState.currentChallengeIndex;
        
        // Submit skip record to backend
        try {
            const response = await fetch(`${API_BASE_URL}/submit-code`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    challenge_id: codingEditorState.filename,
                    challenge_index: currentIndex,
                    code: "",  // Empty code for skipped
                    language: codingEditorState.language,
                    skipped: true  // Mark as skipped
                })
            });

            if (!response.ok) {
                console.warn('Failed to record skip on backend, continuing locally');
            }
        } catch (error) {
            console.warn('Backend skip submission failed:', error);
            // Continue anyway - record locally
        }

        // Mark current challenge as skipped locally
        codingEditorState.skippedChallenges[currentIndex] = true;

        if (currentIndex < codingEditorState.challenges.length - 1) {
            // Move to next challenge
            codingEditorState.currentChallengeIndex++;
            codingEditorState.language = 'python';
            
            console.log(`Skipped challenge ${currentIndex}, moving to ${codingEditorState.currentChallengeIndex}`);
            
            renderCodingChallengeAdvanced();
            showSuccess('Challenge skipped. Moving to next...');
        } else {
            // Last challenge - finish the round
            console.log(`Skipped challenge ${currentIndex}, finishing coding round`);
            finishCodingRoundAdvanced();
        }
    } catch (error) {
        console.error('Error skipping challenge:', error);
        showError('Failed to skip challenge: ' + error.message);
    }
}

async function finishCodingRoundAdvanced() {
    window.showCountdownLoader(
        'Processing Your Results...',
        'Saving your code and preparing for the final phase.',
        5
    );
    
    setTimeout(() => {
        generateFinalReport();
    }, 1000);
}

// Replace the old renderCodingChallenge with the new one
async function startCodingChallenge() {
    const filename = sessionStorage.getItem('uploaded_filename');
    if (!filename) {
        showError('No session found. Please upload a resume.');
        return;
    }
    
    codingEditorState.filename = filename;
    window.showCountdownLoader(
        'Preparing Coding Challenges...',
        'Designing a real-world task based on your tech stack.',
        20
    );

    try {
        const response = await fetch(`${API_BASE_URL}/generate-challenge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to generate challenges');
        }
        
        const data = await response.json();
        if (!data.challenges || data.challenges.length === 0) {
            throw new Error('No challenges generated');
        }
        
        codingEditorState.challenges = data.challenges;
        codingEditorState.currentChallengeIndex = 0;
        codingEditorState.language = 'python';
        codingEditorState.codeByChallenge = {};
        codingEditorState.skippedChallenges = {}; // Reset skipped challenges
        codingEditorState.testResults = {}; // Reset test results
        codingEditorState.listenersAttached = false;
        
        renderCodingChallengeAdvanced();
    } catch (error) {
        console.error('Coding challenge error:', error);
        window.triggerCriticalFailure('Coding round failed: ' + error.message);
    }
}
