#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
AKS Real-time Metrics Fetcher - Combined Enhanced Version
========================================================
Fetches real-time performance metrics directly from AKS clusters.
Provides current usage data for optimization algorithms with ML capabilities.

INTEGRATION: Works with pod_cost_analyzer.py to provide usage+cost analysis
PURPOSE: Collects "what is happening now" data for optimization calculations
FEATURES: Enhanced error handling, ML-ready metrics, high CPU detection
"""

# ============================================================================
# IMPORTS AND CONFIGURATION
# ============================================================================

import subprocess
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

from app.analytics.algorithmic_cost_analyzer import MLEnhancedHPARecommendationEngine
from app.shared.kubernetes_data_cache import get_or_create_cache, fetch_cluster_data

logger = logging.getLogger(__name__)

class KubernetesParsingUtils:
    @staticmethod
    def parse_cpu_safe(cpu_str: str) -> float:
        """Parse CPU values - Handle comma-separated values for multiple containers"""
        if not cpu_str or not isinstance(cpu_str, str):
            raise ValueError(f"Invalid CPU string: {cpu_str}")
        try:
            cpu_str = cpu_str.strip()
            
            # Handle comma-separated values (multiple containers)
            if ',' in cpu_str:
                total_cpu = 0.0
                cpu_values = [val.strip() for val in cpu_str.split(',')]
                for cpu_val in cpu_values:
                    if cpu_val and cpu_val != '<none>':
                        total_cpu += KubernetesParsingUtils._parse_single_cpu_value(cpu_val)
                return total_cpu
            else:
                return KubernetesParsingUtils._parse_single_cpu_value(cpu_str)
        except Exception as e:
            raise ValueError(f"Failed to parse CPU value '{cpu_str}': {e}")
    
    @staticmethod
    def _parse_single_cpu_value(cpu_str: str) -> float:
        """Parse a single CPU value"""
        cpu_str = cpu_str.strip()
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000.0
        elif cpu_str.endswith('n'):
            return float(cpu_str[:-1]) / 1000000000.0
        else:
            return float(cpu_str)
    
    @staticmethod
    def parse_memory_safe(memory_str: str) -> int:
        """Parse memory values - Handle comma-separated values for multiple containers"""
        if not memory_str or not isinstance(memory_str, str):
            raise ValueError(f"Invalid memory string: {memory_str}")
        try:
            memory_str = memory_str.strip()
            
            # Handle comma-separated values (multiple containers)
            if ',' in memory_str:
                total_memory = 0
                memory_values = [val.strip() for val in memory_str.split(',')]
                for mem_val in memory_values:
                    if mem_val and mem_val != '<none>':
                        total_memory += KubernetesParsingUtils._parse_single_memory_value(mem_val)
                return total_memory
            else:
                return KubernetesParsingUtils._parse_single_memory_value(memory_str)
        except Exception as e:
            raise ValueError(f"Failed to parse memory value '{memory_str}': {e}")
    
    @staticmethod
    def _parse_single_memory_value(memory_str: str) -> int:
        """Parse a single memory value"""
        memory_str = memory_str.strip()
        if memory_str.endswith('Ki'):
            return int(float(memory_str[:-2]) * 1024)
        elif memory_str.endswith('Mi'):
            return int(float(memory_str[:-2]) * 1024 * 1024)
        elif memory_str.endswith('Gi'):
            return int(float(memory_str[:-2]) * 1024 * 1024 * 1024)
        elif memory_str.endswith('M'):
            # Handle 'M' suffix (megabytes)
            return int(float(memory_str[:-1]) * 1024 * 1024)
        elif memory_str.endswith('K'):
            # Handle 'K' suffix (kilobytes)
            return int(float(memory_str[:-1]) * 1024)
        elif memory_str.endswith('G'):
            # Handle 'G' suffix (gigabytes)
            return int(float(memory_str[:-1]) * 1024 * 1024 * 1024)
        elif memory_str.endswith('k'):
            # Handle lowercase 'k' suffix (kilobytes) - common in kubectl output
            return int(float(memory_str[:-1]) * 1024)
        elif memory_str.endswith('m'):
            # Handle lowercase 'm' suffix (megabytes) - common in kubectl output
            return int(float(memory_str[:-1]) * 1024 * 1024)
        elif memory_str.endswith('g'):
            # Handle lowercase 'g' suffix (gigabytes) - common in kubectl output
            return int(float(memory_str[:-1]) * 1024 * 1024 * 1024)
        else:
            return int(float(memory_str))


class AKSRealTimeMetricsFetcher:
    """Enhanced AKS Real-time Metrics Collection with ML Capabilities"""
    
    def __init__(self, resource_group: str, cluster_name: str, subscription_id: str, cache=None):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.subscription_id = subscription_id
        self.connection_verified = False
        self.parser = KubernetesParsingUtils()
        
        # CACHE-FIRST: Use provided cache or create new one (backward compatibility)
        if cache:
            logger.info(f"🎯 {cluster_name}: Using shared cache instance for realtime metrics")
            self.cache = cache
        else:
            logger.info(f"⚠️ {cluster_name}: No shared cache provided - creating new cache instance")
            self.cache = get_or_create_cache(cluster_name, resource_group, subscription_id)


    # Add these methods to the AKSRealTimeMetricsFetcher class in aks_realtime_metrics.py

    def _categorize_cpu_usage_severity(self, cpu_millicores: float, cpu_percentage: float) -> str:
        """
        Categorize CPU usage severity for ALL workloads
        """
        if cpu_millicores >= 4000 or cpu_percentage >= 100:  # >= 4 CPU cores or 100%
            return 'critical'
        elif cpu_millicores >= 2000 or cpu_percentage >= 75:  # >= 2 CPU cores or 75%
            return 'high'
        elif cpu_millicores >= 1000 or cpu_percentage >= 50:  # >= 1 CPU core or 50%
            return 'moderate'
        else:
            return 'normal'

    def _categorize_cpu_usage(self, cpu_millicores: float) -> str:
        """Categorize CPU usage levels"""
        if cpu_millicores >= 2000:  # >= 2 CPU cores
            return 'very_high'
        elif cpu_millicores >= 1000:  # >= 1 CPU core
            return 'high'
        elif cpu_millicores >= 500:  # >= 0.5 CPU cores
            return 'moderate'
        else:
            return 'normal'

    def _convert_millicores_to_percentage(self, cpu_millicores: float) -> float:
        """Convert millicores to percentage (assuming 4-core nodes)"""
        return min(100.0, (cpu_millicores / 4000) * 100)  # 4000m = 4 cores = 100%

    def _convert_bytes_to_percentage(self, memory_bytes: float) -> float:
        """Convert bytes to percentage (assuming 16GB nodes)"""
        return min(100.0, (memory_bytes / (16 * 1024 * 1024 * 1024)) * 100)  # 16GB = 100%

    def _calculate_resource_concentration(self, workload_data: List[Dict]) -> Dict:
        """Calculate resource concentration metrics: Require real data"""
        if not workload_data:
            raise ValueError("No workload data provided for resource concentration calculation")
        
        cpu_values = [w.get('cpu_millicores', 0) for w in workload_data]
        memory_values = [w.get('memory_bytes', 0) for w in workload_data]
        
        # Top 20% resource consumers
        top_20_cpu = sorted(cpu_values, reverse=True)[:len(cpu_values)//5] if cpu_values else []
        top_20_memory = sorted(memory_values, reverse=True)[:len(memory_values)//5] if memory_values else []
        
        return {
            'cpu_concentration': sum(top_20_cpu) / sum(cpu_values) if sum(cpu_values) > 0 else 0,
            'memory_concentration': sum(top_20_memory) / sum(memory_values) if sum(memory_values) > 0 else 0,
            'top_cpu_consumer': max(cpu_values) if cpu_values else 0,
            'top_memory_consumer': max(memory_values) if memory_values else 0
        }    

    def _convert_nodes_text_to_basic_json(self, nodes_text: str) -> Dict[str, Any]:
        """Convert kubectl get nodes text output to basic JSON structure for fallback"""
        try:
            items = []
            lines = nodes_text.strip().split('\n')
            
            # Skip header line if present
            if lines and 'NAME' in lines[0]:
                lines = lines[1:]
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        node_name = parts[0]
                        status = parts[1] if len(parts) > 1 else 'Unknown'
                        
                        # Create basic node structure
                        items.append({
                            'metadata': {'name': node_name},
                            'status': {
                                'conditions': [{'type': 'Ready', 'status': 'True' if status == 'Ready' else 'False'}],
                                'allocatable': {'cpu': '4', 'memory': '16Gi'}  # Default values
                            }
                        })
            
            logger.info(f"✅ Converted {len(items)} nodes from text format")
            return {'items': items}
            
        except Exception as e:
            logger.error(f"❌ Failed to convert nodes text to JSON: {e}")
            return {'items': []}

    def _classify_hpa_scaling_strategy(self, cpu_metrics: List, memory_metrics: List, other_metrics: List) -> str:
        """Classify HPA scaling strategy based on actual metrics"""
        has_cpu = len(cpu_metrics) > 0
        has_memory = len(memory_metrics) > 0
        has_custom = len(other_metrics) > 0
        
        if has_custom and not has_cpu and not has_memory:
            return 'custom'
        elif has_cpu and has_memory:
            if len(cpu_metrics) > len(memory_metrics):
                return 'cpu_dominant'
            elif len(memory_metrics) > len(cpu_metrics):
                return 'memory_dominant'
            else:
                return 'mixed'
        elif has_cpu and not has_memory:
            return 'cpu_only'
        elif has_memory and not has_cpu:
            return 'memory_only'
        elif has_custom:
            return 'custom'
        else:
            return 'unknown'

    def _convert_hpa_text_to_basic_json(self, hpa_text: str) -> Dict[str, Any]:
        """Convert kubectl get hpa text output to basic JSON structure for fallback"""
        try:
            items = []
            lines = hpa_text.strip().split('\n')
            
            # Skip header line if present
            if lines and ('NAMESPACE' in lines[0] or 'NAME' in lines[0]):
                lines = lines[1:]
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        namespace = parts[0] if len(parts) > 2 else 'default'
                        name = parts[1] if len(parts) > 2 else parts[0]
                        target = parts[2] if len(parts) > 2 else 'unknown'
                        
                        # Create basic HPA structure
                        items.append({
                            'metadata': {'namespace': namespace, 'name': name},
                            'spec': {
                                'scaleTargetRef': {'name': target},
                                'minReplicas': 1,
                                'maxReplicas': 10
                            },
                            'status': {'currentReplicas': 1}
                        })
            
            logger.info(f"✅ Converted {len(items)} HPAs from text format")
            return {'items': items}
            
        except Exception as e:
            logger.error(f"❌ Failed to convert HPA text to JSON: {e}")
            return {'items': []}

    def _process_enhanced_node_data(self, top_nodes_output: str, node_info_json: str, pod_resources: Dict) -> Dict:
        """
         Process enhanced node data with resource requests
        """
        try:
            logger.info("🔧 Processing enhanced node data with resource requests...")
            
            # Parse node information with validation
            if not node_info_json or node_info_json.strip() == '':
                logger.warning("⚠️ Node info JSON is empty, cannot process enhanced node data")
                return {
                    'nodes': [],
                    'enhanced_data_available': False,
                    'error': 'Empty node_info_json',
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'empty_data_error'
                }
            
            try:
                nodes_data = json.loads(node_info_json)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse node_info_json: {e}")
                logger.error(f"📝 Node JSON preview: '{node_info_json[:100]}...'")
                return {
                    'nodes': [],
                    'enhanced_data_available': False,
                    'error': f'JSON decode error: {e}',
                    'timestamp': datetime.now().isoformat(),
                    'data_source': 'json_decode_error'
                }
            node_metrics = []
            
            # Parse top nodes output
            node_usage = {}
            if top_nodes_output:
                top_lines = top_nodes_output.strip().split('\n')
                for line in top_lines:
                    if line.strip() and not line.startswith('NAME'):
                        parts = line.split()
                        if len(parts) >= 5:
                            node_name = parts[0]
                            cpu_usage = self.parser.parse_cpu_safe(parts[1])
                            memory_usage = self.parser.parse_memory_safe(parts[3])
                            
                            node_usage[node_name] = {
                                'cpu_usage_cores': cpu_usage,
                                'memory_usage_bytes': memory_usage
                            }
            
            # Process each node with enhanced data
            for node in nodes_data.get('items', []):
                node_name = node['metadata']['name']
                
                # Get allocatable resources
                allocatable = node['status'].get('allocatable', {})
                cpu_allocatable = self.parser.parse_cpu_safe(allocatable.get('cpu', '0'))
                memory_allocatable = self.parser.parse_memory_safe(allocatable.get('memory', '0Ki'))
                
                # Get actual usage
                usage = node_usage.get(node_name, {})
                cpu_usage_cores = usage.get('cpu_usage_cores', cpu_allocatable * 0.35)
                memory_usage_bytes = usage.get('memory_usage_bytes', memory_allocatable * 0.60)
                
                # Calculate usage percentages
                cpu_usage_pct = (cpu_usage_cores / cpu_allocatable * 100) if cpu_allocatable > 0 else 35.0
                memory_usage_pct = (memory_usage_bytes / memory_allocatable * 100) if memory_allocatable > 0 else 60.0
                
                # NEW: Calculate request percentages from actual pod data
                node_pod_data = pod_resources.get(node_name, {})
                total_cpu_requests_cores = node_pod_data.get('total_cpu_requests', 0) / 1000
                total_memory_requests_bytes = node_pod_data.get('total_memory_requests', 0)
                
                # Calculate request percentages
                if cpu_allocatable > 0 and total_cpu_requests_cores > 0:
                    cpu_request_pct = (total_cpu_requests_cores / cpu_allocatable) * 100
                else:
                    # Intelligent estimation when no real request data
                    cpu_request_pct = min(100, cpu_usage_pct * 1.4 + 20)
                
                if memory_allocatable > 0 and total_memory_requests_bytes > 0:
                    memory_request_pct = (total_memory_requests_bytes / memory_allocatable) * 100
                else:
                    # Intelligent estimation when no real request data
                    memory_request_pct = min(100, memory_usage_pct * 1.3 + 25)
                
                # Get node status
                conditions = node['status'].get('conditions', [])
                ready_condition = next((c for c in conditions if c['type'] == 'Ready'), {})
                is_ready = ready_condition.get('status') == 'True'
                
                # Build enhanced node data
                enhanced_node = {
                    'name': node_name,
                    'cpu_usage_pct': round(cpu_usage_pct, 1),
                    'memory_usage_pct': round(memory_usage_pct, 1),
                    'cpu_request_pct': round(cpu_request_pct, 1),  # NEW: Real request data
                    'memory_request_pct': round(memory_request_pct, 1),  # NEW: Real request data
                    'cpu_allocatable_cores': cpu_allocatable,
                    'memory_allocatable_bytes': memory_allocatable,
                    'cpu_usage_cores': cpu_usage_cores,
                    'memory_usage_bytes': memory_usage_bytes,
                    'cpu_requests_cores': total_cpu_requests_cores,  # NEW
                    'memory_requests_bytes': total_memory_requests_bytes,  # NEW
                    'ready': is_ready,
                    'cpu_gap_pct': round(max(0, cpu_request_pct - cpu_usage_pct), 1),
                    'memory_gap_pct': round(max(0, memory_request_pct - memory_usage_pct), 1),
                    'pod_count': node_pod_data.get('pod_count', 0),  # NEW
                    'has_real_requests': total_cpu_requests_cores > 0 or total_memory_requests_bytes > 0  # NEW
                }
                
                node_metrics.append(enhanced_node)
                
                # Enhanced logging
                req_type = "REAL" if enhanced_node['has_real_requests'] else "ESTIMATED"
                logger.info(f"✅ {req_type} Node {node_name}: "
                        f"CPU={cpu_usage_pct:.1f}%/{cpu_request_pct:.1f}%, "
                        f"Memory={memory_usage_pct:.1f}%/{memory_request_pct:.1f}%, "
                        f"Pods={node_pod_data.get('pod_count', 0)}")
            
            return {
                'nodes': node_metrics,
                'total_nodes': len(node_metrics),
                'ready_nodes': sum(1 for n in node_metrics if n['ready']),
                'nodes_with_real_requests': sum(1 for n in node_metrics if n['has_real_requests']),
                'average_cpu_usage': round(sum(n['cpu_usage_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'average_memory_usage': round(sum(n['memory_usage_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'average_cpu_requests': round(sum(n['cpu_request_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'average_memory_requests': round(sum(n['memory_request_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'kubectl_enhanced_with_requests',
                'enhanced_data_available': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing enhanced node data: {e}")
            # Return empty structure to maintain compatibility
            return {
                'nodes': [],
                'enhanced_data_available': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'data_source': 'processing_error'
            }
        
    def _get_enhanced_node_resource_data(self) -> Dict[str, Any]:
        """
         Get comprehensive node data including resource requests/limits
        """
        try:
            logger.info("📊  Fetching enhanced node resource data...")
            
            # Get data from cache (already fetched in get_node_metrics)
            cache_data = self.cache.get_resource_usage_data()
            top_nodes = cache_data.get('node_usage', '')
            
            # Check if metrics server data is available
            if not top_nodes:
                logger.info("📊 Metrics server data unavailable, using resource request estimates")
            
            # Use your original fallback strategy: Try JSON first, then text format
            node_info = cache_data.get('nodes', {})
            
            # If JSON is empty or problematic, fallback to text format
            if not node_info or (isinstance(node_info, dict) and not node_info.get('items')):
                logger.warning("🔄 JSON nodes data empty or invalid, attempting text format fallback")
                logger.info(f"🔍 Debug: node_info type={type(node_info)}, content preview: {str(node_info)[:100]}...")
                
                nodes_text = cache_data.get('nodes_text', '')
                logger.info(f"🔍 Debug: nodes_text length={len(nodes_text)}, preview: '{nodes_text[:100]}...'")
                
                if nodes_text and nodes_text.strip():
                    # Convert text to basic structure for processing
                    logger.info("🔄 Converting nodes text to JSON structure...")
                    node_info = self._convert_nodes_text_to_basic_json(nodes_text)
                    logger.info(f"✅ Converted to {len(node_info.get('items', []))} nodes from text format")
                else:
                    logger.error("❌ Both JSON and text node data unavailable from cache")
                    # Let's check what keys are actually available in cache
                    available_keys = list(cache_data.keys())
                    logger.error(f"📋 Available cache keys: {available_keys[:10]}...")  # Show first 10 keys
                    node_info = {'items': []}
            
            # Step 3: NEW - Get pod resource requests per node
            pod_resources = self._get_pod_resource_requests_by_node()
            
            # Step 4: Process and combine all data
            # Convert node_info dict to JSON string if needed
            if isinstance(node_info, dict):
                node_info_json = json.dumps(node_info)
            else:
                node_info_json = node_info
            return self._process_enhanced_node_data(top_nodes, node_info_json, pod_resources)
            
        except Exception as e:
            logger.error(f"❌ Enhanced node resource data failed: {e}")
            # Return empty structure to maintain compatibility
            return {
                'enhanced_data_available': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'data_source': 'error_fallback'
            }
        
    def _get_pod_resource_requests_by_node(self) -> Dict[str, Dict]:
        """
        COMPLETELY  Pod resource requests with better JSON handling
        """
        try:
            logger.info("🚀 Fetching pod resource requests from CACHE...")
            
            # Get data from cache instead of individual kubectl calls
            cache_data = self.cache.get_resource_usage_data()
            
            # Method 1: Use cached custom columns data (most efficient)
            describe_output = cache_data.get('pod_resources', '')
            if describe_output:
                logger.info("✅ Using cached custom columns data for resource requests")
                return self._parse_custom_columns_resource_requests(describe_output)
            
            # Method 2: Use cached basic pod data as fallback
            basic_output = cache_data.get('pods_basic', '')
            if basic_output:
                logger.info("✅ Using cached basic pod listing for resource estimation")
                return self._estimate_resource_requests_from_basic_data(basic_output)
            
            logger.warning("⚠️ No pod resource data available in cache")
            
            # All fetching methods failed - no real data available
            logger.error("❌ All pod resource collection methods failed to fetch data from cluster")
            raise ValueError("Failed to collect pod resource data from cluster using any fetching method")
            
        except Exception as e:
            logger.error(f"❌ Pod resource requests collection failed: {e}")
            # No fallback, fail if real data unavailable
            raise ValueError(f"Failed to collect pod resource requests: {e}")

    def _estimate_resource_requests_from_basic_data(self, output: str) -> Dict[str, Dict]:
        """Estimate resource requests from basic pod data"""
        try:
            # Count pods per node and estimate resources
            node_pod_counts = {}
            lines = output.strip().split('\n')
            
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 7:  # Basic pod format
                    namespace = parts[0]
                    # Skip system namespaces for estimation
                    if namespace not in ['kube-system', 'kube-public', 'kube-node-lease']:
                        # Extract node name (usually last field or second to last)
                        node_name = parts[-2] if len(parts) > 7 else 'unknown'
                        
                        if node_name != 'unknown' and '/' not in node_name:
                            if node_name not in node_pod_counts:
                                node_pod_counts[node_name] = 0
                            node_pod_counts[node_name] += 1
            
            # Estimate resources based on pod counts
            node_resources = {}
            for node_name, pod_count in node_pod_counts.items():
                # Conservative estimates: 100m CPU and 128Mi memory per pod
                estimated_cpu = pod_count * 100  # millicores
                estimated_memory = pod_count * 128 * 1024 * 1024  # bytes
                
                node_resources[node_name] = {
                    'total_cpu_requests': estimated_cpu,
                    'total_memory_requests': estimated_memory,
                    'pod_count': pod_count,
                    'containers': [],
                    'estimation_method': 'basic_pod_count'
                }
            
            logger.info(f"✅  Estimated resources for {len(node_resources)} nodes")
            return node_resources
            
        except Exception as e:
            logger.error(f"❌ Basic estimation failed: {e}")
            # No fallback, fail if real data unavailable
            raise ValueError(f"Failed to estimate resource requests from basic data: {e}")
        
    def _parse_custom_columns_resource_requests(self, output: str) -> Dict[str, Dict]:
        """Parse custom columns output for resource requests"""
        try:
            node_resources = {}
            lines = output.strip().split('\n')
            
            for line in lines[1:]:  # Skip header
                if not line.strip():
                    continue
                    
                parts = line.split()
                if len(parts) >= 5:
                    namespace = parts[0]
                    pod_name = parts[1]
                    cpu_req_str = parts[2] if parts[2] != '<none>' else '0'
                    mem_req_str = parts[3] if parts[3] != '<none>' else '0'
                    node_name = parts[4] if parts[4] != '<none>' else 'unknown'
                    
                    if node_name != 'unknown' and node_name != 'NODE':
                        if node_name not in node_resources:
                            node_resources[node_name] = {
                                'total_cpu_requests': 0,
                                'total_memory_requests': 0,
                                'pod_count': 0,
                                'containers': []
                            }
                        
                        # Parse CPU
                        cpu_millicores = self.parser.parse_cpu_safe(cpu_req_str) * 1000
                        memory_bytes = self.parser.parse_memory_safe(mem_req_str)
                        
                        node_resources[node_name]['total_cpu_requests'] += cpu_millicores
                        node_resources[node_name]['total_memory_requests'] += memory_bytes
                        node_resources[node_name]['pod_count'] += 1
                        
                        node_resources[node_name]['containers'].append({
                            'pod': pod_name,
                            'namespace': namespace,
                            'cpu_request_millicores': cpu_millicores,
                            'memory_request_bytes': memory_bytes
                        })
            
            logger.info(f"✅  Parsed resource requests for {len(node_resources)} nodes")
            return node_resources
            
        except Exception as e:
            logger.error(f"❌ Custom columns parsing failed: {e}")
            # No fallback, fail if real data unavailable  
            raise ValueError(f"Failed to parse custom columns resource requests: {e}")

    def get_hpa_metrics_with_high_cpu_detection(self) -> Dict:
        """
        MAIN METHOD: Get HPA metrics with proper high CPU detection
        Use this instead of the failing _get_detailed_hpa_metrics method
        """
        try:
            logger.info("🔍  Getting HPA metrics with high CPU detection...")
            
            # Try the most reliable method first
            result = self._get_detailed_hpa_metrics()
            
            # Add debugging information
            result['debug_info'] = {
                'large_output_handling': True,
                'high_cpu_detection_active': True,
                'parsing_strategies': ['custom_columns', 'chunked_json', 'basic_text'],
                'timestamp': datetime.now().isoformat()
            }
            
            if result['total_hpas'] > 0:
                logger.info(f"✅ Successfully detected {result['total_hpas']} HPAs using {result.get('parsing_method', 'unknown')} method")
                
                if result['high_cpu_hpas']:
                    max_cpu = max([hpa['cpu_utilization'] for hpa in result['high_cpu_hpas']])
                    logger.info(f"🔥 Highest CPU detected: {max_cpu}%")
                else:
                    logger.info("📊 No high CPU HPAs detected (all under 200%)")
            else:
                logger.warning("⚠️ No HPAs found in cluster")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ HPA metrics with high CPU detection failed: {e}")
            return {
                'current_hpa_pattern': 'detection_failed',
                'confidence': 'low',
                'total_hpas': 0,
                'high_cpu_hpas': [],
                'error': str(e)
            }

    def _clean_command_output(self, raw_output: str) -> str:
        """ENHANCED: Clean kubectl output with better large output handling"""
        try:
            if not raw_output:
                return ""
            
            # For very large outputs, use chunked processing
            if len(raw_output) > 500000:  # 500KB
                logger.warning(f"⚠️ ENHANCED: Processing large output ({len(raw_output)} chars)")
                return self._process_large_output_in_chunks(raw_output)
            
            # Remove command metadata lines
            lines = raw_output.split('\n')
            clean_lines = []
            
            for line in lines:
                # Skip Azure CLI metadata lines
                if any(skip_pattern in line.lower() for skip_pattern in [
                    'command started at',
                    'command finished at',
                    'exitcode=',
                    'command started',
                    'command finished'
                ]):
                    continue
                clean_lines.append(line)
            
            clean_output = '\n'.join(clean_lines).strip()
            
            # For JSON output, try to find and extract valid JSON
            if '{' in clean_output and '}' in clean_output:
                return self._extract_valid_json_safely(clean_output)
            
            return clean_output
            
        except Exception as e:
            logger.error(f"❌ ENHANCED: Error cleaning command output: {e}")
            return raw_output

    def _process_large_output_in_chunks(self, large_output: str) -> str:
        """Process large output in chunks to avoid JSON parsing issues"""
        try:
            # For JSON outputs that are too large, switch to text format
            logger.info("🔄 ENHANCED: Processing large output, switching to text format")
            
            # Try to identify if this is JSON that got truncated
            if large_output.strip().startswith('{'):
                # This was supposed to be JSON but got truncated
                logger.warning("⚠️ ENHANCED: Large JSON detected, likely truncated")
                return ""  # Return empty to trigger fallback
            
            # For text output, just clean and return
            return large_output.strip()
            
        except Exception as e:
            logger.error(f"❌ Large output processing failed: {e}")
            return large_output

    def _extract_valid_json_safely(self, clean_output: str) -> str:
        """Safely extract valid JSON from cleaned output"""
        try:
            # Find the start and end of JSON
            start_idx = clean_output.find('{')
            if start_idx == -1:
                return clean_output
            
            # For large JSON, try to find a reasonable end point
            if len(clean_output) > 400000:  # 400KB
                logger.warning("⚠️ ENHANCED: JSON too large, truncating safely")
                # Try to find a good breaking point
                truncate_point = min(400000, len(clean_output))
                clean_output = clean_output[:truncate_point]
            
            # Find the last closing brace
            end_idx = clean_output.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_content = clean_output[start_idx:end_idx]
                
                # Validate it's proper JSON
                try:
                    json.loads(json_content)
                    return json_content
                except json.JSONDecodeError as json_error:
                    logger.warning(f"⚠️ ENHANCED: JSON validation failed: {json_error}")
                    return ""  # Return empty to trigger fallback
            
            return clean_output
            
        except Exception as e:
            logger.error(f"❌ JSON extraction failed: {e}")
            return clean_output

    def verify_cluster_connection(self) -> bool:
        """Verify AKS cluster connectivity with subscription context"""
        try:
            subscription_info = f" in subscription {self.subscription_id[:8]}" if self.subscription_id else ""
            logger.info(f"Verifying connection to AKS cluster {self.cluster_name}{subscription_info}")
            
            # Build verification command with subscription context
            cmd = [
                'az', 'aks', 'command', 'invoke',
                '--resource-group', self.resource_group,
                '--name', self.cluster_name,
                '--command', 'kubectl cluster-info'
            ]
            
            # Add subscription context if available
            if self.subscription_id:
                cmd.extend(['--subscription', self.subscription_id])
            
            logger.info(f"🔧 DEBUG: Executing verification command with subscription context")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            logger.info(f"🔧 DEBUG: Return code: {result.returncode}")
            logger.info(f"🔧 DEBUG: STDOUT length: {len(result.stdout)}")
            logger.info(f"🔧 DEBUG: STDERR: {result.stderr}")
            
            if result.returncode == 0 and result.stdout.strip():
                # Check if the output contains cluster info (even with metadata)
                if "Kubernetes control plane" in result.stdout or "Kubernetes master" in result.stdout:
                    logger.info(f"✅ Successfully connected to AKS cluster{subscription_info}")
                    self.connection_verified = True
                    return True
                else:
                    logger.warning(f"⚠️ Connected but no cluster info found{subscription_info}")
                    # Still consider it successful if we got a response
                    self.connection_verified = True
                    return True
            else:
                if "ResourceGroupNotFound" in result.stderr and self.subscription_id:
                    logger.error(f"❌ Cluster verification failed: Resource group not found in subscription {self.subscription_id[:8]}")
                    logger.error(f"❌ Please verify the subscription ID and resource group are correct")
                else:
                    logger.error(f"❌ Failed to verify cluster connection. Return code: {result.returncode}")
                    logger.error(f"❌ STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Connection timeout to AKS cluster")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during connection verification: {e}")
            return False

    def execute_kubectl_command(self, kubectl_cmd: str, timeout: int = 60) -> Optional[str]:
        """
        SINGLE SOURCE OF TRUTH: All kubectl commands go through cache
        No direct kubectl execution - everything comes from centralized cache
        """
        logger.debug(f"🎯 Querying cache for: {kubectl_cmd[:50]}...")
        
        try:
            cache_data = self.cache.get_all_data()
            
            # Map kubectl commands to cache keys - COMPLETE MAPPING
            if "kubectl top nodes" in kubectl_cmd:
                if "--no-headers" in kubectl_cmd:
                    return cache_data.get('node_usage', '')
                else:
                    return cache_data.get('node_usage_headers', '')
            elif "kubectl get nodes" in kubectl_cmd:
                if "-o json" in kubectl_cmd:
                    nodes_data = cache_data.get('nodes', {})
                    return json.dumps(nodes_data) if nodes_data else None
                else:
                    return cache_data.get('nodes_text', '')
            elif "kubectl top pods" in kubectl_cmd:
                if "--no-headers" in kubectl_cmd:
                    return cache_data.get('pod_usage', '')
                else:
                    return cache_data.get('pod_usage_headers', '')
            elif "kubectl get hpa" in kubectl_cmd:
                if "custom-columns" in kubectl_cmd:
                    return cache_data.get('hpa_custom', '')
                elif "--no-headers" in kubectl_cmd:
                    return cache_data.get('hpa_no_headers', '')
                elif "--all-namespaces" in kubectl_cmd and "-o json" in kubectl_cmd:
                    hpa_data = cache_data.get('hpa', {})
                    return json.dumps(hpa_data) if hpa_data else None
                elif "--all-namespaces" in kubectl_cmd:
                    return cache_data.get('hpa_text', '')
                else:
                    return cache_data.get('hpa_basic', '')
            
            # For any unmapped commands, use dynamic execution
            logger.debug(f"⚠️ Unmapped command, using dynamic execution: {kubectl_cmd[:30]}...")
            return self.cache.execute_dynamic_command(kubectl_cmd, timeout)
            
        except Exception as e:
            logger.error(f"❌ Cache query failed for {kubectl_cmd[:30]}...: {e}")
            return None

    def _safe_kubectl_command(self, kubectl_cmd: str, timeout: int = 60) -> Optional[str]:
        """Safe kubectl command execution with fallback"""
        return self.execute_kubectl_command(kubectl_cmd, timeout)
    
    def _safe_kubectl_yaml_command(self, kubectl_cmd: str, timeout: int = 60) -> Optional[Dict]:
        """Safe kubectl YAML/JSON command execution"""
        try:
            output = self.execute_kubectl_command(kubectl_cmd, timeout)
            if output:
                return json.loads(output)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ YAML command failed: {e}")
            return None

    def get_node_metrics(self) -> Dict[str, Any]:
        """Get node metrics using centralized cache (PERFORMANCE OPTIMIZED)"""
        logger.info("🚀 Fetching real-time node metrics from CACHE...")
        
        try:
            # Get data from cache (data is auto-fetched when cache is created)
            cache_data = self.cache.get_resource_usage_data()
            top_nodes = cache_data.get('node_usage', '')
            node_info = cache_data.get('nodes', {})
            
            if not top_nodes:
                logger.warning("⚠️ No node usage data in cache")
            else:
                logger.info(f"✅ Node usage from cache: {len(top_nodes)} chars")
            
            if not node_info:
                logger.warning("⚠️ No node info data in cache")
            else:
                logger.info(f"✅ Node info from cache: {len(node_info.get('items', []))} nodes")
            
            if not node_info:
                logger.error("❌ Could not fetch node information")
                return self._empty_node_metrics()
            
            return self._process_node_metrics(top_nodes, node_info)
            
        except Exception as e:
            logger.error(f"❌ Error fetching node metrics: {e}")
            return self._empty_node_metrics()

    def _process_node_metrics(self, top_nodes_output: Optional[str], node_info_json: str) -> Dict[str, Any]:
        """Process node metrics with better JSON handling"""
        try:
            logger.info("🔧 DEBUG: Processing node metrics...")
            
            # Parse node information JSON
            try:
                nodes_data = json.loads(node_info_json)
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed: {e}")
                logger.error(f"❌ JSON preview: {node_info_json[:500]}...")
                return self._empty_node_metrics()
            
            node_metrics = []
            
            # Parse top nodes output if available
            node_usage = {}
            if top_nodes_output:
                logger.info(f"🔧 DEBUG: Processing top nodes output: {len(top_nodes_output)} chars")
                top_lines = top_nodes_output.strip().split('\n')
                
                for line_idx, line in enumerate(top_lines):
                    if line.strip() and not line.startswith('NAME'):
                        parts = line.split()
                        logger.info(f"🔧 DEBUG: Line {line_idx}: {line}")
                        
                        if len(parts) >= 5:
                            node_name = parts[0]
                            cpu_usage = self.parser.parse_cpu_safe(parts[1])
                            memory_usage = self.parser.parse_memory_safe(parts[3])
                            
                            node_usage[node_name] = {
                                'cpu_usage_cores': cpu_usage,
                                'memory_usage_bytes': memory_usage
                            }
                            
                            logger.info(f"✅ Parsed node {node_name}: CPU={cpu_usage}, Memory={memory_usage}")
            else:
                logger.warning("⚠️ No top nodes data - using capacity estimates")
            
            # Process each node
            for node in nodes_data.get('items', []):
                node_name = node['metadata']['name']
                
                # Get allocatable resources
                allocatable = node['status'].get('allocatable', {})
                cpu_allocatable = self.parser.parse_cpu_safe(allocatable.get('cpu', '0'))
                memory_allocatable = self.parser.parse_memory_safe(allocatable.get('memory', '0Ki'))
                
                # Get usage data or use estimates
                if node_name in node_usage:
                    usage = node_usage[node_name]
                    cpu_usage_pct = (usage['cpu_usage_cores'] / cpu_allocatable * 100) if cpu_allocatable > 0 else 0
                    memory_usage_pct = (usage['memory_usage_bytes'] / memory_allocatable * 100) if memory_allocatable > 0 else 0
                else:
                    # Realistic estimates when metrics unavailable
                    logger.warning(f"⚠️ No usage data for {node_name}, using estimates")
                    cpu_usage_pct = 35.0
                    memory_usage_pct = 60.0
                    usage = {
                        'cpu_usage_cores': cpu_allocatable * 0.35,
                        'memory_usage_bytes': int(memory_allocatable * 0.60)
                    }
                
                # Get node status
                conditions = node['status'].get('conditions', [])
                ready_condition = next((c for c in conditions if c['type'] == 'Ready'), {})
                is_ready = ready_condition.get('status') == 'True'
                
                node_metrics.append({
                    'name': node_name,
                    'cpu_usage_pct': round(cpu_usage_pct, 1),
                    'memory_usage_pct': round(memory_usage_pct, 1),
                    'cpu_allocatable_cores': cpu_allocatable,
                    'memory_allocatable_bytes': memory_allocatable,
                    'cpu_usage_cores': usage['cpu_usage_cores'],
                    'memory_usage_bytes': usage['memory_usage_bytes'],
                    'ready': is_ready,
                    'cpu_gap_pct': max(0, round(100 - cpu_usage_pct, 1)),
                    'memory_gap_pct': max(0, round(100 - memory_usage_pct, 1))
                })
                
                logger.info(f"✅ Node {node_name}: CPU={cpu_usage_pct:.1f}%, Memory={memory_usage_pct:.1f}%, Ready={is_ready}")
            
            logger.info(f"✅ Successfully processed {len(node_metrics)} nodes")
            
            return {
                'nodes': node_metrics,
                'total_nodes': len(node_metrics),
                'ready_nodes': sum(1 for n in node_metrics if n['ready']),
                'average_cpu_usage': round(sum(n['cpu_usage_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'average_memory_usage': round(sum(n['memory_usage_pct'] for n in node_metrics) / len(node_metrics), 1) if node_metrics else 0,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'kubectl_enhanced'
            }
            
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


    def get_hpa_implementation_status(self) -> Dict[str, Any]:
        """Get HPA implementation status with ENHANCED metrics extraction from cache"""
        logger.info("🔍 Detecting current HPA implementation with ENHANCED metrics extraction from cache...")
        
        try:
            # STEP 1: Get basic HPA list with text output to avoid JSON truncation
            # Use cached HPA data with fallback strategy  
            cache_data = self.cache.get_resource_usage_data()
            hpa_data = cache_data.get('hpa', {})
            
            # Handle case where hpa_data might be a string (JSON) instead of dict
            if isinstance(hpa_data, str):
                try:
                    hpa_data = json.loads(hpa_data) if hpa_data.strip() else {}
                except json.JSONDecodeError:
                    logger.warning("⚠️ Failed to parse HPA JSON data")
                    hpa_data = {}
            
            # If JSON is empty or problematic, fallback to text format 
            if not hpa_data or (isinstance(hpa_data, dict) and not hpa_data.get('items')):
                logger.info("🔄 HPA JSON data empty, using text format fallback")
                hpa_text = cache_data.get('hpa_text', '') or cache_data.get('hpa_custom', '')
                if hpa_text:
                    # Convert text to basic structure for processing
                    hpa_data = self._convert_hpa_text_to_basic_json(hpa_text)
                else:
                    logger.warning("⚠️ Both JSON and text HPA data unavailable")
                    hpa_data = {'items': []}
            
            # FIXED: Extract REAL CPU/Memory metrics from spec.metrics instead of using defaults
            hpa_details = []  # Store complete HPA details with metrics for chart generator
            if hpa_data and 'items' in hpa_data:
                logger.info(f"🔍 Processing {len(hpa_data['items'])} HPAs from cache with complete metrics extraction")
                
                for item in hpa_data['items']:
                    metadata = item.get('metadata', {})
                    spec = item.get('spec', {})
                    status = item.get('status', {})
                    
                    namespace = metadata.get('namespace', '')
                    name = metadata.get('name', '')
                    min_replicas = spec.get('minReplicas', 1)
                    max_replicas = spec.get('maxReplicas', 10)
                    current_replicas = status.get('currentReplicas', 1)
                    target_ref = spec.get('scaleTargetRef', {}).get('name', '')
                    
                    # CRITICAL FIX: Extract actual CPU/Memory metrics from spec.metrics
                    metrics = spec.get('metrics', [])
                    cpu_metrics = []
                    memory_metrics = []
                    other_metrics = []
                    
                    for metric in metrics:
                        if metric.get('type') == 'Resource':
                            resource_name = metric.get('resource', {}).get('name', '')
                            target = metric.get('resource', {}).get('target', {})
                            
                            if resource_name == 'cpu':
                                target_value = target.get('averageUtilization', target.get('averageValue', 'unknown'))
                                cpu_metrics.append({
                                    'type': 'cpu',
                                    'target_value': target_value,
                                    'target_type': 'averageUtilization' if 'averageUtilization' in target else 'averageValue'
                                })
                            elif resource_name == 'memory':
                                target_value = target.get('averageUtilization', target.get('averageValue', 'unknown'))
                                memory_metrics.append({
                                    'type': 'memory', 
                                    'target_value': target_value,
                                    'target_type': 'averageUtilization' if 'averageUtilization' in target else 'averageValue'
                                })
                        else:
                            # Custom metrics (Pods, Object, External)
                            other_metrics.append({
                                'type': metric.get('type', 'unknown'),
                                'details': metric
                            })
                    
                    # Create complete HPA detail with REAL metrics classification
                    hpa_detail = {
                        'namespace': namespace,
                        'name': name,
                        'current_replicas': str(current_replicas),
                        'min_replicas': str(min_replicas),
                        'max_replicas': str(max_replicas),
                        'hpa_id': f"{namespace}/{name}",
                        'target_ref': target_ref,
                        'cpu_metrics': cpu_metrics,
                        'memory_metrics': memory_metrics,
                        'other_metrics': other_metrics,
                        'scaling_strategy': self._classify_hpa_scaling_strategy(cpu_metrics, memory_metrics, other_metrics)
                    }
                    hpa_details.append(hpa_detail)
                    
                    logger.debug(f"📊 HPA Detail: {namespace}/{name} = Strategy: {hpa_detail['scaling_strategy']}, "
                               f"CPU metrics: {len(cpu_metrics)}, Memory metrics: {len(memory_metrics)}, "
                               f"Current:{current_replicas}, Min:{min_replicas}, Max:{max_replicas}")
                
                logger.info(f"✅ Extracted complete metrics from {len(hpa_details)} HPAs")
            
            # Process the extracted HPA details to generate summary statistics
            hpa_count = len(hpa_details)
            cpu_based = sum(1 for hpa in hpa_details if hpa['scaling_strategy'] in ['cpu_only', 'cpu_dominant'])
            memory_based = sum(1 for hpa in hpa_details if hpa['scaling_strategy'] in ['memory_only', 'memory_dominant']) 
            mixed_based = sum(1 for hpa in hpa_details if hpa['scaling_strategy'] == 'mixed')
            custom_based = sum(1 for hpa in hpa_details if hpa['scaling_strategy'] == 'custom')
            hpa_list = [hpa['hpa_id'] for hpa in hpa_details[:10]]  # Limit to first 10 for display
            
            # Determine pattern based on REAL metrics classification
            if hpa_count == 0:
                pattern = 'no_hpa_detected'
                confidence = 'high'
            elif cpu_based > 0 and memory_based == 0 and custom_based == 0:
                pattern = 'cpu_based_dominant'
                confidence = 'high'  # High confidence because based on actual metrics
            elif memory_based > 0 and cpu_based == 0 and custom_based == 0:
                pattern = 'memory_based_dominant'
                confidence = 'high'  # High confidence because based on actual metrics
            elif mixed_based > 0:
                pattern = 'mixed_implementation'
                confidence = 'high'  # High confidence because based on actual metrics
            elif custom_based > 0:
                pattern = 'custom_metrics_based'
                confidence = 'high'  # High confidence because based on actual metrics  
            elif cpu_based > memory_based:
                pattern = 'cpu_based_dominant'
                confidence = 'high'  # High confidence because based on actual metrics
            elif memory_based > cpu_based:
                pattern = 'memory_based_dominant'
                confidence = 'high'  # High confidence because based on actual metrics
            else:
                pattern = 'mixed_implementation'
                confidence = 'high'  # High confidence because based on actual metrics
            
            logger.info(f"✅ HPA detection: {hpa_count} HPAs found, pattern: {pattern}")
            logger.info(f"✅ Metrics breakdown: CPU-based:{cpu_based}, Memory-based:{memory_based}, Mixed:{mixed_based}, Custom:{custom_based}")
            logger.info(f"✅ Collected {len(hpa_details)} HPA replica details with COMPLETE metrics for chart generator")
            
            return {
                'current_hpa_pattern': pattern,
                'confidence': confidence,
                'total_hpas': hpa_count,
                'hpa_list': hpa_list[:10],  # Limit to first 10 for display
                'hpa_details': hpa_details,  # ENHANCED: Complete HPA details with real metrics classification
                'cpu_based_count': cpu_based,
                'memory_based_count': memory_based,
                'mixed_based_count': mixed_based,
                'custom_based_count': custom_based,
                'analysis_timestamp': datetime.now().isoformat(),
                'detection_method': 'real_metrics_extraction_from_cache'
            }
            
        except Exception as e:
            logger.error(f"❌ HPA detection failed: {e}")
            return {
                'current_hpa_pattern': 'detection_failed',
                'confidence': 'low',
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }

    def _get_enhanced_node_metrics(self) -> Dict[str, Any]:
        """Get enhanced node metrics with additional ML features"""
        try:
            logger.info("📊 Fetching enhanced node metrics for ML analysis...")
            
            # Get base node metrics using existing method
            base_metrics = self.get_node_metrics()
            
            if not base_metrics.get('nodes'):
                logger.warning("⚠️ No base node metrics available")
                return base_metrics
            
            # Enhance node data with additional ML features
            enhanced_nodes = []
            nodes = base_metrics['nodes']
            
            for node in nodes:
                enhanced_node = node.copy()
                
                # Calculate additional features for ML
                cpu_usage = node.get('cpu_usage_pct', 0)
                memory_usage = node.get('memory_usage_pct', 0)
                
                # Add efficiency ratios
                enhanced_node['cpu_efficiency_ratio'] = self._calculate_cpu_efficiency(cpu_usage)
                enhanced_node['memory_efficiency_ratio'] = self._calculate_memory_efficiency(memory_usage)
                
                # Add resource balance indicator
                enhanced_node['resource_balance_score'] = 1 - abs(cpu_usage - memory_usage) / 100
                
                # Add utilization category
                enhanced_node['utilization_category'] = self._categorize_utilization(cpu_usage, memory_usage)
                
                # Add gaps if not already present
                if 'cpu_gap_pct' not in enhanced_node:
                    enhanced_node['cpu_gap_pct'] = max(0, 100 - cpu_usage)
                    enhanced_node['memory_gap_pct'] = max(0, 100 - memory_usage)
                
                enhanced_nodes.append(enhanced_node)
            
            # Update metrics with enhanced data
            enhanced_metrics = base_metrics.copy()
            enhanced_metrics['nodes'] = enhanced_nodes
            
            # Add cluster-level ML features
            enhanced_metrics.update(self._calculate_cluster_ml_features(enhanced_nodes))
            
            logger.info(f"✅ Enhanced {len(enhanced_nodes)} nodes with ML features")
            return enhanced_metrics
            
        except Exception as e:
            logger.error(f"❌ Enhanced node metrics failed: {e}")
            # No fallback, fail if real data unavailable
            raise ValueError(f"Failed to collect enhanced node metrics: {e}")

    def _calculate_cpu_efficiency(self, cpu_usage: float) -> float:
        """Calculate CPU efficiency score (optimal around 70%)"""
        optimal_cpu = 70
        
        if cpu_usage <= 0:
            return 0.0
        elif cpu_usage <= optimal_cpu:
            # For normal/low CPU: Use improved scaling for better display values
            # This gives more meaningful efficiency scores for normal usage
            base_efficiency = cpu_usage / optimal_cpu
            
            # Apply a curve that makes normal CPU usage show reasonable efficiency
            # For example: 35% CPU → ~75% efficiency instead of 50%
            if cpu_usage <= 35:
                # Lower usage gets boosted efficiency (well-optimized systems)
                return min(1.0, base_efficiency * 1.5)
            else:
                # Near-optimal usage gets good efficiency
                return base_efficiency
        else:
            # For high CPU: Penalize over-utilization
            return max(0.1, optimal_cpu / cpu_usage)

    def _calculate_memory_efficiency(self, memory_usage: float) -> float:
        """Calculate memory efficiency score (optimal around 75%)"""
        optimal_memory = 75
        if memory_usage <= optimal_memory:
            return memory_usage / optimal_memory
        else:
            return max(0.1, optimal_memory / memory_usage)

    def _categorize_utilization(self, cpu_usage: float, memory_usage: float) -> str:
        """Categorize node utilization pattern"""
        if cpu_usage > 80 or memory_usage > 85:
            return 'high_utilization'
        elif cpu_usage < 30 and memory_usage < 40:
            return 'low_utilization'
        elif abs(cpu_usage - memory_usage) > 30:
            return 'imbalanced_utilization'
        else:
            return 'balanced_utilization'

    def _calculate_cluster_ml_features(self, nodes: List[Dict]) -> Dict:
        """Calculate cluster-level features for ML - Require real data"""
        if not nodes:
            raise ValueError("No node data provided for cluster ML features calculation")
        
        cpu_values = [node.get('cpu_usage_pct', 0) for node in nodes]
        memory_values = [node.get('memory_usage_pct', 0) for node in nodes]
        
        return {
            'cluster_cpu_variance': float(np.var(cpu_values)),
            'cluster_memory_variance': float(np.var(memory_values)),
            'cluster_avg_cpu': float(np.mean(cpu_values)),
            'cluster_avg_memory': float(np.mean(memory_values)),
            'cluster_efficiency_score': float(np.mean([
                node.get('cpu_efficiency_ratio', 0.5) * 0.6 + 
                node.get('memory_efficiency_ratio', 0.5) * 0.4 
                for node in nodes
            ])),
            'cluster_balance_score': float(np.mean([
                node.get('resource_balance_score', 0.5) for node in nodes
            ])),
            'high_utilization_nodes': len([
                node for node in nodes 
                if node.get('utilization_category') == 'high_utilization'
            ]),
            'low_utilization_nodes': len([
                node for node in nodes 
                if node.get('utilization_category') == 'low_utilization'
            ])
        }
    
    def _parse_hpa_custom_columns(self, output: str) -> Dict:
        """Parse HPA data from custom columns output"""
        try:
            lines = output.strip().split('\n')
            
            hpa_details = []
            high_cpu_hpas = []
            cpu_based_count = 0
            memory_based_count = 0
            
            # Skip header line
            for line in lines[1:] if len(lines) > 1 else []:
                if not line.strip():
                    continue
                    
                parts = line.split()
                if len(parts) >= 7:
                    namespace = parts[0]
                    name = parts[1]
                    current_cpu_str = parts[2]
                    target_cpu_str = parts[3]
                    min_replicas = parts[4]
                    max_replicas = parts[5]
                    current_replicas = parts[6]
                    
                    # Parse CPU values
                    try:
                        # Handle multiple values or <none>
                        if current_cpu_str != '<none>' and current_cpu_str != '<unknown>':
                            # Take first value if comma-separated
                            current_cpu_val = current_cpu_str.split(',')[0]
                            if current_cpu_val.replace('.', '').isdigit():
                                current_cpu = float(current_cpu_val)
                                
                                hpa_detail = {
                                    'namespace': namespace,
                                    'name': name,
                                    'current_cpu': current_cpu,
                                    'target_cpu': target_cpu_str,
                                    'min_replicas': min_replicas,
                                    'max_replicas': max_replicas,
                                    'current_replicas': current_replicas
                                }
                                
                                hpa_details.append(hpa_detail)
                                cpu_based_count += 1
                                
                                # DETECT HIGH CPU
                                if current_cpu > 100:  # > 100% CPU (anything above target is high)
                                    severity = 'critical' if current_cpu > 1000 else 'high'
                                    high_cpu_hpas.append({
                                        'namespace': namespace,
                                        'name': name,
                                        'cpu_utilization': current_cpu,
                                        'severity': severity,
                                        'target_cpu': target_cpu_str,
                                        'current_replicas': current_replicas
                                    })
                                    
                                    logger.info(f"🔥 HIGH CPU HPA DETECTED: {namespace}/{name} = {current_cpu}% (target: {target_cpu_str}%)")
                                
                    except ValueError:
                        logger.debug(f"Could not parse CPU values for {namespace}/{name}: {current_cpu_str}")
                        continue
            
            # Determine pattern
            total_hpas = len(hpa_details)
            if total_hpas == 0:
                pattern = 'no_hpa_detected'
                confidence = 'high'
            elif cpu_based_count > 0:
                pattern = 'cpu_based_dominant'
                confidence = 'high'
            else:
                pattern = 'mixed_implementation'
                confidence = 'medium'
            
            return {
                'current_hpa_pattern': pattern,
                'confidence': confidence,
                'total_hpas': total_hpas,
                'high_cpu_hpas': high_cpu_hpas,
                'hpa_details': hpa_details,
                'cpu_based_count': cpu_based_count,
                'parsing_method': 'custom_columns'
            }
            
        except Exception as e:
            logger.error(f"❌ Custom columns parsing failed: {e}")
            return {'total_hpas': 0, 'parsing_method': 'custom_columns_failed'}

    def _parse_hpa_json_safe(self, hpa_data: Dict) -> Dict:
        """Safely parse HPA JSON data with chunking support"""
        try:
            hpa_items = hpa_data.get('items', [])
            
            hpa_details = []
            high_cpu_hpas = []
            cpu_based_count = 0
            memory_based_count = 0
            
            # Process in chunks to avoid memory issues
            chunk_size = 50  # Process 50 HPAs at a time
            for i in range(0, len(hpa_items), chunk_size):
                chunk = hpa_items[i:i + chunk_size]
                
                for hpa in chunk:
                    try:
                        namespace = hpa['metadata']['namespace']
                        name = hpa['metadata']['name']
                        
                        # Extract current metrics safely
                        current_metrics = hpa.get('status', {}).get('currentMetrics', [])
                        target_metrics = hpa.get('spec', {}).get('metrics', [])
                        
                        hpa_detail = {
                            'namespace': namespace,
                            'name': name,
                            'current_metrics': [],
                            'target_metrics': []
                        }
                        
                        # Process current metrics
                        for metric in current_metrics:
                            if metric.get('type') == 'Resource':
                                resource_name = metric['resource']['name']
                                current_value = metric['resource']['current'].get('averageUtilization', 0)
                                
                                hpa_detail['current_metrics'].append({
                                    'resource': resource_name,
                                    'current_utilization': current_value
                                })
                                
                                # HIGH CPU DETECTION
                                if resource_name == 'cpu' and current_value > 200:
                                    high_cpu_hpas.append({
                                        'namespace': namespace,
                                        'name': name,
                                        'cpu_utilization': current_value,
                                        'severity': 'critical' if current_value > 1000 else 'high'
                                    })
                                    
                                    logger.info(f"🔥 HIGH CPU HPA DETECTED: {namespace}/{name} = {current_value}%")
                                
                                # Count metric types
                                if resource_name == 'cpu':
                                    cpu_based_count += 1
                                elif resource_name == 'memory':
                                    memory_based_count += 1
                        
                        hpa_details.append(hpa_detail)
                        
                    except Exception as hpa_error:
                        logger.warning(f"⚠️ Error processing HPA in chunk: {hpa_error}")
                        continue
            
            # Determine pattern
            total_hpas = len(hpa_details)
            total_metrics = cpu_based_count + memory_based_count
            
            if total_metrics == 0:
                pattern = 'no_hpa_detected'
                confidence = 'high'
            elif cpu_based_count > memory_based_count:
                pattern = 'cpu_based_dominant'
                confidence = 'high'
            elif memory_based_count > cpu_based_count:
                pattern = 'memory_based_dominant'
                confidence = 'high'
            else:
                pattern = 'hybrid_approach'
                confidence = 'medium'
            
            return {
                'current_hpa_pattern': pattern,
                'confidence': confidence,
                'total_hpas': total_hpas,
                'high_cpu_hpas': high_cpu_hpas,
                'hpa_details': hpa_details,
                'cpu_based_count': cpu_based_count,
                'memory_based_count': memory_based_count,
                'parsing_method': 'json_chunked'
            }
            
        except Exception as e:
            logger.error(f"❌ JSON safe parsing failed: {e}")
            return {'total_hpas': 0, 'parsing_method': 'json_safe_failed'}

    def _parse_hpa_basic_text(self, output: str) -> Dict:
        """Basic text parsing as final fallback"""
        try:
            lines = output.strip().split('\n')
            hpa_count = 0
            
            for line in lines:
                if line.strip() and not line.startswith('NAMESPACE') and not line.startswith('NAME'):
                    parts = line.split()
                    if len(parts) >= 6:  # Basic HPA format
                        hpa_count += 1
            
            pattern = 'basic_detection' if hpa_count > 0 else 'no_hpa_detected'
            
            return {
                'current_hpa_pattern': pattern,
                'confidence': 'low',
                'total_hpas': hpa_count,
                'high_cpu_hpas': [],
                'hpa_details': [],
                'parsing_method': 'basic_text'
            }
            
        except Exception as e:
            logger.error(f"❌ Basic text parsing failed: {e}")
            return {'total_hpas': 0, 'parsing_method': 'basic_text_failed'}


    def _get_detailed_hpa_metrics(self) -> Dict:
        """
        Get detailed HPA metrics with better large output handling
        """
        try:
            logger.info("📈 Collecting HPA metrics with large output handling...")
            
            # STRATEGY 1: Try custom columns first (most reliable for large clusters)
            logger.info("🔧 Trying custom columns approach for HPA data...")
            # Your exact working command (simplified)
            # Get HPA high CPU data from cache (exact same format for CPU detection)
            cache_data = self.cache.get_resource_usage_data()
            hpa_output = cache_data.get('hpa_high_cpu', '')
            logger.info(f"🔧 Using cached HPA high CPU data for analysis ({len(hpa_output)} chars)")
            logger.info(f"🔍 MAIN METHOD DEBUG: First 500 chars of HPA data: {hpa_output[:500]}")
            
            hpa_analysis = {
                'current_hpa_pattern': 'no_hpa_detected',
                'confidence': 'low',
                'total_hpas': 0,
                'high_cpu_hpas': [],
                'hpa_details': [],
                'parsing_method': 'custom_cmd'
            }
            
            if hpa_output and len(hpa_output.strip()) > 0:
                # Use the same parsing logic as debug method since it works correctly
                lines = hpa_output.split('\n')
                hpa_details = []
                high_cpu_hpas = []
                
                for line in lines[1:] if len(lines) > 1 else []:
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        namespace = parts[0]
                        name = parts[1]
                        current_cpu = parts[2]
                        target_cpu = parts[3]
                        
                        try:
                            cpu_val = float(current_cpu)
                            if cpu_val > 100:  # Use same threshold as debug method
                                high_cpu_hpas.append({
                                    'namespace': namespace,
                                    'name': name,
                                    'cpu_utilization': cpu_val,
                                    'target_cpu': target_cpu,
                                    'severity': 'critical' if cpu_val > 1000 else 'high'
                                })
                                logger.info(f"🔥 MAIN METHOD HIGH CPU HPA DETECTED: {namespace}/{name} = {cpu_val}%")
                            
                            hpa_details.append({
                                'namespace': namespace,
                                'name': name,
                                'current_cpu': cpu_val,
                                'target_cpu': target_cpu
                            })
                        except ValueError:
                            pass
                
                hpa_analysis.update({
                    'current_hpa_pattern': 'mixed_implementation' if hpa_details else 'no_hpa_detected',
                    'confidence': 'high' if hpa_details else 'low',
                    'total_hpas': len(hpa_details),
                    'high_cpu_hpas': high_cpu_hpas,
                    'hpa_details': hpa_details,
                    'parsing_method': 'debug_method_logic'
                })
                #hpa_analysis.update(self._parse_hpa_custom_columns(hpa_output))
                
                # If custom columns worked, we're done
                if hpa_analysis['total_hpas'] > 0:
                    logger.info(f"✅ Custom columns parsing successful: {hpa_analysis['total_hpas']} HPAs")
                    return hpa_analysis
            
            # STRATEGY 2: Try simplified JSON with streaming
            logger.info("🔧 Trying simplified JSON approach...")
            simple_json_cmd = 'kubectl get hpa --all-namespaces -o json --chunk-size=100'
            hpa_data = self._safe_kubectl_yaml_command(simple_json_cmd, timeout=180)
            
            if hpa_data and 'items' in hpa_data:
                hpa_analysis.update(self._parse_hpa_json_safe(hpa_data))
                
                if hpa_analysis['total_hpas'] > 0:
                    logger.info(f"✅ Simplified JSON parsing successful: {hpa_analysis['total_hpas']} HPAs")
                    return hpa_analysis
            
            # STRATEGY 3: Fallback to basic text parsing using cached data
            logger.info("🔧 Using fallback text parsing with cached HPA data...")
            cache_data = self.cache.get_resource_usage_data()
            basic_output = cache_data.get('hpa_text', '')
            
            if basic_output:
                hpa_analysis.update(self._parse_hpa_basic_text(basic_output))
                logger.info(f"✅ Basic text parsing completed: {hpa_analysis['total_hpas']} HPAs found")
            else:
                # No fake data, fail if ALL fetching methods fail
                logger.error("❌ All HPA fetching methods failed - no data available")
                raise ValueError("Failed to fetch HPA data from cluster using any method")
            
            return hpa_analysis
            
        except Exception as e:
            logger.error(f"❌ All HPA parsing methods failed: {e}")
            # No fallback, fail if real data unavailable
            raise ValueError(f"Failed to collect HPA data: {e}")

    def _parse_hpa_metrics(self, hpa_output: str) -> Dict:
        """
        Parse HPA metrics using the working kubectl command format
        """
        try:
            lines = hpa_output.strip().split('\n')
            
            hpa_details = []
            high_cpu_hpas = []
            total_cpu_utilization = 0
            workload_count = 0
            
            # Skip header line
            for line in lines[1:] if len(lines) > 1 else []:
                if not line.strip():
                    continue
                    
                parts = line.split()
                if len(parts) >= 4:
                    namespace = parts[0]
                    name = parts[1]
                    current_cpu_str = parts[2]
                    target_cpu_str = parts[3]
                    
                    # Skip <none> values
                    if current_cpu_str == '<none>' or target_cpu_str == '<none>':
                        continue
                    
                    try:
                        current_cpu = float(current_cpu_str)
                        target_cpu = float(target_cpu_str)
                        
                        hpa_detail = {
                            'namespace': namespace,
                            'name': name,
                            'current_cpu': current_cpu,
                            'target_cpu': target_cpu,
                            'cpu_ratio': current_cpu / target_cpu if target_cpu > 0 else 0
                        }
                        
                        hpa_details.append(hpa_detail)
                        total_cpu_utilization += current_cpu
                        workload_count += 1
                        
                        # DETECT HIGH CPU
                        if current_cpu > 100:  # >100% = optimization candidate (aligned with debug method)
                            severity = 'critical' if current_cpu > 1000 else 'high'
                            high_cpu_hpas.append({
                                'namespace': namespace,
                                'name': name,
                                'cpu_utilization': current_cpu,
                                'target_cpu': target_cpu,
                                'severity': severity,
                                'recommendation': 'OPTIMIZE_APPLICATION' if current_cpu > 300 else 'INVESTIGATE'
                            })
                            
                            logger.info(f"🔥 MAIN METHOD HIGH CPU WORKLOAD: {namespace}/{name} = {current_cpu}% (target: {target_cpu}%)")
                    
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse CPU values: {current_cpu_str}, {target_cpu_str}")
                        continue
            
            # Calculate average from REAL workload data
            avg_cpu = total_cpu_utilization / workload_count if workload_count > 0 else 0
            
            # Determine pattern based on REAL data
            if workload_count == 0:
                pattern = 'no_hpa_detected'
                confidence = 'high'
            else:
                pattern = 'workload_based_analysis'
                confidence = 'high'
            
            logger.info(f"✅ WORKING PARSER: {workload_count} workloads, avg CPU: {avg_cpu:.1f}%")
            logger.info(f"✅ High CPU workloads detected: {len(high_cpu_hpas)}")
            
            return {
                'current_hpa_pattern': pattern,
                'confidence': confidence,
                'total_hpas': workload_count,
                'high_cpu_hpas': high_cpu_hpas,
                'hpa_details': hpa_details,
                'average_cpu_utilization': avg_cpu,
                'max_cpu_utilization': max([h['current_cpu'] for h in hpa_details]) if hpa_details else 0,
                'parsing_method': 'working_command_parser',
                'workload_data_available': True
            }
            
        except Exception as e:
            logger.error(f"❌ Working HPA parser failed: {e}")
            return {'total_hpas': 0, 'parsing_method': 'working_parser_failed'}

    def _get_detailed_pod_metrics(self) -> Dict:
        """Get detailed pod-level metrics for ML analysis"""
        try:
            # Get pod resource usage
            top_pods_cmd = "kubectl top pods --all-namespaces --no-headers"
            pod_output = self._safe_kubectl_command(top_pods_cmd)
            
            pod_data = {
                'pods': [],
                'namespace_aggregates': {},
                'resource_totals': {'cpu_millicores': 0, 'memory_bytes': 0}
            }
            
            if pod_output:
                lines = pod_output.split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            namespace = parts[0]
                            pod_name = parts[1]
                            cpu_str = parts[2]
                            memory_str = parts[3]
                            
                            # Skip headers
                            if namespace.upper() in ['NAMESPACE', 'NAME']:
                                continue
                            
                            # Parse resources
                            cpu_millicores = self.parser.parse_cpu_safe(cpu_str)
                            memory_bytes = self.parser.parse_memory_safe(memory_str)
                            
                            if cpu_millicores >= 0 and memory_bytes >= 0:
                                pod_info = {
                                    'namespace': namespace,
                                    'name': pod_name,
                                    'cpu_millicores': cpu_millicores,
                                    'memory_bytes': memory_bytes,
                                    'cpu_percentage': (cpu_millicores / 4000) * 100  # Assume 4-core nodes
                                }
                                
                                pod_data['pods'].append(pod_info)
                                pod_data['resource_totals']['cpu_millicores'] += cpu_millicores
                                pod_data['resource_totals']['memory_bytes'] += memory_bytes
                                
                                # Aggregate by namespace
                                if namespace not in pod_data['namespace_aggregates']:
                                    pod_data['namespace_aggregates'][namespace] = {
                                        'pod_count': 0,
                                        'total_cpu': 0,
                                        'total_memory': 0
                                    }
                                
                                pod_data['namespace_aggregates'][namespace]['pod_count'] += 1
                                pod_data['namespace_aggregates'][namespace]['total_cpu'] += cpu_millicores
                                pod_data['namespace_aggregates'][namespace]['total_memory'] += memory_bytes
            
            pod_data['total_pods'] = len(pod_data['pods'])
            pod_data['namespace_count'] = len(pod_data['namespace_aggregates'])
            
            logger.info(f"📊 Pod metrics: {pod_data['total_pods']} pods across {pod_data['namespace_count']} namespaces")
            return pod_data
            
        except Exception as e:
            logger.error(f"❌ Pod metrics collection failed: {e}")
            return {'pods': [], 'namespace_aggregates': {}, 'total_pods': 0}


    def _add_ml_metadata(self, ml_data: Dict) -> Dict:
        """Add metadata needed for ML feature extraction"""
        return {
            'ml_metadata': {
                'feature_extraction_ready': True,
                'has_workload_cpu_data': bool(ml_data.get('workload_cpu_analysis', {}).get('high_cpu_workloads')),
                'has_hpa_data': ml_data.get('hpa_implementation', {}).get('total_hpas', 0) > 0,
                'node_count': len(ml_data.get('nodes', [])),
                'max_detected_cpu': ml_data.get('workload_cpu_analysis', {}).get('max_workload_cpu', 0),
                'collection_timestamp': datetime.now().isoformat(),
                'ready_for_enterprise_ml': True
            }
        }

    def get_ml_ready_metrics(self) -> Dict[str, Any]:
        """
        Get metrics with ALL workloads data preserved
        """
        try:
            logger.info("🤖 FIXED: Collecting ML-ready metrics with ALL workloads...")
            
            # Step 1: Get enhanced node-level metrics
            try:
                node_metrics = self._get_enhanced_node_resource_data()
                logger.info("✅ Got enhanced node metrics")
            except Exception as node_error:
                logger.error(f"❌ Enhanced node metrics failed: {node_error}")
                # No fallback, fail if real data unavailable
                raise ValueError(f"Failed to collect enhanced node metrics: {node_error}")
            
            # Step 2: Get HPA implementation status with detailed replica information
            try:
                hpa_metrics = self.get_hpa_implementation_status()
                logger.info("✅ Got HPA implementation status with detailed replica data")
            except Exception as hpa_error:
                logger.warning(f"⚠️ HPA implementation status failed: {hpa_error}")
                hpa_metrics = {
                    'current_hpa_pattern': 'detection_failed',
                    'confidence': 'low',
                    'total_hpas': 0,
                    'hpa_details': [],
                    'cpu_based_count': 0,
                    'memory_based_count': 0
                }
            
            # Step 3: CRITICAL FIX - Get ALL workload-level resource consumption
            try:
                # Use the fixed method that saves ALL workloads
                pod_metrics = self._get_workload_level_metrics()
                logger.info("✅ Got ALL workload metrics (fixed method)")
                
                # Validate that we got all workloads
                total_workloads = pod_metrics.get('total_workloads', 0)
                high_cpu_count = pod_metrics.get('high_cpu_count', 0)
                
                if total_workloads > 0:
                    logger.info(f"✅ WORKLOAD DATA: {total_workloads} total workloads, {high_cpu_count} high CPU")
                    
                    # Validate all_workloads field exists
                    if 'all_workloads' not in pod_metrics or not pod_metrics['all_workloads']:
                        raise ValueError("No workload data collected - all_workloads field is missing or empty")
                    
                else:
                    logger.warning("⚠️ No workload data found in metrics")
                
            except Exception as pod_error:
                logger.warning(f"⚠️ Workload metrics failed: {pod_error}")
                pod_metrics = {
                    'pods': [], 
                    'all_workloads': [],  # Ensure this field exists
                    'namespace_aggregates': {}, 
                    'total_workloads': 0,
                    'high_cpu_count': 0,
                    'data_completeness': {
                        'all_workloads_saved': False,
                        'error_occurred': True,
                        'error_message': str(pod_error)
                    }
                }
            
            # Step 4: High CPU analysis is now integrated directly in workload metrics
            high_cpu_analysis = {
                'high_cpu_workloads': pod_metrics.get('high_cpu_pods', []),
                'high_cpu_pods': pod_metrics.get('high_cpu_pods', []),
                'all_workloads_analyzed': pod_metrics.get('all_workloads', []),
                'total_workloads_analyzed': pod_metrics.get('total_workloads', 0),
                'max_workload_cpu': max([w.get('hpa_cpu_utilization', w.get('cpu_percentage', 0)) for w in pod_metrics.get('high_cpu_pods', [])], default=0),
                'recommendation_category': 'CRITICAL' if pod_metrics.get('high_cpu_count', 0) > 0 else 'MONITOR',
                'namespace_breakdown': pod_metrics.get('namespace_aggregates', {})
            }
            
            # Step 5: Debug log high CPU data before creating summary
            logger.info(f"🔍 DEBUG before high_cpu_summary: HPAs={len(hpa_metrics.get('high_cpu_hpas', []))}, "
                       f"workloads={len(high_cpu_analysis.get('high_cpu_workloads', []))}, "
                       f"pods={len(high_cpu_analysis.get('high_cpu_pods', []))}")
            
            # Step 6: Combine into ML-ready format with ALL workload data preserved
            ml_ready_data = {
                'nodes': node_metrics.get('nodes', []),
                'hpa_implementation': hpa_metrics,
                'workload_cpu_analysis': high_cpu_analysis,
                'pod_resource_data': pod_metrics,
                
                # ===== CRITICAL: PRESERVE ALL WORKLOAD DATA AT TOP LEVEL =====
                'all_workloads': pod_metrics.get('all_workloads', []),  # 🆕 Top-level access to all workloads
                'total_workloads': pod_metrics.get('total_workloads', 0),
                'workload_namespace_breakdown': pod_metrics.get('namespace_aggregates', {}),
                'workload_distribution': pod_metrics.get('workload_distribution', {}),
                
                # ===== FIXED: HIGH CPU DATA FROM INTEGRATED POD METRICS (includes HPA) =====
                'high_cpu_summary': {
                    'high_cpu_hpas': hpa_metrics.get('high_cpu_hpas', []),
                    'high_cpu_workloads': pod_metrics.get('high_cpu_pods', []),  # Use integrated data
                    'high_cpu_pods': pod_metrics.get('high_cpu_pods', []),      # Use integrated data
                    'max_cpu_utilization': self._calculate_max_cpu_utilization(hpa_metrics, pod_metrics),
                    'total_high_cpu_count': pod_metrics.get('high_cpu_count', 0),  # Use recalculated count
                    'severity_category': 'CRITICAL' if pod_metrics.get('high_cpu_count', 0) > 0 else 'MONITOR'
                },
                
                # Status and metadata
                'status': 'success',
                'ml_features_ready': True,
                'high_cpu_detected': pod_metrics.get('high_cpu_count', 0) > 0,
                'enhanced_data_available': node_metrics.get('enhanced_data_available', False),
                'nodes_with_real_requests': node_metrics.get('nodes_with_real_requests', 0),
                'completely_fixed': True,
                'all_workloads_preserved': True,  # 🆕 Flag indicating the fix is applied
                'high_cpu_ui_ready': True  # 🆕 Flag indicating high CPU data is UI-ready
            }
            
            # Step 6: Add comprehensive metadata
            ml_ready_data['ml_metadata'] = {
                'feature_extraction_ready': True,
                'has_real_request_data': node_metrics.get('nodes_with_real_requests', 0) > 0,
                'has_workload_cpu_data': bool(high_cpu_analysis.get('high_cpu_workloads')),
                'has_all_workload_data': bool(pod_metrics.get('all_workloads')),  # 🆕 Flag for all workloads
                'has_hpa_data': hpa_metrics.get('total_hpas', 0) > 0,
                'node_count': len(node_metrics.get('nodes', [])),
                'total_workloads_collected': len(pod_metrics.get('all_workloads', [])),  # 🆕 Total workload count
                'high_cpu_workloads_count': len(high_cpu_analysis.get('high_cpu_workloads', [])),
                'max_detected_cpu': high_cpu_analysis.get('max_workload_cpu', 0),
                'collection_timestamp': datetime.now().isoformat(),
                'ready_for_enterprise_ml': True,
                'collection_method': 'all_workloads_preserved_fixed',  # 🆕 Indicates fix applied
                'fixes_applied': [
                    'fixed_method_names',
                    'enhanced_json_parsing',
                    'large_output_handling',
                    'fallback_mechanisms',
                    'all_workloads_preservation',  # 🆕 New fix
                    'conditional_filtering_removed'  # 🆕 New fix
                ],
                'data_completeness': pod_metrics.get('data_completeness', {})
            }
            
            total_nodes = len(ml_ready_data['nodes'])
            total_workloads = len(ml_ready_data.get('all_workloads', []))
            
            # ===== FINAL SUCCESS LOGGING =====
            logger.info(f"✅ FIXED: ML-ready metrics collected with ALL workloads preserved")
            logger.info(f"📊 SUMMARY: {total_nodes} nodes, {total_workloads} total workloads")
            logger.info(f"📊 HIGH CPU: {len(high_cpu_analysis.get('high_cpu_workloads', []))} high CPU workloads")
            logger.info(f"✅ ALL WORKLOADS SAVED: No conditional filtering applied")
            
            return ml_ready_data
            
        except Exception as e:
            logger.error(f"❌ FIXED: ML-ready metrics collection failed: {e}")
            # Return empty but valid structure to maintain compatibility
            return {
                'status': 'error',
                'error': str(e),
                'nodes': [],
                'all_workloads': [],
                'total_workloads': 0,
                'hpa_implementation': {'total_hpas': 0, 'confidence': 'low'},
                'workload_cpu_analysis': {'high_cpu_workloads': [], 'max_workload_cpu': 0},
                'pod_resource_data': {'all_workloads': [], 'total_workloads': 0},
                'high_cpu_summary': {'high_cpu_workloads': [], 'max_cpu_utilization': 0},
                'ml_features_ready': False,
                'enhanced_data_available': False,
                'all_workloads_preserved': False,
                'timestamp': datetime.now().isoformat()
            }


    def get_enhanced_metrics_for_ml(self) -> Dict[str, Any]:
        """Collect comprehensive metrics optimized for ML analysis"""
        logger.info("🤖 Fetching enhanced metrics for ML analysis...")
        
        try:
            # Get base comprehensive metrics
            base_metrics = self.get_comprehensive_metrics()
            
            if base_metrics.get('status') != 'success':
                raise ValueError("Failed to get base metrics")
            
            # Enhance with ML-specific data
            enhanced_metrics = base_metrics.copy()
            
            # Add workload-level CPU/Memory data
            workload_metrics = self._get_workload_level_metrics()
            if workload_metrics:
                enhanced_metrics['workload_metrics'] = workload_metrics
            
            # Add HPA performance data
            hpa_performance = self._get_hpa_performance_metrics()
            if hpa_performance:
                enhanced_metrics['hpa_performance'] = hpa_performance
            
            # Add resource efficiency indicators
            efficiency_indicators = self._calculate_resource_efficiency_indicators(enhanced_metrics)
            enhanced_metrics['efficiency_indicators'] = efficiency_indicators
            
            # Add temporal patterns (for ML time-based features)
            temporal_patterns = self._extract_temporal_patterns()
            enhanced_metrics['temporal_patterns'] = temporal_patterns
            
            logger.info("✅ Enhanced metrics collection completed for ML")
            return enhanced_metrics
            
        except Exception as e:
            logger.error(f"❌ Enhanced metrics collection failed: {e}")
            # No fallback, fail if real data unavailable
            raise ValueError(f"Failed to collect ML-ready metrics: {e}")

    def _get_workload_level_metrics(self) -> Optional[Dict]:
        """
        FIXED: Get ALL workload-level CPU/Memory usage, not just high-CPU detection
        Save all 393 pods, not just the high CPU ones
        """
        try:
            logger.info("🔍 Collecting ALL workload-level metrics (not just high CPU)...")
            
            # Get pod-level resource usage from cache
            cache_data = self.cache.get_resource_usage_data()
            pod_output = cache_data.get('pod_usage', '')
            
            # CRITICAL FIX: Also get HPA high CPU data for accurate high CPU detection
            hpa_high_cpu_output = cache_data.get('hpa_high_cpu', '')
            logger.info(f"📊 Got HPA high CPU data: {len(hpa_high_cpu_output)} chars")
            logger.info(f"🔍 DEBUG: HPA high CPU data first 200 chars: {hpa_high_cpu_output[:200]}")
            
            # Handle metrics server unavailability
            if not pod_output:
                logger.info("📊 Pod metrics unavailable (metrics server issue), using pod resource requests as estimates")
            
            workload_data = {
                'pods': [],
                'namespace_aggregates': {},
                'resource_totals': {'cpu_millicores': 0, 'memory_bytes': 0},
                'all_workloads': [],      # 🆕 Store ALL workloads here
                'high_cpu_pods': [],      # Preserve high CPU ones for compatibility
                'workload_distribution': {},
                'cpu_severity_breakdown': {
                    'normal': [],
                    'moderate': [],
                    'high': [],
                    'critical': []
                }
            }
            
            if not pod_output:
                logger.warning("⚠️ Could not get pod-level metrics")
                return workload_data  # Return empty structure instead of None
            
            # Enhanced parsing with better error handling
            lines = pod_output.split('\n')
            parsed_lines = 0
            total_cpu_millicores = 0
            total_memory_bytes = 0
            
            for line_num, line in enumerate(lines):
                if not line.strip():
                    continue
                
                # Skip command metadata lines
                if any(skip in line.lower() for skip in ['command started', 'command finished', 'exitcode']):
                    continue
                
                try:
                    parts = line.split()
                    if len(parts) >= 4:
                        namespace = parts[0]
                        pod_name = parts[1]
                        cpu_str = parts[2]
                        memory_str = parts[3]
                        
                        # Skip header-like lines
                        if namespace.upper() in ['NAMESPACE', 'NAME'] or cpu_str.upper() == 'CPU':
                            continue
                        
                        # Parse using existing utility
                        cpu_millicores = self.parser.parse_cpu_safe(cpu_str)
                        memory_bytes = self.parser.parse_memory_safe(memory_str)
                        
                        if cpu_millicores >= 0 and memory_bytes >= 0:
                            # Calculate CPU percentage (assuming 4-core nodes as baseline)
                            cpu_percentage = self._convert_millicores_to_percentage(cpu_millicores)
                            memory_percentage = self._convert_bytes_to_percentage(memory_bytes)
                            
                            # Determine severity level for ALL pods
                            severity = self._categorize_cpu_usage_severity(cpu_millicores, cpu_percentage)
                            
                            # ===== CRITICAL FIX: CREATE WORKLOAD DATA FOR ALL PODS =====
                            workload_entry = {
                                'namespace': namespace,
                                'pod': pod_name,
                                'name': pod_name,  # Alias for compatibility
                                'cpu_millicores': cpu_millicores,
                                'memory_bytes': memory_bytes,
                                'cpu_percentage': cpu_percentage,
                                'memory_percentage': memory_percentage,
                                'cpu_cores': cpu_millicores / 1000,
                                'severity': severity,
                                'category': self._categorize_cpu_usage(cpu_millicores),
                                'line_number': line_num,
                                'raw_line': line.strip(),
                                'type': 'pod_metrics',
                                'saved_unconditionally': True  # 🆕 Flag to indicate this was saved regardless of CPU
                            }
                            
                            # ===== SAVE ALL WORKLOADS UNCONDITIONALLY =====
                            workload_data['pods'].append(workload_entry)
                            workload_data['all_workloads'].append(workload_entry)  # 🆕 Save ALL workloads
                            
                            # Add to severity breakdown
                            workload_data['cpu_severity_breakdown'][severity].append(workload_entry)
                            
                            total_cpu_millicores += cpu_millicores
                            total_memory_bytes += memory_bytes
                            parsed_lines += 1
                            
                            # ===== ALSO TRACK HIGH CPU PODS (FOR COMPATIBILITY) =====
                            # Only add to high_cpu_pods if it meets high CPU criteria
                            if (cpu_millicores > 500 or cpu_percentage > 50):
                                high_cpu_entry = {
                                    **workload_entry,
                                    'high_cpu_reason': f'CPU: {cpu_millicores}m ({cpu_percentage:.1f}%)'
                                }
                                workload_data['high_cpu_pods'].append(high_cpu_entry)
                                
                                logger.info(f"🔥 High CPU pod: {namespace}/{pod_name} = {cpu_millicores}m ({cpu_percentage:.1f}%)")
                            
                            # Log ALL workloads being saved (not just high CPU ones)
                            #logger.debug(f"💾 SAVED WORKLOAD: {namespace}/{pod_name} = {cpu_millicores}m ({cpu_percentage:.1f}%) [severity: {severity}]")
                            
                except Exception as parse_error:
                    logger.warning(f"⚠️ Error parsing pod metrics line {line_num}: {parse_error}")
                    logger.debug(f"🔧 Problematic line: {line}")
                    continue
            
            # Update totals
            workload_data['resource_totals']['cpu_millicores'] = total_cpu_millicores
            workload_data['resource_totals']['memory_bytes'] = total_memory_bytes
            
            # CRITICAL FIX: Process HPA high CPU data to identify high CPU workloads
            if hpa_high_cpu_output:
                logger.info(f"🔍 DEBUG: Processing HPA high CPU data for cluster {self.cluster_name}")
                high_cpu_workloads_from_hpa = self._process_hpa_high_cpu_data(hpa_high_cpu_output)
                logger.info(f"🔍 DEBUG: Found {len(high_cpu_workloads_from_hpa)} high CPU workloads from HPA data for {self.cluster_name}")
                
                # Merge HPA high CPU findings with pod metrics
                for hpa_workload in high_cpu_workloads_from_hpa:
                    # Check if this workload is already in our all_workloads
                    existing_workload = None
                    for workload in workload_data['all_workloads']:
                        if (workload['name'] == hpa_workload['name'] and 
                            workload['namespace'] == hpa_workload['namespace']):
                            existing_workload = workload
                            break
                    
                    if existing_workload:
                        # Update existing workload with HPA high CPU data
                        existing_workload['hpa_cpu_utilization'] = hpa_workload.get('cpu_utilization', 0)
                        existing_workload['hpa_detected'] = True
                        existing_workload['hpa_cpu_target'] = hpa_workload.get('cpu_target', 0)
                        
                        # Ensure it's marked as high CPU if HPA detected it
                        if hpa_workload.get('cpu_utilization', 0) > 100:
                            if existing_workload not in workload_data['high_cpu_pods']:
                                existing_workload['high_cpu_reason'] = f"HPA detected: {hpa_workload.get('cpu_utilization', 0)}%"
                                workload_data['high_cpu_pods'].append(existing_workload)
                                logger.info(f"🔥 HPA HIGH CPU: {existing_workload['namespace']}/{existing_workload['name']} = {hpa_workload.get('cpu_utilization', 0)}%")
                    else:
                        # Add new workload from HPA data (in case pod metrics missed it)
                        new_workload = {
                            'name': hpa_workload['name'],
                            'namespace': hpa_workload['namespace'],
                            'cpu_millicores': 0,  # Will be updated if we get metrics
                            'memory_bytes': 0,
                            'cpu_percentage': 0,
                            'memory_percentage': 0,
                            'hpa_cpu_utilization': hpa_workload.get('cpu_utilization', 0),
                            'hpa_detected': True,
                            'hpa_cpu_target': hpa_workload.get('cpu_target', 0),
                            'severity': 'critical' if hpa_workload.get('cpu_utilization', 0) > 200 else 'high',
                            'source': 'hpa_high_cpu'
                        }
                        
                        workload_data['all_workloads'].append(new_workload)
                        if hpa_workload.get('cpu_utilization', 0) > 100:
                            new_workload['high_cpu_reason'] = f"HPA detected: {hpa_workload.get('cpu_utilization', 0)}%"
                            workload_data['high_cpu_pods'].append(new_workload)
                            logger.info(f"🔥 NEW HPA HIGH CPU: {new_workload['namespace']}/{new_workload['name']} = {hpa_workload.get('cpu_utilization', 0)}%")
                
                logger.info(f"✅ Processed {len(high_cpu_workloads_from_hpa)} HPA high CPU workloads")
            
            # Recalculate totals after HPA integration
            total_workloads = len(workload_data['all_workloads'])
            high_cpu_count = len(workload_data['high_cpu_pods'])
            
            if not workload_data['all_workloads']:
                logger.warning("⚠️ No valid workload data parsed from pod metrics")
                return workload_data  # Still return the structure
            
            # ===== AGGREGATE BY NAMESPACE (FOR ALL WORKLOADS) =====
            for workload in workload_data['all_workloads']:
                namespace = workload['namespace']
                
                if namespace not in workload_data['namespace_aggregates']:
                    workload_data['namespace_aggregates'][namespace] = {
                        'pod_count': 0,
                        'total_cpu': 0,
                        'total_memory': 0,
                        'workload_list': []
                    }
                
                workload_data['namespace_aggregates'][namespace]['pod_count'] += 1
                workload_data['namespace_aggregates'][namespace]['total_cpu'] += workload['cpu_millicores']
                workload_data['namespace_aggregates'][namespace]['total_memory'] += workload['memory_bytes']
                workload_data['namespace_aggregates'][namespace]['workload_list'].append(workload)
            
            # ===== CALCULATE DISTRIBUTION STATS =====
            total_workloads = len(workload_data['all_workloads'])
            high_cpu_count = len(workload_data['high_cpu_pods'])
            
            workload_data['workload_distribution'] = {
                'total_workloads': total_workloads,
                'high_cpu_count': high_cpu_count,
                'normal_cpu_count': total_workloads - high_cpu_count,
                'high_cpu_percentage': (high_cpu_count / total_workloads * 100) if total_workloads > 0 else 0,
                'severity_counts': {
                    severity: len(pods) for severity, pods in workload_data['cpu_severity_breakdown'].items()
                }
            }
            
            # Calculate cluster-wide workload metrics
            result = {
                **workload_data,
                'total_workloads': total_workloads,  # 🆕 Total count of ALL workloads
                'total_cpu_millicores': total_cpu_millicores,
                'total_memory_bytes': total_memory_bytes,
                'high_cpu_count': high_cpu_count,
                'average_cpu_per_pod': total_cpu_millicores / total_workloads if total_workloads > 0 else 0,
                'average_memory_per_pod': total_memory_bytes / total_workloads if total_workloads > 0 else 0,
                'resource_concentration': self._calculate_resource_concentration(workload_data['all_workloads']),
                'raw_workload_data': workload_data['all_workloads'],  # 🆕 ALL workloads, not limited
                'parsing_stats': {
                    'lines_processed': len(lines),
                    'lines_parsed': parsed_lines,
                    'parsing_success_rate': (parsed_lines / max(len(lines), 1)) * 100
                },
                'data_completeness': {
                    'all_workloads_saved': True,  # 🆕 Flag indicating all workloads are preserved
                    'filtering_disabled': True,   # 🆕 Flag indicating no filtering was applied
                    'conditional_save_disabled': True  # 🆕 Flag indicating conditional logic was bypassed
                }
            }
            
            # ===== CRITICAL SUCCESS LOGGING =====
            logger.info(f"✅ FIXED: ALL workload metrics collected - {total_workloads} total workloads")
            logger.info(f"📊 Breakdown: {high_cpu_count} high-CPU, {total_workloads - high_cpu_count} normal-CPU")
            logger.info(f"📊 Severity breakdown: normal={len(workload_data['cpu_severity_breakdown']['normal'])}, moderate={len(workload_data['cpu_severity_breakdown']['moderate'])}, high={len(workload_data['cpu_severity_breakdown']['high'])}, critical={len(workload_data['cpu_severity_breakdown']['critical'])}")
            logger.info(f"✅ Data saved unconditionally for ALL {total_workloads} workloads")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting workload-level metrics: {e}")
            # Return empty structure instead of None to maintain data flow
            return {
                'pods': [],
                'all_workloads': [],
                'high_cpu_pods': [],
                'total_workloads': 0,
                'namespace_aggregates': {},
                'data_completeness': {
                    'all_workloads_saved': False,
                    'error_occurred': True,
                    'error_message': str(e)
                }
            }

    def _categorize_cpu_usage_severity(self, cpu_millicores: float, cpu_percentage: float) -> str:
        """
        Categorize CPU usage severity for ALL workloads
        """
        if cpu_millicores >= 4000 or cpu_percentage >= 100:  # >= 4 CPU cores or 100%
            return 'critical'
        elif cpu_millicores >= 2000 or cpu_percentage >= 75:  # >= 2 CPU cores or 75%
            return 'high'
        elif cpu_millicores >= 1000 or cpu_percentage >= 50:  # >= 1 CPU core or 50%
            return 'moderate'
        else:
            return 'normal'

    def _get_hpa_performance_metrics(self) -> Optional[Dict]:
        """Get HPA performance metrics with truncation safety"""
        try:
            logger.info("📈 Collecting HPA performance metrics...")
            
            # Use text output instead of JSON to avoid truncation issues
            # Get HPA no-headers data from cache
            cache_data = self.cache.get_resource_usage_data()
            hpa_output = cache_data.get('hpa_no_headers', '') or cache_data.get('hpa_text', '')
            logger.info(f"📈 Using cached HPA text data for performance analysis")
            
            if not hpa_output:
                logger.warning("⚠️ No HPA output received")
                return None
            
            # Parse text output instead of JSON
            hpa_performance = {
                'total_hpas': 0,
                'active_hpas': 0,
                'metric_types': {'cpu': 0, 'memory': 0},
                'performance_indicators': []
            }
            
            lines = hpa_output.split('\n')
            for line in lines:
                if line.strip() and not any(skip in line.lower() for skip in ['command started', 'command finished']):
                    parts = line.split()
                    if len(parts) >= 6:  # Basic HPA format
                        namespace = parts[0]
                        name = parts[1]
                        # Skip header lines
                        if namespace.upper() != 'NAMESPACE':
                            hpa_performance['total_hpas'] += 1
                            hpa_performance['active_hpas'] += 1  # Assume active if listed
                            hpa_performance['metric_types']['cpu'] += 1  # Default assumption
            
            logger.info(f"✅ HPA performance: {hpa_performance['total_hpas']} total")
            return hpa_performance
            
        except Exception as e:
            logger.error(f"❌ Error getting HPA performance metrics: {e}")
            return None

    def _calculate_resource_efficiency_indicators(self, metrics: Dict) -> Dict:
        """Calculate resource efficiency indicators for ML analysis"""
        try:
            efficiency = {
                'cpu_efficiency': 0.0,
                'memory_efficiency': 0.0,
                'resource_balance': 0.0,
                'utilization_variance': 0.0,
                'optimization_potential': 'medium'
            }
            
            nodes = metrics.get('nodes', [])
            if not nodes:
                return efficiency
            
            # Calculate efficiency scores
            cpu_utils = [node.get('cpu_usage_pct', 0) for node in nodes]
            memory_utils = [node.get('memory_usage_pct', 0) for node in nodes]
            
            if cpu_utils:
                avg_cpu = np.mean(cpu_utils)
                efficiency['cpu_efficiency'] = self._calculate_utilization_efficiency(avg_cpu, 70)
                efficiency['cpu_variance'] = float(np.var(cpu_utils))
            
            if memory_utils:
                avg_memory = np.mean(memory_utils)
                efficiency['memory_efficiency'] = self._calculate_utilization_efficiency(avg_memory, 75)
                efficiency['memory_variance'] = float(np.var(memory_utils))
            
            # Resource balance
            if cpu_utils and memory_utils:
                efficiency['resource_balance'] = 1.0 - abs(np.mean(cpu_utils) - np.mean(memory_utils)) / 100
                efficiency['utilization_variance'] = float(np.mean([np.var(cpu_utils), np.var(memory_utils)]))
            
            # Optimization potential
            avg_efficiency = (efficiency['cpu_efficiency'] + efficiency['memory_efficiency']) / 2
            if avg_efficiency < 0.5:
                efficiency['optimization_potential'] = 'high'
            elif avg_efficiency < 0.7:
                efficiency['optimization_potential'] = 'medium'
            else:
                efficiency['optimization_potential'] = 'low'
            
            return efficiency
            
        except Exception as e:
            logger.error(f"❌ Error calculating efficiency indicators: {e}")
            return {'optimization_potential': 'unknown'}

    def _extract_temporal_patterns(self) -> Dict:
        """Extract temporal patterns for ML time-based features"""
        current_time = datetime.now()
        
        return {
            'hour_of_day': current_time.hour,
            'day_of_week': current_time.weekday(),
            'is_business_hours': 9 <= current_time.hour <= 17,
            'is_weekend': current_time.weekday() >= 5,
            'is_peak_hours': current_time.hour in [10, 11, 14, 15, 16],
            'timestamp': current_time.isoformat(),
            'timezone': str(current_time.astimezone().tzinfo)
        }

    def _calculate_utilization_efficiency(self, actual_util: float, target_util: float) -> float:
        """Calculate efficiency score for a utilization metric"""
        if actual_util <= 0:
            return 0.0
        elif actual_util <= target_util:
            # For normal/low utilization: Apply improved scaling
            base_efficiency = actual_util / target_util
            
            # Boost efficiency for lower utilization (indicates good optimization)
            # This makes normal CPU/memory usage show meaningful efficiency scores
            if actual_util <= (target_util * 0.5):  # Less than half of target
                return min(1.0, base_efficiency * 1.5)
            else:
                return base_efficiency
        else:
            # Penalize over-utilization but not too harshly
            penalty = (actual_util - target_util) / target_util
            return max(0.1, 1.0 - (penalty * 0.6))

    def _convert_millicores_to_percentage(self, millicores: float) -> float:
        """Convert millicores to percentage (assuming 4-core nodes)"""
        return min(100.0, (millicores / 4000) * 100)  # 4000m = 4 cores = 100%

    def _convert_bytes_to_percentage(self, bytes_val: float) -> float:
        """Convert bytes to percentage (assuming 16GB nodes)"""
        return min(100.0, (bytes_val / (16 * 1024 * 1024 * 1024)) * 100)  # 16GB = 100%

    def _analyze_workload_distribution(self, workload_data: List[Dict]) -> Dict:
        """Analyze how workloads are distributed across namespaces"""
        distribution = {}
        for workload in workload_data:
            namespace = workload['namespace']
            if namespace not in distribution:
                distribution[namespace] = {'count': 0, 'total_cpu': 0, 'total_memory': 0}
            
            distribution[namespace]['count'] += 1
            distribution[namespace]['total_cpu'] += workload['cpu_millicores']
            distribution[namespace]['total_memory'] += workload['memory_bytes']
        
        return distribution

    def _calculate_resource_concentration(self, workload_data: List[Dict]) -> Dict:
        """Calculate resource concentration metrics - Require real data"""
        if not workload_data:
            raise ValueError("No workload data provided for resource concentration calculation")
        
        cpu_values = [w['cpu_millicores'] for w in workload_data]
        memory_values = [w['memory_bytes'] for w in workload_data]
        
        # Top 20% resource consumers
        top_20_cpu = sorted(cpu_values, reverse=True)[:len(cpu_values)//5]
        top_20_memory = sorted(memory_values, reverse=True)[:len(memory_values)//5]
        
        return {
            'cpu_concentration': sum(top_20_cpu) / sum(cpu_values) if sum(cpu_values) > 0 else 0,
            'memory_concentration': sum(top_20_memory) / sum(memory_values) if sum(memory_values) > 0 else 0,
            'top_cpu_consumer': max(cpu_values) if cpu_values else 0,
            'top_memory_consumer': max(memory_values) if memory_values else 0
        }

    def _process_hpa_high_cpu_data(self, hpa_high_cpu_output: str) -> List[Dict]:
        """Process HPA high CPU data to extract high CPU workloads"""
        high_cpu_workloads = []
        
        try:
            if not hpa_high_cpu_output:
                logger.info(f"🔍 DEBUG: No HPA high CPU output for cluster {self.cluster_name}")
                return high_cpu_workloads
            
            # Filter out <none> values as the original command did with grep
            hpa_lines = hpa_high_cpu_output.split('\n')
            
            # Debug: Check if customer-survey-genesis is in raw data
            survey_lines = [line for line in hpa_lines if 'customer-survey-genesis' in line]
            if survey_lines:
                logger.info(f"🔍 DEBUG: Found {len(survey_lines)} customer-survey-genesis lines in raw HPA data")
                for i, line in enumerate(survey_lines):
                    logger.info(f"🔍 DEBUG: Raw line {i}: '{line}'")
            else:
                logger.info(f"🔍 DEBUG: No customer-survey-genesis lines found in raw HPA data")
            
            filtered_lines = [line for line in hpa_lines if '<none>' not in line and line.strip()]
            logger.info(f"🔍 DEBUG: Cluster {self.cluster_name} - Processing {len(filtered_lines)} HPA lines (after filtering <none>)")
            
            # Debug: Check if customer-survey-genesis survives filtering
            survey_filtered = [line for line in filtered_lines if 'customer-survey-genesis' in line]
            if survey_filtered:
                logger.info(f"🔍 DEBUG: Found {len(survey_filtered)} customer-survey-genesis lines after filtering")
            else:
                logger.info(f"🔍 DEBUG: No customer-survey-genesis lines found after filtering")
            
            for line in filtered_lines:
                if line.strip() and not line.startswith('NAMESPACE'):
                    parts = line.split()
                    if len(parts) >= 4:
                        namespace = parts[0]
                        name = parts[1]
                        current_cpu = parts[2]
                        target_cpu = parts[3]
                        
                        # Debug specific workload
                        if 'customer-survey-genesis' in name:
                            logger.info(f"🔍 DEBUG: Found customer-survey-genesis line: {line}")
                            logger.info(f"🔍 DEBUG: Parts: {parts}")
                            logger.info(f"🔍 DEBUG: current_cpu='{current_cpu}', target_cpu='{target_cpu}'")
                        
                        try:
                            cpu_val = float(current_cpu)
                            target_val = float(target_cpu) if target_cpu.replace('.', '').isdigit() else 0
                            
                            # Debug specific workload processing
                            if 'customer-survey-genesis' in name:
                                logger.info(f"🔍 DEBUG: Parsed cpu_val={cpu_val}, target_val={target_val}")
                            
                            # Consider any CPU > 100% as high CPU
                            if cpu_val > 100:
                                high_cpu_workloads.append({
                                    'namespace': namespace,
                                    'name': name,
                                    'cpu_utilization': cpu_val,
                                    'cpu_target': target_val
                                })
                                logger.info(f"🔥 HPA HIGH CPU DETECTED in {self.cluster_name}: {namespace}/{name} = {cpu_val}% (target: {target_val}%)")
                            else:
                                logger.debug(f"🔍 HPA Normal CPU in {self.cluster_name}: {namespace}/{name} = {cpu_val}% (target: {target_val}%)")
                        except (ValueError, IndexError) as e:
                            if 'customer-survey-genesis' in line:
                                logger.error(f"❌ FAILED to parse customer-survey-genesis line: {line}, error: {e}")
                            logger.debug(f"⚠️ Could not parse HPA line: {line}")
                            continue
            
            logger.info(f"✅ Extracted {len(high_cpu_workloads)} high CPU workloads from HPA data for cluster {self.cluster_name}")
            return high_cpu_workloads
            
        except Exception as e:
            logger.error(f"❌ Error processing HPA high CPU data: {e}")
            return high_cpu_workloads

    def _calculate_max_cpu_utilization(self, hpa_metrics: Dict, pod_metrics: Dict) -> float:
        """Calculate the maximum CPU utilization from all high CPU sources"""
        max_cpu = 0.0
        
        # Check HPA high CPU workloads (these have cpu_utilization field)
        hpa_high_cpu = hpa_metrics.get('high_cpu_hpas', [])
        for workload in hpa_high_cpu:
            cpu_val = workload.get('cpu_utilization', 0)
            if cpu_val > max_cpu:
                max_cpu = cpu_val
        
        # Check pod high CPU workloads (these might have different field names)
        pod_high_cpu = pod_metrics.get('high_cpu_pods', [])
        for workload in pod_high_cpu:
            # Try multiple possible field names for CPU percentage
            cpu_val = max(
                workload.get('cpu_utilization', 0),
                workload.get('hpa_cpu_utilization', 0),
                workload.get('cpu_percentage', 0),
                workload.get('current_cpu', 0)
            )
            if cpu_val > max_cpu:
                max_cpu = cpu_val
        
        logger.info(f"🔍 CALCULATED MAX CPU: {max_cpu}% from {len(hpa_high_cpu)} HPA workloads and {len(pod_high_cpu)} pod workloads")
        return max_cpu

    def debug_high_cpu_detection(self) -> Dict:
        """Debug method to specifically look for high CPU usage patterns"""
        try:
            logger.info("🔍 DEBUG: Specifically looking for high CPU usage patterns...")
            
            # Get HPA high CPU metrics from cache (with CPU_CURRENT and CPU_TARGET columns)
            cache_data = self.cache.get_resource_usage_data()
            hpa_high_cpu_output = cache_data.get('hpa_high_cpu', '')
            
            # Filter out <none> values as the original command did with grep
            if hpa_high_cpu_output:
                hpa_lines = hpa_high_cpu_output.split('\n')
                filtered_lines = [line for line in hpa_lines if '<none>' not in line and line.strip()]
                hpa_output = '\n'.join(filtered_lines)
            else:
                hpa_output = ''
                
            logger.info(f"🔍 Using cached HPA high CPU detection data ({len(hpa_output)} chars)")
            
            debug_info = {
                'high_cpu_hpas': [],
                'hpa_raw_output': hpa_output if hpa_output else "No HPA output",
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            if hpa_output:
                lines = hpa_output.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('NAMESPACE'):
                        parts = line.split()
                        if len(parts) >= 4:
                            namespace = parts[0]
                            name = parts[1]
                            current_cpu = parts[2]
                            target_cpu = parts[3]
                            
                            try:
                                cpu_val = float(current_cpu)
                                if cpu_val > 100:  # High CPU usage
                                    debug_info['high_cpu_hpas'].append({
                                        'namespace': namespace,
                                        'name': name,
                                        'current_cpu': cpu_val,
                                        'target_cpu': target_cpu
                                    })
                                    logger.info(f"🔥 DEBUG: Found high CPU HPA: {namespace}/{name} = {cpu_val}%")
                            except ValueError:
                                pass
            
            logger.info(f"🔍 DEBUG: Found {len(debug_info['high_cpu_hpas'])} high CPU HPAs")
            return debug_info
            
        except Exception as e:
            logger.error(f"❌ Debug high CPU detection failed: {e}")
            return {'error': str(e)}

    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics including HPA detection"""
        logger.info("🚀 Fetching comprehensive real-time AKS metrics...")
        
        start_time = datetime.now()
        
        if not self.verify_cluster_connection():
            return {
                'status': 'error',
                'message': 'Failed to connect to AKS cluster',
                'timestamp': start_time.isoformat()
            }
        
        try:
            # Get node metrics
            node_metrics = self.get_node_metrics()
            
            # Get HPA implementation status
            hpa_status = self.get_hpa_implementation_status()
            
            if node_metrics.get('nodes'):
                return {
                    'metadata': {
                        'cluster_name': self.cluster_name,
                        'resource_group': self.resource_group,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'Real-time AKS Cluster Metrics with HPA Detection',
                        'data_source': 'kubectl via az aks command invoke',
                        'collection_time_ms': int((datetime.now() - start_time).total_seconds() * 1000),
                        'integration_ready': True
                    },
                    'nodes': node_metrics.get('nodes', []),
                    'total_nodes': node_metrics.get('total_nodes', 0),
                    'ready_nodes': node_metrics.get('ready_nodes', 0),
                    'status': 'success',
                    'data_quality': 'high' if node_metrics['nodes'] else 'low',
                    
                    # HPA implementation data
                    'hpa_implementation': hpa_status,
                    'current_hpa_pattern': hpa_status.get('current_hpa_pattern'),
                    'hpa_detection_confidence': hpa_status.get('confidence')
                }
            else:
                return {
                    'status': 'error',
                    'message': 'No node metrics available',
                    'timestamp': start_time.isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error collecting comprehensive metrics: {e}")
            return {
                'status': 'error',
                'message': f'Error collecting metrics: {str(e)}',
                'timestamp': start_time.isoformat()
            }


# ============================================================================
# MAIN INTEGRATION FUNCTIONS
# ============================================================================

def get_aks_realtime_metrics(resource_group: str, cluster_name: str, subscription_id: str) -> Dict[str, Any]:
    """
    Enhanced main integration function with better error handling
    
    Args:
        resource_group: Azure resource group name
        cluster_name: AKS cluster name
        
    Returns:
        Comprehensive real-time metrics ready for cost analysis integration
        
    INTEGRATION: Used by app.py alongside pod_cost_analyzer.py results
    """
    logger.info(f"🎯 Starting enhanced AKS metrics collection for {cluster_name}")
    
    try:
        fetcher = AKSRealTimeMetricsFetcher(resource_group, cluster_name, subscription_id)
        result = fetcher.get_comprehensive_metrics()
        
        if result.get('status') == 'success':
            logger.info(f"✅ Successfully collected AKS metrics: {result.get('total_nodes', 0)} nodes")
        else:
            logger.error(f"❌ AKS metrics collection failed: {result.get('message', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Exception in get_aks_realtime_metrics: {e}")
        return {
            'status': 'error',
            'message': f'Failed to initialize metrics collection: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }


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
from app.analytics.pod_cost_analyzer import get_enhanced_pod_cost_breakdown
costs = get_enhanced_pod_cost_breakdown("my-rg", "my-cluster", 1000.0)

# Combine for comprehensive analysis
from app.analytics.algorithmic_cost_analyzer import integrate_consistent_analysis
results = integrate_consistent_analysis("my-rg", "my-cluster", 
                                       cost_data=billing_data,
                                       metrics_data=metrics,
                                       pod_data=costs)
"""