#!/usr/bin/env python3
"""
Kubernetes Dashboard API Modules
=================================
Modular API handlers for Kubernetes dashboard components.
Follows .clauderc principles: fail fast, no silent failures, explicit parameters.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

import logging
from typing import Dict, List, Any, Optional
from flask import jsonify
from infrastructure.services.kubernetes_data_service import KubernetesDataService


class PodsDashboardAPI:
    """API handler for pods dashboard component"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._data_service = None
    
    @property
    def data_service(self):
        """Lazy load data service"""
        if self._data_service is None:
            self._data_service = KubernetesDataService()
        return self._data_service
    
    def get_pods_overview(self, cluster_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        Get formatted pods data for dashboard display
        
        Args:
            cluster_id: Required cluster identifier
            subscription_id: Required subscription identifier
            
        Returns:
            Dictionary with formatted pods data for UI
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        # Get raw pods data
        pods_data = self.data_service.get_pods_data(cluster_id, subscription_id)
        
        # Format pods for dashboard
        formatted_pods = []
        for pod in pods_data:
            formatted_pod = {
                'name': pod.get('name', 'Unknown'),
                'namespace': pod.get('namespace', 'default'),
                'status': pod.get('status', 'Unknown'),
                'node': pod.get('node', 'Unknown'),
                'restarts': self._parse_restarts(pod.get('restarts', '0')),
                'cpu_request': self._parse_cpu_value(pod.get('cpu_request', '0')),
                'memory_request': self._parse_memory_value(pod.get('memory_request', '0')),
                'cpu_limit': self._parse_cpu_value(pod.get('cpu_limit', '0')),
                'memory_limit': self._parse_memory_value(pod.get('memory_limit', '0')),
                'health_score': self._calculate_pod_health(pod),
                'severity': self._calculate_pod_severity(pod)
            }
            formatted_pods.append(formatted_pod)
        
        # Calculate summary statistics
        summary = self._calculate_pods_summary(formatted_pods)
        
        return {
            'cluster_id': cluster_id,
            'subscription_id': subscription_id,
            'pods': formatted_pods,
            'summary': summary,
            'total_count': len(formatted_pods)
        }
    
    def _parse_restarts(self, restarts_str: str) -> int:
        """Parse restart count from string"""
        try:
            return int(restarts_str) if restarts_str else 0
        except (ValueError, TypeError):
            return 0
    
    def _parse_cpu_value(self, cpu_str: str) -> float:
        """Parse CPU value from string format to cores"""
        if not cpu_str or cpu_str == '0':
            return 0.0
        
        try:
            if isinstance(cpu_str, str) and cpu_str.endswith('m'):
                return float(cpu_str[:-1]) / 1000
            else:
                return float(cpu_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_memory_value(self, memory_str: str) -> float:
        """Parse memory value from string format to GB"""
        if not memory_str or memory_str == '0':
            return 0.0
        
        try:
            if isinstance(memory_str, str):
                if memory_str.endswith('Mi'):
                    return float(memory_str[:-2]) / 1024
                elif memory_str.endswith('Gi'):
                    return float(memory_str[:-2])
                elif memory_str.endswith('Ki'):
                    return float(memory_str[:-2]) / (1024 * 1024)
            return float(memory_str) / (1024 * 1024 * 1024)
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_pod_health(self, pod: Dict[str, Any]) -> int:
        """Calculate pod health score (0-100)"""
        status = pod.get('status', '').lower()
        restarts = self._parse_restarts(pod.get('restarts', '0'))
        
        if status in ['failed', 'error']:
            return 0
        elif status == 'pending':
            return 30
        elif status == 'running' or status == 'succeeded':
            base_score = 100
            restart_penalty = min(restarts * 10, 50)
            return max(base_score - restart_penalty, 50)
        else:
            return 50
    
    def _calculate_pod_severity(self, pod: Dict[str, Any]) -> str:
        """Calculate pod severity level"""
        status = pod.get('status', '').lower()
        restarts = self._parse_restarts(pod.get('restarts', '0'))
        
        if status in ['failed', 'error']:
            return 'critical'
        elif status == 'pending' or restarts > 5:
            return 'high'
        elif restarts > 2:
            return 'medium'
        elif status in ['running', 'succeeded']:
            return 'low'
        else:
            return 'unknown'
    
    def _calculate_pods_summary(self, pods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for pods"""
        if not pods:
            return {
                'healthy_count': 0,
                'warning_count': 0,
                'critical_count': 0,
                'total_cpu_request': 0,
                'total_memory_request': 0
            }
        
        summary = {
            'healthy_count': 0,
            'warning_count': 0,
            'critical_count': 0,
            'total_cpu_request': 0,
            'total_memory_request': 0,
            'avg_health_score': 0
        }
        
        health_scores = []
        
        for pod in pods:
            severity = pod.get('severity', 'unknown')
            if severity == 'low':
                summary['healthy_count'] += 1
            elif severity in ['medium', 'high']:
                summary['warning_count'] += 1
            elif severity == 'critical':
                summary['critical_count'] += 1
            
            summary['total_cpu_request'] += pod.get('cpu_request', 0)
            summary['total_memory_request'] += pod.get('memory_request', 0)
            health_scores.append(pod.get('health_score', 50))
        
        if health_scores:
            summary['avg_health_score'] = sum(health_scores) / len(health_scores)
        
        return summary


class WorkloadsDashboardAPI:
    """API handler for workloads dashboard component"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._data_service = None
    
    @property
    def data_service(self):
        """Lazy load data service"""
        if self._data_service is None:
            self._data_service = KubernetesDataService()
        return self._data_service
    
    def get_workloads_overview(self, cluster_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        Get formatted workloads data for dashboard display
        
        Args:
            cluster_id: Required cluster identifier
            subscription_id: Required subscription identifier
            
        Returns:
            Dictionary with formatted workloads data for UI
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        # Get deployments data
        deployments = self.data_service.get_deployments_data(cluster_id, subscription_id)
        
        # Get workload metrics if available
        workload_metrics = self.data_service.get_workload_metrics(cluster_id, subscription_id)
        
        # Format workloads for dashboard
        formatted_workloads = []
        for deployment in deployments:
            formatted_workload = {
                'name': deployment.get('name', 'Unknown'),
                'namespace': deployment.get('namespace', 'default'),
                'type': 'Deployment',
                'replicas': {
                    'current': self._parse_int(deployment.get('ready', '0')),
                    'desired': self._parse_int(deployment.get('replicas', '0'))
                },
                'image': deployment.get('image', 'Unknown'),
                'status': self._calculate_deployment_status(deployment),
                'health_score': self._calculate_deployment_health(deployment)
            }
            formatted_workloads.append(formatted_workload)
        
        # Calculate summary
        summary = self._calculate_workloads_summary(formatted_workloads)
        
        return {
            'cluster_id': cluster_id,
            'subscription_id': subscription_id,
            'workloads': formatted_workloads,
            'metrics': workload_metrics,
            'summary': summary,
            'total_count': len(formatted_workloads)
        }
    
    def _parse_int(self, value: str) -> int:
        """Parse integer from string"""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    def _calculate_deployment_status(self, deployment: Dict[str, Any]) -> str:
        """Calculate deployment status"""
        ready = self._parse_int(deployment.get('ready', '0'))
        desired = self._parse_int(deployment.get('replicas', '0'))
        
        if ready == desired and ready > 0:
            return 'healthy'
        elif ready == 0:
            return 'critical'
        elif ready < desired:
            return 'warning'
        else:
            return 'unknown'
    
    def _calculate_deployment_health(self, deployment: Dict[str, Any]) -> int:
        """Calculate deployment health score"""
        ready = self._parse_int(deployment.get('ready', '0'))
        desired = self._parse_int(deployment.get('replicas', '0'))
        
        if desired == 0:
            return 50
        
        return int((ready / desired) * 100)
    
    def _calculate_workloads_summary(self, workloads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for workloads"""
        if not workloads:
            return {
                'healthy_count': 0,
                'warning_count': 0,
                'critical_count': 0,
                'total_replicas': 0
            }
        
        summary = {
            'healthy_count': 0,
            'warning_count': 0,
            'critical_count': 0,
            'total_replicas': 0,
            'avg_health_score': 0
        }
        
        health_scores = []
        
        for workload in workloads:
            status = workload.get('status', 'unknown')
            if status == 'healthy':
                summary['healthy_count'] += 1
            elif status == 'warning':
                summary['warning_count'] += 1
            elif status == 'critical':
                summary['critical_count'] += 1
            
            summary['total_replicas'] += workload['replicas']['current']
            health_scores.append(workload.get('health_score', 50))
        
        if health_scores:
            summary['avg_health_score'] = sum(health_scores) / len(health_scores)
        
        return summary


class ResourcesDashboardAPI:
    """API handler for resources dashboard component"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._data_service = None
    
    @property
    def data_service(self):
        """Lazy load data service"""
        if self._data_service is None:
            self._data_service = KubernetesDataService()
        return self._data_service
    
    def get_resources_overview(self, cluster_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        Get formatted resources data for dashboard display
        
        Args:
            cluster_id: Required cluster identifier
            subscription_id: Required subscription identifier
            
        Returns:
            Dictionary with formatted resources data for UI
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        # Get all resource data
        analysis_data = self.data_service.get_cluster_data(cluster_id, subscription_id)
        
        # Get services data from the new service method
        services_data = self.data_service.get_services_data(cluster_id, subscription_id)
        
        # Get storage volumes from the new storage method
        storage = self.data_service.get_storage_data(cluster_id, subscription_id)
        
        # Extract network resources  
        network = analysis_data.get('network_resources', {})
        # Add counts if not present
        if network:
            if 'public_ip_count' not in network and 'public_ips' in network:
                network['public_ip_count'] = len(network['public_ips']) if isinstance(network['public_ips'], list) else 0
            if 'load_balancer_count' not in network and 'load_balancers' in network:
                network['load_balancer_count'] = len(network['load_balancers']) if isinstance(network['load_balancers'], list) else 0
            # Calculate costs if not present
            if 'public_ip_cost' not in network:
                network['public_ip_cost'] = network.get('public_ip_count', 0) * 3.65  # ~$3.65 per IP per month
            if 'load_balancer_cost' not in network:
                network['load_balancer_cost'] = network.get('load_balancer_count', 0) * 18.25  # ~$18.25 per LB per month
        
        # Extract anomalies
        anomalies = analysis_data.get('anomaly_detection', {})
        
        # Extract namespaces and enrich with pod counts
        namespaces = analysis_data.get('namespaces', [])
        
        # Calculate actual pod counts from pods data
        pods_data = analysis_data.get('pods', [])
        pod_counts = {}
        for pod in pods_data:
            ns = pod.get('namespace', 'unknown')
            pod_counts[ns] = pod_counts.get(ns, 0) + 1
        
        # Enrich namespace data with actual counts
        enriched_namespaces = []
        for ns in namespaces:
            if isinstance(ns, dict):
                ns_name = ns.get('name')
                ns['pod_count'] = pod_counts.get(ns_name, 0)
                enriched_namespaces.append(ns)
            else:
                # If namespace is just a string
                enriched_namespaces.append({
                    'name': ns,
                    'pod_count': pod_counts.get(ns, 0),
                    'service_count': 0  # We'll need to get this from services data if available
                })
        
        # Get cost and metrics for compatibility
        cost_data = self.data_service.get_cost_data(cluster_id, subscription_id)
        workload_metrics = self.data_service.get_workload_metrics(cluster_id, subscription_id) 
        summary = self.data_service.get_cluster_summary(cluster_id, subscription_id)
        
        return {
            'cluster_id': cluster_id,
            'subscription_id': subscription_id,
            'services': services_data,  # Add services data
            'storage': storage,
            'network': network,
            'anomalies': anomalies,
            'namespaces': enriched_namespaces,
            'pods': pods_data,  # Include pods data for namespace details
            'deployments': analysis_data.get('deployments', []),  # Include deployments data
            'costs': cost_data,
            'metrics': workload_metrics,
            'summary': summary,
            'charts': self._prepare_chart_data(cost_data, workload_metrics)
        }
    
    def _prepare_chart_data(self, cost_data: Dict, metrics: Dict) -> Dict[str, Any]:
        """Prepare data for charts"""
        return {
            'cost_breakdown': {
                'labels': ['Compute', 'Storage', 'Networking', 'Control Plane', 'Other'],
                'values': [
                    cost_data.get('compute_cost', 0),
                    cost_data.get('storage_cost', 0),
                    cost_data.get('networking_cost', 0),
                    cost_data.get('control_plane_cost', 0),
                    cost_data.get('other_cost', 0)
                ]
            },
            'resource_utilization': {
                'cpu': {
                    'avg': metrics.get('avg_cpu_utilization', 0),
                    'max': metrics.get('max_cpu_utilization', 0)
                },
                'memory': {
                    'avg': metrics.get('avg_memory_utilization', 0),
                    'max': metrics.get('max_memory_utilization', 0)
                }
            },
            'savings_potential': {
                'compute': cost_data.get('compute_savings', 0),
                'storage': cost_data.get('storage_savings', 0),
                'hpa': cost_data.get('hpa_savings', 0),
                'total': cost_data.get('total_savings', 0)
            }
        }