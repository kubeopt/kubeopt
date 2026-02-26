#!/usr/bin/env python3
"""
Kubernetes Data Service
=======================
Base service module for accessing Kubernetes data from the database.
Follows .clauderc principles: fail fast, no silent failures, explicit parameters.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

import logging
from typing import Dict, List, Any, Optional
from infrastructure.persistence.cluster_database import EnhancedMultiSubscriptionClusterManager


class KubernetesDataService:
    """Base service for accessing Kubernetes data from cluster database"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._db = None
    
    @property
    def db(self):
        """Lazy load database connection"""
        if self._db is None:
            self._db = EnhancedMultiSubscriptionClusterManager()
        return self._db
    
    def get_cluster_data(self, cluster_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        Get complete cluster analysis data from database
        
        Args:
            cluster_id: Required cluster identifier
            subscription_id: Required subscription identifier
            
        Returns:
            Complete analysis data dictionary
            
        Raises:
            ValueError: If required parameters are missing
            KeyError: If cluster data is not found
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        self.logger.debug(f"Fetching data for cluster: {cluster_id}")
        
        # Get latest analysis data - this returns enhanced_analysis_data
        analysis_data = self.db.get_latest_analysis(cluster_id)
        if not analysis_data:
            raise KeyError(f"No analysis data found for cluster: {cluster_id}")
        
        # Get the original analysis_data directly from database which has pods
        import sqlite3
        import json
        import gzip
        
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT analysis_data 
                    FROM clusters 
                    WHERE id = ?
                ''', (cluster_id,))
                row = cursor.fetchone()
                
                if row and row['analysis_data']:
                    # Parse the analysis_data which may be compressed
                    if isinstance(row['analysis_data'], bytes):
                        try:
                            # Try gzip decompression first
                            decompressed = gzip.decompress(row['analysis_data'])
                            original_data = json.loads(decompressed.decode('utf-8'))
                        except:
                            # Try as raw bytes
                            original_data = json.loads(row['analysis_data'].decode('utf-8'))
                    else:
                        original_data = json.loads(row['analysis_data'])
                    
                    # Add pods, deployments, and kubectl_data from original data
                    if 'pods' in original_data:
                        analysis_data['pods'] = original_data['pods']
                    if 'deployments' in original_data:
                        analysis_data['deployments'] = original_data['deployments']
                    if 'kubectl_data' in original_data:
                        analysis_data['kubectl_data'] = original_data['kubectl_data']
        except Exception as e:
            self.logger.warning(f"Could not retrieve original analysis data: {e}")
        
        return analysis_data
    
    def get_pods_data(self, cluster_id: str, subscription_id: str) -> List[Dict[str, Any]]:
        """
        Get pods data from cluster analysis
        
        Returns:
            List of pod dictionaries with resource information
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        analysis_data = self.get_cluster_data(cluster_id, subscription_id)
        
        if 'pods' not in analysis_data:
            self.logger.warning(f"No pods data found for cluster {cluster_id}")
            return []
        
        pods_data = analysis_data['pods']
        if not isinstance(pods_data, list):
            raise ValueError(f"Pods data must be a list, got {type(pods_data)}")
        
        return pods_data
    
    def get_deployments_data(self, cluster_id: str, subscription_id: str) -> List[Dict[str, Any]]:
        """
        Get deployments data from cluster analysis
        
        Returns:
            List of deployment dictionaries
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        analysis_data = self.get_cluster_data(cluster_id, subscription_id)
        
        if 'deployments' not in analysis_data:
            self.logger.warning(f"No deployments data found for cluster {cluster_id}")
            return []
        
        deployments_data = analysis_data['deployments']
        
        # Handle different deployment data structures
        if isinstance(deployments_data, dict):
            if 'items' in deployments_data:
                return deployments_data['items']
            else:
                self.logger.warning("Deployments dict doesn't contain 'items' key")
                return []
        elif isinstance(deployments_data, list):
            return deployments_data
        else:
            raise ValueError(f"Unexpected deployments data type: {type(deployments_data)}")
    
    def get_workload_metrics(self, cluster_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        Get workload performance metrics
        
        Returns:
            Dictionary with workload performance data
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        analysis_data = self.get_cluster_data(cluster_id, subscription_id)
        
        workload_metrics = {}
        
        # Calculate metrics from workloads
        if 'workloads' in analysis_data:
            workloads = analysis_data['workloads']
            if workloads and isinstance(workloads, list):
                total_cpu_usage = 0
                total_cpu_request = 0
                total_memory_usage = 0
                total_memory_request = 0
                max_cpu_util = 0
                max_mem_util = 0
                
                for workload in workloads:
                    cpu_usage = 0
                    memory_usage = 0
                    cpu_request = 0
                    memory_request = 0
                    
                    if 'actual_usage' in workload:
                        usage = workload['actual_usage']
                        # Handle nested dict format - actual_usage.cpu.avg_millicores
                        if isinstance(usage.get('cpu'), dict):
                            cpu_usage = usage['cpu'].get('avg_millicores', 0)
                            # Also track percentage if available
                            cpu_percent = usage['cpu'].get('avg_percentage', 0)
                            if cpu_percent > 0:
                                max_cpu_util = max(max_cpu_util, cpu_percent)
                        else:
                            cpu_usage = usage.get('cpu', 0) if usage.get('cpu') is not None else 0
                            
                        if isinstance(usage.get('memory'), dict):
                            # Convert bytes to Mi (1 Mi = 1048576 bytes)
                            memory_bytes = usage['memory'].get('avg_bytes', 0)
                            memory_usage = memory_bytes / 1048576 if memory_bytes else 0
                            # Also track percentage if available
                            mem_percent = usage['memory'].get('avg_percentage', 0)
                            if mem_percent > 0:
                                max_mem_util = max(max_mem_util, mem_percent)
                        else:
                            memory_usage = usage.get('memory', 0) if usage.get('memory') is not None else 0
                        
                        total_cpu_usage += cpu_usage
                        total_memory_usage += memory_usage
                    
                    if 'resources' in workload:
                        resources = workload['resources']
                        if 'requests' in resources:
                            requests = resources['requests']
                            # Handle None values and dict formats
                            cpu_req = requests.get('cpu')
                            if cpu_req is not None:
                                if isinstance(cpu_req, dict):
                                    cpu_request = cpu_req.get('value', 0)
                                else:
                                    cpu_request = cpu_req
                            
                            mem_req = requests.get('memory')
                            if mem_req is not None:
                                if isinstance(mem_req, dict):
                                    memory_request = mem_req.get('value', 0)
                                else:
                                    memory_request = mem_req
                            
                            total_cpu_request += cpu_request
                            total_memory_request += memory_request
                            
                            # Calculate utilization for this workload if we have requests
                            if cpu_request > 0 and cpu_usage > 0:
                                cpu_util = (cpu_usage / cpu_request) * 100
                                max_cpu_util = max(max_cpu_util, cpu_util)
                            if memory_request > 0 and memory_usage > 0:
                                mem_util = (memory_usage / memory_request) * 100
                                max_mem_util = max(max_mem_util, mem_util)
                
                # Calculate average utilization
                if total_cpu_request > 0:
                    workload_metrics['avg_cpu_utilization'] = (total_cpu_usage / total_cpu_request) * 100
                else:
                    workload_metrics['avg_cpu_utilization'] = 0
                    
                if total_memory_request > 0:
                    workload_metrics['avg_memory_utilization'] = (total_memory_usage / total_memory_request) * 100
                else:
                    workload_metrics['avg_memory_utilization'] = 0
                
                workload_metrics['max_cpu_utilization'] = max_cpu_util
                workload_metrics['max_memory_utilization'] = max_mem_util
        
        # Also check node_pools for overall cluster metrics (always check this for better data)
        if 'node_pools' in analysis_data:
            node_pools = analysis_data['node_pools']
            if node_pools and isinstance(node_pools, list):
                total_cpu_percent = 0
                total_memory_percent = 0
                max_cpu_percent = 0
                max_memory_percent = 0
                pool_count = 0
                
                for pool in node_pools:
                    # Check for utilization field (new format)
                    if 'utilization' in pool:
                        util = pool['utilization']
                        cpu_percent = util.get('cpu_percentage', 0)
                        mem_percent = util.get('memory_percentage', 0)
                        
                        # Use 7-day averages if available and non-zero
                        if util.get('avg_cpu_last_7d', 0) > 0:
                            cpu_percent = util['avg_cpu_last_7d']
                        if util.get('avg_memory_last_7d', 0) > 0:
                            mem_percent = util['avg_memory_last_7d']
                        
                        total_cpu_percent += cpu_percent
                        total_memory_percent += mem_percent
                        
                        # Track peak values
                        if util.get('peak_cpu_last_7d', 0) > 0:
                            max_cpu_percent = max(max_cpu_percent, util['peak_cpu_last_7d'])
                        else:
                            max_cpu_percent = max(max_cpu_percent, cpu_percent)
                            
                        if util.get('peak_memory_last_7d', 0) > 0:
                            max_memory_percent = max(max_memory_percent, util['peak_memory_last_7d'])
                        else:
                            max_memory_percent = max(max_memory_percent, mem_percent)
                            
                        pool_count += 1
                    # Fallback to resource_utilization field (old format)
                    elif 'resource_utilization' in pool:
                        util = pool['resource_utilization']
                        # Get capacity and usage
                        if 'cpu' in util:
                            cpu_data = util['cpu']
                            capacity = cpu_data.get('capacity', 0)
                            used = cpu_data.get('used', 0)
                            if capacity > 0:
                                cpu_percent = (used / capacity) * 100
                                total_cpu_percent += cpu_percent
                                max_cpu_percent = max(max_cpu_percent, cpu_percent)
                        if 'memory' in util:
                            mem_data = util['memory']
                            capacity = mem_data.get('capacity', 0)
                            used = mem_data.get('used', 0)
                            if capacity > 0:
                                mem_percent = (used / capacity) * 100
                                total_memory_percent += mem_percent
                                max_memory_percent = max(max_memory_percent, mem_percent)
                        pool_count += 1
                
                # Calculate averages
                if pool_count > 0:
                    # Override workload metrics with node pool data if available
                    workload_metrics['avg_cpu_utilization'] = total_cpu_percent / pool_count
                    workload_metrics['avg_memory_utilization'] = total_memory_percent / pool_count
                    
                    # Set max values
                    if max_cpu_percent > 0:
                        workload_metrics['max_cpu_utilization'] = max_cpu_percent
                    if max_memory_percent > 0:
                        workload_metrics['max_memory_utilization'] = max_memory_percent
        
        # Fallback to checking root level fields
        else:
            metrics_fields = [
                'avg_cpu_utilization', 'avg_memory_utilization',
                'max_cpu_utilization', 'max_memory_utilization',
                'cpu_std_dev', 'memory_std_dev'
            ]
            
            for field in metrics_fields:
                if field in analysis_data:
                    workload_metrics[field] = analysis_data[field]
        
        return workload_metrics
    
    def get_cost_data(self, cluster_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        Get cost and efficiency data
        
        Returns:
            Dictionary with cost breakdown and efficiency metrics
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        analysis_data = self.get_cluster_data(cluster_id, subscription_id)
        
        cost_data = {}
        
        # Check if cost_analysis exists in the data structure
        if 'cost_analysis' in analysis_data:
            cost_analysis = analysis_data['cost_analysis']
            
            # Map cost fields from cost_analysis
            cost_data['total_cost'] = cost_analysis.get('total_cost', 0)
            cost_data['compute_cost'] = cost_analysis.get('node_cost', 0)  # node_cost is compute
            cost_data['storage_cost'] = cost_analysis.get('storage_cost', 0)
            cost_data['networking_cost'] = cost_analysis.get('networking_cost', 0)
            cost_data['control_plane_cost'] = cost_analysis.get('control_plane_cost', 0)
            cost_data['registry_cost'] = cost_analysis.get('registry_cost', 0)
            cost_data['other_cost'] = cost_analysis.get('other_cost', 0)
            
            # Extract savings data from cost_savings
            if 'cost_savings' in cost_analysis:
                savings = cost_analysis['cost_savings']
                cost_data['total_savings'] = savings.get('total_monthly_savings', 0)
                cost_data['compute_savings'] = savings.get('savings_breakdown', {}).get('compute_optimization_savings', 0)
                cost_data['storage_savings'] = savings.get('savings_breakdown', {}).get('storage_optimization_savings', 0)
                cost_data['networking_savings'] = savings.get('savings_breakdown', {}).get('networking_optimization_savings', 0)
                
                # Get optimization score from ROI metrics
                if 'roi_metrics' in savings:
                    roi = savings['roi_metrics']
                    if roi.get('current_monthly_cost', 0) > 0:
                        reduction = roi.get('cost_reduction_percentage', 0)
                        # Convert reduction percentage to optimization score (0-100)
                        cost_data['optimization_score'] = min(100, max(0, 100 - reduction))
                
                # Get efficiency metrics from optimization_potential
                if 'optimization_potential' in savings:
                    opt_potential = savings['optimization_potential']
                    if 'efficiency_metrics' in opt_potential:
                        eff = opt_potential['efficiency_metrics']
                        cost_data['current_cpu_efficiency'] = eff.get('current_cpu_efficiency', 0)
                        cost_data['current_memory_efficiency'] = eff.get('current_memory_efficiency', 0)
                        cost_data['current_efficiency'] = eff.get('current_system_efficiency', 0)
                        cost_data['target_efficiency'] = eff.get('target_system_efficiency', 0)
        else:
            # Fallback to checking root level fields
            cost_fields = [
                'total_cost', 'compute_cost', 'storage_cost', 'networking_cost',
                'control_plane_cost', 'registry_cost', 'monitoring_cost', 'other_cost',
                'idle_cost', 'node_cost', 'load_balancer_cost', 'public_ip_cost'
            ]
            
            for field in cost_fields:
                if field in analysis_data:
                    cost_data[field] = analysis_data[field]
            
            # Extract savings data
            savings_fields = [
                'compute_savings', 'storage_savings', 'hpa_savings', 
                'networking_savings', 'total_savings'
            ]
            
            for field in savings_fields:
                if field in analysis_data:
                    cost_data[field] = analysis_data[field]
            
            # Extract efficiency metrics
            efficiency_fields = [
                'current_efficiency', 'target_efficiency',
                'current_cpu_efficiency', 'current_memory_efficiency',
                'optimization_score', 'confidence_score'
            ]
            
            for field in efficiency_fields:
                if field in analysis_data:
                    cost_data[field] = analysis_data[field]
        
        return cost_data
    
    def get_cluster_summary(self, cluster_id: str, subscription_id: str) -> Dict[str, Any]:
        """
        Get high-level cluster summary
        
        Returns:
            Dictionary with cluster overview statistics
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        analysis_data = self.get_cluster_data(cluster_id, subscription_id)
        
        summary = {
            'cluster_id': cluster_id,
            'subscription_id': subscription_id,
            'timestamp': analysis_data.get('analysis_timestamp'),
            'pod_count': 0,
            'deployment_count': 0,
            'namespace_count': 0,
            'node_count': analysis_data.get('node_count', 0),
            'total_cost': analysis_data.get('total_cost', 0),
            'optimization_score': analysis_data.get('optimization_score', 0),
            'health_score': analysis_data.get('current_health_score', 0)
        }
        
        # Count pods
        pods = self.get_pods_data(cluster_id, subscription_id)
        summary['pod_count'] = len(pods)
        
        # Count unique namespaces from pods
        namespaces = set()
        for pod in pods:
            if 'namespace' in pod:
                namespaces.add(pod['namespace'])
        summary['namespace_count'] = len(namespaces)
        
        # Count deployments
        deployments = self.get_deployments_data(cluster_id, subscription_id)
        summary['deployment_count'] = len(deployments)
        
        return summary
    
    def get_services_data(self, cluster_id: str, subscription_id: str) -> List[Dict[str, Any]]:
        """
        Get services data from cluster analysis
        
        Returns:
            List of service dictionaries
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        analysis_data = self.get_cluster_data(cluster_id, subscription_id)
        
        # Try to get services from kubectl_data first
        kubectl_data = analysis_data.get('kubectl_data', {})
        if 'services' in kubectl_data:
            services_data = kubectl_data['services']
            if isinstance(services_data, str):
                # Parse custom-columns output
                return self._parse_services_custom_columns(services_data)
            elif isinstance(services_data, list):
                return services_data
        
        # Fallback to direct services key
        if 'services' in analysis_data:
            return analysis_data['services']
        
        self.logger.warning(f"No services data found for cluster {cluster_id}")
        return []
    
    def get_storage_data(self, cluster_id: str, subscription_id: str) -> List[Dict[str, Any]]:
        """
        Get storage volumes data from cluster analysis
        
        Returns:
            List of storage volume dictionaries
        """
        if not cluster_id:
            raise ValueError("cluster_id parameter is required")
        if not subscription_id:
            raise ValueError("subscription_id parameter is required")
        
        analysis_data = self.get_cluster_data(cluster_id, subscription_id)
        
        # Try kubectl_data first
        kubectl_data = analysis_data.get('kubectl_data', {})
        storage_volumes = []
        
        # Get PVCs
        if 'persistentvolumeclaims' in kubectl_data:
            pvc_data = kubectl_data['persistentvolumeclaims']
            if isinstance(pvc_data, list):
                # Already parsed by kubernetes_data_cache batch processing
                for pvc in pvc_data:
                    if isinstance(pvc, dict):
                        pvc.setdefault('type', 'PersistentVolumeClaim')
                        storage_volumes.append(pvc)
            elif isinstance(pvc_data, str):
                pvcs = self._parse_pvc_custom_columns(pvc_data)
                storage_volumes.extend(pvcs)

        # Get PVs only (filter out StorageClasses which don't belong in the volumes table)
        if 'storage_volumes' in kubectl_data:
            storage_data = kubectl_data['storage_volumes']
            if isinstance(storage_data, list):
                for item in storage_data:
                    if isinstance(item, dict) and item.get('kind') != 'StorageClass':
                        storage_volumes.append(item)
            elif isinstance(storage_data, str):
                volumes = self._parse_storage_custom_columns(storage_data)
                storage_volumes.extend(volumes)
        
        return storage_volumes
    
    def _parse_services_custom_columns(self, services_output: str) -> List[Dict[str, Any]]:
        """Parse kubectl custom-columns output for services"""
        services = []
        lines = services_output.strip().split('\n')
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    service = {
                        'namespace': parts[0] if parts[0] != '<none>' else 'default',
                        'name': parts[1],
                        'type': parts[2],
                        'cluster_ip': parts[3] if parts[3] != '<none>' else '',
                        'external_ip': parts[4] if len(parts) > 4 and parts[4] != '<none>' else '',
                        'ports': parts[5] if len(parts) > 5 else ''
                    }
                    services.append(service)
        
        return services
    
    def _parse_pvc_custom_columns(self, pvc_output: str) -> List[Dict[str, Any]]:
        """Parse kubectl custom-columns output for PVCs"""
        pvcs = []
        lines = pvc_output.strip().split('\n')
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    pvc = {
                        'namespace': parts[0] if parts[0] != '<none>' else 'default',
                        'name': parts[1],
                        'status': parts[2],
                        'size': parts[3],
                        'storage_class': parts[4] if len(parts) > 4 and parts[4] != '<none>' else '',
                        'type': 'PersistentVolumeClaim'
                    }
                    pvcs.append(pvc)
        
        return pvcs
    
    def _parse_storage_custom_columns(self, storage_output: str) -> List[Dict[str, Any]]:
        """Parse kubectl custom-columns output for PVs and storage classes"""
        storage_items = []
        lines = storage_output.strip().split('\n')
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    storage_item = {
                        'kind': parts[0],
                        'name': parts[1],
                        'size': parts[2] if len(parts) > 2 and parts[2] != '<none>' else '',
                        'status': parts[3] if len(parts) > 3 and parts[3] != '<none>' else '',
                        'storage_class': parts[4] if len(parts) > 4 and parts[4] != '<none>' else '',
                        'namespace': 'cluster-wide' if parts[0] == 'PersistentVolume' else 'default'
                    }
                    storage_items.append(storage_item)
        
        return storage_items