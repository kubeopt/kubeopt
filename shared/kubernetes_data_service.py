#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer

CLEAN ARCHITECTURE: Single Source Kubernetes Data Service
========================================================
This is the ONLY file that executes kubectl commands.
All other components get data through clean interface methods.

IMPLEMENTATION NOTE: Use this after testing the current hybrid approach!
"""

from typing import Dict, List, Optional, Any
import logging
from .kubernetes_data_cache import fetch_cluster_data

logger = logging.getLogger(__name__)

class KubernetesDataService:
    """
    Single source of truth for all Kubernetes cluster data.
    ONLY place in the entire application that executes kubectl commands.
    """
    
    def __init__(self, cluster_name: str, resource_group: str, subscription_id: str):
        self.cluster_name = cluster_name
        self.resource_group = resource_group
        self.subscription_id = subscription_id
        self._cache = None
    
    def _get_cache(self):
        """Lazy load cache to ensure fresh data"""
        if self._cache is None:
            self._cache = fetch_cluster_data(self.cluster_name, self.resource_group, self.subscription_id)
        return self._cache
    
    def refresh_data(self):
        """Force refresh of all cluster data"""
        self._cache = fetch_cluster_data(self.cluster_name, self.resource_group, self.subscription_id)
    
    # === CLUSTER INFRASTRUCTURE ===
    
    def get_nodes(self) -> Dict[str, Any]:
        """Get all cluster nodes with full metadata"""
        return self._get_cache().get('nodes') or {"items": []}
    
    def get_node_usage(self) -> str:
        """Get current node resource usage (kubectl top nodes)"""
        return self._get_cache().get('node_usage') or ""
    
    def get_namespaces(self) -> Dict[str, Any]:
        """Get all namespaces"""
        return self._get_cache().get('namespaces') or {"items": []}
    
    def get_version(self) -> Dict[str, Any]:
        """Get cluster version information"""
        return self._get_cache().get('version') or {}
    
    # === WORKLOAD RESOURCES ===
    
    def get_pods(self) -> Dict[str, Any]:
        """Get all running pods with full metadata"""
        return self._get_cache().get('pods') or {"items": []}
    
    def get_pod_usage(self) -> str:
        """Get current pod resource usage (kubectl top pods)"""
        return self._get_cache().get('pod_usage') or ""
    
    def get_pod_resources(self) -> str:
        """Get pod resource requests and limits (custom columns)"""
        return self._get_cache().get('pod_resources') or ""
    
    def get_pod_timestamps(self) -> str:
        """Get pod creation timestamps (custom columns)"""
        return self._get_cache().get('pod_timestamps') or ""
    
    def get_deployments(self) -> Dict[str, Any]:
        """Get all deployments"""
        return self._get_cache().get('deployments') or {"items": []}
    
    def get_deployment_info(self) -> str:
        """Get deployment info (custom columns)"""
        return self._get_cache().get('deployment_info') or ""
    
    def get_replicasets(self) -> Dict[str, Any]:
        """Get all replicasets"""
        return self._get_cache().get('replicasets') or {"items": []}
    
    def get_replicaset_timestamps(self) -> str:
        """Get replicaset creation timestamps (custom columns)"""
        return self._get_cache().get('replicaset_timestamps') or ""
    
    def get_statefulsets(self) -> Dict[str, Any]:
        """Get all statefulsets"""
        return self._get_cache().get('statefulsets') or {"items": []}
    
    # === INFRASTRUCTURE RESOURCES ===
    
    def get_services(self) -> Dict[str, Any]:
        """Get all services"""
        return self._get_cache().get('services') or {"items": []}
    
    def get_services_text(self) -> str:
        """Get services in text format"""
        return self._get_cache().get('services_text') or ""
    
    def get_pvcs(self) -> Dict[str, Any]:
        """Get all persistent volume claims"""
        return self._get_cache().get('pvcs') or {"items": []}
    
    def get_pvc_text(self) -> str:
        """Get PVCs in text format"""
        return self._get_cache().get('pvc_text') or ""
    
    def get_storage_classes(self) -> Dict[str, Any]:
        """Get all storage classes"""
        return self._get_cache().get('storage_classes') or {"items": []}
    
    def get_storage_classes_text(self) -> str:
        """Get storage classes in text format"""
        return self._get_cache().get('storage_classes_text') or ""
    
    # === SECURITY & RBAC ===
    
    def get_service_accounts(self) -> Dict[str, Any]:
        """Get all service accounts"""
        return self._get_cache().get('service_accounts') or {"items": []}
    
    def get_cluster_roles(self) -> Dict[str, Any]:
        """Get all cluster roles"""
        return self._get_cache().get('cluster_roles') or {"items": []}
    
    def get_role_bindings(self) -> Dict[str, Any]:
        """Get all role bindings"""
        return self._get_cache().get('role_bindings') or {"items": []}
    
    def get_cluster_role_bindings(self) -> Dict[str, Any]:
        """Get all cluster role bindings"""
        return self._get_cache().get('cluster_role_bindings') or {"items": []}
    
    def get_network_policies(self) -> Dict[str, Any]:
        """Get all network policies"""
        return self._get_cache().get('network_policies') or {"items": []}
    
    def get_resource_quotas(self) -> Dict[str, Any]:
        """Get all resource quotas"""
        return self._get_cache().get('resource_quotas') or {"items": []}
    
    def get_limit_ranges(self) -> Dict[str, Any]:
        """Get all limit ranges"""
        return self._get_cache().get('limit_ranges') or {"items": []}
    
    def get_secrets(self) -> Dict[str, Any]:
        """Get all secrets (metadata only)"""
        return self._get_cache().get('secrets') or {"items": []}
    
    def get_pod_security_policies(self) -> Dict[str, Any]:
        """Get all pod security policies - DEPRECATED in k8s 1.25+"""
        # PodSecurityPolicies are deprecated in Kubernetes 1.25+
        # Return empty structure to maintain compatibility
        return {"items": []}
    
    # === AUTOSCALING & HPA ===
    
    def get_hpa(self) -> Dict[str, Any]:
        """Get all horizontal pod autoscalers"""
        return self._get_cache().get('hpa') or {"items": []}
    
    def get_hpa_custom(self) -> str:
        """Get HPA data in custom columns format"""
        return self._get_cache().get('hpa_custom') or ""
    
    # === EVENTS & CONFIG ===
    
    def get_events(self) -> Dict[str, Any]:
        """Get cluster events (limited to recent 200)"""
        return self._get_cache().get('events') or {"items": []}
    
    def get_configmaps(self) -> Dict[str, Any]:
        """Get all config maps"""
        return self._get_cache().get('configmaps') or {"items": []}
    
    def get_applications(self) -> Dict[str, Any]:
        """Get ArgoCD applications (if available)"""
        return self._get_cache().get('applications') or {"items": []}
    
    # === CONVENIENCE METHODS FOR COMPONENTS ===
    
    def get_enterprise_metrics_data(self) -> Dict[str, Any]:
        """Get all data needed for enterprise metrics calculation"""
        return {
            'nodes': self.get_nodes(),
            'node_usage': self.get_node_usage(),
            'pods': self.get_pods(),
            'pod_usage': self.get_pod_usage(),
            'pod_resources': self.get_pod_resources(),
            'pod_timestamps': self.get_pod_timestamps(),
            'deployments': self.get_deployments(),
            'deployment_info': self.get_deployment_info(),
            'replicasets': self.get_replicasets(),
            'replicaset_timestamps': self.get_replicaset_timestamps(),
            'namespaces': self.get_namespaces(),
            'services': self.get_services(),
            'pvcs': self.get_pvcs(),
            'statefulsets': self.get_statefulsets(),
            'events': self.get_events(),
            'configmaps': self.get_configmaps(),
            'applications': self.get_applications(),
            'version': self.get_version(),
            # Security data
            'service_accounts': self.get_service_accounts(),
            'cluster_roles': self.get_cluster_roles(),
            'role_bindings': self.get_role_bindings(),
            'cluster_role_bindings': self.get_cluster_role_bindings(),
            'network_policies': self.get_network_policies(),
            'resource_quotas': self.get_resource_quotas(),
            'limit_ranges': self.get_limit_ranges(),
            'secrets': self.get_secrets(),
            'pod_security_policies': self.get_pod_security_policies()
        }
    
    def get_realtime_metrics_data(self) -> Dict[str, Any]:
        """Get all data needed for real-time metrics"""
        return {
            'nodes': self.get_nodes(),
            'node_usage': self.get_node_usage(),
            'pods': self.get_pods(),
            'pod_usage': self.get_pod_usage(),
            'pod_resources': self.get_pod_resources(),
            'hpa': self.get_hpa(),
            'hpa_custom': self.get_hpa_custom()
        }
    
    def get_cost_analysis_data(self) -> Dict[str, Any]:
        """Get all data needed for cost analysis"""
        return {
            'nodes': self.get_nodes(),
            'pods': self.get_pods(),
            'pod_usage': self.get_pod_usage(),
            'pvcs': self.get_pvcs(),
            'pvc_text': self.get_pvc_text(),
            'services': self.get_services(),
            'services_text': self.get_services_text(),
            'storage_classes': self.get_storage_classes(),
            'storage_classes_text': self.get_storage_classes_text()
        }


# === GLOBAL SERVICE INSTANCES ===
_service_instances: Dict[str, KubernetesDataService] = {}

def get_kubernetes_data_service(cluster_name: str, resource_group: str, subscription_id: str) -> KubernetesDataService:
    """Get or create a data service instance for a cluster"""
    service_key = f"{subscription_id}:{resource_group}:{cluster_name}"
    
    if service_key not in _service_instances:
        _service_instances[service_key] = KubernetesDataService(cluster_name, resource_group, subscription_id)
        logger.info(f"🆕 Created data service for {cluster_name}")
    
    return _service_instances[service_key]

def clear_all_services():
    """Clear all service instances (useful for testing)"""
    global _service_instances
    _service_instances.clear()
    logger.info("🗑️ All data services cleared")