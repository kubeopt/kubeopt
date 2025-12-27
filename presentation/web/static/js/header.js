/**
 * Header JavaScript
 * Handles header functionality including user dropdown and cluster switcher
 */

// User Dropdown Management
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    const dropdownMenu = document.getElementById('userDropdownMenu');
    const trigger = dropdown?.querySelector('.user-dropdown-trigger');
    
    const isOpen = dropdown?.classList.contains('open');
    
    if (isOpen) {
        dropdown.classList.remove('open');
        if (dropdownMenu) dropdownMenu.style.display = 'none';
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
    } else {
        dropdown?.classList.add('open');
        if (dropdownMenu) dropdownMenu.style.display = 'block';
        if (trigger) trigger.setAttribute('aria-expanded', 'true');
    }
}

// Close dropdown when clicking outside
function closeUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    const dropdownMenu = document.getElementById('userDropdownMenu');
    const trigger = dropdown?.querySelector('.user-dropdown-trigger');
    
    if (dropdown && dropdown.classList.contains('open')) {
        dropdown.classList.remove('open');
        if (dropdownMenu) dropdownMenu.style.display = 'none';
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
    }
}

// Cluster Switcher Class
class ClusterSwitcher {
    constructor() {
        this.clusters = [];
        this.currentCluster = null;
        this.switcherSection = null;
        this.switcherSelect = null;
        this.currentClusterDisplay = null;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.onDOMContentLoaded();
        });
    }

    onDOMContentLoaded() {
        this.switcherSection = document.getElementById('cluster-switcher-section');
        this.currentClusterBadge = document.getElementById('current-cluster-badge');
        this.currentClusterNameEl = document.getElementById('current-cluster-name');
        
        this.detectCurrentCluster();
    }


    // Ensure cluster list element is available before trying to use it
    ensureClusterListElement() {
        if (!this.clusterList) {
            this.clusterList = document.getElementById('cluster-list');
        }
        return !!this.clusterList;
    }

    // Detect current cluster from URL or window object
    detectCurrentCluster() {
        // Method 1: From URL pattern /cluster/{cluster_id}
        const urlPath = window.location.pathname;
        const clusterMatch = urlPath.match(/\/cluster\/([^\/]+)/);
        
        if (clusterMatch) {
            this.currentCluster = clusterMatch[1];
            return;
        }

        // Method 2: From global window objects
        if (window.clusterInfo && window.clusterInfo.id) {
            this.currentCluster = window.clusterInfo.id;
            return;
        }

        if (window.AppState && window.AppState.currentClusterId) {
            this.currentCluster = window.AppState.currentClusterId;
            return;
        }
    }

    // Load available clusters from API
    async loadClusters() {
        try {
            const response = await fetch('/api/clusters/dropdown');
            const data = await response.json();
            
            if (data.status === 'success' && data.clusters) {
                this.clusters = data.clusters;
                this.populateDropdown();
                this.updateVisibility();
            } else {
                this.loadClustersFromPortfolio();
            }
        } catch (error) {
            console.error('Error loading clusters:', error);
            this.loadClustersFromPortfolio();
        }
    }

    // Fallback: Load clusters from portfolio endpoint
    async loadClustersFromPortfolio() {
        try {
            const response = await fetch('/api/portfolio/summary');
            const data = await response.json();
            
            if (data.status === 'success' && data.clusters) {
                this.clusters = data.clusters.map(cluster => ({
                    id: cluster.id,
                    name: cluster.name,
                    environment: cluster.environment,
                    region: cluster.region
                }));
                this.populateDropdown();
                this.updateVisibility();
            } else {
                this.showNoClustersMessage();
            }
        } catch (error) {
            console.error('Error loading clusters from fallback:', error);
            this.showNoClustersMessage();
        }
    }

    // Show message when no clusters can be loaded
    showNoClustersMessage() {
        if (this.clusterList) {
            this.clusterList.innerHTML = `
                <div class="no-clusters">
                    <i class="fas fa-exclamation-circle"></i>
                    Failed to load clusters
                </div>
            `;
        }
    }

    // Populate the submenu with clusters
    populateDropdown() {
        // Ensure we have the cluster list element
        if (!this.ensureClusterListElement()) {
            return;
        }

        if (!this.clusters.length) {
            this.clusterList.innerHTML = `
                <div class="no-clusters" style="padding: 0.5rem 1rem; color: var(--text-secondary);">
                    <i class="fas fa-info-circle"></i>
                    No clusters available
                </div>
            `;
            return;
        }

        // Create cluster items
        let clusterItemsHTML = '';
        this.clusters.forEach(cluster => {
            const isCurrentCluster = cluster.id === this.currentCluster;
            const iconClass = isCurrentCluster ? 'fas fa-check-circle' : 'fas fa-circle';
            
            clusterItemsHTML += `
                <a href="/cluster/${cluster.id}" class="dropdown-item" style="padding: 0.5rem 1rem; font-size: 0.875rem;">
                    <i class="${iconClass}" style="font-size: 0.75rem; width: 16px;"></i>
                    <span>${cluster.name}</span>
                    ${isCurrentCluster ? '<span style="margin-left: auto; font-size: 0.75rem; color: var(--primary-green);">current</span>' : ''}
                </a>
            `;
        });

        this.clusterList.innerHTML = clusterItemsHTML;
        this.updateCurrentClusterDisplay();
    }

    // Get cluster details for display
    getClusterDetails(cluster) {
        const details = [];
        if (cluster.environment) details.push(cluster.environment);
        if (cluster.region) details.push(cluster.region);
        return details.length > 0 ? details.join(' • ') : 'No details';
    }

    // Update current cluster display
    updateCurrentClusterDisplay() {
        if (!this.currentCluster || !this.currentClusterBadge || !this.currentClusterNameEl) return;

        const currentClusterObj = this.clusters.find(c => c.id === this.currentCluster);
        
        if (currentClusterObj) {
            this.currentClusterNameEl.textContent = `Current: ${currentClusterObj.name}`;
            this.currentClusterBadge.style.display = 'block';
        } else {
            this.currentClusterBadge.style.display = 'none';
        }
    }

    // Update visibility of cluster switcher section
    updateVisibility() {
        // Cluster switcher menu item is always visible - it's a permanent part of the dropdown
        if (this.switcherSection) {
            this.switcherSection.style.display = 'block';
        }
    }

    // Switch to selected cluster
    switchCluster(clusterId) {
        if (!clusterId) return;
        window.location.href = `/cluster/${clusterId}`;
    }

    // Refresh cluster list
    async refreshClusters() {
        await this.loadClusters();
    }

    // Add new cluster to list (for use after cluster creation)
    addCluster(cluster) {
        if (!this.clusters.some(c => c.id === cluster.id)) {
            this.clusters.push(cluster);
            this.populateDropdown();
            this.updateVisibility();
        }
    }

    // Remove cluster from list (for use after cluster deletion)
    removeCluster(clusterId) {
        this.clusters = this.clusters.filter(c => c.id !== clusterId);
        this.populateDropdown();
        this.updateVisibility();
    }
}

// Initialize cluster switcher
let clusterSwitcher = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize cluster switcher after a small delay to ensure DOM is ready
    setTimeout(() => {
        clusterSwitcher = new ClusterSwitcher();
        
        // Setup simple expand/collapse for clusters
        const clusterToggle = document.getElementById('cluster-toggle');
        const clusterListContainer = document.getElementById('cluster-list-container');
        const clusterArrow = document.getElementById('cluster-arrow');
        
        if (clusterToggle && clusterListContainer) {
            clusterToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Toggle visibility
                const isHidden = clusterListContainer.style.display === 'none';
                clusterListContainer.style.display = isHidden ? 'block' : 'none';
                
                // Toggle arrow icon
                if (clusterArrow) {
                    clusterArrow.className = isHidden ? 'fas fa-chevron-up item-arrow' : 'fas fa-chevron-down item-arrow';
                }
                
                // Load clusters if needed and now visible
                if (isHidden && clusterSwitcher) {
                    if (clusterSwitcher.clusters.length === 0) {
                        clusterSwitcher.ensureClusterListElement();
                        clusterSwitcher.loadClusters();
                    }
                }
            });
        }
    }, 100);
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const dropdown = document.getElementById('userDropdown');
        if (dropdown && !dropdown.contains(e.target)) {
            closeUserDropdown();
        }
    });
    
    // Prevent dropdown from closing when clicking inside
    const userDropdownMenu = document.getElementById('userDropdownMenu');
    if (userDropdownMenu) {
        userDropdownMenu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
});

// Global function for template onclick handlers
function switchCluster(clusterId) {
    clusterSwitcher?.switchCluster(clusterId);
}

// Make cluster switcher globally available
window.clusterSwitcher = clusterSwitcher;