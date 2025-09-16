from typing import Dict, List
from ..models.core import ExecutableCommand

class AKSAddonsCommandGenerator:
    """Generator for AKS addons commands"""
    
    def extract_addons_data(self, analysis_results: Dict, cluster_dna, optimization_strategy) -> Dict:
        """Extract data for AKS addons optimizations"""
        addons_data = {
            'ingress_controller': None,
            'cert_manager_enabled': False,
            'external_dns_enabled': False,
            'keda_enabled': False,
            'dapr_enabled': False,
            'gitops_enabled': False,
            'backup_enabled': False
        }
        
        # Extract from cluster DNA
        if hasattr(cluster_dna, 'addons_config'):
            addons_config = cluster_dna.addons_config
            addons_data['ingress_controller'] = addons_config.get('ingress_controller')
            addons_data['cert_manager_enabled'] = addons_config.get('cert_manager', False)
        
        # Extract from analysis results
        if 'addons_analysis' in analysis_results:
            addons_analysis = analysis_results['addons_analysis']
            addons_data['keda_enabled'] = addons_analysis.get('keda_enabled', False)
            addons_data['dapr_enabled'] = addons_analysis.get('dapr_enabled', False)
        
        return addons_data

    def generate_commands(self, addons_data: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate AKS addons commands"""
        commands = []
        
        # Enable ingress controller if not present
        if not addons_data['ingress_controller']:
            commands.append(ExecutableCommand(
                command=f"az aks approuting enable --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']}",
                description="Enable application routing addon for ingress management",
                category="aks_addons",
                priority_score=75,
                savings_estimate=0
            ))
        
        # Enable KEDA for event-driven autoscaling - only if there are event-driven workloads that could benefit
        if not addons_data['keda_enabled'] and addons_data.get('event_driven_workloads', 0) > 0:
            # Calculate savings based on potential for event-driven scaling
            keda_savings = min(300, addons_data.get('event_driven_workloads', 0) * 50)  # Max $50/workload
            commands.append(ExecutableCommand(
                command=f"az aks addon enable --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']} --addon keda",
                description=f"Enable KEDA addon for {addons_data.get('event_driven_workloads', 0)} event-driven workloads (${keda_savings}/month savings)",
                category="aks_addons",
                priority_score=80,
                savings_estimate=keda_savings,
                estimated_duration_minutes=12,
                risk_level="low"
            ))
        
        # Enable Dapr for microservices
        if not addons_data['dapr_enabled']:
            commands.append(ExecutableCommand(
                command=f"az aks addon enable --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']} --addon dapr",
                description="Enable Dapr addon for distributed application runtime capabilities",
                category="aks_addons",
                priority_score=60,
                savings_estimate=0
            ))
        
        # Enable GitOps with Flux
        if not addons_data['gitops_enabled']:
            commands.append(ExecutableCommand(
                command=f"az k8s-configuration flux create --resource-group {variable_context['resource_group']} --cluster-name {variable_context['cluster_name']} --cluster-type managedClusters --name gitops-config --url https://github.com/your-org/k8s-manifests --branch main --kustomization name=apps path=./apps prune=true",
                description="Enable GitOps with Flux for automated application deployment",
                category="aks_addons",
                priority_score=70,
                savings_estimate=0
            ))
        
        # Enable backup addon
        if not addons_data['backup_enabled']:
            commands.append(ExecutableCommand(
                command=f"az aks addon enable --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']} --addon azure-backup",
                description="Enable Azure Backup addon for cluster backup and disaster recovery",
                category="aks_addons", 
                priority_score=65,
                savings_estimate=0
            ))
        
        return commands