"""
Utility Functions for AKS Cost Optimization Tool
"""

import statistics
from typing import Any
from config import logger

def convert_k8s_memory_to_bytes(mem_str):
    """Convert Kubernetes memory string (e.g., 2Gi, 100Mi, 1000Ki) to bytes"""
    if mem_str.endswith('Ki'):
        return float(mem_str[:-2]) * 1024
    elif mem_str.endswith('Mi'):
        return float(mem_str[:-2]) * 1024 * 1024
    elif mem_str.endswith('Gi'):
        return float(mem_str[:-2]) * 1024 * 1024 * 1024
    elif mem_str.endswith('Ti'):
        return float(mem_str[:-2]) * 1024 * 1024 * 1024 * 1024
    elif mem_str.endswith('k'):
        return float(mem_str[:-1]) * 1000
    elif mem_str.endswith('M'):
        return float(mem_str[:-1]) * 1000 * 1000
    elif mem_str.endswith('G'):
        return float(mem_str[:-1]) * 1000 * 1000 * 1000
    elif mem_str.endswith('T'):
        return float(mem_str[:-1]) * 1000 * 1000 * 1000 * 1000
    else:
        return float(mem_str)

def ensure_float(value: Any) -> float:
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_mean(values):
    """Calculate mean safely, handling empty lists"""
    try:
        return statistics.mean(values) if values else 0.0
    except (TypeError, ValueError):
        return 0.0

def validate_cost_data(cost_components):
    """Validate that cost components add up correctly"""
    try:
        component_sum = (
            cost_components.get('node_cost', 0) +
            cost_components.get('storage_cost', 0) +
            cost_components.get('networking_cost', 0) +
            cost_components.get('control_plane_cost', 0) +
            cost_components.get('registry_cost', 0) +
            cost_components.get('other_cost', 0)
        )
        
        total_cost = cost_components.get('total_cost', 0)
        
        # Allow for small rounding differences (1%)
        if abs(component_sum - total_cost) > (total_cost * 0.01):
            logger.warning(f"Cost validation warning: components sum ${component_sum:.2f} != total ${total_cost:.2f}")
            # Fix by adjusting the total to match components
            cost_components['total_cost'] = component_sum
            
        return cost_components
    except Exception as e:
        logger.error(f"Cost validation error: {e}")
        return cost_components

def format_currency(amount):
    """Format currency with appropriate precision"""
    if amount >= 1000:
        return f"${amount:,.0f}"
    else:
        return f"${amount:.2f}"

def time_ago(timestamp_str):
    """Convert timestamp to human-readable time ago"""
    if not timestamp_str:
        return 'Never'
    
    try:
        from datetime import datetime
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        diff = datetime.now() - timestamp.replace(tzinfo=None)
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        else:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
    except:
        return 'Unknown'

def environment_badge_class(environment):
    """Get CSS class for environment badge"""
    env_classes = {
        'production': 'bg-danger',
        'staging': 'bg-warning',
        'development': 'bg-info',
        'testing': 'bg-secondary'
    }
    return env_classes.get(environment.lower(), 'bg-secondary')

def status_indicator_class(cluster):
    """Get CSS class for cluster status indicator"""
    last_analyzed = cluster.get('last_analyzed')
    savings = cluster.get('last_savings', 0)
    
    if not last_analyzed:
        return 'error'
    elif savings > 100:
        return 'warning'
    else:
        return 'healthy'