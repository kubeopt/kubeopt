from typing import Dict, List
from ..models.core import ExecutableCommand

class AKSSecurityCommandGenerator:
    """Generator for AKS security commands"""
    
    def extract_security_data(self, analysis_results: Dict, cluster_dna, optimization_strategy) -> Dict:
        """Extract data for AKS security optimizations"""
        security_data = {
            'rbac_enabled': False,
            'network_policy_enabled': False,
            'pod_security_standards': False,
            'azure_defender_enabled': False,
            'private_cluster': False,
            'authorized_ip_ranges': []
        }
        
        # Extract from cluster DNA
        if hasattr(cluster_dna, 'security_config'):
            sec_config = cluster_dna.security_config
            security_data['rbac_enabled'] = sec_config.get('rbac_enabled', False)
            security_data['network_policy_enabled'] = sec_config.get('network_policy_enabled', False)
        
        # Extract from analysis results
        if 'security_posture' in analysis_results:
            security_posture = analysis_results['security_posture']
            security_data['azure_defender_enabled'] = security_posture.get('defender_enabled', False)
            security_data['private_cluster'] = security_posture.get('private_cluster', False)
        
        return security_data

    def generate_commands(self, security_data: Dict, variable_context: Dict) -> List[ExecutableCommand]:
        """Generate AKS security commands"""
        commands = []
        
        # Enable Azure Defender
        if not security_data['azure_defender_enabled']:
            commands.append(ExecutableCommand(
                command=f"az security pricing create --name KubernetesService --tier Standard --subscription {variable_context['subscription_id']}",
                description="Enable Azure Defender for Kubernetes for enhanced security monitoring",
                category="aks_security",
                priority_score=90,
                savings_estimate=0
            ))
        
        # Network policy enforcement
        if not security_data['network_policy_enabled']:
            network_policy_yaml = """kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF"""
            commands.append(ExecutableCommand(
                command=network_policy_yaml,
                description="Apply default network policy to restrict pod-to-pod communication",
                category="aks_security",
                priority_score=85,
                savings_estimate=0
            ))
        
        # Pod security standards
        commands.append(ExecutableCommand(
            command=f"kubectl label namespace default pod-security.kubernetes.io/enforce=restricted pod-security.kubernetes.io/audit=restricted pod-security.kubernetes.io/warn=restricted",
            description="Enforce pod security standards for enhanced workload security",
            category="aks_security",
            priority_score=80,
            savings_estimate=0
        ))
        
        # Authorized IP ranges check
        commands.append(ExecutableCommand(
            command=f"az aks show --resource-group {variable_context['resource_group']} --name {variable_context['cluster_name']} --query 'apiServerAccessProfile.authorizedIpRanges'",
            description="Review authorized IP ranges configuration",
            category="aks_security",
            priority_score=60,
            savings_estimate=0
        ))
        
        return commands