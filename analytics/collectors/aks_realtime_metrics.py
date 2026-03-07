#!/usr/bin/env python3
"""
Cluster Metrics Collector - Enhanced Version
=============================================
Cloud-agnostic cluster metrics collection with all logical calculations preserved.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: KubeOpt - Kubernetes Cost Optimizer

Key Improvements:
- Consistent variable naming throughout
- No fallback/default values per .clauderc
- All original calculations preserved
- Enhanced error handling and validation
- Uses standards from configuration
"""

import json

# Import performance standards
try:
    from shared.standards.performance_standards import (
        SystemPerformanceStandards as SysPerf
    )
except ImportError:
    # Standards must be available - fail explicitly
    raise ImportError("Performance standards are required but not found")
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

# Import standards
from shared.standards.performance_standards import SystemPerformanceStandards
from shared.standards.cost_optimization_standards import RightSizingCostStandards as CostOptimizationStandards

# Import utilities
from shared.node_data_processor import NodeDataProcessor

logger = logging.getLogger(__name__)


class KubernetesParsingUtils:
    """Utility class for parsing Kubernetes resource values."""
    
    @staticmethod
    def parse_cpu_safe(cpu_str: str) -> float:
        """
        Parse CPU values - handles comma-separated values for multiple containers.
        Returns value in cores (not millicores).
        """
        if not cpu_str or not isinstance(cpu_str, str):
            raise ValueError(f"Invalid CPU string: {cpu_str}")
        
        cpu_str = cpu_str.strip()
        
        # Handle comma-separated values (multiple containers)
        if ',' in cpu_str:
            total_cpu = 0.0
            cpu_values = [val.strip() for val in cpu_str.split(',')]
            for cpu_val in cpu_values:
                if cpu_val and cpu_val not in ['<none>', '<unknown>', 'null']:
                    total_cpu += KubernetesParsingUtils._parse_single_cpu_value(cpu_val)
            return total_cpu
        else:
            return KubernetesParsingUtils._parse_single_cpu_value(cpu_str)
    
    @staticmethod
    def _parse_single_cpu_value(cpu_str: str) -> float:
        """Parse a single CPU value to cores."""
        cpu_str = cpu_str.strip()
        
        # Per .clauderc: NO FALLBACKS - validate real metrics data exists
        if cpu_str in ['<none>', '<unknown>', '', 'null']:
            raise ValueError(f"Invalid CPU metrics data '{cpu_str}' - kubectl metrics collection failed")
        
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000.0  # millicores to cores
        elif cpu_str.endswith('n'):
            return float(cpu_str[:-1]) / 1_000_000_000.0  # nanocores to cores
        else:
            return float(cpu_str)  # already in cores
    
    @staticmethod
    def parse_memory_safe(memory_str: str) -> float:
        """
        Parse memory values - handles comma-separated values for multiple containers.
        Returns value in GB (not bytes).
        """
        if not memory_str or not isinstance(memory_str, str):
            raise ValueError(f"Invalid memory string: {memory_str}")
        
        memory_str = memory_str.strip()
        
        # Handle comma-separated values
        if ',' in memory_str:
            total_memory = 0.0
            memory_values = [val.strip() for val in memory_str.split(',')]
            for mem_val in memory_values:
                if mem_val and mem_val not in ['<none>', '<unknown>', 'null']:
                    total_memory += KubernetesParsingUtils._parse_single_memory_value(mem_val)
            return total_memory
        else:
            return KubernetesParsingUtils._parse_single_memory_value(memory_str)
    
    @staticmethod
    def _parse_single_memory_value(memory_str: str) -> float:
        """Parse a single memory value to GB."""
        memory_str = memory_str.strip()
        
        # Per .clauderc: NO FALLBACKS
        if memory_str in ['<none>', '<unknown>', '', 'null']:
            raise ValueError(f"Invalid memory metrics data '{memory_str}' - kubectl metrics collection failed")
        
        # Convert to GB
        if memory_str.endswith('Ki'):
            return float(memory_str[:-2]) / (1024 * 1024)  # KiB to GB
        elif memory_str.endswith('Mi'):
            return float(memory_str[:-2]) / 1024  # MiB to GB
        elif memory_str.endswith('Gi'):
            return float(memory_str[:-2])  # Already in GiB
        elif memory_str.endswith('Ti'):
            return float(memory_str[:-2]) * 1024  # TiB to GB
        elif memory_str.endswith('K'):
            return float(memory_str[:-1]) / (1000 * 1000)  # KB to GB
        elif memory_str.endswith('M'):
            return float(memory_str[:-1]) / 1000  # MB to GB
        elif memory_str.endswith('G'):
            return float(memory_str[:-1])  # Already in GB
        else:
            # Assume bytes
            return float(memory_str) / (1024 * 1024 * 1024)


class ClusterMetricsFetcher:
    """
    Fetches and processes real-time metrics from Kubernetes clusters.
    Cloud-agnostic implementation with all logical calculations.
    Supports AKS, EKS, and GKE clusters.
    """

    def __init__(self, resource_group: str = '', cluster_name: str = '', subscription_id: str = '', cache=None, cloud_provider: str = 'azure'):
        """Initialize the metrics fetcher.

        Args:
            resource_group: Azure resource group (optional for non-Azure providers)
            cluster_name: Kubernetes cluster name
            subscription_id: Cloud account/subscription/project ID
            cache: Optional shared kubernetes data cache
            cloud_provider: Cloud provider ('azure', 'aws', 'gcp')
        """
        if not cluster_name:
            raise ValueError("cluster_name is required")

        self.resource_group = resource_group or ''
        self.cluster_name = cluster_name
        self.subscription_id = subscription_id or ''
        self.cache = cache
        self.cloud_provider = cloud_provider
        
        # Initialize node processor
        self.node_processor = NodeDataProcessor()
        
        # Performance thresholds from standards
        self.cpu_threshold_optimal = SystemPerformanceStandards.CPU_UTILIZATION_OPTIMAL
        self.cpu_threshold_high = SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE
        self.cpu_threshold_critical = SystemPerformanceStandards.CPU_UTILIZATION_CRITICAL
        
        self.memory_threshold_optimal = SystemPerformanceStandards.MEMORY_UTILIZATION_OPTIMAL
        self.memory_threshold_high = SystemPerformanceStandards.MEMORY_UTILIZATION_HIGH
        self.memory_threshold_critical = SystemPerformanceStandards.MEMORY_UTILIZATION_CRITICAL
        
        # HPA thresholds (using 150% as the high CPU threshold for HPAs)
        # Load HPA threshold from standards file - no static values per .clauderc
        try:
            from shared.standards.standards_loader import get_standards_loader
            loader = get_standards_loader(cloud_provider)
            standards = loader.load_implementation_standards()
            self.hpa_cpu_threshold_high = standards['optimization_thresholds']['savings_calculation']['cost_thresholds']['high_cpu_threshold']
        except Exception as e:
            raise ValueError(f"Failed to load HPA threshold from standards file: {e}") from e
        
        # Cache for node capacities
        self._node_capacities = {}
    
    def get_ml_ready_metrics(self) -> Dict[str, Any]:
        """
        Get metrics with ALL workloads data preserved for ML analysis.
        Complete implementation with all calculations.
        """
        logger.info("🤖 Collecting ML-ready metrics with ALL workloads...")
        
        # Step 1: Get enhanced node-level metrics
        node_metrics = self._get_enhanced_node_resource_data()
        if not node_metrics or not node_metrics.get('nodes'):
            raise ValueError("No valid node metrics available - cannot perform analysis without real node data")
        
        nodes = node_metrics.get('nodes')
        if nodes is None:
            nodes = []
        logger.info(f"✅ Got {len(nodes)} nodes with enhanced metrics")
        
        # Also get original Kubernetes nodes for ML pipeline
        original_nodes_data = self.cache.data.get('nodes')
        original_nodes = []
        if original_nodes_data:
            original_nodes = original_nodes_data.get('items', [])
            logger.info(f"✅ Got {len(original_nodes)} original Kubernetes nodes for ML")
        
        # Step 2: Get HPA implementation status with high CPU detection
        hpa_metrics = self._get_complete_hpa_metrics()
        
        # Step 3: Get ALL workload-level metrics
        workload_metrics = self._get_complete_workload_metrics()
        
        # Step 4: Calculate high CPU summary from all data - NO FALLBACKS
        all_workloads = workload_metrics.get('all_workloads')
        if all_workloads is None:
            raise ValueError("all_workloads missing from workload_metrics")
        
        hpa_cpu_metrics = hpa_metrics.get('hpa_cpu_metrics')
        if hpa_cpu_metrics is None:
            hpa_cpu_metrics = []  # HPAs are optional
        
        top_cpu_summary = self._calculate_top_cpu_summary(all_workloads, hpa_cpu_metrics)
        
        # Step 5: Calculate resource concentration
        resource_concentration = self._calculate_resource_concentration(
            workload_metrics.get('all_workloads', [])
        )
        
        # Step 6: Build complete ML-ready metrics
        ml_metrics = {
            'timestamp': datetime.now().isoformat(),
            'cluster_name': self.cluster_name,
            'subscription_id': self.subscription_id,
            
            # Node metrics - strict .clauderc compliance
            'nodes': node_metrics['nodes'] if 'nodes' in node_metrics else [],
            'original_nodes': original_nodes,  # For ML pipeline that needs status.allocatable
            'node_count': len(node_metrics['nodes']) if 'nodes' in node_metrics else 0,
            'total_cpu_cores': node_metrics['total_cpu_cores'] if 'total_cpu_cores' in node_metrics else 0,
            'total_memory_gb': node_metrics['total_memory_gb'] if 'total_memory_gb' in node_metrics else 0,
            
            # Node-level aggregated metrics
            'avg_cpu_utilization': node_metrics.get('avg_cpu_utilization', 0),
            'avg_memory_utilization': node_metrics.get('avg_memory_utilization', 0),
            'max_cpu_utilization': node_metrics.get('max_cpu_utilization', 0),
            'max_memory_utilization': node_metrics.get('max_memory_utilization', 0),
            
            # Workload metrics - strict .clauderc compliance  
            'all_workloads': workload_metrics['all_workloads'] if 'all_workloads' in workload_metrics else [],
            'total_workloads': workload_metrics['total_workloads'] if 'total_workloads' in workload_metrics else 0,
            'high_cpu_count': workload_metrics.get('high_cpu_count', 0),
            
            # HPA metrics
            'hpa_implementation': hpa_metrics.get('hpa_implementation', {}),
            'hpa_cpu_metrics': hpa_metrics.get('hpa_cpu_metrics', []),
            'cpu_statistics': hpa_metrics.get('cpu_statistics', {}),
            
            # High CPU summary
            'top_cpu_summary': top_cpu_summary,
            
            # Resource concentration
            'resource_concentration': resource_concentration,
            
            # ML features
            'ml_features_ready': True,
            'features': self._extract_ml_features(node_metrics, workload_metrics, hpa_metrics)
        }
        
        # DEBUG: Log final ml_metrics structure before return
        logger.info(f"🔍 DEBUG: Final ml_metrics structure:")
        logger.info(f"🔍 DEBUG: ml_metrics['nodes'] count: {len(ml_metrics.get('nodes', []))}")
        if ml_metrics.get('nodes'):
            for i, node in enumerate(ml_metrics['nodes'][:3]):  # Show first 3 nodes
                cpu_pct = node.get('cpu_usage_pct', 'MISSING')
                name = node.get('name', 'MISSING')
                logger.info(f"🔍 DEBUG FINAL: ml_metrics['nodes'][{i}] = name: '{name}', cpu_usage_pct: {cpu_pct} (type: {type(cpu_pct)})")
                logger.info(f"🔍 DEBUG FINAL: Full node dict keys: {list(node.keys())}")
        else:
            logger.warning(f"🔍 DEBUG FINAL: ml_metrics['nodes'] is empty!")
        
        
        # Validate metrics
        self._validate_ml_metrics(ml_metrics)
        
        return ml_metrics
    
    def _get_enhanced_node_resource_data(self) -> Dict[str, Any]:
        """
        Get enhanced node metrics with all calculations.
        Preserves all original logic but with improved structure.
        """
        logger.info("📊 Fetching enhanced node resource data...")
        
        if not self.cache:
            raise ValueError("Cache is required for node data collection")
        
        # Get raw node data
        nodes_raw = self.cache.get('nodes')
        if not nodes_raw:
            raise ValueError("No nodes data available from cache")
        
        # Extract nodes from JSON structure
        if isinstance(nodes_raw, dict) and 'items' in nodes_raw:
            nodes_list = nodes_raw['items']
        elif isinstance(nodes_raw, list):
            nodes_list = nodes_raw
        else:
            raise ValueError(f"Unexpected nodes data format: {type(nodes_raw)}")
        
        if not nodes_list:
            raise ValueError("No nodes found in nodes data")
        
        # Get node metrics from cache (avoids kubectl authentication issues)
        # The cache already handles Azure Monitor fallback when kubectl fails
        metrics_nodes = self.cache.get('metrics_nodes') or ""
        top_nodes_output = metrics_nodes
        
        # DEBUG: Log the actual kubectl top nodes output
        logger.info(f"🔍 DEBUG: kubectl top nodes raw output for cluster {self.cluster_name}:")
        logger.info(f"🔍 DEBUG: metrics_nodes type={type(metrics_nodes)}, length={len(metrics_nodes) if metrics_nodes else 0}")
        if metrics_nodes:
            logger.info(f"🔍 DEBUG: First 200 chars of metrics_nodes: {repr(metrics_nodes[:200])}")
        else:
            logger.warning(f"🔍 DEBUG: metrics_nodes is empty or None")
        
        # Process nodes with enhanced data
        processed_nodes = []
        total_cpu_cores = 0
        total_memory_gb = 0
        
        for node_raw in nodes_list:
            try:
                # Parse using NodeDataProcessor for consistency
                node_data = self.node_processor.parse_node_data([node_raw])
                if not node_data:
                    continue
                
                node = node_data[0]
                node_name = node.get('name')
                
                # Get allocatable resources
                cpu_cores = node.get('allocatable_cpu', 0)
                memory_gb = node.get('allocatable_memory', 0)
                
                # Get usage from kubernetes_data_cache (single source of truth)
                cpu_usage_pct = 0
                memory_usage_pct = 0
                
                # Extract from cache's top nodes data
                if top_nodes_output:
                    usage_data = self._extract_node_usage_from_top(node_name, top_nodes_output)
                    if usage_data and 'cpu_usage_pct' in usage_data:
                        cpu_usage_pct = usage_data.get('cpu_usage_pct', 0)
                        memory_usage_pct = usage_data.get('memory_usage_pct', 0)
                        logger.info(f"✅ Node {node_name}: Found cache metrics CPU={cpu_usage_pct}%, Memory={memory_usage_pct}%")
                    else:
                        logger.warning(f"⚠️ Node {node_name}: No metrics found in cache top output")
                else:
                    logger.warning(f"⚠️ No metrics_nodes data in cache for {node_name}")
                
                # STRICT VALIDATION per .clauderc: cpu_usage_pct field is required
                # If cache doesn't have it, skip this node but log the issue clearly
                if not isinstance(cpu_usage_pct, (int, float)):
                    logger.error(f"❌ VALIDATION: Node {node_name} excluded - cpu_usage_pct must be numeric, got {type(cpu_usage_pct)} = {cpu_usage_pct}")
                    continue  # Skip this node but continue processing others
                if not isinstance(memory_usage_pct, (int, float)):
                    logger.error(f"❌ VALIDATION: Node {node_name} excluded - memory_usage_pct must be numeric, got {type(memory_usage_pct)} = {memory_usage_pct}")
                    continue  # Skip this node but continue processing others
                
                # STRICT VALIDATION: Zero CPU metrics indicate cache/kubectl failure
                if cpu_usage_pct == 0:
                    raise ValueError(f"Node {node_name}: cpu_usage_pct cannot be 0 - indicates kubectl top failure or cache corruption")
                
                logger.info(f"✅ Node {node_name}: Using cache metrics CPU={cpu_usage_pct}%, Memory={memory_usage_pct}%")
                
                # Calculate efficiency scores
                cpu_efficiency = self._calculate_cpu_efficiency(cpu_usage_pct)
                memory_efficiency = self._calculate_memory_efficiency(memory_usage_pct)
                
                # Categorize usage severity
                cpu_severity = self._categorize_cpu_usage_severity(cpu_usage_pct)
                memory_severity = self._categorize_memory_usage_severity(memory_usage_pct)
                
                # DEBUG: Log the exact values being used to build processed_node
                logger.info(f"🔍 DEBUG BUILD: Creating processed_node for {node_name}")
                logger.info(f"🔍 DEBUG BUILD: cpu_usage_pct = {cpu_usage_pct} (type: {type(cpu_usage_pct)})")
                logger.info(f"🔍 DEBUG BUILD: memory_usage_pct = {memory_usage_pct} (type: {type(memory_usage_pct)})")
                logger.info(f"🔍 DEBUG BUILD: cpu_cores = {cpu_cores}, memory_gb = {memory_gb}")
                
                processed_node = {
                    'name': node_name,
                    'node_name': node_name,  # Add for node optimization algorithm compatibility
                    'cpu_cores': cpu_cores,
                    'memory_gb': memory_gb,
                    'cpu_usage_pct': cpu_usage_pct,
                    'memory_usage_pct': memory_usage_pct,
                    'cpu_efficiency': cpu_efficiency,
                    'memory_efficiency': memory_efficiency,
                    'cpu_severity': cpu_severity,
                    'memory_severity': memory_severity,
                    'nodepool': node.get('nodepool', 'default'),
                    'status': node.get('status', 'Unknown'),
                    'vm_size': node.get('vm_size', 'unknown'),
                    'region': node.get('region', 'unknown')
                }
                
                # DEBUG: Verify what was actually stored in processed_node
                logger.info(f"🔍 DEBUG BUILD: processed_node created with name='{processed_node.get('name')}', cpu_usage_pct={processed_node.get('cpu_usage_pct')}")
                
                processed_nodes.append(processed_node)
                total_cpu_cores += cpu_cores
                total_memory_gb += memory_gb
                
                # DEBUG: Log each processed node
                logger.info(f"🔍 DEBUG: Processed node {node_name} - CPU: {cpu_usage_pct}%, Memory: {memory_usage_pct}%")
                
                # Cache node capacity for later use
                self._node_capacities[node_name] = {
                    'cpu_cores': cpu_cores,
                    'memory_gb': memory_gb
                }
                
            except Exception as e:
                logger.error(f"Failed to process node {node_raw.get('name', 'unknown')}: {e}")
                raise ValueError(f"Node processing failed: {e}")
        
        if not processed_nodes:
            raise ValueError("No nodes could be processed")
        
        return {
            'nodes': processed_nodes,
            'total_cpu_cores': total_cpu_cores,
            'total_memory_gb': total_memory_gb,
            'avg_cpu_utilization': np.mean([n['cpu_usage_pct'] for n in processed_nodes]),
            'avg_memory_utilization': np.mean([n['memory_usage_pct'] for n in processed_nodes]),
            'max_cpu_utilization': max([n['cpu_usage_pct'] for n in processed_nodes]),
            'max_memory_utilization': max([n['memory_usage_pct'] for n in processed_nodes])
        }
    
    def _get_complete_hpa_metrics(self) -> Dict[str, Any]:
        """Get complete HPA metrics with high CPU detection."""
        logger.info("📊 Fetching HPA metrics with high CPU detection...")
        
        try:
            # Get base HPA implementation status
            hpa_status = self.get_hpa_implementation_status()
            
            # Get HPA metrics with high CPU detection
            high_cpu_data = self.get_hpa_metrics_with_high_cpu_detection()
            
            # Combine all HPA data
            hpa_metrics = {
                'hpa_implementation': hpa_status,
                'hpa_cpu_metrics': high_cpu_data.get('hpa_cpu_metrics', []),
                'cpu_statistics': high_cpu_data.get('cpu_statistics', {}),
                'total_hpas': hpa_status.get('total_hpas', 0),
                'cpu_based_count': hpa_status.get('cpu_based_count', 0),
                'memory_based_count': hpa_status.get('memory_based_count', 0),
                'current_hpa_pattern': hpa_status.get('current_hpa_pattern', 'unknown')
            }
            
            logger.info(f"✅ Got {len(hpa_metrics['hpa_cpu_metrics'])} HPAs with CPU metrics")
            
            return hpa_metrics
            
        except Exception as e:
            logger.error(f"Failed to get HPA metrics: {e}")
            # Return empty structure per .clauderc (no fallbacks)
            raise ValueError(f"HPA metrics collection failed: {e}")
    
    def get_hpa_implementation_status(self) -> Dict[str, Any]:
        """
        Analyze current HPA implementation status in the cluster.
        Preserves original logic with improvements.
        """
        logger.info("🔍 Analyzing HPA implementation status...")
        
        if not self.cache:
            raise ValueError("Cache is required for HPA analysis")
        
        # Get HPA data from cache - use consistent method
        try:
            hpa_cache_data = self.cache.get_hpa_data()
            if hpa_cache_data and hpa_cache_data.get('hpa'):
                hpa_data = hpa_cache_data.get('hpa')
                logger.info(f"✅ Retrieved HPA data using get_hpa_data() method for implementation status")
            else:
                # Fallback to direct cache access
                hpa_data = self.cache.get('hpa')
                if not hpa_data:
                    logger.warning("No HPA data found in cache for implementation status")
                    return {
                        'total_hpas': 0,
                        'cpu_based_count': 0,
                        'memory_based_count': 0,
                        'multi_metric_count': 0,
                        'current_hpa_pattern': 'no_hpa',
                        'hpa_details': [],
                        'confidence': 'high'
                    }
        except Exception as e:
            logger.warning(f"Error getting HPA data for implementation status: {e}")
            hpa_data = self.cache.get('hpa')
            if not hpa_data:
                return {
                    'total_hpas': 0,
                    'cpu_based_count': 0,
                    'memory_based_count': 0,
                    'multi_metric_count': 0,
                    'current_hpa_pattern': 'no_hpa',
                    'hpa_details': [],
                    'confidence': 'high'
                }
        
        # Extract HPAs from JSON structure - strict .clauderc compliance
        if isinstance(hpa_data, dict) and 'items' in hpa_data:
            hpas_list = hpa_data['items']
        elif isinstance(hpa_data, list):
            hpas_list = hpa_data
        else:
            logger.warning(f"Unexpected HPA data format: {type(hpa_data)}")
            hpas_list = []
        
        # Analyze HPA configurations
        cpu_based = 0
        memory_based = 0
        multi_metric = 0
        hpa_details = []
        
        for hpa in hpas_list:
            try:
                metadata = hpa.get('metadata', {})
                spec = hpa.get('spec', {})
                status = hpa.get('status', {})
                
                name = metadata.get('name', 'unknown')
                namespace = metadata.get('namespace', 'default')
                
                # Analyze metrics configuration
                metrics = spec.get('metrics', [])
                has_cpu = False
                has_memory = False
                other_metrics = []
                
                # Check for CPU/memory metrics
                for metric in metrics:
                    metric_type = metric.get('type', '')
                    if metric_type == 'Resource':
                        resource = metric.get('resource', {})
                        resource_name = resource.get('name', '')
                        if resource_name == 'cpu':
                            has_cpu = True
                        elif resource_name == 'memory':
                            has_memory = True
                    else:
                        other_metrics.append(metric_type)
                
                # Legacy check for targetCPUUtilizationPercentage
                if not metrics and spec.get('targetCPUUtilizationPercentage'):
                    has_cpu = True
                
                # Categorize HPA
                if has_cpu and has_memory:
                    multi_metric += 1
                elif has_cpu:
                    cpu_based += 1
                elif has_memory:
                    memory_based += 1
                
                # Classify scaling strategy
                scaling_strategy = self._classify_hpa_scaling_strategy(
                    has_cpu, has_memory, other_metrics
                )
                
                hpa_detail = {
                    'name': name,
                    'namespace': namespace,
                    'min_replicas': spec.get('minReplicas', 1),
                    'max_replicas': spec.get('maxReplicas', 10),
                    'current_replicas': status.get('currentReplicas', 0),
                    'desired_replicas': status.get('desiredReplicas', 0),
                    'has_cpu_metric': has_cpu,
                    'has_memory_metric': has_memory,
                    'scaling_strategy': scaling_strategy,
                    'target_cpu': spec.get('targetCPUUtilizationPercentage', 0)
                }
                
                hpa_details.append(hpa_detail)
                
            except Exception as e:
                logger.error(f"Failed to process HPA {hpa.get('metadata', {}).get('name', 'unknown')}: {e}")
                continue
        
        # Determine current HPA pattern
        total_hpas = len(hpas_list)
        if total_hpas == 0:
            pattern = 'no_hpa'
        elif cpu_based > memory_based and cpu_based > multi_metric:
            pattern = 'cpu_dominant'
        elif memory_based > cpu_based:
            pattern = 'memory_dominant'
        elif multi_metric > cpu_based:
            pattern = 'multi_metric'
        else:
            pattern = 'mixed'
        
        return {
            'total_hpas': total_hpas,
            'cpu_based_count': cpu_based,
            'memory_based_count': memory_based,
            'multi_metric_count': multi_metric,
            'current_hpa_pattern': pattern,
            'hpa_details': hpa_details,
            'confidence': 'high'
        }
    
    def get_hpa_metrics_with_high_cpu_detection(self) -> Dict[str, Any]:
        """
        Get HPA metrics with high CPU detection.
        Identifies workloads with >150% CPU utilization.
        """
        logger.info("🔍 Detecting high CPU workloads in HPAs...")
        
        hpa_cpu_metrics = []
        high_cpu_hpas = []
        
        # Get HPA status - use the same method as HPA analyzer for consistency
        try:
            hpa_status_raw = self.cache.get_hpa_data()
            if not hpa_status_raw or not hpa_status_raw.get('hpa'):
                # Try direct cache access as fallback
                hpa_status_raw = self.cache.get('hpa')
                if not hpa_status_raw:
                    logger.warning("No HPA data found in cache")
                    return {
                        'hpa_cpu_metrics': [],
                        'high_cpu_hpas': [],
                        'cpu_statistics': {'avg_cpu': 0, 'max_cpu': 0, 'min_cpu': 0}
                    }
            else:
                # Use the structured HPA data from get_hpa_data()
                hpa_status_raw = hpa_status_raw.get('hpa', hpa_status_raw)
                logger.info(f"✅ Retrieved HPA data using get_hpa_data() method")
        except Exception as e:
            logger.warning(f"Error getting HPA data: {e}, falling back to direct cache access")
            hpa_status_raw = self.cache.get('hpa')
            if not hpa_status_raw:
                return {
                    'hpa_cpu_metrics': [],
                    'high_cpu_hpas': [],
                    'cpu_statistics': {'avg_cpu': 0, 'max_cpu': 0, 'min_cpu': 0}
                }
        
        # Extract HPAs from JSON structure - strict .clauderc compliance
        if isinstance(hpa_status_raw, dict) and 'items' in hpa_status_raw:
            hpa_status = hpa_status_raw['items']
            logger.info(f"🔍 Using items structure with {len(hpa_status)} HPAs")
        elif isinstance(hpa_status_raw, list):
            hpa_status = hpa_status_raw
            logger.info(f"🔍 Using list structure with {len(hpa_status)} HPAs")
        else:
            raise ValueError(f"Unexpected HPA status data format: {type(hpa_status_raw)}")
        
        # Process each HPA
        for hpa in hpa_status:
            try:
                hpa_name = hpa.get('metadata', {}).get('name', 'unknown')
                status = hpa.get('status', {})
                current_metrics = status.get('currentMetrics', [])
                logger.info(f"🔍 HPA {hpa_name}: found {len(current_metrics)} currentMetrics")
                
                # Debug the HPA structure
                if not current_metrics:
                    logger.info(f"⚠️ HPA {hpa_name}: No currentMetrics found. Status keys: {list(status.keys())}")
                    logger.info(f"⚠️ HPA {hpa_name}: Full status: {status}")
                
                for metric in current_metrics:
                    # Debug each metric structure
                    metric_type = metric.get('type')
                    resource_info = metric.get('resource', {})
                    resource_name = resource_info.get('name')
                    logger.info(f"🔍 HPA {hpa_name}: metric type='{metric_type}', resource_name='{resource_name}'")
                    
                    if metric_type == 'Resource' and resource_name == 'cpu':
                        current_util = resource_info.get('current', {})
                        logger.info(f"🔍 HPA {hpa_name}: CPU metric found, current_util keys: {list(current_util.keys())}")
                        logger.info(f"🔍 HPA {hpa_name}: Full current_util: {current_util}")
                        
                        # Parse utilization percentage - accept any valid number including 0
                        util_pct = None
                        if 'averageUtilization' in current_util:
                            util_pct = current_util['averageUtilization']
                        elif 'averageValue' in current_util:
                            # Alternative key format
                            util_pct = current_util['averageValue']
                        
                        if util_pct is not None:
                            logger.info(f"✅ HPA {hpa_name}: CPU utilization = {util_pct}%")
                        else:
                            logger.warning(f"⚠️ HPA {hpa_name}: No utilization value found in {current_util}")
                            # Per .clauderc - no defaults, continue to next metric
                            continue
                        
                        hpa_name = hpa.get('metadata', {}).get('name', 'unknown')
                        namespace = hpa.get('metadata', {}).get('namespace', 'default')
                        
                        cpu_metric = {
                            'name': hpa_name,
                            'namespace': namespace,
                            'cpu_usage_pct': util_pct,
                            'current_replicas': status.get('currentReplicas', 0),
                            'desired_replicas': status.get('desiredReplicas', 0)
                        }
                        
                        hpa_cpu_metrics.append(cpu_metric)
                        logger.info(f"✅ HPA {hpa_name}: Added CPU metric to list")
                        
                        # Check if high CPU (>150%)
                        if util_pct > self.hpa_cpu_threshold_high:
                            cpu_metric['severity'] = self._categorize_hpa_cpu_severity(util_pct)
                            high_cpu_hpas.append(cpu_metric)
                        
            except Exception as e:
                logger.error(f"Failed to process HPA metrics: {e}")
                continue
        
        # Calculate statistics
        cpu_values = [h['cpu_usage_pct'] for h in hpa_cpu_metrics]
        cpu_statistics = {
            'avg_cpu': np.mean(cpu_values) if cpu_values else 0,
            'max_cpu': max(cpu_values) if cpu_values else 0,
            'min_cpu': min(cpu_values) if cpu_values else 0,
            'std_cpu': np.std(cpu_values) if cpu_values else 0
        }
        
        # Final debug logging
        logger.info(f"📊 HPA CPU extraction complete: {len(hpa_cpu_metrics)} CPUs from {len(hpa_status)} HPAs")
        if hpa_cpu_metrics:
            logger.info(f"📊 Sample CPU metrics: {hpa_cpu_metrics[0]}")
        else:
            logger.warning(f"⚠️ No CPU metrics extracted from {len(hpa_status)} HPAs")
        
        return {
            'hpa_cpu_metrics': hpa_cpu_metrics,
            'high_cpu_hpas': high_cpu_hpas,
            'cpu_statistics': cpu_statistics,
            'high_cpu_count': len(high_cpu_hpas)
        }
    
    def _get_complete_workload_metrics(self) -> Dict[str, Any]:
        """Get complete workload metrics for all deployments/pods."""
        logger.info("📊 Getting complete workload metrics...")
        
        all_workloads = []
        high_cpu_workloads = []
        
        # Get deployments - strict .clauderc compliance
        deployments_raw = self.cache.get('deployments')
        if not deployments_raw:
            raise ValueError("No deployments data available from cache")
        
        # Extract deployments from JSON structure
        if isinstance(deployments_raw, dict) and 'items' in deployments_raw:
            deployments = deployments_raw['items']
        elif isinstance(deployments_raw, list):
            deployments = deployments_raw
        else:
            raise ValueError(f"Unexpected deployments data format: {type(deployments_raw)}")
        
        # Get pods for resource usage - strict .clauderc compliance
        pods_raw = self.cache.get('pods')
        if not pods_raw:
            raise ValueError("No pods data available from cache")
        
        # Extract pods from JSON structure
        if isinstance(pods_raw, dict) and 'items' in pods_raw:
            pods = pods_raw['items']
        elif isinstance(pods_raw, list):
            pods = pods_raw
        else:
            raise ValueError(f"Unexpected pods data format: {type(pods_raw)}")
        
        # Process each deployment
        for deployment in deployments:
            try:
                metadata = deployment.get('metadata', {})
                spec = deployment.get('spec', {})
                
                name = metadata.get('name', 'unknown')
                namespace = metadata.get('namespace', 'default')
                replicas = spec.get('replicas', 1)
                
                # Calculate resource usage for this workload
                cpu_usage, memory_usage, cpu_request, memory_request = self._calculate_workload_resources(
                    name, namespace, pods
                )
                
                # Calculate utilization percentages
                cpu_usage_pct = 0
                if cpu_request > 0:
                    cpu_usage_pct = (cpu_usage / cpu_request) * 100
                
                memory_utilization_pct = 0
                if memory_request > 0:
                    memory_utilization_pct = (memory_usage / memory_request) * 100
                
                workload = {
                    'name': name,
                    'namespace': namespace,
                    'type': 'deployment',
                    'replicas': replicas,
                    'cpu_usage_cores': cpu_usage,
                    'memory_usage_gb': memory_usage,
                    'cpu_request_cores': cpu_request,
                    'memory_request_gb': memory_request,
                    'cpu_usage_pct': cpu_usage_pct,
                    'memory_usage_pct': memory_utilization_pct
                }
                
                all_workloads.append(workload)
                
                # Add severity categorization for all workloads
                workload['severity'] = self._categorize_cpu_usage_severity(cpu_usage_pct)
                
            except Exception as e:
                logger.error(f"Failed to process workload {deployment.get('metadata', {}).get('name', 'unknown')}: {e}")
                continue
        
        return {
            'all_workloads': all_workloads,
            'high_cpu_workloads': high_cpu_workloads,
            'total_workloads': len(all_workloads),
            'high_cpu_count': len(high_cpu_workloads)
        }
    
    def _calculate_workload_resources(self, name: str, namespace: str, pods: List[Dict]) -> Tuple[float, float, float, float]:
        """Calculate resource usage for a workload."""
        total_cpu_usage = 0
        total_memory_usage = 0
        total_cpu_request = 0
        total_memory_request = 0
        
        for pod in pods or []:
            try:
                pod_meta = pod.get('metadata', {})
                if pod_meta.get('namespace') != namespace:
                    continue
                
                # Check if pod belongs to this workload
                pod_name = pod_meta.get('name', '')
                if not pod_name.startswith(name):
                    # Check owner references
                    owner_refs = pod_meta.get('ownerReferences', [])
                    belongs = False
                    for owner in owner_refs:
                        if owner.get('name', '').startswith(name):
                            belongs = True
                            break
                    if not belongs:
                        continue
                
                # Get pod specs
                spec = pod.get('spec', {})
                containers = spec.get('containers', [])
                
                for container in containers:
                    resources = container.get('resources', {})
                    requests = resources.get('requests', {})
                    
                    # Parse requests
                    cpu_request = KubernetesParsingUtils.parse_cpu_safe(requests.get('cpu', '0'))
                    memory_request = KubernetesParsingUtils.parse_memory_safe(requests.get('memory', '0'))
                    
                    total_cpu_request += cpu_request
                    total_memory_request += memory_request
                    
                    # Estimate usage (would come from metrics-server in production)
                    # Use standards file values per .clauderc - no static values
                    total_cpu_usage += cpu_request * CostOptimizationStandards.CPU_USAGE_ESTIMATION_FACTOR
                    total_memory_usage += memory_request * CostOptimizationStandards.MEMORY_USAGE_ESTIMATION_FACTOR
                
            except Exception as e:
                logger.debug(f"Error processing pod {pod.get('metadata', {}).get('name', 'unknown')}: {e}")
                continue
        
        return total_cpu_usage, total_memory_usage, total_cpu_request, total_memory_request
    
    def _calculate_top_cpu_summary(self, all_workloads: List[Dict], hpa_cpu_metrics: List[Dict]) -> Dict:
        """Calculate top CPU summary - pass all CPUs and identify the maximum."""
        if not all_workloads and not hpa_cpu_metrics:
            raise ValueError("No workload or HPA data available for CPU analysis")
        
        # Extract all CPU values from workloads
        workload_cpus = [w['cpu_usage_pct'] for w in all_workloads if 'cpu_usage_pct' in w]
        hpa_cpus = [h['cpu_usage_pct'] for h in hpa_cpu_metrics if 'cpu_usage_pct' in h]
        
        # Find maximum CPU from all sources
        all_cpus = workload_cpus + hpa_cpus
        if not all_cpus:
            raise ValueError("No valid CPU usage data found in workloads or HPAs")
        
        max_cpu = max(all_cpus)
        avg_cpu = sum(all_cpus) / len(all_cpus)
        
        # Find top CPU workload
        top_workload = None
        if workload_cpus:
            top_workload = max(all_workloads, key=lambda w: w.get('cpu_usage_pct', 0))
        
        # Calculate optimization score based on CPU efficiency
        cpu_efficiency = min(100, max(0, 100 - max_cpu)) if max_cpu > 0 else 0
        optimization_score = cpu_efficiency
        
        return {
            'all_workloads': all_workloads,
            'all_hpas': hpa_cpu_metrics,
            'max_cpu_utilization': max_cpu,
            'avg_cpu_utilization': avg_cpu,
            'cpu_efficiency': cpu_efficiency,
            'optimization_score': optimization_score,
            'total_workloads': len(all_workloads),
            'total_hpas': len(hpa_cpu_metrics),
            'top_cpu_workload': top_workload
        }
    
    def _calculate_resource_concentration(self, workload_data: List[Dict]) -> Dict:
        """
        Calculate resource concentration (Gini coefficient).
        Identifies if resources are evenly distributed or concentrated.
        """
        if not workload_data:
            return {'gini_coefficient': 0, 'concentration_level': 'unknown'}
        
        # Calculate total resource usage per workload
        resource_values = []
        for workload in workload_data:
            cpu_usage = workload.get('cpu_usage_cores', 0)
            memory_usage = workload.get('memory_usage_gb', 0)
            # Normalize and combine CPU and memory
            total_resource = cpu_usage + (memory_usage / 10)  # Rough normalization
            resource_values.append(total_resource)
        
        # Calculate Gini coefficient
        resource_values = sorted(resource_values)
        n = len(resource_values)
        cumsum = 0
        for i, value in enumerate(resource_values):
            cumsum += (n - i) * value
        
        gini = (n + 1 - 2 * cumsum / sum(resource_values)) / n if sum(resource_values) > 0 else 0
        
        # Determine concentration level
        if gini < 0.3:
            concentration = 'low'  # Resources evenly distributed
        elif gini < 0.6:
            concentration = 'medium'  # Moderate concentration
        else:
            concentration = 'high'  # High concentration in few workloads
        
        return {
            'gini_coefficient': gini,
            'concentration_level': concentration,
            'top_consumers': self._identify_top_consumers(workload_data)
        }
    
    def _identify_top_consumers(self, workloads: List[Dict], top_n: int = 5) -> List[Dict]:
        """Identify top resource consumers."""
        # Sort by combined resource usage
        sorted_workloads = sorted(
            workloads,
            key=lambda w: w.get('cpu_usage_cores', 0) + w.get('memory_usage_gb', 0) / 10,
            reverse=True
        )
        
        return sorted_workloads[:top_n]
    
    def _extract_ml_features(self, node_metrics: Dict, workload_metrics: Dict, hpa_metrics: Dict) -> Dict:
        """Extract features for ML models."""
        features = {
            # Cluster-level features
            'cluster_cpu_usage_pct': node_metrics.get('avg_cpu_usage_pct', 0),
            'cluster_memory_utilization': node_metrics.get('avg_memory_usage_pct', 0),
            'cluster_cpu_variance': np.std([n['cpu_usage_pct'] for n in node_metrics.get('nodes', [])]),
            'cluster_memory_variance': np.std([n['memory_usage_pct'] for n in node_metrics.get('nodes', [])]),
            
            # Workload features
            'total_workloads': workload_metrics.get('total_workloads', 0),
            'high_cpu_ratio': (workload_metrics.get('high_cpu_count', 0) / 
                              max(workload_metrics.get('total_workloads', 1), 1)),
            
            # HPA features
            'hpa_coverage': (hpa_metrics.get('total_hpas', 0) / 
                            max(workload_metrics.get('total_workloads', 1), 1)),
            'hpa_cpu_based_ratio': (hpa_metrics.get('cpu_based_count', 0) / 
                                   max(hpa_metrics.get('total_hpas', 1), 1)),
            
            # Resource distribution
            'resource_gini': workload_metrics.get('resource_concentration', {}).get('gini_coefficient', 0)
        }
        
        return features
    
    def _categorize_cpu_usage_severity(self, cpu_usage_pct: float) -> str:
        """Categorize CPU usage severity based on thresholds."""
        if cpu_usage_pct >= self.cpu_threshold_critical:
            return 'critical'
        elif cpu_usage_pct >= self.cpu_threshold_high:
            return 'high'
        elif cpu_usage_pct >= self.cpu_threshold_optimal:
            return 'optimal'
        else:
            return 'low'
    
    def _categorize_memory_usage_severity(self, memory_usage_pct: float) -> str:
        """Categorize memory usage severity based on thresholds."""
        if memory_usage_pct >= self.memory_threshold_critical:
            return 'critical'
        elif memory_usage_pct >= self.memory_threshold_high:
            return 'high'
        elif memory_usage_pct >= self.memory_threshold_optimal:
            return 'optimal'
        else:
            return 'low'
    
    def _categorize_hpa_cpu_severity(self, cpu_usage_pct: float) -> str:
        """Categorize HPA CPU severity (uses higher thresholds)."""
        if cpu_usage_pct >= 1000:
            return 'critical'
        elif cpu_usage_pct >= 300:
            return 'very_high'
        elif cpu_usage_pct >= 150:
            return 'high'
        else:
            return 'normal'
    
    def _calculate_cpu_efficiency(self, cpu_usage_pct: float) -> float:
        """Calculate CPU efficiency score (0-100)."""
        # Optimal range is 60-80%
        if 60 <= cpu_usage_pct <= 80:
            return 100.0
        elif cpu_usage_pct < 60:
            # Under-utilized
            return max(0, cpu_usage_pct * 100 / 60)
        else:
            # Over-utilized
            return max(0, 100 - (cpu_usage_pct - 80) * 2)
    
    def _calculate_memory_efficiency(self, memory_usage_pct: float) -> float:
        """Calculate memory efficiency score (0-100)."""
        # Optimal range is 65-85%
        if 65 <= memory_usage_pct <= 85:
            return 100.0
        elif memory_usage_pct < 65:
            # Under-utilized
            return max(0, memory_usage_pct * 100 / 65)
        else:
            # Over-utilized
            return max(0, 100 - (memory_usage_pct - 85) * 2)
    
    def _classify_hpa_scaling_strategy(self, has_cpu: bool, has_memory: bool, other_metrics: List) -> str:
        """Classify HPA scaling strategy."""
        if has_cpu and has_memory and other_metrics:
            return 'advanced_multi_metric'
        elif has_cpu and has_memory:
            return 'balanced'
        elif has_cpu:
            return 'cpu_focused'
        elif has_memory:
            return 'memory_focused'
        elif other_metrics:
            return 'custom_metrics'
        else:
            return 'unknown'
    
    def _extract_node_usage_from_top(self, node_name: str, top_output: str) -> Optional[Dict]:
        """Extract node usage from kubectl top output with Azure VMSS name mapping."""
        # DEBUG: Log the parsing attempt
        logger.info(f"🔍 DEBUG PARSE: Trying to extract usage for node '{node_name}' from top output")
        
        if not top_output:
            logger.warning(f"🔍 DEBUG PARSE: top_output is empty for node {node_name}")
            return None
        
        # Try exact name match first
        logger.info(f"🔍 DEBUG PARSE: kubectl top output has {len(top_output.strip().split()) if top_output.strip() else 0} lines")
        for i, line in enumerate(top_output.strip().split('\n')):
            parts = line.split()
            logger.info(f"🔍 DEBUG PARSE: Line {i}: '{line}' -> parts: {parts}")
            if len(parts) >= 5 and parts[0] == node_name:
                try:
                    result = {
                        'cpu_usage_pct': float(parts[2].rstrip('%')),
                        'memory_usage_pct': float(parts[4].rstrip('%'))
                    }
                    logger.info(f"🔍 DEBUG PARSE: EXACT MATCH found for {node_name}: {result}")
                    return result
                except Exception as e:
                    logger.warning(f"🔍 DEBUG PARSE: Failed to parse line for {node_name}: {e}")
                    continue
        
        # If no exact match, try Azure VMSS name mapping (Azure-only)
        # Convert k8s node name (vmss0000e8) to Azure name (vmss_xxx)
        if self.cloud_provider == 'azure' and 'vmss' in node_name:
            # Extract the hex suffix and convert to decimal for Azure naming
            try:
                parts_node = node_name.split('vmss')
                if len(parts_node) == 2:
                    vmss_base = parts_node[0] + 'vmss'
                    hex_suffix = parts_node[1]

                    # Try to match with any line that starts with the vmss base
                    for line in top_output.strip().split('\n'):
                        parts = line.split()
                        if len(parts) >= 5 and parts[0].startswith(vmss_base):
                            try:
                                logger.info(f"🔗 Mapped node {node_name} to Azure metrics {parts[0]}")
                                return {
                                    'cpu_usage_pct': float(parts[2].rstrip('%')),
                                    'memory_usage_pct': float(parts[4].rstrip('%'))
                                }
                            except Exception:
                                continue
            except Exception as e:
                logger.warning(f"Failed to map Azure VMSS name for {node_name}: {e}")
        
        logger.warning(f"No usage data found for node {node_name}")
        return None
    
    def _validate_ml_metrics(self, metrics: Dict):
        """Validate ML metrics structure per .clauderc."""
        required_fields = ['nodes', 'all_workloads', 'top_cpu_summary', 'hpa_implementation']
        
        for field in required_fields:
            if field not in metrics:
                raise ValueError(f"Missing required field in ML metrics: {field}")
        
        if not metrics['nodes']:
            raise ValueError("No nodes data in ML metrics")
        
        # Validate data quality
        if len(metrics['nodes']) == 0:
            raise ValueError("Empty nodes list in ML metrics")
        
        # Validate top_cpu_summary is not empty
        top_cpu = metrics['top_cpu_summary']
        if not top_cpu or not isinstance(top_cpu, dict):
            raise ValueError(f"top_cpu_summary is invalid or empty: {type(top_cpu)}")
        
        required_cpu_fields = ['max_cpu_utilization', 'avg_cpu_utilization', 'all_workloads']
        for field in required_cpu_fields:
            if field not in top_cpu:
                raise ValueError(f"top_cpu_summary missing required field: {field}")
        
        logger.info(f"✅ ML metrics validated: {len(metrics['nodes'])} nodes, {metrics['total_workloads']} workloads")