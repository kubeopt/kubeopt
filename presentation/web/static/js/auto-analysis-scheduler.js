/*!
 * Auto-Analysis Scheduler JavaScript
 * Handles automatic analysis scheduling UI and controls
 */

class AutoAnalysisScheduler {
    constructor() {
        this.statusCheckInterval = null;
        this.isInitialized = false;
    }

    init() {
        if (this.isInitialized) return;
        
        console.log('🕐 Initializing Auto-Analysis Scheduler UI');
        this.addSchedulerStatusToUI();
        this.startStatusChecking();
        this.isInitialized = true;
    }

    addSchedulerStatusToUI() {
        // Find the analyze button and add scheduler status next to it
        const analyzeButton = document.querySelector('button[onclick*="triggerAnalysis"]');
        if (!analyzeButton) return;

        // Create scheduler status element as a small indicator
        const schedulerElement = document.createElement('div');
        schedulerElement.className = 'scheduler-status flex items-center gap-1 ml-2';
        schedulerElement.innerHTML = `
            <div class="scheduler-indicator">
                <span id="scheduler-status-badge" class="flex items-center gap-1 px-2 py-1 rounded text-xs bg-gray-100 text-gray-600 cursor-pointer transition-colors hover:bg-gray-200">
                    <div id="scheduler-status-dot" class="w-2 h-2 bg-gray-400 rounded-full"></div>
                    <span id="scheduler-status-text">Manual</span>
                </span>
            </div>
        `;

        // Insert right after the analyze button
        analyzeButton.parentNode.insertBefore(schedulerElement, analyzeButton.nextSibling);

        // Add event listeners
        this.attachEventListeners();
    }

    attachEventListeners() {
        const statusBadge = document.getElementById('scheduler-status-badge');

        if (statusBadge) {
            statusBadge.addEventListener('click', () => this.showSchedulerDetails());
        }
    }

    async getSchedulerStatus() {
        try {
            const response = await fetch('/api/scheduler/status');
            const data = await response.json();
            
            if (data.status === 'success') {
                return data.scheduler;
            } else {
                console.error('Failed to get scheduler status:', data.message);
                return null;
            }
        } catch (error) {
            console.error('Error fetching scheduler status:', error);
            return null;
        }
    }

    async updateSchedulerUI(status) {
        const statusText = document.getElementById('scheduler-status-text');
        const statusBadge = document.getElementById('scheduler-status-badge');
        const statusDot = document.getElementById('scheduler-status-dot');

        if (!statusText || !statusBadge || !statusDot) return;

        if (status) {
            const isRunning = status.is_running;
            const isEnabled = status.is_enabled;
            const interval = status.interval_hours;
            const nextRun = status.next_analysis_time;

            // Update status text, dot color, and tooltip
            if (isEnabled && isRunning) {
                statusText.textContent = `Auto (${interval}h)`;
                statusDot.className = 'w-2 h-2 bg-green-400 rounded-full';
                statusBadge.className = 'flex items-center gap-1 px-2 py-1 rounded text-xs bg-green-50 text-green-700 cursor-pointer transition-colors hover:bg-green-100';
                statusBadge.title = `✅ Auto-analysis active\nNext run: ${new Date(nextRun).toLocaleString()}`;
            } else if (isEnabled && !isRunning) {
                statusText.textContent = 'Auto (Paused)';
                statusDot.className = 'w-2 h-2 bg-yellow-400 rounded-full';
                statusBadge.className = 'flex items-center gap-1 px-2 py-1 rounded text-xs bg-yellow-50 text-yellow-700 cursor-pointer transition-colors hover:bg-yellow-100';
                statusBadge.title = '⏸️ Auto-analysis paused\nClick to view details';
            } else {
                statusText.textContent = 'Manual';
                statusDot.className = 'w-2 h-2 bg-gray-400 rounded-full';
                statusBadge.className = 'flex items-center gap-1 px-2 py-1 rounded text-xs bg-gray-100 text-gray-600 cursor-pointer transition-colors hover:bg-gray-200';
                statusBadge.title = '🔧 Manual analysis only\nClick to configure auto-analysis';
            }
        } else {
            statusText.textContent = 'Error';
            statusDot.className = 'w-2 h-2 bg-red-400 rounded-full';
            statusBadge.className = 'flex items-center gap-1 px-2 py-1 rounded text-xs bg-red-50 text-red-700 cursor-pointer';
            statusBadge.title = '❌ Failed to get scheduler status';
        }
    }

    async toggleScheduler() {
        try {
            const currentStatus = await this.getSchedulerStatus();
            if (!currentStatus) return;

            const isRunning = currentStatus.is_running;
            const endpoint = isRunning ? '/api/scheduler/stop' : '/api/scheduler/start';
            const action = isRunning ? 'stop' : 'start';

            const toggleBtn = document.getElementById('scheduler-toggle-btn');
            if (toggleBtn) {
                toggleBtn.disabled = true;
                toggleBtn.textContent = isRunning ? 'Stopping...' : 'Starting...';
            }

            const response = await fetch(endpoint, { method: 'POST' });
            const data = await response.json();

            if (data.status === 'success') {
                this.showNotification(`Scheduler ${action}ed successfully`, 'success');
                // Refresh status immediately
                await this.checkAndUpdateStatus();
            } else {
                this.showNotification(`Failed to ${action} scheduler: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error toggling scheduler:', error);
            this.showNotification(`Error toggling scheduler: ${error.message}`, 'error');
        }
    }

    showSchedulerDetails() {
        this.getSchedulerStatus().then(status => {
            if (!status) return;

            const getStatusIcon = (enabled, running) => {
                if (enabled && running) return '<i class="fas fa-play-circle text-green-500"></i>';
                if (enabled && !running) return '<i class="fas fa-pause-circle text-yellow-500"></i>';
                return '<i class="fas fa-stop-circle text-gray-500"></i>';
            };

            const formatTime = (timeString) => {
                if (!timeString || timeString === 'Soon') return 'Soon';
                return new Date(timeString).toLocaleString('en-US', {
                    weekday: 'short',
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            };

            const details = `
                <div class="scheduler-details">
                    <div class="mb-4 p-3 rounded border ${status.is_enabled && status.is_running ? 'bg-green-50 border-green-200' : status.is_enabled ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'}">
                        <div class="flex items-center gap-2 mb-2">
                            ${getStatusIcon(status.is_enabled, status.is_running)}
                            <span class="font-medium">
                                ${status.is_enabled && status.is_running ? 'Active' : status.is_enabled ? 'Paused' : 'Disabled'}
                            </span>
                        </div>
                        <p class="text-sm text-gray-600">
                            ${status.is_enabled && status.is_running ? 'Running every ' + status.interval_hours + ' hours' : 
                              status.is_enabled ? 'Enabled but currently paused' : 
                              'Manual mode only'}
                        </p>
                    </div>

                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Status:</span>
                            <span class="font-medium ${status.is_enabled ? 'text-green-600' : 'text-gray-500'}">
                                ${status.is_enabled ? 'Enabled' : 'Disabled'}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Scheduler:</span>
                            <span class="font-medium ${status.is_running ? 'text-green-600' : 'text-yellow-600'}">
                                ${status.is_running ? 'Running' : 'Stopped'}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Interval:</span>
                            <span class="font-medium">Every ${status.interval_hours}h</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Last Run:</span>
                            <span class="font-medium">${status.last_analysis_time ? formatTime(status.last_analysis_time) : 'Never'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Next Run:</span>
                            <span class="font-medium">${formatTime(status.next_analysis_time)}</span>
                        </div>
                    </div>

                    <div class="mt-4 flex gap-2">
                        ${status.is_enabled && status.is_running ? 
                            '<button onclick="window.autoAnalysisScheduler.toggleScheduler(); this.closest(\'.fixed\').remove();" class="flex-1 px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors text-sm">Pause</button>' :
                            '<button onclick="window.autoAnalysisScheduler.toggleScheduler(); this.closest(\'.fixed\').remove();" class="flex-1 px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors text-sm">Start</button>'
                        }
                        <button onclick="window.autoAnalysisScheduler.forceAnalysisFromModal(); this.closest('.fixed').remove();" class="flex-1 px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm">
                            Run Now
                        </button>
                    </div>

                    <div class="mt-3 text-xs text-gray-500">
                        Configure in <a href="/settings" class="text-blue-600 hover:text-blue-800 hover:underline">Settings → General Settings</a>
                    </div>
                </div>
            `;

            this.showModal('Auto-Analysis Scheduler', details);
        });
    }

    async forceAnalysisFromModal() {
        try {
            const response = await fetch('/api/scheduler/force-analysis', { method: 'POST' });
            const data = await response.json();

            if (data.status === 'success') {
                this.showNotification('Analysis started immediately!', 'success');
            } else {
                this.showNotification(`Failed to start analysis: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error forcing analysis:', error);
            this.showNotification(`Error starting analysis: ${error.message}`, 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (window.showNotification) {
            window.showNotification('Scheduler', message, type);
        } else {
            // Fallback notification
            console.log(`[${type.toUpperCase()}] ${message}`);
            alert(message);
        }
    }

    showModal(title, content) {
        // Simple modal matching existing theme
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg w-full max-w-md mx-auto">
                <div class="flex items-center justify-between p-4 border-b">
                    <h3 class="text-lg font-semibold text-gray-800 flex items-center">
                        <i class="fas fa-clock text-gray-600 mr-2"></i>
                        ${title}
                    </h3>
                    <button class="text-gray-400 hover:text-gray-600 transition-colors" onclick="this.closest('.fixed').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-6">
                    ${content}
                </div>
                <div class="p-4 border-t flex justify-end">
                    <button class="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors" onclick="this.closest('.fixed').remove()">
                        Close
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Simple click outside to close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    async checkAndUpdateStatus() {
        const status = await this.getSchedulerStatus();
        await this.updateSchedulerUI(status);
    }

    startStatusChecking() {
        // Initial status check
        this.checkAndUpdateStatus();

        // Check status every 30 seconds
        this.statusCheckInterval = setInterval(() => {
            this.checkAndUpdateStatus();
        }, 30000);
    }

    stopStatusChecking() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    destroy() {
        this.stopStatusChecking();
        this.isInitialized = false;
    }
}

// Global instance
window.autoAnalysisScheduler = new AutoAnalysisScheduler();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for other UI elements to load
    setTimeout(() => {
        if (window.autoAnalysisScheduler) {
            window.autoAnalysisScheduler.init();
        }
    }, 1000);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutoAnalysisScheduler;
}