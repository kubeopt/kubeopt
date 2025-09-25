#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

# app/enhanced_aks_config_fetcher.py

"""
Enhanced AKS Cluster Configuration Fetcher Integration
====================================================
Place this file in: app/enhanced_aks_config_fetcher.py

This integrates the pure cluster config fetcher into your existing project structure.
"""

# Import the pure cluster config fetcher
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import logging
import concurrent.futures
from enum import Enum
from dataclasses import dataclass

# Import the centralized cache
from shared.kubernetes_data_cache import fetch_cluster_data, get_or_create_cache, KubernetesDataCache

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
        
        # Use centralized cache with data pre-fetching for initialization
        self.cache = fetch_cluster_data(cluster_name, resource_group, subscription_id)
        logger.info(f"✅ {cluster_name}: Initialized config fetcher with pre-populated cache")
        
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
            # Get cluster version info from cache
            version_info = self.cache.get('version')
            if version_info:
                k8s_info['version_info'] = version_info
                logger.info("✅ Kubernetes version info from cache")
            
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
            # Get nodes with detailed information from cache
            nodes_output = self.cache.get('nodes')
            if nodes_output:
                node_data['nodes_raw'] = nodes_output
                logger.info(f"✅ {self.cluster_name}: Got nodes data from cache")
                
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
                node_metrics = self.cache.get('node_usage_headers')
                if node_metrics:
                    node_data['node_metrics_raw'] = node_metrics
                    logger.info("✅ Node metrics from cache")
                else:
                    logger.info("ℹ️ Node metrics not available (metrics-server may not be running)")
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
        
        # NEW: Add monitoring state detection
        config_data['monitoring_state'] = {
            'has_container_insights': False,
            'has_prometheus_operators': False
        }
        
        # Check for Container Insights (omsagent daemonsets)
        daemonsets = resource_data.get('daemonsets', {}).get('items', [])
        for ds in daemonsets:
            if 'omsagent' in ds.get('metadata', {}).get('name', ''):
                config_data['monitoring_state']['has_container_insights'] = True
                break
        
        # Check for Prometheus operators (servicemonitors)
        monitoring_resources = config_data.get('monitoring_resources', {})
        if monitoring_resources.get('servicemonitors', {}).get('item_count', 0) > 0:
            config_data['monitoring_state']['has_prometheus_operators'] = True
        
        logger.info(f"📊 Monitoring State Detected: Container Insights={'Yes' if config_data['monitoring_state']['has_container_insights'] else 'No'}, Prometheus={'Yes' if config_data['monitoring_state']['has_prometheus_operators'] else 'No'}")
        
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
            # Get API resources from cache
            api_resources = self.cache.get('api_resources')
            if api_resources:
                api_data['api_resources_raw'] = api_resources
                api_data['api_resources_list'] = self._parse_api_resources(api_resources)
                logger.info(f"✅ API resources from cache: {len(api_data.get('api_resources_list', []))} resources")
            
            # Get API versions from cache
            api_versions = self.cache.get('api_versions')
            if api_versions:
                api_data['api_versions_raw'] = api_versions
                logger.info("✅ API versions from cache")
            
        except Exception as e:
            logger.warning(f"⚠️ API resources fetch failed: {e}")
            api_data['fetch_error'] = str(e)
        
        return api_data
    
    def _run_az_aks_show(self) -> Optional[Dict]:
        """Get AKS cluster details from centralized cache"""
        try:
            # Use centralized cache instead of direct command execution
            cached_data = self.cache.get('aks_cluster_info')
            if cached_data:
                # If cached data is string, parse as JSON
                if isinstance(cached_data, str):
                    return json.loads(cached_data)
                # If already dict, return directly
                elif isinstance(cached_data, dict):
                    return cached_data
            
            logger.warning(f"AKS cluster info not found in cache")
            return None
                
        except Exception as e:
            logger.warning(f"Failed to get AKS cluster details from cache: {e}")
            return None
    
    def _run_az_aks_nodepool_list(self) -> Optional[List]:
        """Get AKS node pools from centralized cache"""
        try:
            # Use centralized cache instead of direct command execution
            cached_data = self.cache.get('aks_nodepool_list')
            if cached_data:
                # If cached data is string, parse as JSON
                if isinstance(cached_data, str):
                    return json.loads(cached_data)
                # If already list, return directly
                elif isinstance(cached_data, list):
                    return cached_data
            
            logger.warning(f"AKS nodepool list not found in cache")
            return None
                
        except Exception as e:
            logger.warning(f"Failed to get AKS node pools from cache: {e}")
            return None
    
    def _get_managed_identity(self) -> Optional[Dict]:
        """Get managed identity information from centralized cache"""
        try:
            # Use centralized cache instead of direct command execution
            cached_data = self.cache.get('aks_managed_identity')
            if cached_data:
                # If cached data is string, parse as JSON
                if isinstance(cached_data, str):
                    return json.loads(cached_data)
                # If already dict, return directly
                elif isinstance(cached_data, dict):
                    return cached_data
            
            logger.warning(f"AKS managed identity not found in cache")
            return None
                
        except Exception as e:
            logger.warning(f"Failed to get managed identity from cache: {e}")
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
        REPLACED: Use centralized cache instead of direct kubectl execution
        Maps kubectl commands to cached data keys - READ ONLY, NO EXECUTION
        """
        logger.debug(f"🔍 ConfigFetcher: Reading cached data for: {kubectl_cmd}")
        
        # Map kubectl commands to cached data keys - NO EXECUTION, READ ONLY
        if "kubectl version" in kubectl_cmd:
            cached_data = self.cache.get('version')
            if cached_data and isinstance(cached_data, dict):
                return json.dumps(cached_data)
            return None
        elif "kubectl api-resources" in kubectl_cmd:
            return self.cache.get('api_resources')
        elif "kubectl api-versions" in kubectl_cmd:
            return self.cache.get('api_versions')
        elif "kubectl cluster-info" in kubectl_cmd:
            return self.cache.get('cluster_info')
        elif "kubectl config view" in kubectl_cmd:
            cached_data = self.cache.get('config_view')
            if cached_data and isinstance(cached_data, dict):
                return json.dumps(cached_data)
            return cached_data  # Return raw if not dict
        elif "kubectl get nodes" in kubectl_cmd and "-o json" in kubectl_cmd:
            cached_data = self.cache.get('nodes')
            if cached_data and isinstance(cached_data, dict):
                return json.dumps(cached_data)
            return None
        elif "kubectl get namespaces" in kubectl_cmd and "-o json" in kubectl_cmd:
            cached_data = self.cache.get('namespaces')
            if cached_data and isinstance(cached_data, dict):
                return json.dumps(cached_data)
            return None
        elif "kubectl get pods" in kubectl_cmd and "-o json" in kubectl_cmd:
            cached_data = self.cache.get('pods')
            if cached_data and isinstance(cached_data, dict):
                return json.dumps(cached_data)
            return None
        elif "kubectl get services" in kubectl_cmd and "-o json" in kubectl_cmd:
            cached_data = self.cache.get('services')
            if cached_data and isinstance(cached_data, dict):
                return json.dumps(cached_data)
            return None
        elif "kubectl get deployments" in kubectl_cmd and "-o json" in kubectl_cmd:
            cached_data = self.cache.get('deployments')
            if cached_data and isinstance(cached_data, dict):
                return json.dumps(cached_data)
            return None
        else:
            logger.warning(f"⚠️ ConfigFetcher: No cached data mapping for command: {kubectl_cmd}")
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
        Get kubectl data from pre-populated cache (avoid running commands during analysis)
        """
        try:
            # Convert kubectl args to cache key mapping
            kubectl_cmd = ' '.join(kubectl_args)
            
            # Map common kubectl commands to cache keys - this avoids running commands during analysis
            # Note: Commands are in format: get <resource> -o json --all-namespaces (from _fetch_single_resource_type)
            cache_key_mapping = {
                'version -o json': 'version',
                'get nodes -o json': 'nodes',
                'get namespaces -o json': 'namespaces',
                'get pods -o json --all-namespaces': 'pods',
                'get deployments -o json --all-namespaces': 'deployments',
                'get replicasets -o json --all-namespaces': 'replicasets',
                'get statefulsets -o json --all-namespaces': 'statefulsets',
                'get daemonsets -o json --all-namespaces': 'daemonsets',
                'get jobs -o json --all-namespaces': 'jobs',
                'get cronjobs -o json --all-namespaces': 'jobs',
                'get services -o json --all-namespaces': 'services',
                'get endpoints -o json --all-namespaces': 'services',
                'get ingresses -o json --all-namespaces': 'services',
                'get configmaps -o json --all-namespaces': 'configmaps',
                'get secrets -o json --all-namespaces': 'secrets',
                'get persistentvolumes -o json --all-namespaces': 'persistentvolumes',
                'get persistentvolumeclaims -o json --all-namespaces': 'pvcs',
                'get storageclasses -o json --all-namespaces': 'storage_classes',
                'get networkpolicies -o json --all-namespaces': 'network_policies',
                'get serviceaccounts -o json --all-namespaces': 'service_accounts',
                'get roles -o json --all-namespaces': 'cluster_roles',
                'get clusterroles -o json --all-namespaces': 'cluster_roles',
                'get rolebindings -o json --all-namespaces': 'role_bindings',
                'get clusterrolebindings -o json --all-namespaces': 'cluster_role_bindings',
                'get resourcequotas -o json --all-namespaces': 'resource_quotas',
                'get limitranges -o json --all-namespaces': 'limit_ranges',
                'get horizontalpodautoscalers -o json --all-namespaces': 'hpa',
                'get verticalpodautoscalers -o json --all-namespaces': 'hpa',
                'get poddisruptionbudgets -o json --all-namespaces': 'hpa',
                'get servicemonitors -o json --all-namespaces': 'hpa',
                'get podmonitors -o json --all-namespaces': 'hpa',
                'get prometheusrules -o json --all-namespaces': 'hpa',
                'cluster-info --output=json': 'cluster_info',
                'config view --output=json': 'config_view',
                'api-resources --output=wide': 'api_resources',
                'api-versions': 'api_versions'
            }
            
            # Try to get from cache first (this is the key change)
            cache_key = cache_key_mapping.get(kubectl_cmd)
            if cache_key:
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    logger.info(f"✅ {self.cluster_name}: Got {cache_key} from cache")
                    return cached_result
                else:
                    logger.info(f"⚠️ {self.cluster_name}: {cache_key} not in cache, executing command")
            
            # NO FALLBACK TO COMMAND EXECUTION - READ FROM CACHE ONLY
            logger.warning(f"⚠️ {self.cluster_name}: Data for {cache_key or kubectl_cmd} not found in cache, no command execution during analysis")
            return None
                
        except Exception as e:
            logger.debug(f"kubectl command error via cache: {e}")
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