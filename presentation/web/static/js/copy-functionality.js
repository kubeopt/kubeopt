/**
 * ============================================================================
 * AKS COST INTELLIGENCE - COPY TO CLIPBOARD FUNCTIONALITY
 * ============================================================================
 * Enhanced copy functionality with proper error handling and visual feedback
 * ============================================================================
 */

import { showNotification } from './notifications.js';

/**
 * Enhanced copy to clipboard function with proper error handling
 */
export function copyToClipboard(text, buttonElement = null) {
    // Get the button element if not provided
    if (!buttonElement && typeof event !== 'undefined' && event.target) {
        buttonElement = event.target.closest('.copy-btn, button');
    }
    
    console.log('📋 Copy function called:', { text, buttonElement });
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            console.log('✅ Successfully copied to clipboard:', text.substring(0, 50) + '...');
            showCopySuccess(buttonElement, 'Copied to clipboard!');
            showNotification('📋 Copied to clipboard!', 'success', 2000);
        }).catch(err => {
            console.error('❌ Clipboard API failed:', err);
            fallbackCopy(text, buttonElement);
        });
    } else {
        console.log('📋 Using fallback copy method');
        fallbackCopy(text, buttonElement);
    }
}

/**
 * Fallback copy method for older browsers
 */
function fallbackCopy(text, buttonElement = null) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.cssText = `
        position: fixed !important;
        top: -1000px !important;
        left: -1000px !important;
        width: 1px !important;
        height: 1px !important;
        opacity: 0 !important;
        pointer-events: none !important;
    `;
    
    document.body.appendChild(textArea);
    textArea.select();
    textArea.setSelectionRange(0, 99999);
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            console.log('✅ Fallback copy successful');
            showCopySuccess(buttonElement, 'Copied to clipboard!');
            showNotification('📋 Copied to clipboard!', 'success', 2000);
        } else {
            throw new Error('execCommand failed');
        }
    } catch (err) {
        console.error('❌ Fallback copy failed:', err);
        showCopyError(buttonElement, 'Copy failed');
        showNotification('❌ Failed to copy to clipboard', 'error');
    } finally {
        document.body.removeChild(textArea);
    }
}

/**
 * Enhanced copyCommand function
 */
export function copyCommand(elementId, buttonElement = null) {
    console.log('📋 copyCommand called with elementId:', elementId);
    
    const element = document.getElementById(elementId);
    if (!element) {
        console.error('❌ Element not found:', elementId);
        showNotification('❌ Content not found', 'error');
        return;
    }
    
    // Get the text content
    const text = element.textContent || element.innerText || element.value;
    if (!text || text.trim() === '') {
        console.error('❌ No text content found in element:', elementId);
        showNotification('❌ No content to copy', 'error');
        return;
    }
    
    // If buttonElement not provided, try to find it
    if (!buttonElement && typeof event !== 'undefined' && event.target) {
        buttonElement = event.target.closest('.copy-btn, button');
    }
    
    copyToClipboard(text.trim(), buttonElement);
}

/**
 * Show copy success with visual feedback
 */
function showCopySuccess(buttonElement, message = 'Copied!') {
    if (!buttonElement) {
        console.log('✅ Copy successful');
        return;
    }
    
    // Store original content
    const originalHTML = buttonElement.innerHTML;
    const originalText = buttonElement.textContent;
    
    // Show success state
    buttonElement.classList.add('copied');
    
    // Update button content
    if (buttonElement.querySelector('i')) {
        buttonElement.innerHTML = '<i class="fas fa-check"></i> Copied!';
    } else {
        buttonElement.textContent = 'Copied!';
    }
    
    // Add success styling
    buttonElement.style.background = 'linear-gradient(135deg, #059669, #047857)';
    buttonElement.style.transform = 'scale(0.95)';
    
    // Reset after delay
    setTimeout(() => {
        buttonElement.classList.remove('copied');
        buttonElement.innerHTML = originalHTML;
        buttonElement.style.background = '';
        buttonElement.style.transform = '';
    }, 2000);
}

/**
 * Show copy error with visual feedback
 */
function showCopyError(buttonElement, message = 'Copy failed') {
    if (!buttonElement) {
        console.log('❌ Copy failed (no button element for feedback)');
        return;
    }
    
    const originalHTML = buttonElement.innerHTML;
    
    buttonElement.classList.add('copy-error');
    buttonElement.innerHTML = '<i class="fas fa-exclamation"></i> Failed';
    buttonElement.style.background = 'linear-gradient(135deg, #dc2626, #b91c1c)';
    
    setTimeout(() => {
        buttonElement.classList.remove('copy-error');
        buttonElement.innerHTML = originalHTML;
        buttonElement.style.background = '';
    }, 2000);
}

/**
 * Enhanced event handler setup for copy buttons
 */
function setupCopyButtonHandlers() {
    console.log('🔧 Setting up copy button handlers...');
    
    // ✅ CHECK IF ALREADY SETUP
    if (window.copyHandlersSetup) {
        console.log('Copy handlers already setup, skipping...');
        return;
    }
    
    document.addEventListener('click', handleCopyButtonClick);
    window.copyHandlersSetup = true;  // ✅ PREVENT DUPLICATES
    
    console.log('✅ Copy button handlers setup complete');
}

/**
 * Global copy button click handler
 */
function handleCopyButtonClick(event) {
    const copyBtn = event.target.closest('.copy-btn, [onclick*="copy"], [data-copy]');
    if (!copyBtn) return;
    
    console.log('📋 Copy button clicked:', copyBtn);
    
    // Prevent default action
    event.preventDefault();
    event.stopPropagation();
    
    // Get copy target
    let copyTarget = null;
    let copyText = '';
    
    // Method 1: data-copy attribute
    if (copyBtn.hasAttribute('data-copy')) {
        copyText = copyBtn.getAttribute('data-copy');
        console.log('📋 Method 1: Using data-copy attribute');
    }
    
    // Method 2: data-copy-target attribute
    else if (copyBtn.hasAttribute('data-copy-target')) {
        const targetId = copyBtn.getAttribute('data-copy-target');
        copyTarget = document.getElementById(targetId);
        if (copyTarget) {
            copyText = copyTarget.textContent || copyTarget.innerText || copyTarget.value;
            console.log('📋 Method 2: Using data-copy-target attribute');
        }
    }
    
    // Method 3: Check onclick attribute for element ID
    else if (copyBtn.hasAttribute('onclick')) {
        const onclickValue = copyBtn.getAttribute('onclick');
        const match = onclickValue.match(/copyCommand\(['"]([^'"]+)['"]\)/);
        if (match) {
            const elementId = match[1];
            copyTarget = document.getElementById(elementId);
            if (copyTarget) {
                copyText = copyTarget.textContent || copyTarget.innerText || copyTarget.value;
                console.log('📋 Method 3: Using onclick attribute parsing');
            }
        }
    }
    
    // Method 4: Find nearest code block (fallback)
    else {
        copyTarget = copyBtn.closest('.command-wrapper, .code-block, .task-block')
                           ?.querySelector('.command-code, .code-content, pre, code');
        if (copyTarget) {
            copyText = copyTarget.textContent || copyTarget.innerText;
            console.log('📋 Method 4: Using nearest code block');
        }
    }
    
    // Execute copy if we found content
    if (copyText && copyText.trim()) {
        console.log('📋 Copying text:', copyText.substring(0, 50) + '...');
        copyToClipboard(copyText.trim(), copyBtn);
    } else {
        console.error('❌ No content found to copy');
        showCopyError(copyBtn, 'No content found');
        showNotification('❌ No content found to copy', 'error');
    }
}

/**
 * Initialize copy functionality
 */
export function initializeCopyFunctionality() {
    console.log('🚀 Initializing copy functionality...');
    
    // Setup event handlers
    setupCopyButtonHandlers();
    
    // Make functions globally available
    window.copyToClipboard = copyToClipboard;
    window.copyCommand = copyCommand;
    window.showCopySuccess = showCopySuccess;
    window.showCopyError = showCopyError;
    
    // Ensure copy buttons are visible
    setTimeout(() => {
        const copyButtons = document.querySelectorAll('.copy-btn');
        console.log(`🔍 Found ${copyButtons.length} copy buttons`);
        
        copyButtons.forEach((btn, index) => {
            // Make sure copy buttons are visible
            if (btn.style.opacity === '0' || btn.style.display === 'none') {
                btn.style.opacity = '0.8';
                btn.style.display = 'block';
                console.log(`👁️ Made copy button ${index + 1} visible`);
            }
            
            // Add data attributes for easier targeting
            if (!btn.hasAttribute('data-copy') && !btn.hasAttribute('data-copy-target')) {
                const commandWrapper = btn.closest('.command-wrapper, .code-block');
                const codeElement = commandWrapper?.querySelector('.command-code, .code-content, pre, code');
                if (codeElement && codeElement.id) {
                    btn.setAttribute('data-copy-target', codeElement.id);
                    console.log(`🔗 Added data-copy-target to button ${index + 1}`);
                }
            }
        });
    }, 1000);
    
    console.log('✅ Copy functionality initialization complete');
}

/**
 * Copy multiple items at once
 */
export function copyMultiple(items) {
    if (!Array.isArray(items) || items.length === 0) {
        showNotification('❌ No items to copy', 'error');
        return;
    }
    
    const combinedText = items.map(item => {
        if (typeof item === 'string') {
            return item;
        } else if (item.id) {
            const element = document.getElementById(item.id);
            return element ? (element.textContent || element.innerText || element.value) : '';
        } else if (item.text) {
            return item.text;
        }
        return '';
    }).filter(text => text.trim()).join('\n\n');
    
    if (combinedText) {
        copyToClipboard(combinedText);
        showNotification(`📋 Copied ${items.length} items to clipboard`, 'success');
    } else {
        showNotification('❌ No valid content found to copy', 'error');
    }
}

/**
 * Copy with formatting options
 */
export function copyWithFormat(text, format = 'plain') {
    let formattedText = text;
    
    switch (format) {
        case 'json':
            try {
                formattedText = JSON.stringify(JSON.parse(text), null, 2);
            } catch (e) {
                formattedText = text;
            }
            break;
        case 'yaml':
            // Basic YAML formatting
            formattedText = text.replace(/(\w+):/g, '$1:');
            break;
        case 'markdown':
            formattedText = '```\n' + text + '\n```';
            break;
        default:
            formattedText = text;
    }
    
    copyToClipboard(formattedText);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCopyFunctionality);
} else {
    initializeCopyFunctionality();
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.copyToClipboard = copyToClipboard;
    window.copyCommand = copyCommand;
    window.copyMultiple = copyMultiple;
    window.copyWithFormat = copyWithFormat;
    window.initializeCopyFunctionality = initializeCopyFunctionality;
}

console.log('✅ Copy functionality script loaded successfully');