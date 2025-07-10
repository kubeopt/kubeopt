# app/enhanced_aks_config_fetcher.py

"""
Enhanced AKS Cluster Configuration Fetcher Integration
====================================================
Place this file in: app/enhanced_aks_config_fetcher.py

This integrates the pure cluster config fetcher into your existing project structure.
"""

# Import the pure cluster config fetcher
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import subprocess
import logging
import concurrent.futures
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Kubernetes resource types for systematic fetching"""
    # Core Workloads
    DEPLOYMENTS = "deployments"
    REPLICASETS = "replicasets"
    STATEFULSETS = "statefulsets"
    DAEMONSETS = "daemonsets"
    JOBS = "jobs"
    CRONJOBS = "cronjobs"
    PODS = "pods"
    
    # Services and Networking
    SERVICES = "services"
    ENDPOINTS = "endpoints"
    INGRESSES = "ingresses"
    NETWORKPOLICIES = "networkpolicies"
    
    # Configuration and Storage
    CONFIGMAPS = "configmaps"
    SECRETS = "secrets"
    PERSISTENTVOLUMES = "persistentvolumes"
    PERSISTENTVOLUMECLAIMS = "persistentvolumeclaims"
    STORAGECLASSES = "storageclasses"
    
    # RBAC and Security
    SERVICEACCOUNTS = "serviceaccounts"
    ROLES = "roles"
    CLUSTERROLES = "clusterroles"
    ROLEBINDINGS = "rolebindings"
    CLUSTERROLEBINDINGS = "clusterrolebindings"
    
    # Resource Management
    RESOURCEQUOTAS = "resourcequotas"
    LIMITRANGES = "limitranges"
    HORIZONTALPODAUTOSCALERS = "horizontalpodautoscalers"
    VERTICALPODAUTOSCALERS = "verticalpodautoscalers"
    PODDISRUPTIONBUDGETS = "poddisruptionbudgets"
    
    # Monitoring (if available)
    SERVICEMONITORS = "servicemonitors"
    PODMONITORS = "podmonitors"
    PROMETHEUSRULES = "prometheusrules"

@dataclass
class FetchMetrics:
    """Simple metrics for fetch operation"""
    total_resources: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0
    fetch_duration_seconds: float = 0.0
    total_namespaces: int = 0

class PureAKSClusterConfigFetcher:
    """
    Pure AKS Cluster Configuration Fetcher - DATA ONLY
    
    This class ONLY fetches raw cluster configuration data using az aks command.
    It performs NO analysis, calculations, or ML feature generation.
    All analysis is delegated to implementation_generator.py and ML logic.
    """
    
    def __init__(self, resource_group: str, cluster_name: str, subscription_id: str, 
                 max_workers: int = 10, timeout_seconds: int = 300):
        """
        Initialize the pure data fetcher
        
        Args:
            resource_group: Azure resource group name
            cluster_name: AKS cluster name  
            subscription_id: Azure subscription ID
            max_workers: Maximum concurrent workers for parallel fetching
            timeout_seconds: Timeout for individual commands
        """
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.subscription_id = subscription_id
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        
        # Simple state tracking
        self.fetched_resources = set()
        self.failed_resources = set()
        self.metrics = FetchMetrics()
        
        # Resource categories for organization
        self.critical_resources = [
            ResourceType.DEPLOYMENTS, ResourceType.SERVICES, ResourceType.PODS,
            ResourceType.CONFIGMAPS, ResourceType.SECRETS, ResourceType.HORIZONTALPODAUTOSCALERS
        ]
        
        self.optional_resources = [
            ResourceType.SERVICEMONITORS, ResourceType.PODMONITORS, 
            ResourceType.VERTICALPODAUTOSCALERS, ResourceType.PROMETHEUSRULES
        ]
    
    def fetch_raw_cluster_configuration(self, enable_parallel_fetch: bool = True) -> Dict[str, Any]:
        """
        Fetch raw cluster configuration data - NO ANALYSIS
        
        Args:
            enable_parallel_fetch: Whether to use parallel fetching for performance
            
        Returns:
            Raw cluster configuration dictionary with organized resource data
        """
        start_time = datetime.now()
        logger.info(f"🔍 Starting raw cluster config fetch for {self.cluster_name}")
        
        config_data = {
            'cluster_metadata': {
                'resource_group': self.resource_group,
                'cluster_name': self.cluster_name,
                'subscription_id': self.subscription_id,
                'fetch_timestamp': start_time.isoformat(),
                'fetcher_version': '1.0.0-pure'
            },
            'azure_cluster_info': {},
            'kubernetes_cluster_info': {},
            'node_data': {},
            'workload_resources': {},
            'networking_resources': {},
            'storage_resources': {},
            'security_resources': {},
            'configuration_resources': {},
            'scaling_resources': {},
            'monitoring_resources': {},
            'raw_api_resources': {},
            'fetch_metrics': {},
            'status': 'in_progress'
        }
        
        try:
            # Phase 1: Azure cluster information
            logger.info("📋 Phase 1: Fetching Azure cluster information")
            config_data['azure_cluster_info'] = self._fetch_azure_cluster_info()
            
            # Phase 2: Kubernetes cluster information  
            logger.info("📋 Phase 2: Fetching Kubernetes cluster information")
            config_data['kubernetes_cluster_info'] = self._fetch_kubernetes_cluster_info()
            
            # Phase 3: Node data
            logger.info("📋 Phase 3: Fetching node data")
            config_data['node_data'] = self._fetch_node_data()
            
            # Phase 4: Resource discovery and fetching
            logger.info("🔍 Phase 4: Fetching Kubernetes resources")
            if enable_parallel_fetch:
                resource_data = self._fetch_resources_parallel()
            else:
                resource_data = self._fetch_resources_sequential()
            
            # Phase 5: Organize resources by category (NO ANALYSIS)
            logger.info("📁 Phase 5: Organizing resources by category")
            self._organize_resources_by_category(resource_data, config_data)
            
            # Phase 6: Collect API resources list
            logger.info("📋 Phase 6: Fetching API resources")
            config_data['raw_api_resources'] = self._fetch_api_resources()
            
            # Phase 7: Final metrics
            end_time = datetime.now()
            self.metrics.fetch_duration_seconds = (end_time - start_time).total_seconds()
            
            config_data['fetch_metrics'] = {
                'total_resources': self.metrics.total_resources,
                'successful_fetches': self.metrics.successful_fetches,
                'failed_fetches': self.metrics.failed_fetches,
                'fetch_duration_seconds': self.metrics.fetch_duration_seconds,
                'total_namespaces': self.metrics.total_namespaces,
                'successful_resources': list(self.fetched_resources),
                'failed_resources': list(self.failed_resources)
            }
            
            config_data['status'] = 'completed'
            
            logger.info(f"✅ Raw cluster configuration fetch completed in {self.metrics.fetch_duration_seconds:.2f}s")
            logger.info(f"📊 Resources: {self.metrics.successful_fetches}/{self.metrics.total_resources} successful")
            
            return config_data
            
        except Exception as e:
            logger.error(f"❌ Cluster configuration fetch failed: {e}")
            config_data['status'] = 'failed'
            config_data['error'] = str(e)
            config_data['fetch_metrics'] = self._get_error_metrics()
            return config_data
    
    def _fetch_azure_cluster_info(self) -> Dict[str, Any]:
        """Fetch Azure cluster information using Azure CLI"""
        cluster_info = {}
        
        try:
            # Get AKS cluster details
            cluster_details = self._run_az_aks_show()
            if cluster_details:
                cluster_info['aks_cluster_details'] = cluster_details
                logger.info("✅ AKS cluster details fetched")
            
            # Get node pools
            node_pools = self._run_az_aks_nodepool_list()
            if node_pools:
                cluster_info['node_pools'] = node_pools
                logger.info(f"✅ Node pools fetched: {len(node_pools)} pools")
            
            # Get managed identity
            managed_identity = self._get_managed_identity()
            if managed_identity:
                cluster_info['managed_identity'] = managed_identity
                logger.info("✅ Managed identity info fetched")
            
        except Exception as e:
            logger.warning(f"⚠️ Partial failure in Azure cluster info fetch: {e}")
            cluster_info['fetch_error'] = str(e)
        
        return cluster_info
    
    def _fetch_kubernetes_cluster_info(self) -> Dict[str, Any]:
        """Fetch Kubernetes cluster information"""
        k8s_info = {}
        
        try:
            # Get cluster version info
            version_info = self._run_kubectl_command(['version', '--output=json'])
            if version_info:
                k8s_info['version_info'] = version_info
                logger.info("✅ Kubernetes version info fetched")
            
            # Get cluster-info
            cluster_info = self._run_kubectl_command(['cluster-info', '--output=json'])
            if cluster_info:
                k8s_info['cluster_endpoints'] = cluster_info
                logger.info("✅ Cluster endpoints fetched")
            
            # Get cluster configuration
            cluster_config = self._run_kubectl_command(['config', 'view', '--output=json'])
            if cluster_config:
                k8s_info['kubectl_config'] = cluster_config
                logger.info("✅ Kubectl config fetched")
            
        except Exception as e:
            logger.warning(f"⚠️ Partial failure in Kubernetes cluster info fetch: {e}")
            k8s_info['fetch_error'] = str(e)
        
        return k8s_info
    
    def _fetch_node_data(self) -> Dict[str, Any]:
        """Fetch raw node data"""
        node_data = {}
        
        try:
            # Get nodes with detailed information
            nodes_output = self._run_kubectl_command(['get', 'nodes', '-o', 'json'])
            if nodes_output:
                node_data['nodes_raw'] = nodes_output
                
                # Extract basic node list for convenience
                if 'items' in nodes_output:
                    node_data['node_list'] = []
                    for node in nodes_output['items']:
                        node_summary = {
                            'name': node.get('metadata', {}).get('name', 'unknown'),
                            'status': node.get('status', {}),
                            'capacity': node.get('status', {}).get('capacity', {}),
                            'allocatable': node.get('status', {}).get('allocatable', {}),
                            'node_info': node.get('status', {}).get('nodeInfo', {}),
                            'conditions': node.get('status', {}).get('conditions', []),
                            'labels': node.get('metadata', {}).get('labels', {}),
                            'annotations': node.get('metadata', {}).get('annotations', {})
                        }
                        node_data['node_list'].append(node_summary)
                    
                    node_data['node_count'] = len(node_data['node_list'])
                    logger.info(f"✅ Node data fetched: {node_data['node_count']} nodes")
            
            # Get node metrics if available (optional)
            try:
                node_metrics = self._run_kubectl_command(['top', 'nodes'])
                if node_metrics:
                    node_data['node_metrics_raw'] = node_metrics
                    logger.info("✅ Node metrics fetched")
            except:
                logger.info("ℹ️ Node metrics not available (metrics-server may not be installed)")
            
        except Exception as e:
            logger.warning(f"⚠️ Node data fetch failed: {e}")
            node_data['fetch_error'] = str(e)
        
        return node_data
    
    def _fetch_resources_parallel(self) -> Dict[str, Any]:
        """Fetch Kubernetes resources in parallel"""
        logger.info(f"🔄 Fetching resources with {self.max_workers} parallel workers")
        
        resource_data = {}
        
        # Prepare resource fetch tasks
        fetch_tasks = []
        for resource_type in ResourceType:
            fetch_tasks.append(resource_type)
        
        # Execute parallel fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_resource = {
                executor.submit(self._fetch_single_resource_type, resource_type): resource_type
                for resource_type in fetch_tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_resource):
                resource_type = future_to_resource[future]
                try:
                    result = future.result(timeout=self.timeout_seconds)
                    if result:
                        resource_data[resource_type.value] = result
                        self.fetched_resources.add(resource_type.value)
                        self.metrics.successful_fetches += 1
                    else:
                        self.failed_resources.add(resource_type.value)
                        self.metrics.failed_fetches += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch {resource_type.value}: {e}")
                    self.failed_resources.add(resource_type.value)
                    self.metrics.failed_fetches += 1
        
        self.metrics.total_resources = len(fetch_tasks)
        logger.info(f"✅ Parallel resource fetch completed: {self.metrics.successful_fetches}/{self.metrics.total_resources}")
        
        return resource_data
    
    def _fetch_resources_sequential(self) -> Dict[str, Any]:
        """Fetch Kubernetes resources sequentially"""
        logger.info("🔄 Fetching resources sequentially")
        
        resource_data = {}
        
        for resource_type in ResourceType:
            try:
                result = self._fetch_single_resource_type(resource_type)
                if result:
                    resource_data[resource_type.value] = result
                    self.fetched_resources.add(resource_type.value)
                    self.metrics.successful_fetches += 1
                else:
                    self.failed_resources.add(resource_type.value)
                    self.metrics.failed_fetches += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch {resource_type.value}: {e}")
                self.failed_resources.add(resource_type.value)
                self.metrics.failed_fetches += 1
        
        self.metrics.total_resources = len(list(ResourceType))
        logger.info(f"✅ Sequential resource fetch completed: {self.metrics.successful_fetches}/{self.metrics.total_resources}")
        
        return resource_data
    
    def _fetch_single_resource_type(self, resource_type: ResourceType) -> Optional[Dict]:
        """
        Fetch a single type of Kubernetes resource with proper type checking
        """
        try:
            # Construct kubectl args from ResourceType enum
            args = ['get', resource_type.value, '-o', 'json', '--all-namespaces']
            
            # Use the working _run_kubectl_command method
            result = self._run_kubectl_command(args)
            
            # FIX: Handle both dict and string returns properly
            if result:
                if isinstance(result, dict) and 'items' in result:
                    # Successfully got JSON dict with items
                    logger.debug(f"✅ Fetched {len(result['items'])} {resource_type.value}")
                    
                    return {
                        'raw_data': result,
                        'items': result['items'],
                        'item_count': len(result['items']),
                        'kind': result.get('kind'),
                        'apiVersion': result.get('apiVersion'),
                        'fetch_timestamp': datetime.now().isoformat()
                    }
                elif isinstance(result, str):
                    # Got string output - try to parse as JSON
                    logger.debug(f"⚠️ Got string output for {resource_type.value}, attempting manual parse")
                    try:
                        # Try parsing the string as JSON
                        parsed_result = json.loads(result)
                        if isinstance(parsed_result, dict) and 'items' in parsed_result:
                            logger.debug(f"✅ Successfully parsed {len(parsed_result['items'])} {resource_type.value} from string")
                            return {
                                'raw_data': parsed_result,
                                'items': parsed_result['items'],
                                'item_count': len(parsed_result['items']),
                                'kind': parsed_result.get('kind'),
                                'apiVersion': parsed_result.get('apiVersion'),
                                'fetch_timestamp': datetime.now().isoformat()
                            }
                    except json.JSONDecodeError as json_error:
                        logger.debug(f"⚠️ JSON parse failed for {resource_type.value}: {json_error}")
                    
                    # Return empty structure for string that can't be parsed
                    logger.debug(f"⚠️ Could not parse {resource_type.value} output as JSON, treating as empty")
                    return {
                        'raw_data': result,
                        'items': [],
                        'item_count': 0,
                        'parse_error': 'string_output_not_json',
                        'fetch_timestamp': datetime.now().isoformat()
                    }
                else:
                    logger.debug(f"⚠️ Unexpected result type for {resource_type.value}: {type(result)}")
                    return None
            else:
                logger.debug(f"⚠️ No result for {resource_type.value}")
                return None
                
        except Exception as e:
            # Check if this is an optional resource that might not be available
            if resource_type in self.optional_resources:
                logger.debug(f"Optional resource {resource_type.value} not available: {e}")
            else:
                logger.warning(f"⚠️ Failed to fetch {resource_type.value}: {e}")
            return None
    
    def _organize_resources_by_category(self, resource_data: Dict, config_data: Dict):
        """Organize fetched resources into logical categories - NO ANALYSIS"""
        
        # Workload resources
        config_data['workload_resources'] = {
            'deployments': resource_data.get('deployments', {}),
            'replicasets': resource_data.get('replicasets', {}),
            'statefulsets': resource_data.get('statefulsets', {}),
            'daemonsets': resource_data.get('daemonsets', {}),
            'jobs': resource_data.get('jobs', {}),
            'cronjobs': resource_data.get('cronjobs', {}),
            'pods': resource_data.get('pods', {})
        }
        
        # Networking resources
        config_data['networking_resources'] = {
            'services': resource_data.get('services', {}),
            'endpoints': resource_data.get('endpoints', {}),
            'ingresses': resource_data.get('ingresses', {}),
            'networkpolicies': resource_data.get('networkpolicies', {})
        }
        
        # Storage resources
        config_data['storage_resources'] = {
            'persistentvolumes': resource_data.get('persistentvolumes', {}),
            'persistentvolumeclaims': resource_data.get('persistentvolumeclaims', {}),
            'storageclasses': resource_data.get('storageclasses', {})
        }
        
        # Security resources
        config_data['security_resources'] = {
            'serviceaccounts': resource_data.get('serviceaccounts', {}),
            'roles': resource_data.get('roles', {}),
            'clusterroles': resource_data.get('clusterroles', {}),
            'rolebindings': resource_data.get('rolebindings', {}),
            'clusterrolebindings': resource_data.get('clusterrolebindings', {})
        }
        
        # Configuration resources
        config_data['configuration_resources'] = {
            'configmaps': resource_data.get('configmaps', {}),
            'secrets': resource_data.get('secrets', {}),
            'resourcequotas': resource_data.get('resourcequotas', {}),
            'limitranges': resource_data.get('limitranges', {})
        }
        
        # Scaling resources
        config_data['scaling_resources'] = {
            'horizontalpodautoscalers': resource_data.get('horizontalpodautoscalers', {}),
            'verticalpodautoscalers': resource_data.get('verticalpodautoscalers', {}),
            'poddisruptionbudgets': resource_data.get('poddisruptionbudgets', {})
        }
        
        # Monitoring resources
        config_data['monitoring_resources'] = {
            'servicemonitors': resource_data.get('servicemonitors', {}),
            'podmonitors': resource_data.get('podmonitors', {}),
            'prometheusrules': resource_data.get('prometheusrules', {})
        }
        
        # Count unique namespaces across all resources
        namespaces = set()
        for category_data in config_data.values():
            if isinstance(category_data, dict):
                for resource_type, resource_info in category_data.items():
                    if isinstance(resource_info, dict) and 'items' in resource_info:
                        for item in resource_info['items']:
                            ns = item.get('metadata', {}).get('namespace')
                            if ns:
                                namespaces.add(ns)
        
        self.metrics.total_namespaces = len(namespaces)
        logger.info(f"✅ Resources organized: {len(namespaces)} namespaces discovered")
    
    def _fetch_api_resources(self) -> Dict[str, Any]:
        """Fetch available API resources"""
        api_data = {}
        
        try:
            # Get API resources
            api_resources = self._run_kubectl_command(['api-resources', '--output=wide'])
            if api_resources:
                api_data['api_resources_raw'] = api_resources
                api_data['api_resources_list'] = self._parse_api_resources(api_resources)
                logger.info(f"✅ API resources fetched: {len(api_data['api_resources_list'])} resources")
            
            # Get API versions
            api_versions = self._run_kubectl_command(['api-versions'])
            if api_versions:
                api_data['api_versions_raw'] = api_versions
                logger.info("✅ API versions fetched")
            
        except Exception as e:
            logger.warning(f"⚠️ API resources fetch failed: {e}")
            api_data['fetch_error'] = str(e)
        
        return api_data
    
    def _run_az_aks_show(self) -> Optional[Dict]:
        """Get AKS cluster details using Azure CLI"""
        try:
            cmd = [
                'az', 'aks', 'show',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--subscription', self.subscription_id,
                '--output', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_seconds)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning(f"az aks show failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get AKS cluster details: {e}")
            return None
    
    def _run_az_aks_nodepool_list(self) -> Optional[List]:
        """Get AKS node pools using Azure CLI"""
        try:
            cmd = [
                'az', 'aks', 'nodepool', 'list',
                '--resource-group', self.resource_group,
                '--cluster-name', self.cluster_name,
                '--subscription', self.subscription_id,
                '--output', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_seconds)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning(f"az aks nodepool list failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get AKS node pools: {e}")
            return None
    
    def _get_managed_identity(self) -> Optional[Dict]:
        """Get managed identity information"""
        try:
            cmd = [
                'az', 'aks', 'show',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--subscription', self.subscription_id,
                '--query', 'identity',
                '--output', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_seconds)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning(f"Managed identity fetch failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to get managed identity: {e}")
            return None
    
    def _safe_kubectl_yaml_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[Union[Dict, str]]:
        """
        from working pod_cost_analyzer.py - Safe YAML/JSON command execution
        """
        try:
            # Use the working execute_kubectl_command method
            output = self.execute_kubectl_command(kubectl_cmd, timeout)
            if output:
                try:
                    return json.loads(output)
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON parsing failed for {kubectl_cmd}: {e}")
                    return output  # Return raw string
            return None
        except Exception as e:
            logger.debug(f"YAML command failed: {e}")
            return None
    
    def execute_kubectl_command(self, kubectl_cmd: str, timeout: int = None) -> Optional[str]:
        """
        from working aks_realtime_metrics.py - Execute kubectl command that WORKS
        """
        if timeout is None:
            timeout = self.timeout_seconds
            
        try:
            cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', kubectl_cmd
            ]
            
            # Add subscription context (from working code)
            if self.subscription_id:
                cmd.extend(['--subscription', self.subscription_id])
                logger.debug(f"🌐 Using subscription context: {self.subscription_id[:8]} for command: {kubectl_cmd}")
            
            logger.debug(f"🔧 Executing: {kubectl_cmd}")
            start_time = time.time()
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            execution_time = time.time() - start_time
            logger.debug(f"🔧 Command completed in {execution_time:.2f}s")
            logger.debug(f"🔧 Return code: {result.returncode}")
            
            if result.returncode != 0:
                logger.warning(f"❌ Command failed with return code {result.returncode}")
                logger.warning(f"❌ STDERR: {result.stderr}")
                return None
            
            # Use the WORKING output cleaning method
            clean_output = self._clean_command_output(result.stdout)
            
            if not clean_output:
                logger.debug(f"⚠️ No output after cleaning for command: {kubectl_cmd}")
                return None
            
            logger.debug(f"🔧 Clean output length: {len(clean_output)}")
            return clean_output
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Timeout executing kubectl command: {kubectl_cmd}")
            return None
        except Exception as e:
            logger.error(f"❌ Error executing kubectl command '{kubectl_cmd}': {e}")
            return None

    def _clean_command_output(self, raw_output: str) -> str:
        """from working aks_realtime_metrics.py"""
        try:
            if not raw_output:
                return ""
            
            lines = raw_output.split('\n')
            clean_lines = []
            
            for line in lines:
                # Skip Azure CLI metadata lines (EXACT COPY from working code)
                if any(skip_pattern in line.lower() for skip_pattern in [
                    'command started at',
                    'command finished at', 
                    'exitcode=',
                    'command started',
                    'command finished'
                ]):
                    continue
                clean_lines.append(line)
            
            return '\n'.join(clean_lines).strip()
            
        except Exception as e:
            logger.error(f"❌ Error cleaning command output: {e}")
            return raw_output

    def _run_kubectl_command(self, kubectl_args: List[str]) -> Optional[Union[Dict, str]]:
        """
        Run kubectl command using the WORKING method from aks_realtime_metrics.py
        """
        try:
            # Construct az aks command (same as before)
            cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--subscription', self.subscription_id,
                '--command', ' '.join(['kubectl'] + kubectl_args)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout_seconds
            )
            
            if result.returncode == 0:
                # USE THE WORKING OUTPUT CLEANING METHOD (not JSON parsing)
                clean_output = self._clean_command_output(result.stdout)
                
                if not clean_output:
                    return None
                
                # Try to parse as JSON first
                try:
                    return json.loads(clean_output)
                except json.JSONDecodeError:
                    # Return raw output for non-JSON responses
                    return clean_output.strip()
            else:
                logger.debug(f"kubectl command failed: {' '.join(kubectl_args)} - {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning(f"kubectl command timed out: {' '.join(kubectl_args)}")
            return None
        except Exception as e:
            logger.debug(f"kubectl command error: {e}")
            return None
    
    def _parse_api_resources(self, api_resources_output: str) -> List[Dict]:
        """Parse kubectl api-resources output into structured data"""
        resources = []
        try:
            lines = api_resources_output.strip().split('\n')
            if len(lines) > 1:  # Skip header
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        resources.append({
                            'name': parts[0],
                            'shortnames': parts[1] if parts[1] != '<none>' else None,
                            'apiversion': parts[2],
                            'namespaced': parts[3] == 'true',
                            'kind': parts[4] if len(parts) > 4 else None
                        })
        except Exception as e:
            logger.warning(f"Failed to parse API resources: {e}")
        
        return resources
    
    def _get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics when fetch fails"""
        return {
            'total_resources': self.metrics.total_resources,
            'successful_fetches': self.metrics.successful_fetches,
            'failed_fetches': self.metrics.failed_fetches,
            'fetch_duration_seconds': self.metrics.fetch_duration_seconds,
            'successful_resources': list(self.fetched_resources),
            'failed_resources': list(self.failed_resources),
            'error_occurred': True
        }

def create_cluster_config_fetcher(resource_group: str, cluster_name: str, subscription_id: str) -> PureAKSClusterConfigFetcher:
    """
    Factory function to create a cluster config fetcher
    
    Args:
        resource_group: Azure resource group name
        cluster_name: AKS cluster name
        subscription_id: Azure subscription ID
        
    Returns:
        Configured PureAKSClusterConfigFetcher instance
    """
    return PureAKSClusterConfigFetcher(
        resource_group=resource_group,
        cluster_name=cluster_name,
        subscription_id=subscription_id,
        max_workers=8,  # Reasonable default
        timeout_seconds=300  # 5 minute timeout
    )

def fetch_cluster_configuration(resource_group: str, cluster_name: str, subscription_id: str,
                              enable_parallel: bool = True) -> Dict[str, Any]:
    """
    Convenience function to fetch cluster configuration
    
    Args:
        resource_group: Azure resource group name
        cluster_name: AKS cluster name
        subscription_id: Azure subscription ID
        enable_parallel: Whether to use parallel fetching
        
    Returns:
        Raw cluster configuration data ready for implementation generator
    """
    fetcher = create_cluster_config_fetcher(resource_group, cluster_name, subscription_id)
    return fetcher.fetch_raw_cluster_configuration(enable_parallel_fetch=enable_parallel)

# Export the main classes and functions
__all__ = [
    'PureAKSClusterConfigFetcher',
    'create_cluster_config_fetcher', 
    'fetch_cluster_configuration',
    'ResourceType',
    'FetchMetrics'
]