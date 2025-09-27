/**
 * IMPLEMENTATION PLAN INTERACTIONS - Event Handlers and User Interactions
 * Handles all user interactions, toggles, copying, and dynamic functionality
 */

import { showCopyNotification } from './plan-utils.js';

let PLAN_DATA_CACHE = null;

/**
 * EXISTING GLOBAL FUNCTIONS - PRESERVED EXACTLY
 */
window.toggleCompletePhase = function(phaseId) {
    console.log(`🔄 Toggling phase: ${phaseId}`);
    const content = document.getElementById(`complete-content-${phaseId}`);
    if (content) {
        const isExpanded = content.style.maxHeight !== '0px' && content.style.maxHeight !== '';
        
        if (isExpanded) {
            content.style.maxHeight = '0px';
            console.log(`   ✅ Collapsed phase ${phaseId}`);
        } else {
            content.style.maxHeight = '5000px'; // Large height for commands
            console.log(`   ✅ Expanded phase ${phaseId}`);
        }
    } else {
        console.error(`❌ Could not find element: complete-content-${phaseId}`);
    }
};

window.toggleCommandSection = function(commandId) {
    console.log(`🔄 Toggling command section: ${commandId}`);
    const content = document.getElementById(commandId);
    const toggleBtn = document.getElementById(`toggle-${commandId}`);
    
    if (content) {
        const isCollapsed = content.style.maxHeight === '0px' || content.style.maxHeight === '';
        
        if (isCollapsed) {
            content.style.maxHeight = '600px';
            if (toggleBtn) {
                toggleBtn.innerHTML = '⬆️ Hide Commands';
                toggleBtn.style.background = 'rgba(104, 211, 145, 0.2)';
            }
            console.log(`   ✅ Expanded command section ${commandId}`);
        } else {
            content.style.maxHeight = '0px';
            if (toggleBtn) {
                toggleBtn.innerHTML = '⬇️ Show Commands';
                toggleBtn.style.background = 'rgba(255,255,255,0.1)';
            }
            console.log(`   ✅ Collapsed command section ${commandId}`);
        }
    } else {
        console.error(`❌ Could not find command section: ${commandId}`);
    }
};

window.copyCompleteCommand = function(command) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(command).then(() => {
            console.log('📋 Command copied');
            showCopyNotification('All commands copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Copy failed:', err);
            showCopyNotification('Failed to copy commands', 'error');
        });
    }
};

window.copyStoredCommand = function(commandId, index, buttonElement) {
    const command = window.commandStore?.[commandId];
    if (command && navigator.clipboard) {
        navigator.clipboard.writeText(command).then(() => {
            console.log(`📋 Individual command ${index} copied`);
            showCopyNotification(`Command ${index} copied to clipboard!`, 'success');
            
            // Visual feedback on the button - only if it's a button element
            if (buttonElement && buttonElement.tagName === 'BUTTON') {
                const originalText = buttonElement.innerHTML;
                buttonElement.innerHTML = '✅ Copied!';
                buttonElement.style.background = 'rgba(72, 187, 120, 0.3)';
                setTimeout(() => {
                    buttonElement.innerHTML = originalText;
                    buttonElement.style.background = 'rgba(104, 211, 145, 0.2)';
                }, 2000);
            }
        }).catch(err => {
            console.error('Copy failed:', err);
            showCopyNotification('Failed to copy command', 'error');
        });
    }
};

window.copyCommandGroup = function(phaseId, groupIndex, buttonElement) {
    if (!window.completeImplementationData?.weeks) return;
    
    let commandGroup = null;
    window.completeImplementationData.weeks.forEach(week => {
        week.phases.forEach(phase => {
            if (phase.id === phaseId && phase.commands[groupIndex]) {
                commandGroup = phase.commands[groupIndex];
            }
        });
    });
    
    if (commandGroup?.commands && navigator.clipboard) {
        const commandText = commandGroup.commands.join('\n\n');
        navigator.clipboard.writeText(commandText).then(() => {
            console.log('📋 Command group copied');
            showCopyNotification('All commands copied to clipboard!', 'success');
            
            // Visual feedback on the button
            if (buttonElement && buttonElement.tagName === 'BUTTON') {
                const originalText = buttonElement.innerHTML;
                buttonElement.innerHTML = '✅ All Copied!';
                buttonElement.style.background = '#38a169';
                setTimeout(() => {
                    buttonElement.innerHTML = originalText;
                    buttonElement.style.background = '#48bb78';
                }, 2000);
            }
        }).catch(err => {
            console.error('Copy failed:', err);
            showCopyNotification('Failed to copy commands', 'error');
        });
    }
};

window.copyAllCompleteCommands = function() {
    if (window.completeImplementationData && window.completeImplementationData.weeks) {
        let allCommands = [];
        
        window.completeImplementationData.weeks.forEach(week => {
            week.phases.forEach(phase => {
                if (phase.commands && phase.commands.length > 0) {
                    phase.commands.forEach(commandGroup => {
                        allCommands.push(`# ${commandGroup.title || 'Commands'}`);
                        allCommands.push('');
                        allCommands = allCommands.concat(commandGroup.commands);
                        allCommands.push('');
                    });
                }
            });
        });
        
        const commandText = allCommands.join('\n');
        if (navigator.clipboard && commandText.trim()) {
            navigator.clipboard.writeText(commandText).then(() => {
                console.log('📋 All commands copied');
                showCopyNotification('All implementation commands copied to clipboard!');
            }).catch(err => console.error('Copy failed:', err));
        }
    }
};

window.expandAllCompleteSections = function() {
    document.querySelectorAll('[id^="complete-content-"]').forEach(content => {
        content.style.maxHeight = '5000px';
    });
    document.querySelectorAll('[id^="cmd-"]').forEach(content => {
        content.style.maxHeight = '600px';
    });
};

window.collapseAllCompleteSections = function() {
    document.querySelectorAll('[id^="complete-content-"]').forEach(content => {
        content.style.maxHeight = '0px';
    });
    document.querySelectorAll('[id^="cmd-"]').forEach(content => {
        content.style.maxHeight = '0px';
    });
};

window.refreshCompletePlan = function() {
    if (PLAN_DATA_CACHE) {
        // Trigger the same event as displayImplementationPlan
        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('implementationPlanDataReady', { 
                detail: { planData: PLAN_DATA_CACHE } 
            }));
        }
    } else {
        const savedData = sessionStorage.getItem('implementationPlanData');
        if (savedData) {
            try {
                const planData = JSON.parse(savedData);
                PLAN_DATA_CACHE = planData;
                // Trigger the event
                if (typeof window !== 'undefined') {
                    window.dispatchEvent(new CustomEvent('implementationPlanDataReady', { 
                        detail: { planData } 
                    }));
                }
            } catch (error) {
                // Use the global function
                if (window.loadImplementationPlan) {
                    window.loadImplementationPlan();
                }
            }
        } else {
            // Use the global function
            if (window.loadImplementationPlan) {
                window.loadImplementationPlan();
            }
        }
    }
};

window.exportCompletePlan = function() {
    const content = document.getElementById('implementation-plan-container');
    if (content) {
        const text = content.innerText;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `complete-implementation-plan-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
};

// FIXED Tab switching functionality - Simplified approach
window.switchFrameworkTab = function(tabId, buttonElement) {
    console.log('🔄 Switching to tab:', tabId);
    
    // Hide all tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.framework-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab panel
    const targetPanel = document.getElementById(`framework-tab-${tabId}`);
    if (targetPanel) {
        targetPanel.classList.add('active');
        console.log('✅ Activated tab panel:', `framework-tab-${tabId}`);
    } else {
        console.error('❌ Tab panel not found:', `framework-tab-${tabId}`);
    }
    
    // Add active class to clicked tab
    if (buttonElement) {
        buttonElement.classList.add('active');
        console.log('✅ Activated tab button');
    }
    
    // Scroll tab into view if needed
    if (buttonElement) {
        buttonElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
};

// NEW: Simplified function for "View Details" buttons
window.switchFrameworkTabById = function(tabId) {
    console.log('🔄 Switching to tab by ID:', tabId);
    
    // Hide all tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.framework-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab panel
    const targetPanel = document.getElementById(`framework-tab-${tabId}`);
    if (targetPanel) {
        targetPanel.classList.add('active');
        console.log('✅ Activated tab panel:', `framework-tab-${tabId}`);
    } else {
        console.error('❌ Tab panel not found:', `framework-tab-${tabId}`);
        return;
    }
    
    // Find and activate the corresponding tab button
    const targetButton = document.querySelector(`[data-tab="${tabId}"]`);
    if (targetButton) {
        targetButton.classList.add('active');
        console.log('✅ Activated tab button for:', tabId);
        
        // Scroll tab into view if needed
        targetButton.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    } else {
        console.error('❌ Tab button not found for:', tabId);
    }
};

// Placeholder functions for action buttons
window.deployOptimizations = function() {
    showCopyNotification('Deployment feature coming soon!');
};

window.scheduleOptimization = function() {
    showCopyNotification('Scheduling feature coming soon!');
};

// 🎉 BONUS FEATURES! 🎉

// Command Search
window.searchCommands = function(searchTerm) {
    const commandItems = document.querySelectorAll('.command-item');
    const term = searchTerm.toLowerCase();
    
    commandItems.forEach(item => {
        const searchText = item.getAttribute('data-search-text') || '';
        const commandText = item.querySelector('.command-text');
        
        if (term === '') {
            item.style.display = 'block';
            if (commandText) {
                commandText.innerHTML = commandText.innerHTML.replace(/<span class="search-highlight">(.*?)<\/span>/g, '$1');
            }
        } else if (searchText.includes(term)) {
            item.style.display = 'block';
            item.classList.add('animate-bounce');
            setTimeout(() => item.classList.remove('animate-bounce'), 1000);
            
            // Highlight matching text
            if (commandText) {
                let content = commandText.innerHTML;
                content = content.replace(/<span class="search-highlight">(.*?)<\/span>/g, '$1');
                const regex = new RegExp(`(${term})`, 'gi');
                content = content.replace(regex, '<span class="search-highlight">$1</span>');
                commandText.innerHTML = content;
            }
        } else {
            item.style.display = 'none';
        }
    });
    
    const visibleCount = Array.from(commandItems).filter(item => item.style.display !== 'none').length;
    if (term && visibleCount === 0) {
        showCopyNotification(`No commands found matching "${searchTerm}"`, 'error');
    } else if (term && visibleCount > 0) {
        showCopyNotification(`Found ${visibleCount} commands matching "${searchTerm}"`, 'success');
    }
};

// Command Validation
window.validateCommand = function(commandId) {
    const command = window.commandStore?.[commandId];
    if (!command) return;
    
    const validationDiv = document.getElementById(`validation-${commandId}`);
    if (!validationDiv) return;
    
    validationDiv.style.display = 'block';
    validationDiv.innerHTML = '🔍 Validating command...';
    validationDiv.className = 'command-validation';
    
    // Simulate validation logic
    setTimeout(() => {
        let result = { type: 'success', message: '✅ Command syntax looks good!' };
        
        // Basic validation checks
        if (command.includes('rm -rf /')) {
            result = { type: 'error', message: '⚠️ DANGER: This command could delete system files!' };
        } else if (command.includes('sudo') && !command.includes('kubectl')) {
            result = { type: 'warning', message: '⚠️ This command requires sudo privileges' };
        } else if (command.includes('--force') || command.includes('--yes')) {
            result = { type: 'warning', message: '⚠️ This command uses force flags - use with caution' };
        } else if (!command.includes('kubectl') && !command.includes('az') && !command.includes('echo')) {
            result = { type: 'warning', message: '💡 This doesn\'t appear to be a standard Kubernetes/Azure command' };
        }
        
        validationDiv.innerHTML = result.message;
        validationDiv.className = `command-validation validation-${result.type}`;
    }, 1000);
};

// Terminal Preview
window.previewCommand = function(commandId) {
    console.log('🖥️ Preview requested for commandId:', commandId);
    
    const command = window.commandStore?.[commandId];
    if (!command) {
        console.error('❌ Command not found in store for ID:', commandId);
        showCopyNotification('Command not found for preview', 'error');
        return;
    }
    
    console.log('✅ Found command for preview:', command.substring(0, 100) + '...');
    
    const modal = document.createElement('div');
    modal.className = 'terminal-preview';
    modal.innerHTML = `
        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-controls">
                    <div class="terminal-control control-close" onclick="this.closest('.terminal-preview').remove()"></div>
                    <div class="terminal-control control-minimize"></div>
                    <div class="terminal-control control-maximize"></div>
                </div>
                <span style="color: #e2e8f0; font-weight: 600; margin-left: 10px;">Terminal Preview - Command ${commandId}</span>
                <button onclick="this.closest('.terminal-preview').remove()" style="margin-left: auto; background: #dc3545; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;">✕ Close</button>
            </div>
            <div class="terminal-content">
                <div style="color: #68d391; margin-bottom: 10px;">$ # Command Preview</div>
                <div style="color: #87ceeb; margin-bottom: 15px;"># This is how your command will look in the terminal:</div>
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 6px; border-left: 4px solid #68d391;">
                    <pre style="margin: 0; white-space: pre-wrap; color: #e2e8f0; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 13px; line-height: 1.5;">${command.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
                </div>
                <div style="margin-top: 15px; padding: 10px; background: rgba(255, 193, 7, 0.1); border-radius: 6px; border-left: 4px solid #ffc107; color: #ffc107;">
                    💡 <strong>Preview Mode:</strong> This is a safe preview. No commands will be executed.
                </div>
                <div style="margin-top: 15px; padding: 10px; background: rgba(72, 187, 120, 0.1); border-radius: 6px; border-left: 4px solid #48bb78; color: #48bb78;">
                    📝 <strong>Command Length:</strong> ${command.length} characters | <strong>Lines:</strong> ${command.split('\n').length}
                </div>
                <div style="margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="copyStoredCommand('${commandId}', 1, this); showCopyNotification('Command copied from preview!', 'success');" style="background: #48bb78; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: 500;">
                        📋 Copy Command
                    </button>
                    <button onclick="validateCommandInPreview('${commandId}')" style="background: #17a2b8; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: 500;">
                        🔍 Validate Syntax
                    </button>
                    <button onclick="showCommandDetails('${commandId}')" style="background: #6f42c1; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: 500;">
                        📊 Command Details
                    </button>
                </div>
                <div id="preview-validation-${commandId}" style="margin-top: 15px;"></div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Close on Escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
    
    console.log('✅ Preview modal created successfully');
};

// Enhanced validation for preview
window.validateCommandInPreview = function(commandId) {
    const command = window.commandStore?.[commandId];
    if (!command) return;
    
    const validationDiv = document.getElementById(`preview-validation-${commandId}`);
    if (!validationDiv) return;
    
    validationDiv.innerHTML = '🔍 Analyzing command...';
    validationDiv.style.padding = '10px';
    validationDiv.style.borderRadius = '6px';
    validationDiv.style.marginTop = '10px';
    
    setTimeout(() => {
        let results = [];
        
        // Enhanced validation checks
        if (command.includes('rm -rf /')) {
            results.push({ type: 'error', message: '🚨 CRITICAL: This command could delete system files!' });
        }
        if (command.includes('sudo') && !command.includes('kubectl')) {
            results.push({ type: 'warning', message: '⚠️ Requires sudo privileges' });
        }
        if (command.includes('--force') || command.includes('--yes') || command.includes('-y')) {
            results.push({ type: 'warning', message: '⚠️ Uses force flags - proceed with caution' });
        }
        if (command.includes('kubectl delete') && !command.includes('--dry-run')) {
            results.push({ type: 'warning', message: '⚠️ Deletes Kubernetes resources - consider --dry-run first' });
        }
        if (command.match(/\$\{.*\}/)) {
            results.push({ type: 'info', message: '💡 Contains variables - ensure they are set before execution' });
        }
        if (command.includes('curl') && !command.includes('https://')) {
            results.push({ type: 'warning', message: '⚠️ HTTP request detected - verify endpoints are secure' });
        }
        
        if (results.length === 0) {
            results.push({ type: 'success', message: '✅ Command looks safe to execute!' });
        }
        
        validationDiv.innerHTML = results.map(result => {
            const bgColor = result.type === 'error' ? 'rgba(220, 53, 69, 0.1)' : 
                           result.type === 'warning' ? 'rgba(255, 193, 7, 0.1)' : 
                           result.type === 'success' ? 'rgba(72, 187, 120, 0.1)' : 
                           'rgba(23, 162, 184, 0.1)';
            const borderColor = result.type === 'error' ? '#dc3545' : 
                               result.type === 'warning' ? '#ffc107' : 
                               result.type === 'success' ? '#48bb78' : 
                               '#17a2b8';
            const textColor = result.type === 'error' ? '#dc3545' : 
                             result.type === 'warning' ? '#ffc107' : 
                             result.type === 'success' ? '#48bb78' : 
                             '#17a2b8';
            
            return `<div style="background: ${bgColor}; border-left: 4px solid ${borderColor}; color: ${textColor}; padding: 8px 12px; margin-bottom: 8px; border-radius: 4px; font-size: 14px;">${result.message}</div>`;
        }).join('');
    }, 800);
};

// Command details analyzer
window.showCommandDetails = function(commandId) {
    const command = window.commandStore?.[commandId];
    if (!command) return;
    
    const lines = command.split('\n');
    const words = command.split(/\s+/);
    const hasKubectl = command.includes('kubectl');
    const hasAz = command.includes('az');
    const hasEcho = command.includes('echo');
    const hasComments = command.includes('#');
    const hasPipes = command.includes('|');
    const hasRedirects = command.includes('>') || command.includes('>>');
    
    const details = `
        <div style="background: rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; color: #667eea; padding: 15px; border-radius: 6px;">
            <h4 style="margin: 0 0 10px 0;">📊 Command Analysis</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 13px;">
                <div><strong>Lines:</strong> ${lines.length}</div>
                <div><strong>Words:</strong> ${words.length}</div>
                <div><strong>Characters:</strong> ${command.length}</div>
                <div><strong>Type:</strong> ${hasKubectl ? 'Kubernetes' : hasAz ? 'Azure CLI' : hasEcho ? 'Shell Script' : 'Other'}</div>
            </div>
            <div style="margin-top: 10px; font-size: 13px;">
                <strong>Features:</strong> 
                ${hasComments ? '💬 Comments ' : ''}
                ${hasPipes ? '🔗 Pipes ' : ''}
                ${hasRedirects ? '📁 File Redirects ' : ''}
                ${hasKubectl ? '☸️ Kubernetes ' : ''}
                ${hasAz ? '☁️ Azure ' : ''}
            </div>
        </div>
    `;
    
    const validationDiv = document.getElementById(`preview-validation-${commandId}`);
    if (validationDiv) {
        validationDiv.innerHTML = details;
    }
};

// Progress Tracking
window.updateCommandProgress = function(commandHash, isCompleted) {
    if (!window.commandProgress) window.commandProgress = {};
    window.commandProgress[commandHash] = isCompleted;
    
    // Save to localStorage
    localStorage.setItem('commandProgress', JSON.stringify(window.commandProgress));
    
    const totalCommands = Object.keys(window.commandProgress).length;
    const completedCommands = Object.values(window.commandProgress).filter(Boolean).length;
    const progressPercent = totalCommands > 0 ? Math.round((completedCommands / totalCommands) * 100) : 0;
    
    if (isCompleted) {
        showCopyNotification(`✅ Command marked as completed! Progress: ${progressPercent}%`, 'success');
    }
};

window.showProgressTracker = function() {
    if (!window.commandProgress) {
        const saved = localStorage.getItem('commandProgress');
        window.commandProgress = saved ? JSON.parse(saved) : {};
    }
    
    const totalCommands = document.querySelectorAll('.command-item').length;
    const trackedCommands = Object.keys(window.commandProgress).length;
    const completedCommands = Object.values(window.commandProgress).filter(Boolean).length;
    const progressPercent = trackedCommands > 0 ? Math.round((completedCommands / trackedCommands) * 100) : 0;
    
    const modal = document.createElement('div');
    modal.className = 'progress-modal';
    modal.innerHTML = `
        <div class="progress-window">
            <div class="progress-header">
                <h3 style="margin: 0; font-size: 24px;">📊 Implementation Progress</h3>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Track your command execution progress</p>
            </div>
            <div class="progress-content">
                <div style="background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 12px; padding: 20px; color: white; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <span style="font-size: 18px; font-weight: 600;">Overall Progress</span>
                        <span style="font-size: 24px; font-weight: 700;">${progressPercent}%</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); border-radius: 10px; height: 12px; overflow: hidden;">
                        <div style="background: #48bb78; height: 100%; width: ${progressPercent}%; transition: all 0.5s ease;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 14px;">
                        <span>${completedCommands} completed</span>
                        <span>${totalCommands} total commands</span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div style="background: #f0fff4; border: 1px solid #48bb78; border-radius: 8px; padding: 15px; text-align: center;">
                        <div style="color: #48bb78; font-size: 24px; font-weight: bold;">${completedCommands}</div>
                        <div style="color: #22543d; font-size: 14px;">Completed</div>
                    </div>
                    <div style="background: #fff5f0; border: 1px solid #fd7e14; border-radius: 8px; padding: 15px; text-align: center;">
                        <div style="color: #fd7e14; font-size: 24px; font-weight: bold;">${trackedCommands - completedCommands}</div>
                        <div style="color: #9c4221; font-size: 14px;">Remaining</div>
                    </div>
                    <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; padding: 15px; text-align: center;">
                        <div style="color: #0ea5e9; font-size: 24px; font-weight: bold;">${totalCommands}</div>
                        <div style="color: #0c4a6e; font-size: 14px;">Total Commands</div>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button onclick="this.closest('.progress-modal').remove()" style="background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; margin-right: 10px;">
                        ✅ Close Progress
                    </button>
                    <button onclick="resetProgress()" style="background: #dc3545; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px;">
                        🔄 Reset Progress
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
};

window.resetProgress = function() {
    window.commandProgress = {};
    localStorage.removeItem('commandProgress');
    document.querySelectorAll('input[type="checkbox"][id^="progress-"]').forEach(cb => cb.checked = false);
    document.querySelector('.progress-modal')?.remove();
    showCopyNotification('🔄 Progress reset successfully!', 'success');
};

// Initialize theme on load
document.addEventListener('DOMContentLoaded', function() {
    // Load saved progress
    const savedProgress = localStorage.getItem('commandProgress');
    if (savedProgress) {
        window.commandProgress = JSON.parse(savedProgress);
        // Apply saved checkboxes
        setTimeout(() => {
            Object.entries(window.commandProgress).forEach(([hash, completed]) => {
                const checkbox = document.getElementById(`progress-${hash}`);
                if (checkbox) checkbox.checked = completed;
            });
        }, 1000);
    }
});

// Export functions
export function refreshImplementationPlan() {
    window.refreshCompletePlan();
}

export function expandAllSections() {
    window.expandAllCompleteSections();
}

export function collapseAllSections() {
    window.collapseAllCompleteSections();
}

export function exportImplementationPlan() {
    window.exportCompletePlan();
}

// Set plan data cache (for module interaction)
export function setPlanDataCache(data) {
    PLAN_DATA_CACHE = data;
    if (typeof window !== 'undefined') {
        window.completeImplementationData = data;
    }
}