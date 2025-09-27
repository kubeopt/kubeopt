/**
 * ============================================================================
 * AKS COST INTELLIGENCE - PROGRESS ANIMATION FUNCTIONS
 * ============================================================================
 * Progress bars, loading animations, and visual feedback systems
 * ============================================================================
 */

import { showNotification } from './notifications.js';

/**
 * Enhanced progress animation with proper completion
 */
export function startEnhancedProgressAnimation() {
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    if (!fill || !text) {
        console.log('⚠️ Progress elements not found');
        return;
    }
    
    const progressSteps = [
        { percentage: 10, text: '🔌 Connecting to Azure...', color: '#007AFF' },
        { percentage: 25, text: '💰 Fetching cost data...', color: '#5AC8FA' },
        { percentage: 45, text: '📊 Analyzing cluster metrics...', color: '#AF52DE' },
        { percentage: 65, text: '🎯 Calculating optimization opportunities...', color: '#FF9500' },
        { percentage: 85, text: '💡 Generating insights...', color: '#34C759' }
    ];
    
    let stepIndex = 0;
    
    function advanceProgress() {
        if (stepIndex < progressSteps.length && fill && text) {
            const step = progressSteps[stepIndex];
            
            // Animate progress bar
            fill.style.width = step.percentage + '%';
            fill.style.background = `linear-gradient(90deg, ${step.color}, ${step.color}dd)`;
            fill.style.boxShadow = `0 0 20px ${step.color}44`;
            
            // Update text with animation
            text.style.opacity = '0.5';
            setTimeout(() => {
                text.textContent = step.text;
                text.style.opacity = '1';
            }, 150);
            
            stepIndex++;
            setTimeout(advanceProgress, 800);
        }
    }
    
    advanceProgress();
}

/**
 * Complete progress with success state
 */
export function completeProgressWithSuccess() {
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    if (fill && text) {
        fill.style.width = '100%';
        fill.style.background = 'linear-gradient(90deg, #28a745, #32CD32)';
        fill.style.boxShadow = '0 0 30px #28a74544';
        
        text.style.opacity = '0.5';
        setTimeout(() => {
            text.textContent = '🎉 Analysis completed successfully!';
            text.style.opacity = '1';
            text.style.color = '#28a745';
            text.style.fontWeight = 'bold';
        }, 200);
    }
}

/**
 * Multi-step progress animation
 */
export function createMultiStepProgress(container, steps) {
    if (!container || !steps.length) return null;
    
    const progressId = 'multi-step-progress-' + Date.now();
    
    const progressHTML = `
        <div id="${progressId}" class="multi-step-progress">
            <div class="progress-header mb-3">
                <h6 class="text-primary mb-2">Processing Steps</h6>
                <div class="step-indicators">
                    ${steps.map((step, index) => `
                        <div class="step-indicator" data-step="${index}">
                            <div class="step-circle">
                                <span class="step-number">${index + 1}</span>
                                <i class="fas fa-check step-check" style="display: none;"></i>
                            </div>
                            <div class="step-label">${step.title}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="progress mb-3" style="height: 8px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     style="width: 0%; transition: width 0.5s ease;" 
                     role="progressbar"></div>
            </div>
            
            <div class="progress-status">
                <div class="current-step-text text-muted">Ready to begin...</div>
                <div class="progress-percentage text-end">0%</div>
            </div>
        </div>
    `;
    
    container.innerHTML = progressHTML;
    
    // Add CSS for multi-step progress
    addMultiStepProgressCSS();
    
    let currentStep = -1;
    
    return {
        nextStep: () => {
            currentStep++;
            if (currentStep < steps.length) {
                updateMultiStepProgress(progressId, currentStep, steps);
                return true;
            }
            return false;
        },
        
        complete: () => {
            completeMultiStepProgress(progressId, steps.length);
        },
        
        error: (message) => {
            errorMultiStepProgress(progressId, message);
        },
        
        getCurrentStep: () => currentStep,
        
        setStep: (stepIndex) => {
            if (stepIndex >= 0 && stepIndex < steps.length) {
                currentStep = stepIndex;
                updateMultiStepProgress(progressId, currentStep, steps);
            }
        }
    };
}

/**
 * Update multi-step progress
 */
function updateMultiStepProgress(progressId, currentStep, steps) {
    const container = document.getElementById(progressId);
    if (!container) return;
    
    const progressBar = container.querySelector('.progress-bar');
    const statusText = container.querySelector('.current-step-text');
    const percentage = container.querySelector('.progress-percentage');
    
    const progress = ((currentStep + 1) / steps.length) * 100;
    
    // Update progress bar
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }
    
    // Update status text
    if (statusText && steps[currentStep]) {
        statusText.innerHTML = `
            <i class="fas fa-cog fa-spin me-2 text-primary"></i>
            ${steps[currentStep].description || steps[currentStep].title}
        `;
    }
    
    // Update percentage
    if (percentage) {
        percentage.textContent = Math.round(progress) + '%';
    }
    
    // Update step indicators
    container.querySelectorAll('.step-indicator').forEach((indicator, index) => {
        const circle = indicator.querySelector('.step-circle');
        const number = indicator.querySelector('.step-number');
        const check = indicator.querySelector('.step-check');
        
        if (index < currentStep) {
            // Completed step
            circle.className = 'step-circle completed';
            number.style.display = 'none';
            check.style.display = 'block';
        } else if (index === currentStep) {
            // Current step
            circle.className = 'step-circle active';
            number.style.display = 'block';
            check.style.display = 'none';
        } else {
            // Pending step
            circle.className = 'step-circle';
            number.style.display = 'block';
            check.style.display = 'none';
        }
    });
}

/**
 * Complete multi-step progress
 */
function completeMultiStepProgress(progressId, totalSteps) {
    const container = document.getElementById(progressId);
    if (!container) return;
    
    const progressBar = container.querySelector('.progress-bar');
    const statusText = container.querySelector('.current-step-text');
    const percentage = container.querySelector('.progress-percentage');
    
    // Complete progress bar
    if (progressBar) {
        progressBar.style.width = '100%';
        progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
        progressBar.classList.add('bg-success');
    }
    
    // Update status
    if (statusText) {
        statusText.innerHTML = `
            <i class="fas fa-check-circle me-2 text-success"></i>
            All steps completed successfully!
        `;
    }
    
    if (percentage) {
        percentage.textContent = '100%';
    }
    
    // Mark all steps as completed
    container.querySelectorAll('.step-indicator').forEach(indicator => {
        const circle = indicator.querySelector('.step-circle');
        const number = indicator.querySelector('.step-number');
        const check = indicator.querySelector('.step-check');
        
        circle.className = 'step-circle completed';
        number.style.display = 'none';
        check.style.display = 'block';
    });
}

/**
 * Show error in multi-step progress
 */
function errorMultiStepProgress(progressId, message) {
    const container = document.getElementById(progressId);
    if (!container) return;
    
    const progressBar = container.querySelector('.progress-bar');
    const statusText = container.querySelector('.current-step-text');
    
    if (progressBar) {
        progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
        progressBar.classList.add('bg-danger');
    }
    
    if (statusText) {
        statusText.innerHTML = `
            <i class="fas fa-exclamation-circle me-2 text-danger"></i>
            ${message || 'An error occurred during processing'}
        `;
    }
}

/**
 * Circular progress indicator
 */
export function createCircularProgress(container, options = {}) {
    const {
        size = 80,
        strokeWidth = 8,
        color = '#007bff',
        backgroundColor = '#e9ecef',
        showPercentage = true,
        animated = true
    } = options;
    
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    
    const progressHTML = `
        <div class="circular-progress" style="width: ${size}px; height: ${size}px;">
            <svg width="${size}" height="${size}" class="circular-progress-svg">
                <circle
                    cx="${size / 2}"
                    cy="${size / 2}"
                    r="${radius}"
                    stroke="${backgroundColor}"
                    stroke-width="${strokeWidth}"
                    fill="none"
                />
                <circle
                    cx="${size / 2}"
                    cy="${size / 2}"
                    r="${radius}"
                    stroke="${color}"
                    stroke-width="${strokeWidth}"
                    fill="none"
                    stroke-dasharray="${circumference}"
                    stroke-dashoffset="${circumference}"
                    stroke-linecap="round"
                    class="progress-circle ${animated ? 'animated' : ''}"
                />
            </svg>
            ${showPercentage ? `
                <div class="circular-progress-text">
                    <span class="percentage">0%</span>
                </div>
            ` : ''}
        </div>
    `;
    
    container.innerHTML = progressHTML;
    addCircularProgressCSS();
    
    const progressCircle = container.querySelector('.progress-circle');
    const percentageText = container.querySelector('.percentage');
    
    return {
        setProgress: (percentage) => {
            const offset = circumference - (percentage / 100) * circumference;
            if (progressCircle) {
                progressCircle.style.strokeDashoffset = offset;
            }
            if (percentageText) {
                percentageText.textContent = Math.round(percentage) + '%';
            }
        },
        
        complete: () => {
            if (progressCircle) {
                progressCircle.style.strokeDashoffset = 0;
                progressCircle.style.stroke = '#28a745';
            }
            if (percentageText) {
                percentageText.textContent = '100%';
                percentageText.style.color = '#28a745';
            }
        },
        
        reset: () => {
            if (progressCircle) {
                progressCircle.style.strokeDashoffset = circumference;
                progressCircle.style.stroke = color;
            }
            if (percentageText) {
                percentageText.textContent = '0%';
                percentageText.style.color = '';
            }
        }
    };
}

/**
 * Loading spinner with custom messages
 */
export function showLoadingSpinner(container, message = 'Loading...') {
    const spinnerHTML = `
        <div class="loading-spinner-container">
            <div class="loading-spinner">
                <div class="spinner-ring">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
            </div>
            <div class="loading-message mt-3">
                ${message}
            </div>
        </div>
    `;
    
    container.innerHTML = spinnerHTML;
    addLoadingSpinnerCSS();
    
    return {
        updateMessage: (newMessage) => {
            const messageEl = container.querySelector('.loading-message');
            if (messageEl) {
                messageEl.textContent = newMessage;
            }
        },
        
        hide: () => {
            const spinnerContainer = container.querySelector('.loading-spinner-container');
            if (spinnerContainer) {
                spinnerContainer.style.opacity = '0';
                setTimeout(() => {
                    container.innerHTML = '';
                }, 300);
            }
        }
    };
}

/**
 * Pulse animation for elements
 */
export function addPulseAnimation(element, duration = 2000) {
    if (!element) return;
    
    element.style.animation = `pulse ${duration}ms ease-in-out infinite`;
    
    return () => {
        element.style.animation = '';
    };
}

/**
 * Fade in animation
 */
export function fadeIn(element, duration = 300) {
    if (!element) return Promise.resolve();
    
    return new Promise((resolve) => {
        element.style.opacity = '0';
        element.style.transition = `opacity ${duration}ms ease`;
        element.style.display = 'block';
        
        setTimeout(() => {
            element.style.opacity = '1';
            setTimeout(resolve, duration);
        }, 10);
    });
}

/**
 * Fade out animation
 */
export function fadeOut(element, duration = 300) {
    if (!element) return Promise.resolve();
    
    return new Promise((resolve) => {
        element.style.transition = `opacity ${duration}ms ease`;
        element.style.opacity = '0';
        
        setTimeout(() => {
            element.style.display = 'none';
            resolve();
        }, duration);
    });
}

/**
 * Slide down animation
 */
export function slideDown(element, duration = 300) {
    if (!element) return Promise.resolve();
    
    return new Promise((resolve) => {
        element.style.overflow = 'hidden';
        element.style.height = '0px';
        element.style.transition = `height ${duration}ms ease`;
        element.style.display = 'block';
        
        const fullHeight = element.scrollHeight + 'px';
        
        setTimeout(() => {
            element.style.height = fullHeight;
            setTimeout(() => {
                element.style.height = '';
                element.style.overflow = '';
                resolve();
            }, duration);
        }, 10);
    });
}

/**
 * Slide up animation
 */
export function slideUp(element, duration = 300) {
    if (!element) return Promise.resolve();
    
    return new Promise((resolve) => {
        element.style.overflow = 'hidden';
        element.style.height = element.scrollHeight + 'px';
        element.style.transition = `height ${duration}ms ease`;
        
        setTimeout(() => {
            element.style.height = '0px';
            setTimeout(() => {
                element.style.display = 'none';
                element.style.height = '';
                element.style.overflow = '';
                resolve();
            }, duration);
        }, 10);
    });
}

/**
 * CSS for multi-step progress
 */
function addMultiStepProgressCSS() {
    if (document.getElementById('multi-step-progress-css')) return;
    
    const style = document.createElement('style');
    style.id = 'multi-step-progress-css';
    style.textContent = `
        .multi-step-progress {
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        
        .step-indicators {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .step-indicator {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            position: relative;
        }
        
        .step-indicator:not(:last-child)::after {
            content: '';
            position: absolute;
            top: 20px;
            left: 60%;
            width: 80%;
            height: 2px;
            background: #dee2e6;
            z-index: 1;
        }
        
        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #fff;
            border: 2px solid #dee2e6;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .step-circle.active {
            border-color: #007bff;
            background: #007bff;
            color: white;
            animation: pulse-border 2s infinite;
        }
        
        .step-circle.completed {
            border-color: #28a745;
            background: #28a745;
            color: white;
        }
        
        .step-label {
            margin-top: 0.5rem;
            font-size: 0.875rem;
            text-align: center;
            max-width: 80px;
        }
        
        .step-number {
            font-weight: bold;
            font-size: 0.875rem;
        }
        
        .step-check {
            font-size: 1rem;
        }
        
        .progress-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        @keyframes pulse-border {
            0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(0, 123, 255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }
        }
        
        @media (max-width: 768px) {
            .step-indicators {
                flex-direction: column;
                gap: 1rem;
            }
            
            .step-indicator:not(:last-child)::after {
                display: none;
            }
            
            .step-label {
                max-width: none;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * CSS for circular progress
 */
function addCircularProgressCSS() {
    if (document.getElementById('circular-progress-css')) return;
    
    const style = document.createElement('style');
    style.id = 'circular-progress-css';
    style.textContent = `
        .circular-progress {
            position: relative;
            display: inline-block;
        }
        
        .circular-progress-svg {
            transform: rotate(-90deg);
        }
        
        .progress-circle {
            transition: stroke-dashoffset 0.5s ease;
        }
        
        .progress-circle.animated {
            animation: rotate 2s linear infinite;
        }
        
        .circular-progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }
        
        .percentage {
            font-weight: bold;
            font-size: 1.2em;
        }
        
        @keyframes rotate {
            from { transform: rotate(-90deg); }
            to { transform: rotate(270deg); }
        }
    `;
    document.head.appendChild(style);
}

/**
 * CSS for loading spinner
 */
function addLoadingSpinnerCSS() {
    if (document.getElementById('loading-spinner-css')) return;
    
    const style = document.createElement('style');
    style.id = 'loading-spinner-css';
    style.textContent = `
        .loading-spinner-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            transition: opacity 0.3s ease;
        }
        
        .spinner-ring {
            display: inline-block;
            position: relative;
            width: 80px;
            height: 80px;
        }
        
        .spinner-ring div {
            box-sizing: border-box;
            display: block;
            position: absolute;
            width: 64px;
            height: 64px;
            margin: 8px;
            border: 8px solid #007bff;
            border-radius: 50%;
            animation: spinner-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
            border-color: #007bff transparent transparent transparent;
        }
        
        .spinner-ring div:nth-child(1) { animation-delay: -0.45s; }
        .spinner-ring div:nth-child(2) { animation-delay: -0.3s; }
        .spinner-ring div:nth-child(3) { animation-delay: -0.15s; }
        
        @keyframes spinner-ring {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-message {
            color: #6c757d;
            font-size: 1rem;
            text-align: center;
        }
    `;
    document.head.appendChild(style);
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.startEnhancedProgressAnimation = startEnhancedProgressAnimation;
    window.completeProgressWithSuccess = completeProgressWithSuccess;
    window.createMultiStepProgress = createMultiStepProgress;
    window.createCircularProgress = createCircularProgress;
    window.showLoadingSpinner = showLoadingSpinner;
    window.addPulseAnimation = addPulseAnimation;
    window.fadeIn = fadeIn;
    window.fadeOut = fadeOut;
    window.slideDown = slideDown;
    window.slideUp = slideUp;
}

console.log('✅ Progress animation functions loaded successfully');