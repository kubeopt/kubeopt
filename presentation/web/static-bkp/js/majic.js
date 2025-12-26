/**
 * 🪄 LIGHTWEIGHT DASHBOARD MAGIC
 * Subtle but powerful improvements that make everything feel premium
 */

// ========== 1. SMART SKELETON LOADING ========== 
function addSkeletonLoading() {
    const style = document.createElement('style');
    style.textContent = `
        .skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: 8px;
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        [data-theme="dark"] .skeleton {
            background: linear-gradient(90deg, #374151 25%, #4b5563 50%, #374151 75%);
            background-size: 200% 100%;
        }
    `;
    document.head.appendChild(style);
}

// ========== 2. STAGGERED CHART ANIMATIONS ========== 
function enhanceChartAnimations() {
    document.querySelectorAll('.chart-container').forEach((chart, index) => {
        chart.style.opacity = '0';
        chart.style.transform = 'translateY(20px)';
        chart.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        
        setTimeout(() => {
            chart.style.opacity = '1';
            chart.style.transform = 'translateY(0)';
        }, index * 100 + 200);
    });
}

// ========== 3. SMART AUTO-REFRESH INDICATOR ========== 
function addSmartRefreshIndicator() {
    const indicator = document.createElement('div');
    indicator.innerHTML = `
        <div class="refresh-indicator" style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(10px);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: #666;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        ">
            <i class="fas fa-sync-alt" style="margin-right: 6px; animation: spin 1s linear infinite;"></i>
            Auto-refreshing...
        </div>
    `;
    document.body.appendChild(indicator);
    
    // Show during chart updates
    const observer = new MutationObserver(() => {
        const refreshDiv = document.querySelector('.refresh-indicator');
        if (refreshDiv) {
            refreshDiv.style.opacity = '1';
            setTimeout(() => refreshDiv.style.opacity = '0', 2000);
        }
    });
    
    document.querySelectorAll('.chart-container').forEach(chart => {
        observer.observe(chart, { childList: true, subtree: true });
    });
}

// ========== 4. KEYBOARD SHORTCUTS ========== 
function addKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Alt + R = Refresh
        if (e.altKey && e.key === 'r') {
            e.preventDefault();
            if (typeof window.initializeCharts === 'function') {
                window.initializeCharts();
                showMiniToast('🔄 Charts refreshed');
            }
        }
        
        // Alt + D = Dashboard
        if (e.altKey && e.key === 'd') {
            e.preventDefault();
            showContent('dashboard', document.querySelector('[onclick*="dashboard"]'));
            showMiniToast('📊 Dashboard');
        }
        
        // Alt + I = Implementation
        if (e.altKey && e.key === 'i') {
            e.preventDefault();
            showContent('implementation', document.querySelector('[onclick*="implementation"]'));
            showMiniToast('🚀 Implementation');
        }
        
        // Alt + A = Alerts
        if (e.altKey && e.key === 'a') {
            e.preventDefault();
            showContent('alerts', document.querySelector('[onclick*="alerts"]'));
            showMiniToast('🔔 Alerts');
        }
        
        // ? = Show shortcuts
        if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            showShortcutsModal();
        }
    });
}

// ========== 5. MINI TOAST NOTIFICATIONS ========== 
function showMiniToast(message) {
    const toast = document.createElement('div');
    toast.innerHTML = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        z-index: 10000;
        transform: translateY(100px);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    setTimeout(() => toast.style.transform = 'translateY(0)', 100);
    setTimeout(() => {
        toast.style.transform = 'translateY(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// ========== 6. SHORTCUTS MODAL ========== 
function showShortcutsModal() {
    const modal = document.createElement('div');
    modal.innerHTML = `
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(5px);
        " onclick="this.remove()">
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.2);
                max-width: 400px;
                width: 90%;
            " onclick="event.stopPropagation()">
                <h3 style="margin: 0 0 1rem 0; color: #333;">⌨️ Keyboard Shortcuts</h3>
                <div style="font-size: 14px; line-height: 1.8;">
                    <div><kbd>Alt + R</kbd> Refresh charts</div>
                    <div><kbd>Alt + D</kbd> Dashboard tab</div>
                    <div><kbd>Alt + I</kbd> Implementation tab</div>
                    <div><kbd>Alt + A</kbd> Alerts tab</div>
                    <div><kbd>?</kbd> Show this help</div>
                    <div><kbd>Esc</kbd> Close modals</div>
                </div>
                <button onclick="this.closest('div').remove()" style="
                    margin-top: 1rem;
                    background: linear-gradient(135deg, #3b82f6, #2563eb);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                ">Got it!</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// ========== 7. SMART METRIC COUNTERS ========== 
function addCounterAnimations() {
    const animateValue = (element, start, end, duration) => {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                current = end;
                clearInterval(timer);
            }
            
            if (element.textContent.includes('$')) {
                element.textContent = '$' + Math.round(current).toLocaleString();
            } else if (element.textContent.includes('%')) {
                element.textContent = current.toFixed(1) + '%';
            } else {
                element.textContent = Math.round(current).toString();
            }
        }, 16);
    };
    
    // Observe metric value changes
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' || mutation.type === 'characterData') {
                const element = mutation.target.nodeType === 1 ? mutation.target : mutation.target.parentElement;
                if (element?.classList?.contains('metric-value')) {
                    const newValue = parseFloat(element.textContent.replace(/[^0-9.-]/g, ''));
                    if (!isNaN(newValue) && newValue > 0) {
                        animateValue(element, 0, newValue, 1000);
                    }
                }
            }
        });
    });
    
    document.querySelectorAll('.metric-value').forEach(metric => {
        observer.observe(metric, { childList: true, subtree: true, characterData: true });
    });
}

// ========== 8. PARALLAX SCROLL EFFECT ========== 
function addSubtleParallax() {
    let ticking = false;
    
    const updateParallax = () => {
        const scrolled = window.pageYOffset;
        const parallax = document.querySelectorAll('.metric-card, .chart-container');
        const speed = 0.2;
        
        parallax.forEach((element, index) => {
            const yPos = -(scrolled * speed * (index % 3 + 1) * 0.1);
            element.style.transform = `translateY(${yPos}px)`;
        });
        
        ticking = false;
    };
    
    const requestTick = () => {
        if (!ticking) {
            requestAnimationFrame(updateParallax);
            ticking = true;
        }
    };
    
    // Only on desktop to avoid performance issues
    if (window.innerWidth > 1024) {
        window.addEventListener('scroll', requestTick);
    }
}

// ========== 9. SMART COLOR ADAPTATION ========== 
function addSmartColors() {
    const updateColors = () => {
        const hour = new Date().getHours();
        const root = document.documentElement;
        
        if (hour >= 6 && hour < 12) {
            // Morning - energetic blues
            root.style.setProperty('--accent-hue', '210');
        } else if (hour >= 12 && hour < 18) {
            // Afternoon - warm oranges
            root.style.setProperty('--accent-hue', '25');
        } else {
            // Evening/Night - calm purples
            root.style.setProperty('--accent-hue', '270');
        }
    };
    
    const style = document.createElement('style');
    style.textContent = `
        :root {
            --accent-hue: 210;
        }
        
        .metric-card:hover {
            background: hsla(var(--accent-hue), 60%, 95%, 0.8) !important;
        }
        
        .btn-primary, .bg-blue-500 {
            background: linear-gradient(135deg, 
                hsl(var(--accent-hue), 70%, 55%), 
                hsl(var(--accent-hue), 70%, 45%)) !important;
        }
    `;
    document.head.appendChild(style);
    
    updateColors();
    setInterval(updateColors, 900000); // Update every 15 minutes
}

// ========== 10. PERFORMANCE MONITOR ========== 
function addPerformanceMonitor() {
    let frameCount = 0;
    let lastTime = performance.now();
    
    const monitor = document.createElement('div');
    monitor.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 20px;
        background: rgba(0,0,0,0.8);
        color: #0f0;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 11px;
        z-index: 10000;
        opacity: 0.7;
        pointer-events: none;
    `;
    document.body.appendChild(monitor);
    
    const updateFPS = () => {
        frameCount++;
        const now = performance.now();
        
        if (now >= lastTime + 1000) {
            const fps = Math.round((frameCount * 1000) / (now - lastTime));
            monitor.textContent = `${fps} FPS`;
            frameCount = 0;
            lastTime = now;
            
            // Change color based on performance
            if (fps >= 55) monitor.style.color = '#0f0';
            else if (fps >= 30) monitor.style.color = '#ff0';
            else monitor.style.color = '#f00';
        }
        
        requestAnimationFrame(updateFPS);
    };
    
    requestAnimationFrame(updateFPS);
}

// ========== INITIALIZE ALL MAGIC ========== 
function initializeLightweightMagic() {
    
    // Add CSS for kbd styling
    const style = document.createElement('style');
    style.textContent = `
        kbd {
            background: #f4f4f4;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 2px 6px;
            font-family: monospace;
            font-size: 12px;
            margin-right: 8px;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    // Initialize features
    setTimeout(() => {
        addSkeletonLoading();
        enhanceChartAnimations();
        addSmartRefreshIndicator();
        addKeyboardShortcuts();
        addCounterAnimations();
        addSubtleParallax();
        addSmartColors();
        
        // Optional: Performance monitor (remove in production)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            addPerformanceMonitor();
        }
        
        // Show shortcuts hint after 5 seconds
        setTimeout(() => {
            showMiniToast('💡 Press ? for keyboard shortcuts');
        }, 5000);
        
    }, 1000);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeLightweightMagic);
} else {
    initializeLightweightMagic();
}

// Make functions globally available
window.showMiniToast = showMiniToast;
window.showShortcutsModal = showShortcutsModal;