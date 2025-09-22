#!/usr/bin/env python3
"""
CPU Optimization Configuration Examples
=======================================
Organizations can customize these configurations based on their specific needs,
risk tolerance, and operational requirements.
"""

# Example configurations for different organization types

CONSERVATIVE_ENTERPRISE_CONFIG = {
    """Configuration for conservative enterprises with strict change control"""
    
    # Lower thresholds - trigger optimization earlier
    'critical_cpu_threshold': 150,          # Emergency response at 150% CPU
    'high_cpu_threshold': 70,               # High usage optimization at 70% CPU
    'target_cpu_utilization': 60,           # Target 60% CPU utilization
    'low_efficiency_threshold': 60,         # Efficiency optimization at 60%
    'target_efficiency': 85,                # Target 85% efficiency
    'peak_critical_threshold': 250,         # Peak CPU critical at 250%
    'peak_high_threshold': 120,             # Peak CPU high at 120%
    
    # Organization settings
    'organization_name': 'Enterprise Corporation',
    'cloud_provider': 'azure',              # Specific cloud provider
    'cluster_naming_pattern': 'enterprise', # Custom naming pattern
    
    # Conservative safety settings
    'enable_emergency_actions': False,       # Disable high-risk actions
    'require_manual_confirmation': True,     # Require manual approval
    'max_replica_scale': 8,                 # Conservative scaling limits
    
    # Conservative resource limits
    'default_cpu_request': '50m',           # Lower default requests
    'default_cpu_limit': '500m',            # Lower default limits
    'default_memory_request': '64Mi',       # Lower memory requests
    'default_memory_limit': '1Gi',          # Lower memory limits
    
    # Cost calculation - conservative estimates
    'cost_efficiency_factor': 0.3,          # Conservative savings estimates
    
    # Longer monitoring intervals for stability
    'monitoring_interval_seconds': 60,      # Monitor every minute
    'validation_timeout_minutes': 15,       # Longer validation timeouts
}

AGGRESSIVE_STARTUP_CONFIG = {
    """Configuration for fast-growing startups with high risk tolerance"""
    
    # Higher thresholds - maximize resource utilization
    'critical_cpu_threshold': 300,          # Emergency response at 300% CPU
    'high_cpu_threshold': 90,               # High usage optimization at 90% CPU
    'target_cpu_utilization': 80,           # Target 80% CPU utilization
    'low_efficiency_threshold': 40,         # Lower efficiency threshold
    'target_efficiency': 75,                # Lower target efficiency
    'peak_critical_threshold': 500,         # Peak CPU critical at 500%
    'peak_high_threshold': 200,             # Peak CPU high at 200%
    
    # Organization settings
    'organization_name': 'Growth Startup Inc.',
    'cloud_provider': 'multi',              # Multi-cloud templates
    'cluster_naming_pattern': 'startup',    # Startup naming pattern
    
    # Aggressive safety settings
    'enable_emergency_actions': True,       # Enable all actions
    'require_manual_confirmation': False,   # Auto-execute optimizations
    'max_replica_scale': 50,               # Aggressive scaling limits
    
    # Aggressive resource limits
    'default_cpu_request': '200m',         # Higher default requests
    'default_cpu_limit': '2000m',          # Higher default limits
    'default_memory_request': '256Mi',     # Higher memory requests
    'default_memory_limit': '4Gi',         # Higher memory limits
    
    # Cost calculation - aggressive savings
    'cost_efficiency_factor': 0.5,         # Optimistic savings estimates
    
    # Faster monitoring for rapid response
    'monitoring_interval_seconds': 15,     # Monitor every 15 seconds
    'validation_timeout_minutes': 5,       # Shorter validation timeouts
}

COST_OPTIMIZED_CONFIG = {
    """Configuration for cost-conscious organizations"""
    
    # Balanced thresholds optimized for cost efficiency
    'critical_cpu_threshold': 180,          # Emergency response at 180% CPU
    'high_cpu_threshold': 75,               # High usage optimization at 75% CPU
    'target_cpu_utilization': 70,           # Target 70% CPU utilization
    'low_efficiency_threshold': 55,         # Efficiency optimization at 55%
    'target_efficiency': 80,                # Target 80% efficiency
    'peak_critical_threshold': 350,         # Peak CPU critical at 350%
    'peak_high_threshold': 150,             # Peak CPU high at 150%
    
    # Organization settings
    'organization_name': 'Cost-Conscious Business',
    'cloud_provider': 'gcp',               # Cost-optimized cloud
    'cluster_naming_pattern': 'cost-opt',  # Cost optimization focus
    
    # Balanced safety settings
    'enable_emergency_actions': True,       # Enable necessary actions
    'require_manual_confirmation': True,    # Review high-cost changes
    'max_replica_scale': 20,               # Reasonable scaling limits
    
    # Cost-optimized resource limits
    'default_cpu_request': '100m',         # Balanced requests
    'default_cpu_limit': '1000m',          # Balanced limits
    'default_memory_request': '128Mi',     # Balanced memory requests
    'default_memory_limit': '2Gi',         # Balanced memory limits
    
    # Cost calculation - focus on savings
    'cost_per_cpu_hour': 0.04,            # Lower cost assumptions
    'cost_efficiency_factor': 0.6,        # Optimistic cost savings
    
    # Standard monitoring
    'monitoring_interval_seconds': 30,     # Monitor every 30 seconds
    'validation_timeout_minutes': 10,      # Standard validation timeouts
}

DEVOPS_FRIENDLY_CONFIG = {
    """Configuration for DevOps-focused organizations with automation"""
    
    # DevOps-optimized thresholds
    'critical_cpu_threshold': 200,          # Standard emergency threshold
    'high_cpu_threshold': 80,               # Standard high usage threshold
    'target_cpu_utilization': 70,           # Balanced target utilization
    'low_efficiency_threshold': 50,         # Standard efficiency threshold
    'target_efficiency': 80,                # Standard target efficiency
    'peak_critical_threshold': 400,         # Standard peak critical
    'peak_high_threshold': 150,             # Standard peak high
    
    # Organization settings
    'organization_name': 'DevOps-First Organization',
    'cloud_provider': 'multi',              # Multi-cloud support
    'cluster_naming_pattern': 'auto',       # Auto-detect naming
    
    # DevOps-friendly safety settings
    'enable_emergency_actions': True,       # Enable automation
    'require_manual_confirmation': False,   # Automated execution
    'max_replica_scale': 30,               # DevOps-friendly scaling
    
    # Automation-friendly resource limits
    'default_cpu_request': '100m',         # Standard requests
    'default_cpu_limit': '1500m',          # Generous limits for automation
    'default_memory_request': '128Mi',     # Standard memory requests
    'default_memory_limit': '3Gi',         # Generous memory limits
    
    # Cost calculation
    'cost_efficiency_factor': 0.4,         # Realistic savings estimates
    
    # DevOps monitoring - frequent but not overwhelming
    'monitoring_interval_seconds': 30,     # Every 30 seconds
    'validation_timeout_minutes': 8,       # Quick validation
    
    # Custom DevOps commands
    'custom_monitoring_commands': [
        'kubectl get hpa --all-namespaces -o wide',
        'kubectl get vpa --all-namespaces -o wide || echo "VPA not installed"',
        'kubectl top nodes --sort-by=cpu',
        'kubectl top pods --all-namespaces --sort-by=cpu | head -20'
    ],
    
    'custom_validation_steps': [
        'Verify all critical deployments are healthy',
        'Check that monitoring dashboards show expected improvements',
        'Validate that CI/CD pipelines are not affected',
        'Confirm that application performance metrics are stable'
    ]
}

DEFAULT_CONFIG = {
    """Default configuration for general use"""
    
    # Standard thresholds
    'critical_cpu_threshold': 200,          # Emergency response at 200% CPU
    'high_cpu_threshold': 80,               # High usage optimization at 80% CPU
    'target_cpu_utilization': 70,           # Target 70% CPU utilization
    'low_efficiency_threshold': 50,         # Efficiency optimization at 50%
    'target_efficiency': 80,                # Target 80% efficiency
    'peak_critical_threshold': 400,         # Peak CPU critical at 400%
    'peak_high_threshold': 150,             # Peak CPU high at 150%
    
    # Generic organization settings
    'organization_name': 'Your Organization',
    'cloud_provider': 'multi',              # Generic templates
    'cluster_naming_pattern': 'auto',       # Auto-detect
    
    # Balanced safety settings
    'enable_emergency_actions': True,       # Enable necessary actions
    'require_manual_confirmation': True,    # Require confirmation
    'max_replica_scale': 20,               # Reasonable scaling
    
    # Standard resource limits
    'default_cpu_request': '100m',
    'default_cpu_limit': '1000m',
    'default_memory_request': '128Mi',
    'default_memory_limit': '2Gi',
    
    # Standard cost calculation
    'cost_per_cpu_hour': 0.05,
    'cost_efficiency_factor': 0.4,
    
    # Standard monitoring
    'monitoring_interval_seconds': 30,
    'validation_timeout_minutes': 10,
}

def get_config_by_profile(profile_name: str) -> dict:
    """Get configuration by profile name"""
    profiles = {
        'conservative': CONSERVATIVE_ENTERPRISE_CONFIG,
        'aggressive': AGGRESSIVE_STARTUP_CONFIG,
        'cost-optimized': COST_OPTIMIZED_CONFIG,
        'devops': DEVOPS_FRIENDLY_CONFIG,
        'default': DEFAULT_CONFIG
    }
    
    return profiles.get(profile_name.lower(), DEFAULT_CONFIG)

def list_available_profiles() -> list:
    """List all available configuration profiles"""
    return [
        'conservative',    # Conservative Enterprise
        'aggressive',      # Aggressive Startup
        'cost-optimized',  # Cost-Optimized
        'devops',         # DevOps-Friendly
        'default'         # Default Configuration
    ]

# Example usage:
# config = get_config_by_profile('conservative')
# planner = create_cpu_optimization_planner(config)