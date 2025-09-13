from typing import Dict, List
from ..models.core import ExecutableCommand

class AKSMaintenanceCommandGenerator:
    """Generator for AKS maintenance commands"""
    
    def extract_maintenance_data(self, analysis_results: Dict, cluster_dna, optimization_strategy) -> Dict:
        """Extract data for AKS maintenance optimizations"""
        maintenance_data = {
            'kubernetes_version': 'unknown',
            'node_image_version': 'unknown',
            'auto_upgrade_enabled': False,
            'maintenance_window_configured': False,
            'planned_maintenance_events': []
        }
        
        # Extract from cluster DNA
        if hasattr(cluster_dna, 'cluster_version'):
            maintenance_data['kubernetes_version'] = cluster_dna.cluster_version
        
        # Extract from analysis results
        if 'cluster_info' in analysis_results:
            cluster_info = analysis_results['cluster_info']
            maintenance_data['kubernetes_version'] = cluster_info.get('kubernetes_version', 'unknown')
            maintenance_data['auto_upgrade_enabled'] = cluster_info.get('auto_upgrade_enabled', False)
        
        return maintenance_data

    def generate_commands(self, maintenance_data: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate AKS maintenance commands"""
        commands = []
        
        # Enable auto-upgrade
        if not maintenance_data['auto_upgrade_enabled']:
            commands.append(ExecutableCommand(
                command=f"az aks update --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']} --enable-auto-upgrade --auto-upgrade-channel stable",
                description="Enable automatic cluster upgrades for better security and performance",
                category="aks_maintenance",
                priority_score=75,
                savings_estimate=0
            ))
        
        # Configure maintenance window
        if not maintenance_data['maintenance_window_configured']:
            commands.append(ExecutableCommand(
                command=f"az aks maintenanceconfiguration add --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --config-name default --weekday Saturday --start-hour 2",
                description="Configure maintenance window to minimize business impact",
                category="aks_maintenance",
                priority_score=65,
                savings_estimate=0
            ))
        
        # Cluster version check
        commands.append(ExecutableCommand(
            command=f"az aks get-upgrades --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']}",
            description="Check available Kubernetes version upgrades",
            category="aks_maintenance",
            priority_score=50,
            savings_estimate=0
        ))
        
        return commands