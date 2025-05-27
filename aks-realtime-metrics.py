"""
AKS Real-time Metrics Fetcher
============================
Fetches real-time metrics directly from AKS cluster using kubectl commands
via Azure CLI's 'az aks command invoke' feature for private clusters.
"""

import subprocess
import json
import logging
import yaml
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AKSRealTimeMetricsFetcher:
    """Fetches real-time metrics directly from AKS cluster using kubectl commands"""
    
    def __init__(self, resource_group: str, cluster_name: str):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.connection_verified = False
        
    def verify_cluster_connection(self) -> bool:
        """Verify we can connect to the AKS cluster"""
        try:
            logger.info(f"Verifying connection to AKS cluster {self.cluster_name}")
            
            cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', 'kubectl cluster-info'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
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
        except Exception as e:
            logger.error(f"❌ Unexpected error during connection verification: {e}")
            return False
    
    def execute_kubectl_command(self, kubectl_cmd: str) -> Optional[str]:
        """Execute a kubectl command via az aks command invoke"""
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
            
            logger.debug(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
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
    
    def get_node_metrics(self) -> Dict[str, Any]:
        """Get real-time node resource usage metrics"""
        logger.info("📊 Fetching real-time node metrics...")
        
        # Get node resource usage
        top_nodes = self.execute_kubectl_command("kubectl top nodes --no-headers")
        if not top_nodes:
            logger.warning("⚠️ Could not fetch node metrics")
            return {}
        
        # Get node capacity and allocatable resources
        node_info = self.execute_kubectl_command("kubectl get nodes -o json")
        if not node_info:
            logger.warning("⚠️ Could not fetch node information")
            return {}
        
        try:
            nodes_data = json.loads(node_info)
            node_metrics = []
            
            # Parse top nodes output
            top_lines = top_nodes.strip().split('\n')
            node_usage = {}
            
            for line in top_lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 5:
                        node_name = parts[0]
                        cpu_usage = self._parse_cpu_value(parts[1])
                        memory_usage = self._parse_memory_value(parts[3])
                        node_usage[node_name] = {
                            'cpu_usage': cpu_usage,
                            'memory_usage': memory_usage
                        }
            
            # Combine with node capacity information
            for node in nodes_data.get('items', []):
                node_name = node['metadata']['name']
                if node_name not in node_usage:
                    continue
                
                # Get allocatable resources
                allocatable = node['status'].get('allocatable', {})
                cpu_allocatable = self._parse_cpu_value(allocatable.get('cpu', '0'))
                memory_allocatable = self._parse_memory_value(allocatable.get('memory', '0Ki'))
                
                # Calculate utilization percentages
                usage = node_usage[node_name]
                cpu_usage_pct = (usage['cpu_usage'] / cpu_allocatable * 100) if cpu_allocatable > 0 else 0
                memory_usage_pct = (usage['memory_usage'] / memory_allocatable * 100) if memory_allocatable > 0 else 0
                
                # Get node conditions and taints
                conditions = node['status'].get('conditions', [])
                ready_condition = next((c for c in conditions if c['type'] == 'Ready'), {})
                is_ready = ready_condition.get('status') == 'True'
                
                node_metrics.append({
                    'name': node_name,
                    'cpu_usage_pct': round(cpu_usage_pct, 1),
                    'memory_usage_pct': round(memory_usage_pct, 1),
                    'cpu_allocatable': cpu_allocatable,
                    'memory_allocatable': memory_allocatable,
                    'cpu_usage_cores': usage['cpu_usage'],
                    'memory_usage_bytes': usage['memory_usage'],
                    'ready': is_ready,
                    'node_info': {
                        'kernel_version': node['status']['nodeInfo'].get('kernelVersion', ''),
                        'os_image': node['status']['nodeInfo'].get('osImage', ''),
                        'container_runtime': node['status']['nodeInfo'].get('containerRuntimeVersion', '')
                    }
                })
            
            logger.info(f"✅ Successfully fetched metrics for {len(node_metrics)} nodes")
            return {
                'nodes': node_metrics,
                'total_nodes': len(node_metrics),
                'ready_nodes': sum(1 for n in node_metrics if n['ready']),
                'timestamp': datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing node information JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Error processing node metrics: {e}")
            return {}
    
    def get_pod_metrics(self) -> Dict[str, Any]:
        """Get real-time pod resource usage metrics"""
        logger.info("📊 Fetching real-time pod metrics...")
        
        # Get pod resource usage
        top_pods = self.execute_kubectl_command("kubectl top pods --all-namespaces --no-headers")
        if not top_pods:
            logger.warning("⚠️ Could not fetch pod metrics")
            return {}
        
        # Get pod information with resource requests/limits
        pod_info = self.execute_kubectl_command("kubectl get pods --all-namespaces -o json")
        if not pod_info:
            logger.warning("⚠️ Could not fetch pod information")
            return {}
        
        try:
            pods_data = json.loads(pod_info)
            pod_metrics = []
            
            # Parse top pods output
            top_lines = top_pods.strip().split('\n')
            pod_usage = {}
            
            for line in top_lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        namespace = parts[0]
                        pod_name = parts[1]
                        cpu_usage = self._parse_cpu_value(parts[2])
                        memory_usage = self._parse_memory_value(parts[3])
                        
                        pod_key = f"{namespace}/{pod_name}"
                        pod_usage[pod_key] = {
                            'cpu_usage': cpu_usage,
                            'memory_usage': memory_usage
                        }
            
            # Process pod information
            namespace_stats = {}
            deployment_stats = {}
            
            for pod in pods_data.get('items', []):
                namespace = pod['metadata']['namespace']
                pod_name = pod['metadata']['name']
                pod_key = f"{namespace}/{pod_name}"
                
                if pod_key not in pod_usage:
                    continue
                
                # Get owner reference (deployment, replicaset, etc.)
                owner_refs = pod['metadata'].get('ownerReferences', [])
                deployment_name = None
                
                for owner in owner_refs:
                    if owner.get('kind') == 'ReplicaSet':
                        # Extract deployment name from replicaset
                        rs_name = owner.get('name', '')
                        deployment_name = '-'.join(rs_name.split('-')[:-1]) if '-' in rs_name else rs_name
                        break
                
                # Get resource requests and limits
                containers = pod['spec'].get('containers', [])
                total_cpu_request = 0
                total_memory_request = 0
                total_cpu_limit = 0
                total_memory_limit = 0
                
                for container in containers:
                    resources = container.get('resources', {})
                    requests = resources.get('requests', {})
                    limits = resources.get('limits', {})
                    
                    total_cpu_request += self._parse_cpu_value(requests.get('cpu', '0'))
                    total_memory_request += self._parse_memory_value(requests.get('memory', '0'))
                    total_cpu_limit += self._parse_cpu_value(limits.get('cpu', '0')) if limits.get('cpu') else 0
                    total_memory_limit += self._parse_memory_value(limits.get('memory', '0')) if limits.get('memory') else 0
                
                usage = pod_usage[pod_key]
                
                pod_metric = {
                    'namespace': namespace,
                    'pod_name': pod_name,
                    'deployment': deployment_name,
                    'cpu_usage': usage['cpu_usage'],
                    'memory_usage': usage['memory_usage'],
                    'cpu_request': total_cpu_request,
                    'memory_request': total_memory_request,
                    'cpu_limit': total_cpu_limit,
                    'memory_limit': total_memory_limit,
                    'cpu_usage_pct': (usage['cpu_usage'] / total_cpu_request * 100) if total_cpu_request > 0 else 0,
                    'memory_usage_pct': (usage['memory_usage'] / total_memory_request * 100) if total_memory_request > 0 else 0,
                    'status': pod['status'].get('phase', 'Unknown')
                }
                
                pod_metrics.append(pod_metric)
                
                # Aggregate by namespace
                if namespace not in namespace_stats:
                    namespace_stats[namespace] = {
                        'pod_count': 0,
                        'total_cpu_usage': 0,
                        'total_memory_usage': 0,
                        'total_cpu_request': 0,
                        'total_memory_request': 0
                    }
                
                ns_stats = namespace_stats[namespace]
                ns_stats['pod_count'] += 1
                ns_stats['total_cpu_usage'] += usage['cpu_usage']
                ns_stats['total_memory_usage'] += usage['memory_usage']
                ns_stats['total_cpu_request'] += total_cpu_request
                ns_stats['total_memory_request'] += total_memory_request
                
                # Aggregate by deployment
                if deployment_name:
                    deploy_key = f"{namespace}/{deployment_name}"
                    if deploy_key not in deployment_stats:
                        deployment_stats[deploy_key] = {
                            'namespace': namespace,
                            'deployment': deployment_name,
                            'pod_count': 0,
                            'total_cpu_usage': 0,
                            'total_memory_usage': 0,
                            'total_cpu_request': 0,
                            'total_memory_request': 0,
                            'pods': []
                        }
                    
                    deploy_stats = deployment_stats[deploy_key]
                    deploy_stats['pod_count'] += 1
                    deploy_stats['total_cpu_usage'] += usage['cpu_usage']
                    deploy_stats['total_memory_usage'] += usage['memory_usage']
                    deploy_stats['total_cpu_request'] += total_cpu_request
                    deploy_stats['total_memory_request'] += total_memory_request
                    deploy_stats['pods'].append(pod_name)
            
            # Calculate averages and percentages for deployments
            deployments = []
            for deploy_key, stats in deployment_stats.items():
                avg_cpu_usage = (stats['total_cpu_usage'] / stats['total_cpu_request'] * 100) if stats['total_cpu_request'] > 0 else 0
                avg_memory_usage = (stats['total_memory_usage'] / stats['total_memory_request'] * 100) if stats['total_memory_request'] > 0 else 0
                
                deployments.append({
                    'name': stats['deployment'],
                    'namespace': stats['namespace'],
                    'pod_count': stats['pod_count'],
                    'cpu_usage_avg': round(avg_cpu_usage, 1),
                    'memory_usage_avg': round(avg_memory_usage, 1),
                    'total_cpu_cores': round(stats['total_cpu_usage'], 3),
                    'total_memory_mb': round(stats['total_memory_usage'] / (1024*1024), 1),
                    'cpu_request_cores': round(stats['total_cpu_request'], 3),
                    'memory_request_mb': round(stats['total_memory_request'] / (1024*1024), 1),
                    'cpu_gap': max(0, round(100 - avg_cpu_usage, 1)),
                    'memory_gap': max(0, round(100 - avg_memory_usage, 1))
                })
            
            logger.info(f"✅ Successfully processed {len(pod_metrics)} pods, {len(deployments)} deployments")
            
            return {
                'pods': pod_metrics,
                'deployments': deployments,
                'namespaces': namespace_stats,
                'total_pods': len(pod_metrics),
                'total_deployments': len(deployments),
                'timestamp': datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing pod information JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Error processing pod metrics: {e}")
            return {}
    
    def get_hpa_metrics(self) -> Dict[str, Any]:
        """Get Horizontal Pod Autoscaler metrics and configurations"""
        logger.info("📊 Fetching HPA metrics...")
        
        # Get HPA status
        hpa_list = self.execute_kubectl_command("kubectl get hpa --all-namespaces -o json")
        if not hpa_list:
            logger.warning("⚠️ Could not fetch HPA information")
            return {'hpas': [], 'total_hpas': 0}
        
        try:
            hpa_data = json.loads(hpa_list)
            hpa_metrics = []
            
            for hpa in hpa_data.get('items', []):
                namespace = hpa['metadata']['namespace']
                name = hpa['metadata']['name']
                
                spec = hpa.get('spec', {})
                status = hpa.get('status', {})
                
                # Get scaling target
                scale_target = spec.get('scaleTargetRef', {})
                target_kind = scale_target.get('kind', '')
                target_name = scale_target.get('name', '')
                
                # Get current/desired replicas
                current_replicas = status.get('currentReplicas', 0)
                desired_replicas = status.get('desiredReplicas', 0)
                min_replicas = spec.get('minReplicas', 1)
                max_replicas = spec.get('maxReplicas', 10)
                
                # Get metrics configuration
                metrics = spec.get('metrics', [])
                metric_configs = []
                current_metrics = status.get('currentMetrics', [])
                
                for i, metric in enumerate(metrics):
                    metric_type = metric.get('type', '')
                    metric_config = {'type': metric_type}
                    
                    if metric_type == 'Resource':
                        resource = metric.get('resource', {})
                        metric_config.update({
                            'resource_name': resource.get('name', ''),
                            'target_type': resource.get('target', {}).get('type', ''),
                            'target_value': resource.get('target', {}).get('averageUtilization', 0)
                        })
                        
                        # Get current utilization
                        if i < len(current_metrics) and current_metrics[i].get('type') == 'Resource':
                            current_resource = current_metrics[i].get('resource', {})
                            metric_config['current_value'] = current_resource.get('current', {}).get('averageUtilization', 0)
                    
                    metric_configs.append(metric_config)
                
                # Get scaling events/conditions
                conditions = status.get('conditions', [])
                scaling_active = any(c.get('type') == 'ScalingActive' and c.get('status') == 'True' for c in conditions)
                scaling_limited = any(c.get('type') == 'ScalingLimited' and c.get('status') == 'True' for c in conditions)
                
                hpa_metrics.append({
                    'namespace': namespace,
                    'name': name,
                    'target_kind': target_kind,
                    'target_name': target_name,
                    'current_replicas': current_replicas,
                    'desired_replicas': desired_replicas,
                    'min_replicas': min_replicas,
                    'max_replicas': max_replicas,
                    'metrics': metric_configs,
                    'scaling_active': scaling_active,
                    'scaling_limited': scaling_limited,
                    'last_scale_time': status.get('lastScaleTime'),
                    'conditions': conditions
                })
            
            logger.info(f"✅ Successfully fetched {len(hpa_metrics)} HPA configurations")
            
            return {
                'hpas': hpa_metrics,
                'total_hpas': len(hpa_metrics),
                'timestamp': datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing HPA information JSON: {e}")
            return {'hpas': [], 'total_hpas': 0}
        except Exception as e:
            logger.error(f"❌ Error processing HPA metrics: {e}")
            return {'hpas': [], 'total_hpas': 0}
    
    def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage usage and PV/PVC information"""
        logger.info("📊 Fetching storage metrics...")
        
        # Get Persistent Volumes
        pv_info = self.execute_kubectl_command("kubectl get pv -o json")
        pvc_info = self.execute_kubectl_command("kubectl get pvc --all-namespaces -o json")
        
        storage_metrics = {
            'persistent_volumes': [],
            'persistent_volume_claims': [],
            'storage_classes': set(),
            'total_storage_requested': 0,
            'total_storage_capacity': 0
        }
        
        try:
            # Process Persistent Volumes
            if pv_info:
                pv_data = json.loads(pv_info)
                for pv in pv_data.get('items', []):
                    name = pv['metadata']['name']
                    capacity = pv['spec'].get('capacity', {}).get('storage', '0Gi')
                    storage_class = pv['spec'].get('storageClassName', 'default')
                    access_modes = pv['spec'].get('accessModes', [])
                    status = pv['status'].get('phase', 'Unknown')
                    
                    capacity_bytes = self._parse_storage_value(capacity)
                    
                    storage_metrics['persistent_volumes'].append({
                        'name': name,
                        'capacity': capacity,
                        'capacity_bytes': capacity_bytes,
                        'storage_class': storage_class,
                        'access_modes': access_modes,
                        'status': status
                    })
                    
                    storage_metrics['storage_classes'].add(storage_class)
                    storage_metrics['total_storage_capacity'] += capacity_bytes
            
            # Process Persistent Volume Claims
            if pvc_info:
                pvc_data = json.loads(pvc_info)
                for pvc in pvc_data.get('items', []):
                    namespace = pvc['metadata']['namespace']
                    name = pvc['metadata']['name']
                    
                    spec = pvc.get('spec', {})
                    status = pvc.get('status', {})
                    
                    requested = spec.get('resources', {}).get('requests', {}).get('storage', '0Gi')
                    storage_class = spec.get('storageClassName', 'default')
                    access_modes = spec.get('accessModes', [])
                    pvc_status = status.get('phase', 'Unknown')
                    
                    requested_bytes = self._parse_storage_value(requested)
                    
                    storage_metrics['persistent_volume_claims'].append({
                        'namespace': namespace,
                        'name': name,
                        'requested': requested,
                        'requested_bytes': requested_bytes,
                        'storage_class': storage_class,
                        'access_modes': access_modes,
                        'status': pvc_status
                    })
                    
                    storage_metrics['storage_classes'].add(storage_class)
                    storage_metrics['total_storage_requested'] += requested_bytes
            
            storage_metrics['storage_classes'] = list(storage_metrics['storage_classes'])
            storage_metrics['timestamp'] = datetime.now().isoformat()
            
            logger.info(f"✅ Successfully fetched storage metrics: {len(storage_metrics['persistent_volumes'])} PVs, {len(storage_metrics['persistent_volume_claims'])} PVCs")
            
            return storage_metrics
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing storage information JSON: {e}")
            return storage_metrics
        except Exception as e:
            logger.error(f"❌ Error processing storage metrics: {e}")
            return storage_metrics
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get all metrics in one comprehensive call"""
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
            # Fetch all metrics
            node_metrics = self.get_node_metrics()
            pod_metrics = self.get_pod_metrics()
            hpa_metrics = self.get_hpa_metrics()
            storage_metrics = self.get_storage_metrics()
            
            # Calculate cluster-wide statistics
            cluster_stats = self._calculate_cluster_stats(node_metrics, pod_metrics)
            
            # Prepare comprehensive response in the same format as your existing structure
            comprehensive_metrics = {
                'metadata': {
                    'cluster_name': self.cluster_name,
                    'resource_group': self.resource_group,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Real-time AKS Cluster',
                    'data_source': 'kubectl via az aks command invoke',
                    'collection_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
                },
                'nodes': node_metrics.get('nodes', []),
                'deployments': self._format_deployments_for_analysis(pod_metrics.get('deployments', [])),
                'hpa_data': hpa_metrics,
                'storage_data': storage_metrics,
                'cluster_stats': cluster_stats,
                'pod_data': pod_metrics,
                'total_nodes': node_metrics.get('total_nodes', 0),
                'ready_nodes': node_metrics.get('ready_nodes', 0),
                'total_pods': pod_metrics.get('total_pods', 0),
                'total_deployments': pod_metrics.get('total_deployments', 0),
                'total_hpas': hpa_metrics.get('total_hpas', 0)
            }
            
            logger.info(f"✅ Successfully collected comprehensive metrics in {(datetime.now() - start_time).total_seconds():.2f}s")
            
            return comprehensive_metrics
            
        except Exception as e:
            logger.error(f"❌ Error collecting comprehensive metrics: {e}")
            return {
                'status': 'error',
                'message': f'Error collecting metrics: {str(e)}',
                'timestamp': start_time.isoformat()
            }
    
    def _format_deployments_for_analysis(self, deployments: List[Dict]) -> List[Dict]:
        """Format deployments data to match the expected analysis structure"""
        formatted_deployments = []
        
        for deploy in deployments:
            # Create CPU and memory usage patterns (simplified for real-time)
            cpu_pattern = [
                {'time': 'Current', 'cpu_usage': deploy['cpu_usage_avg'], 'memory_usage': deploy['memory_usage_avg']}
            ]
            
            formatted_deployments.append({
                'name': deploy['name'],
                'namespace': deploy['namespace'],
                'cpu_usage_avg': deploy['cpu_usage_avg'],
                'memory_usage_avg': deploy['memory_usage_avg'],
                'cpu_usage_pattern': cpu_pattern,
                'replica_count': deploy['pod_count'],
                'cpu_gap': deploy['cpu_gap'],
                'memory_gap': deploy['memory_gap'],
                'optimization_potential': {
                    'cpu_over_provisioned': deploy['cpu_gap'] > 30,
                    'memory_over_provisioned': deploy['memory_gap'] > 30,
                    'hpa_candidate': deploy['cpu_gap'] > 20 or deploy['memory_gap'] > 20
                }
            })
        
        return formatted_deployments
    
    def _calculate_cluster_stats(self, node_metrics: Dict, pod_metrics: Dict) -> Dict[str, Any]:
        """Calculate cluster-wide statistics"""
        nodes = node_metrics.get('nodes', [])
        deployments = pod_metrics.get('deployments', [])
        
        if not nodes:
            return {}
        
        # Node statistics
        total_cpu_capacity = sum(n['cpu_allocatable'] for n in nodes)
        total_memory_capacity = sum(n['memory_allocatable'] for n in nodes)
        total_cpu_usage = sum(n['cpu_usage_cores'] for n in nodes)
        total_memory_usage = sum(n['memory_usage_bytes'] for n in nodes)
        
        # Deployment statistics
        if deployments:
            avg_cpu_gap = sum(d['cpu_gap'] for d in deployments) / len(deployments)
            avg_memory_gap = sum(d['memory_gap'] for d in deployments) / len(deployments)
            over_provisioned_deployments = sum(1 for d in deployments if d['cpu_gap'] > 25 or d['memory_gap'] > 25)
        else:
            avg_cpu_gap = 0
            avg_memory_gap = 0
            over_provisioned_deployments = 0
        
        return {
            'total_cpu_capacity_cores': round(total_cpu_capacity, 2),
            'total_memory_capacity_gb': round(total_memory_capacity / (1024**3), 2),
            'cluster_cpu_usage_pct': round((total_cpu_usage / total_cpu_capacity * 100) if total_cpu_capacity > 0 else 0, 1),
            'cluster_memory_usage_pct': round((total_memory_usage / total_memory_capacity * 100) if total_memory_capacity > 0 else 0, 1),
            'average_cpu_gap': round(avg_cpu_gap, 1),
            'average_memory_gap': round(avg_memory_gap, 1),
            'over_provisioned_deployments': over_provisioned_deployments,
            'optimization_opportunity_pct': round((over_provisioned_deployments / len(deployments) * 100) if deployments else 0, 1)
        }
    
    def _parse_cpu_value(self, cpu_str: str) -> float:
        """Parse CPU value from various formats (cores, millicores)"""
        if not cpu_str or cpu_str == '0':
            return 0.0
        
        cpu_str = cpu_str.strip()
        
        if cpu_str.endswith('m'):
            # Millicores
            return float(cpu_str[:-1]) / 1000.0
        elif cpu_str.endswith('n'):
            # Nanocores
            return float(cpu_str[:-1]) / 1000000000.0
        else:
            # Cores
            return float(cpu_str)
    
    def _parse_memory_value(self, memory_str: str) -> int:
        """Parse memory value from various formats (bytes, Ki, Mi, Gi)"""
        if not memory_str or memory_str == '0':
            return 0
        
        memory_str = memory_str.strip()
        
        if memory_str.endswith('Ki'):
            return int(float(memory_str[:-2]) * 1024)
        elif memory_str.endswith('Mi'):
            return int(float(memory_str[:-2]) * 1024 * 1024)
        elif memory_str.endswith('Gi'):
            return int(float(memory_str[:-2]) * 1024 * 1024 * 1024)
        elif memory_str.endswith('Ti'):
            return int(float(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024)
        elif memory_str.endswith('k'):
            return int(float(memory_str[:-1]) * 1000)
        elif memory_str.endswith('M'):
            return int(float(memory_str[:-1]) * 1000 * 1000)
        elif memory_str.endswith('G'):
            return int(float(memory_str[:-1]) * 1000 * 1000 * 1000)
        elif memory_str.endswith('T'):
            return int(float(memory_str[:-1]) * 1000 * 1000 * 1000 * 1000)
        else:
            return int(float(memory_str))
    
    def _parse_storage_value(self, storage_str: str) -> int:
        """Parse storage value from various formats"""
        return self._parse_memory_value(storage_str)  # Same parsing logic