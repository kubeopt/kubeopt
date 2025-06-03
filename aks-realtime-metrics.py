"""
AKS Real-time Metrics Fetcher - Enhanced Version
================================================
Fetches real-time performance metrics directly from AKS clusters.
Provides current usage data for optimization algorithms.

INTEGRATION: Works with pod_cost_analyzer.py to provide usage+cost analysis
PURPOSE: Collects "what is happening now" data for optimization calculations
"""

# ============================================================================
# IMPORTS AND CONFIGURATION
# ============================================================================

import subprocess
import json
import logging
import yaml
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import shared utilities from pod_cost_analyzer to avoid duplication
try:
    from pod_cost_analyzer import KubernetesParsingUtils
except ImportError:
    # Fallback: Define minimal parsing if pod_cost_analyzer not available
    class KubernetesParsingUtils:
        @staticmethod
        def parse_cpu_safe(cpu_str: str) -> float:
            """Minimal CPU parsing fallback"""
            if not cpu_str or not isinstance(cpu_str, str):
                return 0.0
            try:
                if cpu_str.endswith('m'):
                    return float(cpu_str[:-1]) / 1000.0
                else:
                    return float(cpu_str)
            except:
                return 0.0
        
        @staticmethod
        def parse_memory_safe(memory_str: str) -> int:
            """Minimal memory parsing fallback"""
            if not memory_str or not isinstance(memory_str, str):
                return 0
            try:
                if memory_str.endswith('Ki'):
                    return int(float(memory_str[:-2]) * 1024)
                elif memory_str.endswith('Mi'):
                    return int(float(memory_str[:-2]) * 1024 * 1024)
                elif memory_str.endswith('Gi'):
                    return int(float(memory_str[:-2]) * 1024 * 1024 * 1024)
                else:
                    return int(float(memory_str))
            except:
                return 0

logger = logging.getLogger(__name__)

# ============================================================================
# CORE REAL-TIME METRICS FETCHER
# ============================================================================

class AKSRealTimeMetricsFetcher:
    """
    Real-time AKS Metrics Collection Engine
    
    PURPOSE: Collects current performance data for optimization analysis
    INTEGRATION: Provides usage patterns to complement cost data from pod_cost_analyzer.py
    """
    
    def __init__(self, resource_group: str, cluster_name: str):
        """
        Initialize Real-time Metrics Fetcher
        
        Args:
            resource_group: Azure resource group name
            cluster_name: AKS cluster name
        """
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.connection_verified = False
        
        # Initialize shared parsing utilities
        self.parser = KubernetesParsingUtils()
        
        # Cache for frequently accessed data
        self._metrics_cache = {}
        self._cache_timeout = 30  # seconds
        
    # ------------------------------------------------------------------------
    # CONNECTION AND KUBECTL EXECUTION
    # ------------------------------------------------------------------------
        
    def verify_cluster_connection(self) -> bool:
        """
        Verify connectivity to AKS cluster via az aks command invoke
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Verifying connection to AKS cluster {self.cluster_name}")
            
            cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', 'kubectl cluster-info'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
            if "Kubernetes control plane" in result.stdout:
                logger.info("✅ Successfully connected to AKS cluster")
                self.connection_verified = True
                return True
            else:
                logger.error("❌ Failed to verify cluster connection")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error connecting to AKS cluster: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Connection timeout to AKS cluster")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during connection verification: {e}")
            return False
    
    def execute_kubectl_command(self, kubectl_cmd: str, timeout: int = 30) -> Optional[str]:
        """
        Execute kubectl command via az aks command invoke with proper error handling
        
        Args:
            kubectl_cmd: The kubectl command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Command output string or None if failed
        """
        # Verify connection on first use
        if not self.connection_verified:
            if not self.verify_cluster_connection():
                return None
        
        try:
            cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', kubectl_cmd
            ]
            
            logger.debug(f"Executing kubectl: {kubectl_cmd}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Timeout executing kubectl command: {kubectl_cmd}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error executing kubectl command '{kubectl_cmd}': {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error executing command: {e}")
            return None

    # ------------------------------------------------------------------------
    # NODE METRICS COLLECTION
    # ------------------------------------------------------------------------
    
    def get_node_metrics(self) -> Dict[str, Any]:
        """
        Collect real-time node resource usage and capacity metrics
        
        Returns:
            Dictionary containing node metrics, utilization, and capacity info
        """
        logger.info("📊 Fetching real-time node metrics...")
        
        try:
            # Get current node resource usage
            top_nodes = self.execute_kubectl_command("kubectl top nodes --no-headers")
            if not top_nodes:
                logger.warning("⚠️ Could not fetch node usage metrics")
                return self._empty_node_metrics()
            
            # Get node capacity and detailed information
            node_info = self.execute_kubectl_command("kubectl get nodes -o json")
            if not node_info:
                logger.warning("⚠️ Could not fetch node information")
                return self._empty_node_metrics()
            
            # Parse and combine the data
            return self._process_node_metrics(top_nodes, node_info)
            
        except Exception as e:
            logger.error(f"❌ Error fetching node metrics: {e}")
            return self._empty_node_metrics()
    
    def _process_node_metrics(self, top_nodes_output: str, node_info_json: str) -> Dict[str, Any]:
        """
        Process raw node metrics into structured format
        
        Args:
            top_nodes_output: Output from 'kubectl top nodes'
            node_info_json: Output from 'kubectl get nodes -o json'
            
        Returns:
            Processed node metrics dictionary
        """
        try:
            nodes_data = json.loads(node_info_json)
            node_metrics = []
            
            # Parse 'kubectl top nodes' output
            top_lines = top_nodes_output.strip().split('\n')
            node_usage = {}
            
            for line in top_lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        node_name = parts[0]
                        cpu_usage = self.parser.parse_cpu_safe(parts[1])  # Using shared parser
                        memory_usage = self.parser.parse_memory_safe(parts[3])  # Using shared parser
                        
                        node_usage[node_name] = {
                            'cpu_usage_cores': cpu_usage,
                            'memory_usage_bytes': memory_usage
                        }
            
            # Combine with detailed node information
            for node in nodes_data.get('items', []):
                node_name = node['metadata']['name']
                if node_name not in node_usage:
                    continue
                
                # Extract allocatable resources
                allocatable = node['status'].get('allocatable', {})
                cpu_allocatable = self.parser.parse_cpu_safe(allocatable.get('cpu', '0'))
                memory_allocatable = self.parser.parse_memory_safe(allocatable.get('memory', '0Ki'))
                
                # Calculate utilization percentages
                usage = node_usage[node_name]
                cpu_usage_pct = (usage['cpu_usage_cores'] / cpu_allocatable * 100) if cpu_allocatable > 0 else 0
                memory_usage_pct = (usage['memory_usage_bytes'] / memory_allocatable * 100) if memory_allocatable > 0 else 0
                
                # Get node health status
                conditions = node['status'].get('conditions', [])
                ready_condition = next((c for c in conditions if c['type'] == 'Ready'), {})
                is_ready = ready_condition.get('status') == 'True'
                
                # Extract node system information
                node_info = node['status'].get('nodeInfo', {})
                
                node_metrics.append({
                    'name': node_name,
                    'cpu_usage_pct': round(cpu_usage_pct, 1),
                    'memory_usage_pct': round(memory_usage_pct, 1),
                    'cpu_allocatable_cores': cpu_allocatable,
                    'memory_allocatable_bytes': memory_allocatable,
                    'cpu_usage_cores': usage['cpu_usage_cores'],
                    'memory_usage_bytes': usage['memory_usage_bytes'],
                    'ready': is_ready,
                    'node_info': {
                        'kernel_version': node_info.get('kernelVersion', ''),
                        'os_image': node_info.get('osImage', ''),
                        'container_runtime': node_info.get('containerRuntimeVersion', ''),
                        'kubelet_version': node_info.get('kubeletVersion', '')
                    },
                    # Resource gaps for optimization analysis
                    'cpu_gap_pct': max(0, round(100 - cpu_usage_pct, 1)),
                    'memory_gap_pct': max(0, round(100 - memory_usage_pct, 1))
                })
            
            logger.info(f"✅ Successfully processed metrics for {len(node_metrics)} nodes")
            
            return {
                'nodes': node_metrics,
                'total_nodes': len(node_metrics),
                'ready_nodes': sum(1 for n in node_metrics if n['ready']),
                'average_cpu_usage': round(sum(n['cpu_usage_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'average_memory_usage': round(sum(n['memory_usage_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'kubectl_top_nodes'
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing node information JSON: {e}")
            return self._empty_node_metrics()
        except Exception as e:
            logger.error(f"❌ Error processing node metrics: {e}")
            return self._empty_node_metrics()

    def _empty_node_metrics(self) -> Dict[str, Any]:
        """Return empty node metrics structure"""
        return {
            'nodes': [],
            'total_nodes': 0,
            'ready_nodes': 0,
            'average_cpu_usage': 0,
            'average_memory_usage': 0,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'unavailable'
        }

    # ------------------------------------------------------------------------
    # POD METRICS COLLECTION
    # ------------------------------------------------------------------------
    
    def get_pod_metrics(self) -> Dict[str, Any]:
        """
        Collect real-time pod resource usage and allocation metrics
        
        Returns:
            Dictionary containing pod metrics, deployment aggregations, and namespace summaries
        """
        logger.info("📊 Fetching real-time pod metrics...")
        
        try:
            # Get pod resource usage via kubectl top
            top_pods = self.execute_kubectl_command("kubectl top pods --all-namespaces --no-headers")
            if not top_pods:
                logger.warning("⚠️ Could not fetch pod usage metrics")
                return self._empty_pod_metrics()
            
            # Get detailed pod information with resource requests/limits
            pod_info = self.execute_kubectl_command("kubectl get pods --all-namespaces -o json")
            if not pod_info:
                logger.warning("⚠️ Could not fetch pod configuration")
                return self._empty_pod_metrics()
            
            # Process and combine the data
            return self._process_pod_metrics(top_pods, pod_info)
            
        except Exception as e:
            logger.error(f"❌ Error fetching pod metrics: {e}")
            return self._empty_pod_metrics()
    
    def _process_pod_metrics(self, top_pods_output: str, pod_info_json: str) -> Dict[str, Any]:
        """
        Process raw pod metrics into structured format with deployment aggregations
        
        Args:
            top_pods_output: Output from 'kubectl top pods'
            pod_info_json: Output from 'kubectl get pods -o json'
            
        Returns:
            Processed pod metrics with namespace and deployment aggregations
        """
        try:
            pods_data = json.loads(pod_info_json)
            pod_metrics = []
            
            # Parse 'kubectl top pods' output
            top_lines = top_pods_output.strip().split('\n')
            pod_usage = {}
            
            for line in top_lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        namespace = parts[0]
                        pod_name = parts[1]
                        cpu_usage = self.parser.parse_cpu_safe(parts[2])  # Using shared parser
                        memory_usage = self.parser.parse_memory_safe(parts[3])  # Using shared parser
                        
                        pod_key = f"{namespace}/{pod_name}"
                        pod_usage[pod_key] = {
                            'cpu_usage_cores': cpu_usage,
                            'memory_usage_bytes': memory_usage
                        }
            
            # Process detailed pod information and aggregate by namespace/deployment
            namespace_stats = {}
            deployment_stats = {}
            
            for pod in pods_data.get('items', []):
                namespace = pod['metadata']['namespace']
                pod_name = pod['metadata']['name']
                pod_key = f"{namespace}/{pod_name}"
                
                if pod_key not in pod_usage:
                    continue
                
                # Extract deployment name from owner references
                deployment_name = self._extract_deployment_name(pod)
                
                # Get resource requests and limits from containers
                resource_info = self._extract_pod_resources(pod)
                
                usage = pod_usage[pod_key]
                
                # Calculate utilization percentages
                cpu_usage_pct = (usage['cpu_usage_cores'] / resource_info['cpu_request']) * 100 if resource_info['cpu_request'] > 0 else 0
                memory_usage_pct = (usage['memory_usage_bytes'] / resource_info['memory_request']) * 100 if resource_info['memory_request'] > 0 else 0
                
                pod_metric = {
                    'namespace': namespace,
                    'pod_name': pod_name,
                    'deployment': deployment_name,
                    'cpu_usage_cores': usage['cpu_usage_cores'],
                    'memory_usage_bytes': usage['memory_usage_bytes'],
                    'cpu_request': resource_info['cpu_request'],
                    'memory_request': resource_info['memory_request'],
                    'cpu_limit': resource_info['cpu_limit'],
                    'memory_limit': resource_info['memory_limit'],
                    'cpu_usage_pct': round(cpu_usage_pct, 1),
                    'memory_usage_pct': round(memory_usage_pct, 1),
                    'cpu_gap': max(0, round(100 - cpu_usage_pct, 1)),
                    'memory_gap': max(0, round(100 - memory_usage_pct, 1)),
                    'status': pod['status'].get('phase', 'Unknown')
                }
                
                pod_metrics.append(pod_metric)
                
                # Aggregate by namespace
                self._aggregate_namespace_stats(namespace_stats, namespace, usage, resource_info)
                
                # Aggregate by deployment
                if deployment_name:
                    self._aggregate_deployment_stats(deployment_stats, namespace, deployment_name, pod_name, usage, resource_info)
            
            # Calculate deployment averages and efficiency
            deployments = self._calculate_deployment_efficiency(deployment_stats)
            
            logger.info(f"✅ Successfully processed {len(pod_metrics)} pods, {len(deployments)} deployments")
            
            return {
                'pods': pod_metrics,
                'deployments': deployments,
                'namespaces': namespace_stats,
                'total_pods': len(pod_metrics),
                'total_deployments': len(deployments),
                'total_namespaces': len(namespace_stats),
                'timestamp': datetime.now().isoformat(),
                'data_source': 'kubectl_top_pods'
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing pod information JSON: {e}")
            return self._empty_pod_metrics()
        except Exception as e:
            logger.error(f"❌ Error processing pod metrics: {e}")
            return self._empty_pod_metrics()

    def _extract_deployment_name(self, pod: Dict) -> Optional[str]:
        """
        Extract deployment name from pod owner references
        
        Args:
            pod: Pod metadata dictionary
            
        Returns:
            Deployment name or None if not found
        """
        owner_refs = pod['metadata'].get('ownerReferences', [])
        
        for owner in owner_refs:
            if owner.get('kind') == 'ReplicaSet':
                # Extract deployment name from replicaset (remove hash suffix)
                rs_name = owner.get('name', '')
                if '-' in rs_name:
                    return '-'.join(rs_name.split('-')[:-1])
                return rs_name
            elif owner.get('kind') == 'Deployment':
                return owner.get('name', '')
        
        return None

    def _extract_pod_resources(self, pod: Dict) -> Dict[str, float]:
        """
        Extract resource requests and limits from pod containers
        
        Args:
            pod: Pod configuration dictionary
            
        Returns:
            Dictionary with aggregated resource values
        """
        containers = pod['spec'].get('containers', [])
        total_cpu_request = 0.0
        total_memory_request = 0.0
        total_cpu_limit = 0.0
        total_memory_limit = 0.0
        
        for container in containers:
            resources = container.get('resources', {})
            requests = resources.get('requests', {})
            limits = resources.get('limits', {})
            
            # Use shared parser for consistency
            total_cpu_request += self.parser.parse_cpu_safe(requests.get('cpu', '0'))
            total_memory_request += self.parser.parse_memory_safe(requests.get('memory', '0'))
            total_cpu_limit += self.parser.parse_cpu_safe(limits.get('cpu', '0')) if limits.get('cpu') else 0
            total_memory_limit += self.parser.parse_memory_safe(limits.get('memory', '0')) if limits.get('memory') else 0
        
        return {
            'cpu_request': total_cpu_request,
            'memory_request': total_memory_request,
            'cpu_limit': total_cpu_limit,
            'memory_limit': total_memory_limit
        }

    def _aggregate_namespace_stats(self, namespace_stats: Dict, namespace: str, usage: Dict, resources: Dict):
        """Aggregate statistics by namespace"""
        if namespace not in namespace_stats:
            namespace_stats[namespace] = {
                'pod_count': 0,
                'total_cpu_usage': 0.0,
                'total_memory_usage': 0.0,
                'total_cpu_request': 0.0,
                'total_memory_request': 0.0
            }
        
        ns_stats = namespace_stats[namespace]
        ns_stats['pod_count'] += 1
        ns_stats['total_cpu_usage'] += usage['cpu_usage_cores']
        ns_stats['total_memory_usage'] += usage['memory_usage_bytes']
        ns_stats['total_cpu_request'] += resources['cpu_request']
        ns_stats['total_memory_request'] += resources['memory_request']

    def _aggregate_deployment_stats(self, deployment_stats: Dict, namespace: str, deployment_name: str, 
                                  pod_name: str, usage: Dict, resources: Dict):
        """Aggregate statistics by deployment"""
        deploy_key = f"{namespace}/{deployment_name}"
        
        if deploy_key not in deployment_stats:
            deployment_stats[deploy_key] = {
                'namespace': namespace,
                'deployment': deployment_name,
                'pod_count': 0,
                'total_cpu_usage': 0.0,
                'total_memory_usage': 0.0,
                'total_cpu_request': 0.0,
                'total_memory_request': 0.0,
                'pods': []
            }
        
        deploy_stats = deployment_stats[deploy_key]
        deploy_stats['pod_count'] += 1
        deploy_stats['total_cpu_usage'] += usage['cpu_usage_cores']
        deploy_stats['total_memory_usage'] += usage['memory_usage_bytes']
        deploy_stats['total_cpu_request'] += resources['cpu_request']
        deploy_stats['total_memory_request'] += resources['memory_request']
        deploy_stats['pods'].append(pod_name)

    def _calculate_deployment_efficiency(self, deployment_stats: Dict) -> List[Dict]:
        """
        Calculate efficiency metrics for each deployment
        
        Args:
            deployment_stats: Raw deployment statistics
            
        Returns:
            List of deployment efficiency metrics
        """
        deployments = []
        
        for deploy_key, stats in deployment_stats.items():
            # Calculate average utilization percentages
            avg_cpu_usage = (stats['total_cpu_usage'] / stats['total_cpu_request'] * 100) if stats['total_cpu_request'] > 0 else 0
            avg_memory_usage = (stats['total_memory_usage'] / stats['total_memory_request'] * 100) if stats['total_memory_request'] > 0 else 0
            
            # Calculate resource gaps (optimization potential)
            cpu_gap = max(0, round(100 - avg_cpu_usage, 1))
            memory_gap = max(0, round(100 - avg_memory_usage, 1))
            
            # Determine optimization opportunities
            hpa_candidate = avg_cpu_usage < 70 or avg_memory_usage < 75
            over_provisioned = cpu_gap > 30 or memory_gap > 30
            
            deployments.append({
                'name': stats['deployment'],
                'namespace': stats['namespace'],
                'pod_count': stats['pod_count'],
                'cpu_usage_avg': round(avg_cpu_usage, 1),
                'memory_usage_avg': round(avg_memory_usage, 1),
                'total_cpu_cores': round(stats['total_cpu_usage'], 3),
                'total_memory_gb': round(stats['total_memory_usage'] / (1024**3), 2),
                'cpu_request_cores': round(stats['total_cpu_request'], 3),
                'memory_request_gb': round(stats['total_memory_request'] / (1024**3), 2),
                'cpu_gap': cpu_gap,
                'memory_gap': memory_gap,
                'optimization_potential': {
                    'hpa_candidate': hpa_candidate,
                    'over_provisioned': over_provisioned,
                    'right_sizing_needed': cpu_gap > 20 or memory_gap > 20
                }
            })
        
        # Sort by highest optimization potential first
        deployments.sort(key=lambda x: x['cpu_gap'] + x['memory_gap'], reverse=True)
        return deployments

    def _empty_pod_metrics(self) -> Dict[str, Any]:
        """Return empty pod metrics structure"""
        return {
            'pods': [],
            'deployments': [],
            'namespaces': {},
            'total_pods': 0,
            'total_deployments': 0,
            'total_namespaces': 0,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'unavailable'
        }

    # ------------------------------------------------------------------------
    # HPA METRICS COLLECTION
    # ------------------------------------------------------------------------
    
    def get_hpa_metrics(self) -> Dict[str, Any]:
        """
        Collect Horizontal Pod Autoscaler metrics and configurations
        
        Returns:
            Dictionary containing HPA status, configurations, and scaling activity
        """
        logger.info("📊 Fetching HPA metrics...")
        
        try:
            # Get HPA configurations and status
            hpa_list = self.execute_kubectl_command("kubectl get hpa --all-namespaces -o json")
            if not hpa_list:
                logger.warning("⚠️ Could not fetch HPA information")
                return self._empty_hpa_metrics()
            
            return self._process_hpa_metrics(hpa_list)
            
        except Exception as e:
            logger.error(f"❌ Error fetching HPA metrics: {e}")
            return self._empty_hpa_metrics()
    
    def _process_hpa_metrics(self, hpa_json: str) -> Dict[str, Any]:
        """
        Process HPA configurations into analysis-ready format
        
        Args:
            hpa_json: Raw HPA data in JSON format
            
        Returns:
            Processed HPA metrics dictionary
        """
        try:
            hpa_data = json.loads(hpa_json)
            hpa_metrics = []
            
            for hpa in hpa_data.get('items', []):
                namespace = hpa['metadata']['namespace']
                name = hpa['metadata']['name']
                
                spec = hpa.get('spec', {})
                status = hpa.get('status', {})
                
                # Get scaling target information
                scale_target = spec.get('scaleTargetRef', {})
                target_kind = scale_target.get('kind', '')
                target_name = scale_target.get('name', '')
                
                # Get replica information
                current_replicas = status.get('currentReplicas', 0)
                desired_replicas = status.get('desiredReplicas', 0)
                min_replicas = spec.get('minReplicas', 1)
                max_replicas = spec.get('maxReplicas', 10)
                
                # Process metrics configuration
                metrics_config = self._process_hpa_metrics_config(spec.get('metrics', []), status.get('currentMetrics', []))
                
                # Get scaling status
                conditions = status.get('conditions', [])
                scaling_active = any(c.get('type') == 'ScalingActive' and c.get('status') == 'True' for c in conditions)
                scaling_limited = any(c.get('type') == 'ScalingLimited' and c.get('status') == 'True' for c in conditions)
                
                # Calculate efficiency metrics
                replica_efficiency = (current_replicas / max_replicas * 100) if max_replicas > 0 else 0
                scaling_headroom = max_replicas - current_replicas
                
                hpa_metrics.append({
                    'namespace': namespace,
                    'name': name,
                    'target_kind': target_kind,
                    'target_name': target_name,
                    'current_replicas': current_replicas,
                    'desired_replicas': desired_replicas,
                    'min_replicas': min_replicas,
                    'max_replicas': max_replicas,
                    'replica_efficiency': round(replica_efficiency, 1),
                    'scaling_headroom': scaling_headroom,
                    'metrics_config': metrics_config,
                    'scaling_active': scaling_active,
                    'scaling_limited': scaling_limited,
                    'last_scale_time': status.get('lastScaleTime'),
                    'conditions': conditions,
                    # Analysis indicators
                    'memory_hpa_candidate': not any(m.get('resource_name') == 'memory' for m in metrics_config),
                    'under_utilized': replica_efficiency < 60,
                    'over_provisioned': scaling_headroom > current_replicas
                })
            
            logger.info(f"✅ Successfully processed {len(hpa_metrics)} HPA configurations")
            
            return {
                'hpas': hpa_metrics,
                'total_hpas': len(hpa_metrics),
                'memory_hpa_opportunities': sum(1 for hpa in hpa_metrics if hpa['memory_hpa_candidate']),
                'under_utilized_hpas': sum(1 for hpa in hpa_metrics if hpa['under_utilized']),
                'timestamp': datetime.now().isoformat(),
                'data_source': 'kubectl_get_hpa'
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing HPA information JSON: {e}")
            return self._empty_hpa_metrics()
        except Exception as e:
            logger.error(f"❌ Error processing HPA metrics: {e}")
            return self._empty_hpa_metrics()

    def _process_hpa_metrics_config(self, metrics_spec: List, current_metrics: List) -> List[Dict]:
        """Process HPA metrics configuration"""
        metric_configs = []
        
        for i, metric in enumerate(metrics_spec):
            metric_type = metric.get('type', '')
            metric_config = {'type': metric_type}
            
            if metric_type == 'Resource':
                resource = metric.get('resource', {})
                metric_config.update({
                    'resource_name': resource.get('name', ''),
                    'target_type': resource.get('target', {}).get('type', ''),
                    'target_value': resource.get('target', {}).get('averageUtilization', 0)
                })
                
                # Get current utilization if available
                if i < len(current_metrics) and current_metrics[i].get('type') == 'Resource':
                    current_resource = current_metrics[i].get('resource', {})
                    metric_config['current_value'] = current_resource.get('current', {}).get('averageUtilization', 0)
            
            metric_configs.append(metric_config)
        
        return metric_configs

    def _empty_hpa_metrics(self) -> Dict[str, Any]:
        """Return empty HPA metrics structure"""
        return {
            'hpas': [],
            'total_hpas': 0,
            'memory_hpa_opportunities': 0,
            'under_utilized_hpas': 0,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'unavailable'
        }

    # ------------------------------------------------------------------------
    # STORAGE METRICS COLLECTION
    # ------------------------------------------------------------------------
    
    def get_storage_metrics(self) -> Dict[str, Any]:
        """
        Collect storage usage, PV/PVC information, and storage class analysis
        
        Returns:
            Dictionary containing storage metrics and optimization opportunities
        """
        logger.info("📊 Fetching storage metrics...")
        
        try:
            # Get Persistent Volumes and Claims
            pv_info = self.execute_kubectl_command("kubectl get pv -o json")
            pvc_info = self.execute_kubectl_command("kubectl get pvc --all-namespaces -o json")
            
            return self._process_storage_metrics(pv_info, pvc_info)
            
        except Exception as e:
            logger.error(f"❌ Error fetching storage metrics: {e}")
            return self._empty_storage_metrics()
    
    def _process_storage_metrics(self, pv_json: Optional[str], pvc_json: Optional[str]) -> Dict[str, Any]:
        """
        Process storage information into analysis-ready format
        
        Args:
            pv_json: Persistent Volume data in JSON format
            pvc_json: Persistent Volume Claim data in JSON format
            
        Returns:
            Processed storage metrics dictionary
        """
        storage_metrics = {
            'persistent_volumes': [],
            'persistent_volume_claims': [],
            'storage_classes': set(),
            'total_storage_requested': 0,
            'total_storage_capacity': 0,
            'unbound_pvcs': 0,
            'optimization_opportunities': []
        }
        
        try:
            # Process Persistent Volumes
            if pv_json:
                pv_data = json.loads(pv_json)
                for pv in pv_data.get('items', []):
                    pv_metric = self._process_single_pv(pv)
                    storage_metrics['persistent_volumes'].append(pv_metric)
                    storage_metrics['storage_classes'].add(pv_metric['storage_class'])
                    storage_metrics['total_storage_capacity'] += pv_metric['capacity_bytes']
            
            # Process Persistent Volume Claims
            if pvc_json:
                pvc_data = json.loads(pvc_json)
                for pvc in pvc_data.get('items', []):
                    pvc_metric = self._process_single_pvc(pvc)
                    storage_metrics['persistent_volume_claims'].append(pvc_metric)
                    storage_metrics['storage_classes'].add(pvc_metric['storage_class'])
                    storage_metrics['total_storage_requested'] += pvc_metric['requested_bytes']
                    
                    if pvc_metric['status'] != 'Bound':
                        storage_metrics['unbound_pvcs'] += 1
            
            # Convert storage classes set to list
            storage_metrics['storage_classes'] = list(storage_metrics['storage_classes'])
            
            # Calculate storage efficiency and optimization opportunities
            storage_metrics.update(self._calculate_storage_efficiency(storage_metrics))
            
            storage_metrics['timestamp'] = datetime.now().isoformat()
            storage_metrics['data_source'] = 'kubectl_get_pv_pvc'
            
            logger.info(f"✅ Successfully processed storage metrics: "
                       f"{len(storage_metrics['persistent_volumes'])} PVs, "
                       f"{len(storage_metrics['persistent_volume_claims'])} PVCs")
            
            return storage_metrics
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing storage information JSON: {e}")
            return storage_metrics
        except Exception as e:
            logger.error(f"❌ Error processing storage metrics: {e}")
            return storage_metrics

    def _process_single_pv(self, pv: Dict) -> Dict:
        """Process a single Persistent Volume"""
        name = pv['metadata']['name']
        capacity = pv['spec'].get('capacity', {}).get('storage', '0Gi')
        storage_class = pv['spec'].get('storageClassName', 'default')
        access_modes = pv['spec'].get('accessModes', [])
        status = pv['status'].get('phase', 'Unknown')
        
        capacity_bytes = self.parser.parse_memory_safe(capacity)  # Using shared parser
        
        return {
            'name': name,
            'capacity': capacity,
            'capacity_bytes': capacity_bytes,
            'storage_class': storage_class,
            'access_modes': access_modes,
            'status': status,
            'reclaim_policy': pv['spec'].get('persistentVolumeReclaimPolicy', 'Retain')
        }

    def _process_single_pvc(self, pvc: Dict) -> Dict:
        """Process a single Persistent Volume Claim"""
        namespace = pvc['metadata']['namespace']
        name = pvc['metadata']['name']
        
        spec = pvc.get('spec', {})
        status = pvc.get('status', {})
        
        requested = spec.get('resources', {}).get('requests', {}).get('storage', '0Gi')
        storage_class = spec.get('storageClassName', 'default')
        access_modes = spec.get('accessModes', [])
        pvc_status = status.get('phase', 'Unknown')
        
        requested_bytes = self.parser.parse_memory_safe(requested)  # Using shared parser
        
        return {
            'namespace': namespace,
            'name': name,
            'requested': requested,
            'requested_bytes': requested_bytes,
            'storage_class': storage_class,
            'access_modes': access_modes,
            'status': pvc_status,
            'volume_name': status.get('volumeName', '')
        }

    def _calculate_storage_efficiency(self, storage_metrics: Dict) -> Dict:
        """Calculate storage efficiency and optimization opportunities"""
        total_capacity = storage_metrics['total_storage_capacity']
        total_requested = storage_metrics['total_storage_requested']
        
        # Calculate utilization
        utilization_pct = (total_requested / total_capacity * 100) if total_capacity > 0 else 0
        
        # Find optimization opportunities
        optimization_opportunities = []
        
        if utilization_pct < 50:
            optimization_opportunities.append({
                'type': 'over_provisioned',
                'description': f'Storage utilization only {utilization_pct:.1f}% - consider smaller volumes',
                'potential_savings': 'High'
            })
        
        if storage_metrics['unbound_pvcs'] > 0:
            optimization_opportunities.append({
                'type': 'unbound_pvcs',
                'description': f'{storage_metrics["unbound_pvcs"]} unbound PVCs found - cleanup opportunity',
                'potential_savings': 'Medium'
            })
        
        # Check for premium storage optimization
        premium_volumes = [pv for pv in storage_metrics['persistent_volumes'] 
                          if 'premium' in pv['storage_class'].lower()]
        if premium_volumes:
            optimization_opportunities.append({
                'type': 'storage_class_optimization',
                'description': f'{len(premium_volumes)} premium storage volumes - review if standard SSD sufficient',
                'potential_savings': 'High'
            })
        
        return {
            'storage_utilization_pct': round(utilization_pct, 1),
            'storage_efficiency_score': min(100, utilization_pct),
            'optimization_opportunities': optimization_opportunities,
            'total_optimization_potential': len(optimization_opportunities)
        }

    def _empty_storage_metrics(self) -> Dict[str, Any]:
        """Return empty storage metrics structure"""
        return {
            'persistent_volumes': [],
            'persistent_volume_claims': [],
            'storage_classes': [],
            'total_storage_requested': 0,
            'total_storage_capacity': 0,
            'unbound_pvcs': 0,
            'storage_utilization_pct': 0,
            'storage_efficiency_score': 0,
            'optimization_opportunities': [],
            'total_optimization_potential': 0,
            'timestamp': datetime.now().isoformat(),
            'data_source': 'unavailable'
        }

    # ------------------------------------------------------------------------
    # COMPREHENSIVE METRICS COLLECTION
    # ------------------------------------------------------------------------
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """
        MAIN INTEGRATION METHOD: Collect all metrics in one comprehensive operation
        
        Returns:
            Complete metrics dataset formatted for integration with cost analysis
        """
        logger.info("🚀 Fetching comprehensive real-time AKS metrics...")
        
        start_time = datetime.now()
        
        # Verify connection first
        if not self.verify_cluster_connection():
            return {
                'status': 'error',
                'message': 'Failed to connect to AKS cluster',
                'timestamp': start_time.isoformat()
            }
        
        try:
            # Collect all metric types
            logger.info("📊 Collecting node metrics...")
            node_metrics = self.get_node_metrics()
            
            logger.info("📊 Collecting pod metrics...")
            pod_metrics = self.get_pod_metrics()
            
            logger.info("📊 Collecting HPA metrics...")
            hpa_metrics = self.get_hpa_metrics()
            
            logger.info("📊 Collecting storage metrics...")
            storage_metrics = self.get_storage_metrics()
            
            # Calculate cluster-wide statistics
            cluster_stats = self._calculate_cluster_statistics(node_metrics, pod_metrics)
            
            # Format for integration with algorithmic_cost_analyzer.py
            comprehensive_metrics = {
                'metadata': {
                    'cluster_name': self.cluster_name,
                    'resource_group': self.resource_group,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Real-time AKS Cluster Metrics',
                    'data_source': 'kubectl via az aks command invoke',
                    'collection_time_ms': int((datetime.now() - start_time).total_seconds() * 1000),
                    'integration_ready': True
                },
                
                # Core metrics for algorithmic analysis
                'nodes': node_metrics.get('nodes', []),
                'deployments': self._format_deployments_for_analysis(pod_metrics.get('deployments', [])),
                'cluster_stats': cluster_stats,
                
                # Additional analysis data
                'hpa_data': hpa_metrics,
                'storage_data': storage_metrics,
                'pod_data': pod_metrics,
                
                # Summary statistics
                'total_nodes': node_metrics.get('total_nodes', 0),
                'ready_nodes': node_metrics.get('ready_nodes', 0),
                'total_pods': pod_metrics.get('total_pods', 0),
                'total_deployments': pod_metrics.get('total_deployments', 0),
                'total_hpas': hpa_metrics.get('total_hpas', 0),
                
                # Status indicators
                'status': 'success',
                'data_quality': 'high' if node_metrics['nodes'] and pod_metrics['pods'] else 'medium'
            }
            
            collection_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Successfully collected comprehensive metrics in {collection_time:.2f}s")
            
            return comprehensive_metrics
            
        except Exception as e:
            logger.error(f"❌ Error collecting comprehensive metrics: {e}")
            return {
                'status': 'error',
                'message': f'Error collecting metrics: {str(e)}',
                'timestamp': start_time.isoformat()
            }
    
    def _format_deployments_for_analysis(self, deployments: List[Dict]) -> List[Dict]:
        """
        Format deployment data for integration with cost analysis algorithms
        
        Args:
            deployments: Raw deployment metrics
            
        Returns:
            Deployments formatted for algorithmic analysis
        """
        formatted_deployments = []
        
        for deploy in deployments:
            # Create usage pattern data (current point in time)
            usage_pattern = [
                {
                    'time': 'Current', 
                    'cpu_usage': deploy['cpu_usage_avg'], 
                    'memory_usage': deploy['memory_usage_avg']
                }
            ]
            
            formatted_deployments.append({
                'name': deploy['name'],
                'namespace': deploy['namespace'],
                'cpu_usage_avg': deploy['cpu_usage_avg'],
                'memory_usage_avg': deploy['memory_usage_avg'],
                'cpu_usage_pattern': usage_pattern,
                'replica_count': deploy['pod_count'],
                'cpu_gap': deploy['cpu_gap'],
                'memory_gap': deploy['memory_gap'],
                'optimization_potential': deploy.get('optimization_potential', {}),
                # Additional fields for algorithm integration
                'hpa_suitability': deploy['cpu_gap'] > 20 or deploy['memory_gap'] > 20,
                'efficiency_score': 100 - ((deploy['cpu_gap'] + deploy['memory_gap']) / 2)
            })
        
        return formatted_deployments
    
    def _calculate_cluster_statistics(self, node_metrics: Dict, pod_metrics: Dict) -> Dict[str, Any]:
        """
        Calculate cluster-wide statistics for optimization analysis
        
        Args:
            node_metrics: Node metrics data
            pod_metrics: Pod metrics data
            
        Returns:
            Cluster-wide statistics dictionary
        """
        nodes = node_metrics.get('nodes', [])
        deployments = pod_metrics.get('deployments', [])
        
        if not nodes:
            return {}
        
        # Node-level statistics
        total_cpu_capacity = sum(n['cpu_allocatable_cores'] for n in nodes)
        total_memory_capacity = sum(n['memory_allocatable_bytes'] for n in nodes)
        total_cpu_usage = sum(n['cpu_usage_cores'] for n in nodes)
        total_memory_usage = sum(n['memory_usage_bytes'] for n in nodes)
        
        # Deployment-level statistics
        if deployments:
            avg_cpu_gap = sum(d['cpu_gap'] for d in deployments) / len(deployments)
            avg_memory_gap = sum(d['memory_gap'] for d in deployments) / len(deployments)
            over_provisioned_deployments = sum(1 for d in deployments if d['cpu_gap'] > 25 or d['memory_gap'] > 25)
            hpa_candidates = sum(1 for d in deployments if d.get('optimization_potential', {}).get('hpa_candidate', False))
        else:
            avg_cpu_gap = 0
            avg_memory_gap = 0
            over_provisioned_deployments = 0
            hpa_candidates = 0
        
        return {
            # Cluster capacity and usage
            'total_cpu_capacity_cores': round(total_cpu_capacity, 2),
            'total_memory_capacity_gb': round(total_memory_capacity / (1024**3), 2),
            'cluster_cpu_usage_pct': round((total_cpu_usage / total_cpu_capacity * 100) if total_cpu_capacity > 0 else 0, 1),
            'cluster_memory_usage_pct': round((total_memory_usage / total_memory_capacity * 100) if total_memory_capacity > 0 else 0, 1),
            
            # Optimization indicators
            'average_cpu_gap': round(avg_cpu_gap, 1),
            'average_memory_gap': round(avg_memory_gap, 1),
            'over_provisioned_deployments': over_provisioned_deployments,
            'hpa_candidates': hpa_candidates,
            'optimization_opportunity_pct': round((over_provisioned_deployments / len(deployments) * 100) if deployments else 0, 1),
            
            # Efficiency scores
            'cluster_efficiency_score': round(100 - ((avg_cpu_gap + avg_memory_gap) / 2), 1),
            'resource_utilization_efficiency': round(((total_cpu_usage / total_cpu_capacity) + (total_memory_usage / total_memory_capacity)) / 2 * 100, 1) if total_cpu_capacity > 0 and total_memory_capacity > 0 else 0
        }

# ============================================================================
# INTEGRATION NOTES AND MAIN FUNCTION
# ============================================================================

def get_aks_realtime_metrics(resource_group: str, cluster_name: str) -> Dict[str, Any]:
    """
    MAIN INTEGRATION FUNCTION for app.py and other modules
    
    Args:
        resource_group: Azure resource group name
        cluster_name: AKS cluster name
        
    Returns:
        Comprehensive real-time metrics ready for cost analysis integration
        
    INTEGRATION: Used by app.py alongside pod_cost_analyzer.py results
    """
    fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name)
    return fetcher.get_comprehensive_metrics()

# ============================================================================
# INTEGRATION DOCUMENTATION
# ============================================================================

"""
INTEGRATION WITH pod_cost_analyzer.py:

This file (aks-realtime-metrics.py) provides CURRENT USAGE DATA:
- Real-time CPU/memory utilization per node/pod
- Current deployment resource consumption patterns
- HPA configurations and scaling behavior
- Storage usage and allocation patterns

The pod_cost_analyzer.py provides COST DISTRIBUTION:
- How actual billing costs map to namespaces/workloads
- Cost attribution for financial analysis
- Historical cost patterns from Azure billing

SHARED COMPONENTS:
- KubernetesParsingUtils: Common CPU/memory parsing logic
- kubectl execution patterns: Consistent command execution
- Error handling: Unified error reporting approach

DATA FLOW INTEGRATION:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ Azure Billing   │    │ AKS Cluster      │    │ Optimization        │
│ (Actual Costs)  │    │ (Current Usage)  │    │ Algorithms          │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                       │                        │
         ▼                       ▼                        │
┌─────────────────┐    ┌──────────────────┐              │
│pod_cost_analyzer│    │aks-realtime-     │              │
│.py              │    │metrics.py        │              │
│                 │    │                  │              │
│• Cost breakdown │    │• Usage patterns  │              │
│• Namespace costs│    │• Node metrics    │              │
│• Workload costs │    │• Pod utilization │              │
└─────────────────┘    └──────────────────┘              │
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 ▼
                    ┌──────────────────────┐
                    │ algorithmic_cost_    │
                    │ analyzer.py          │
                    │                      │
                    │ • Optimization calc  │
                    │ • HPA recommendations│
                    │ • Right-sizing       │
                    │ • Savings potential  │
                    └──────────────────────┘

USAGE EXAMPLES:

# Get real-time metrics for optimization
metrics = get_aks_realtime_metrics("my-rg", "my-cluster")

# Get cost distribution 
from pod_cost_analyzer import get_enhanced_pod_cost_breakdown
costs = get_enhanced_pod_cost_breakdown("my-rg", "my-cluster", 1000.0)

# Combine for comprehensive analysis
from algorithmic_cost_analyzer import integrate_consistent_analysis
results = integrate_consistent_analysis("my-rg", "my-cluster", 
                                       cost_data=billing_data,
                                       metrics_data=metrics,
                                       pod_data=costs)
"""