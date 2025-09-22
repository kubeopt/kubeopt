#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer

Enhanced HPA Analyzer Module
============================
Dedicated module for comprehensive HPA analysis with robust detection logic.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HPAAnalyzer:
    """
    Comprehensive HPA analyzer with enhanced detection capabilities
    
    This class provides robust HPA analysis including:
    - Multi-metric detection (CPU, Memory, Custom)
    - API version compatibility checking
    - Deployment-to-HPA mapping
    - Scaling strategy classification
    - Optimization scoring
    """
    
    @staticmethod
    def detect_hpa_metrics(hpa: Dict) -> Dict:
        """
        Enhanced HPA metrics detection that returns comprehensive metric information
        
        Args:
            hpa: HPA configuration dictionary
            
        Returns:
            Dict with detailed metrics information including:
            - primary_metric: The main scaling metric
            - cpu/memory: Resource targets if present
            - custom: List of custom metrics
            - has_multiple: Whether HPA uses multiple metrics
            - scaling_strategy: Classified strategy (cpu-based, memory-based, balanced, etc.)
            - api_version: HPA API version
        """
        metrics_info = {
            'primary_metric': None,
            'cpu': None,
            'memory': None,
            'custom': [],
            'has_multiple': False,
            'scaling_strategy': 'unknown',
            'api_version': hpa.get('apiVersion', 'unknown'),
            'total_metrics': 0
        }
        
        try:
            metrics = hpa.get('spec', {}).get('metrics', [])
            metrics_info['total_metrics'] = len(metrics)
            
            if len(metrics) > 1:
                metrics_info['has_multiple'] = True
            
            for idx, metric in enumerate(metrics):
                if metric.get('type') == 'Resource':
                    resource_name = metric.get('resource', {}).get('name', '')
                    target = metric.get('resource', {}).get('target', {})
                    
                    # Extract target value (could be utilization or averageValue)
                    if 'averageUtilization' in target:
                        target_value = f"{target['averageUtilization']}%"
                        target_numeric = target['averageUtilization']
                    elif 'averageValue' in target:
                        target_value = target['averageValue']
                        target_numeric = HPAAnalyzer._parse_resource_value(target['averageValue'])
                    else:
                        target_value = 'unknown'
                        target_numeric = 0
                    
                    if resource_name == 'cpu':
                        metrics_info['cpu'] = {
                            'target': target_value,
                            'target_numeric': target_numeric,
                            'type': target.get('type', 'Utilization')
                        }
                    elif resource_name == 'memory':
                        metrics_info['memory'] = {
                            'target': target_value,
                            'target_numeric': target_numeric,
                            'type': target.get('type', 'Utilization')
                        }
                        
                    # First metric is typically the primary scaling driver
                    if idx == 0:
                        metrics_info['primary_metric'] = resource_name
                        
                elif metric.get('type') in ['Pods', 'Object', 'External']:
                    custom_metric = {
                        'type': metric['type'],
                        'name': 'unknown',
                        'target': 'unknown',
                        'target_type': 'unknown'
                    }
                    
                    # Extract custom metric name and target
                    if metric['type'] == 'Pods':
                        pods_metric = metric.get('pods', {}).get('metric', {})
                        custom_metric['name'] = pods_metric.get('name', 'unknown')
                        target = metric.get('pods', {}).get('target', {})
                    elif metric['type'] == 'Object':
                        object_metric = metric.get('object', {}).get('metric', {})
                        custom_metric['name'] = object_metric.get('name', 'unknown')
                        target = metric.get('object', {}).get('target', {})
                    elif metric['type'] == 'External':
                        external_metric = metric.get('external', {}).get('metric', {})
                        custom_metric['name'] = external_metric.get('name', 'unknown')
                        target = metric.get('external', {}).get('target', {})
                    
                    # Extract target value for custom metrics
                    if 'averageValue' in target:
                        custom_metric['target'] = target['averageValue']
                        custom_metric['target_type'] = 'AverageValue'
                    elif 'value' in target:
                        custom_metric['target'] = target['value']
                        custom_metric['target_type'] = 'Value'
                    
                    metrics_info['custom'].append(custom_metric)
                    
                    if idx == 0:
                        metrics_info['primary_metric'] = f"custom_{metric['type'].lower()}"
            
            # Classify scaling strategy
            metrics_info['scaling_strategy'] = HPAAnalyzer._classify_scaling_strategy(metrics_info)
            
            logger.debug(f"HPA metrics detected: {metrics_info['scaling_strategy']} strategy with {metrics_info['total_metrics']} metrics")
            
        except Exception as e:
            logger.error(f"Error detecting HPA metrics: {e}")
            metrics_info['error'] = str(e)
        
        return metrics_info
    
    @staticmethod
    def _create_metrics_info_from_enhanced_data(hpa: Dict) -> Dict:
        """Create metrics_info structure from enhanced data structure"""
        try:
            cpu_metrics = hpa.get('cpu_metrics', [])
            memory_metrics = hpa.get('memory_metrics', [])
            other_metrics = hpa.get('other_metrics', [])
            scaling_strategy = hpa.get('scaling_strategy', 'unknown')
            
            # Map enhanced scaling strategy to traditional metrics_info format
            strategy_mapping = {
                'cpu_only': 'cpu-based',
                'memory_only': 'memory-based', 
                'mixed': 'balanced',
                'cpu_dominant': 'balanced',
                'memory_dominant': 'balanced',
                'custom': 'custom-metrics',
                'unknown': 'unknown'
            }
            
            metrics_info = {
                'total_metrics': len(cpu_metrics) + len(memory_metrics) + len(other_metrics),
                'has_multiple': (len(cpu_metrics) + len(memory_metrics) + len(other_metrics)) > 1,
                'cpu': cpu_metrics[0]['target_value'] if cpu_metrics else None,
                'memory': memory_metrics[0]['target_value'] if memory_metrics else None,
                'custom': other_metrics,
                'primary_metric': 'cpu' if cpu_metrics else ('memory' if memory_metrics else 'custom'),
                'scaling_strategy': strategy_mapping.get(scaling_strategy, 'unknown'),
                'enhanced_data': True  # Flag to indicate this came from enhanced structure
            }
            
            logger.debug(f"Created metrics_info from enhanced data: {metrics_info['scaling_strategy']} strategy")
            return metrics_info
            
        except Exception as e:
            logger.error(f"Error creating metrics_info from enhanced data: {e}")
            return {
                'total_metrics': 0,
                'has_multiple': False,
                'cpu': None,
                'memory': None,
                'custom': [],
                'primary_metric': 'unknown',
                'scaling_strategy': 'unknown',
                'error': str(e)
            }
    
    @staticmethod
    def _classify_scaling_strategy(metrics_info: Dict) -> str:
        """
        Classify the scaling strategy based on metrics information
        
        Returns one of:
        - 'balanced': Both CPU and memory
        - 'cpu-based': CPU only
        - 'memory-based': Memory only
        - 'hybrid': Mix of standard and custom metrics
        - 'custom-metrics': Custom metrics only
        - 'unknown': Unable to determine
        """
        has_cpu = metrics_info['cpu'] is not None
        has_memory = metrics_info['memory'] is not None
        has_custom = len(metrics_info['custom']) > 0
        
        if metrics_info['has_multiple']:
            if has_cpu and has_memory:
                if has_custom:
                    return 'hybrid'  # CPU + Memory + Custom
                else:
                    return 'balanced'  # CPU + Memory
            elif (has_cpu or has_memory) and has_custom:
                return 'hybrid'  # Standard + Custom
            elif has_custom:
                return 'custom-metrics'  # Multiple custom metrics
        
        # Single metric strategies
        if has_cpu and not has_memory and not has_custom:
            return 'cpu-based'
        elif has_memory and not has_cpu and not has_custom:
            return 'memory-based'
        elif has_custom and not has_cpu and not has_memory:
            return 'custom-metrics'
        else:
            return 'unknown'
    
    @staticmethod
    def get_hpa_version(hpa: Dict) -> str:
        """
        Check HPA API version for compatibility
        
        Args:
            hpa: HPA configuration dictionary
            
        Returns:
            'v1', 'v2', 'v2beta1', 'v2beta2', or 'unknown'
        """
        api_version = hpa.get('apiVersion', '').lower()
        
        if 'v2beta2' in api_version:
            return 'v2beta2'
        elif 'v2beta1' in api_version:
            return 'v2beta1'
        elif 'v2' in api_version:
            return 'v2'  # Supports multiple metrics
        elif 'v1' in api_version:
            return 'v1'  # Only CPU support
        else:
            return 'unknown'
    
    @staticmethod
    def get_deployment_hpa_mapping(hpa_list: List[Dict], deployments: List[Dict]) -> Dict:
        """
        Map deployments to their HPAs (if they exist)
        
        Args:
            hpa_list: List of HPA objects
            deployments: List of deployment objects
            
        Returns:
            Dictionary mapping namespace/workload to HPA info
        """
        hpa_map = {}
        
        try:
            # Map existing HPAs to their targets
            for hpa in hpa_list:
                try:
                    target = hpa.get('spec', {}).get('scaleTargetRef', {})
                    target_kind = target.get('kind', '')
                    target_name = target.get('name', '')
                    namespace = hpa.get('metadata', {}).get('namespace', 'default')
                    
                    if target_kind in ['Deployment', 'StatefulSet', 'ReplicaSet', 'ReplicationController']:
                        key = f"{namespace}/{target_name}"
                        
                        # Get comprehensive HPA metrics
                        hpa_metrics = HPAAnalyzer.detect_hpa_metrics(hpa)
                        
                        hpa_info = {
                            'hpa_name': hpa.get('metadata', {}).get('name'),
                            'target_kind': target_kind,
                            'target_name': target_name,
                            'namespace': namespace,
                            'has_hpa': True,
                            'hpa_version': HPAAnalyzer.get_hpa_version(hpa),
                            'metrics_info': hpa_metrics,
                            'optimization_score': HPAAnalyzer.calculate_optimization_score(hpa, hpa_metrics),
                            'min_replicas': hpa.get('spec', {}).get('minReplicas', 1),
                            'max_replicas': hpa.get('spec', {}).get('maxReplicas', 10),
                            'current_replicas': hpa.get('status', {}).get('currentReplicas', 0),
                            'desired_replicas': hpa.get('status', {}).get('desiredReplicas', 0),
                            'last_scale_time': hpa.get('status', {}).get('lastScaleTime'),
                            'conditions': hpa.get('status', {}).get('conditions', [])
                        }
                        
                        # Add simple type for backward compatibility
                        strategy = hpa_metrics['scaling_strategy']
                        if strategy == 'balanced':
                            hpa_info['hpa_type'] = 'mixed'
                        elif strategy == 'cpu-based':
                            hpa_info['hpa_type'] = 'cpu'
                        elif strategy == 'memory-based':
                            hpa_info['hpa_type'] = 'memory'
                        elif strategy in ['custom-metrics', 'hybrid']:
                            hpa_info['hpa_type'] = 'custom'
                        else:
                            hpa_info['hpa_type'] = 'unknown'
                        
                        hpa_map[key] = hpa_info
                        logger.debug(f"Mapped HPA {hpa_info['hpa_name']} to {key} ({strategy})")
                        
                except Exception as e:
                    logger.warning(f"Error processing HPA {hpa.get('metadata', {}).get('name', 'unknown')}: {e}")
            
            # Identify workloads without HPA
            for deployment in deployments:
                try:
                    name = deployment.get('metadata', {}).get('name', '')
                    namespace = deployment.get('metadata', {}).get('namespace', 'default')
                    key = f"{namespace}/{name}"
                    
                    if key not in hpa_map:
                        candidate_score = HPAAnalyzer.calculate_candidate_score(deployment)
                        
                        hpa_map[key] = {
                            'hpa_name': None,
                            'target_kind': 'Deployment',
                            'target_name': name,
                            'namespace': namespace,
                            'has_hpa': False,
                            'hpa_version': None,
                            'hpa_type': None,
                            'metrics_info': {'scaling_strategy': 'none'},
                            'optimization_score': 0.0,
                            'candidate_score': candidate_score,
                            'replicas': deployment.get('spec', {}).get('replicas', 1),
                            'should_have_hpa': candidate_score > 0.6,
                            'recommendation_priority': HPAAnalyzer._get_priority_level(candidate_score)
                        }
                        
                        if candidate_score > 0.6:
                            logger.debug(f"Deployment {key} is a good HPA candidate (score: {candidate_score:.2f})")
                            
                except Exception as e:
                    logger.warning(f"Error processing deployment {deployment.get('metadata', {}).get('name', 'unknown')}: {e}")
            
            logger.info(f"HPA mapping complete: {len([v for v in hpa_map.values() if v['has_hpa']])} with HPA, "
                       f"{len([v for v in hpa_map.values() if not v['has_hpa'] and v.get('should_have_hpa')])} candidates")
            
        except Exception as e:
            logger.error(f"Error creating deployment-HPA mapping: {e}")
        
        return hpa_map
    
    @staticmethod
    def calculate_optimization_score(hpa: Dict, metrics_info: Optional[Dict] = None) -> float:
        """
        Calculate HPA optimization score with enhanced logic
        
        Args:
            hpa: HPA configuration dictionary
            metrics_info: Pre-calculated metrics info (optional)
            
        Returns:
            Score between 0.0 and 1.0 (higher is better)
        """
        if metrics_info is None:
            metrics_info = HPAAnalyzer.detect_hpa_metrics(hpa)
        
        score_factors = []
        
        try:
            # 1. Metrics configuration scoring
            strategy = metrics_info['scaling_strategy']
            if strategy == 'balanced':
                score_factors.append(0.9)  # Best: Both CPU and memory
            elif strategy in ['cpu-based', 'memory-based']:
                score_factors.append(0.7)  # Good: Single standard metric
            elif strategy == 'hybrid':
                score_factors.append(0.8)  # Very good: Mixed metrics
            elif strategy == 'custom-metrics':
                score_factors.append(0.6)  # Depends on implementation
            else:
                score_factors.append(0.3)  # Poor: Unknown or no metrics
            
            # 2. API version scoring
            version = metrics_info['api_version']
            if 'v2' in version:
                score_factors.append(0.9)  # Modern API with full features
            elif 'v1' in version:
                score_factors.append(0.6)  # Legacy API with limitations
            else:
                score_factors.append(0.5)  # Unknown version
            
            # 3. Replica configuration scoring
            min_replicas = hpa.get('spec', {}).get('minReplicas', 1)
            max_replicas = hpa.get('spec', {}).get('maxReplicas', 10)
            
            if min_replicas >= 2 and max_replicas >= min_replicas * 3:
                score_factors.append(0.9)  # Excellent scaling range
            elif min_replicas >= 1 and max_replicas >= min_replicas * 2:
                score_factors.append(0.7)  # Good scaling range
            else:
                score_factors.append(0.4)  # Limited scaling range
            
            # 4. Target configuration scoring
            cpu_info = metrics_info.get('cpu')
            if cpu_info:
                cpu_target = cpu_info.get('target_numeric', 70)
                if 60 <= cpu_target <= 80:
                    score_factors.append(0.9)  # Optimal range
                elif 50 <= cpu_target <= 90:
                    score_factors.append(0.7)  # Acceptable range
                else:
                    score_factors.append(0.4)  # Suboptimal range
            
            # 5. Behavior configuration (v2 only)
            if hpa.get('spec', {}).get('behavior'):
                score_factors.append(0.9)  # Has advanced behavior config
            else:
                score_factors.append(0.5)  # No behavior config
            
            # Calculate final score
            final_score = sum(score_factors) / len(score_factors) if score_factors else 0.0
            
            logger.debug(f"HPA optimization score: {final_score:.2f} (factors: {len(score_factors)})")
            
        except Exception as e:
            logger.error(f"Error calculating optimization score: {e}")
            final_score = 0.0
        
        return final_score
    
    @staticmethod
    def calculate_candidate_score(deployment: Dict) -> float:
        """
        Calculate HPA candidate score for deployment
        
        Args:
            deployment: Deployment configuration dictionary
            
        Returns:
            Score between 0.0 and 1.0 (higher means better candidate)
        """
        score = 0.5  # Base score
        
        try:
            # Replica analysis
            replicas = deployment.get('spec', {}).get('replicas', 1)
            if replicas >= 3:
                score += 0.3  # High replica count suggests need for scaling
            elif replicas >= 2:
                score += 0.2
            
            # Resource requests analysis
            containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
            has_resource_requests = False
            has_limits = False
            
            for container in containers:
                resources = container.get('resources', {})
                if resources.get('requests'):
                    has_resource_requests = True
                    score += 0.1
                if resources.get('limits'):
                    has_limits = True
                    score += 0.1
            
            # Both requests and limits indicate mature resource management
            if has_resource_requests and has_limits:
                score += 0.1
            
            # Namespace analysis (production workloads more likely to need HPA)
            namespace = deployment.get('metadata', {}).get('namespace', '')
            if namespace in ['production', 'prod', 'default']:
                score += 0.1
            elif namespace in ['staging', 'stage']:
                score += 0.05
            
            # Labels analysis
            labels = deployment.get('metadata', {}).get('labels', {})
            if 'app' in labels or 'application' in labels:
                score += 0.05  # Properly labeled applications
            
        except Exception as e:
            logger.warning(f"Error calculating candidate score: {e}")
        
        return min(1.0, max(0.0, score))  # Clamp to 0-1 range
    
    @staticmethod
    def _get_priority_level(score: float) -> str:
        """Get priority level based on candidate score"""
        if score >= 0.8:
            return 'high'
        elif score >= 0.6:
            return 'medium'
        elif score >= 0.4:
            return 'low'
        else:
            return 'minimal'
    
    @staticmethod
    def _parse_resource_value(value: str) -> float:
        """Parse resource value string to numeric (best effort)"""
        try:
            # Handle common resource formats like "100m", "1Gi", etc.
            if isinstance(value, (int, float)):
                return float(value)
            
            value_str = str(value).lower()
            if 'm' in value_str:  # milliCPU
                return float(value_str.replace('m', '')) / 1000
            elif 'gi' in value_str:  # Gibibytes
                return float(value_str.replace('gi', '')) * 1024 * 1024 * 1024
            elif 'mi' in value_str:  # Mebibytes
                return float(value_str.replace('mi', '')) * 1024 * 1024
            elif 'ki' in value_str:  # Kibibytes
                return float(value_str.replace('ki', '')) * 1024
            else:
                return float(value_str)
        except:
            return 0.0
    
    @staticmethod
    def _fetch_complete_hpa_specs_directly() -> List[Dict]:
        """Emergency method to fetch complete HPA specs with kubectl when data is incomplete"""
        try:
            import subprocess
            import json
            
            # This is a last resort - try to get complete HPA specs directly
            logger.warning("🚨 EMERGENCY: Attempting direct kubectl HPA fetch due to incomplete data")
            
            # Try to get cluster info from the current metrics context
            # This is a fallback method - ideally we wouldn't need this
            result = subprocess.run([
                'kubectl', 'get', 'hpa', '--all-namespaces', '-o', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"❌ Direct kubectl HPA fetch failed: {result.stderr}")
                return []
            
            hpa_data = json.loads(result.stdout)
            if 'items' in hpa_data:
                logger.info(f"✅ Emergency fetch got {len(hpa_data['items'])} complete HPA specs")
                return hpa_data['items']
            
        except Exception as e:
            logger.error(f"❌ Emergency HPA fetch failed: {e}")
        
        return []
    
    @staticmethod  
    def analyze_hpa_state(k8s_cache, **kwargs) -> Dict:
        """
        Comprehensive HPA state analysis for a cluster using SINGLE DATA SOURCE
        
        Args:
            k8s_cache: KubernetesDataCache instance - SINGLE SOURCE OF TRUTH
            **kwargs: Ignored for backward compatibility
            
        Returns:
            Comprehensive HPA analysis results
        """
        logger.info(f"🎯 UNIFIED HPA ANALYSIS: Using kubernetes_data_cache as SINGLE SOURCE OF TRUTH")
        
        hpa_state = {
            'existing_hpas': [],
            'suboptimal_hpas': [],
            'missing_hpa_candidates': [],
            'summary': {},
            'deployment_mapping': {},
            'version_distribution': {},
            'strategy_distribution': {}
        }
        
        try:
            # SINGLE SOURCE: Get data from kubernetes_data_cache only
            hpa_data = k8s_cache.get_hpa_data()
            
            # Extract workloads (deployments, statefulsets, etc.)
            all_workloads = []
            
            # Add deployments
            deployments_data = hpa_data.get('deployments', {})
            if deployments_data and 'items' in deployments_data:
                all_workloads.extend(deployments_data['items'])
                logger.info(f"✅ Found {len(deployments_data['items'])} deployments from cache")
            
            # Add statefulsets
            statefulsets_data = hpa_data.get('statefulsets', {})
            if statefulsets_data and 'items' in statefulsets_data:
                all_workloads.extend(statefulsets_data['items'])
                logger.info(f"✅ Found {len(statefulsets_data['items'])} statefulsets from cache")
            
            # Extract HPAs
            hpa_json_data = hpa_data.get('hpa', {})
            existing_hpas = []
            
            if hpa_json_data and 'items' in hpa_json_data:
                existing_hpas = hpa_json_data['items']
                logger.info(f"✅ Found {len(existing_hpas)} HPAs from cache")
            else:
                logger.info("ℹ️ No HPAs found in cluster (this is normal for clusters without autoscaling)")
            
            logger.info(f"📊 UNIFIED ANALYSIS: Processing {len(existing_hpas)} HPAs and {len(all_workloads)} workloads")
            
            # Create deployment-HPA mapping using clean data
            hpa_state['deployment_mapping'] = HPAAnalyzer.get_deployment_hpa_mapping(existing_hpas, all_workloads)
            
            # Analyze each HPA using standard kubectl data format
            version_counts = {}
            strategy_counts = {}
            
            for hpa in existing_hpas:
                try:
                    # Use standard kubectl HPA format (no complex fallback logic)
                    metrics_info = HPAAnalyzer.detect_hpa_metrics(hpa)
                    optimization_score = HPAAnalyzer.calculate_optimization_score(hpa, metrics_info)
                    
                    hpa_analysis = {
                        'name': hpa.get('metadata', {}).get('name'),
                        'namespace': hpa.get('metadata', {}).get('namespace'),
                        'target': hpa.get('spec', {}).get('scaleTargetRef', {}).get('name'),
                        'target_kind': hpa.get('spec', {}).get('scaleTargetRef', {}).get('kind'),
                        'optimization_score': optimization_score,
                        'hpa_version': HPAAnalyzer.get_hpa_version(hpa),
                        'metrics_info': metrics_info,
                        'min_replicas': hpa.get('spec', {}).get('minReplicas', 1),
                        'max_replicas': hpa.get('spec', {}).get('maxReplicas', 10),
                        'current_replicas': hpa.get('status', {}).get('currentReplicas', 0),
                        'desired_replicas': hpa.get('status', {}).get('desiredReplicas', 0)
                    }
                    
                    # Add backward compatibility type mapping
                    strategy = metrics_info['scaling_strategy']
                    if strategy == 'balanced':
                        hpa_analysis['hpa_type'] = 'mixed'
                    elif strategy == 'cpu-based':
                        hpa_analysis['hpa_type'] = 'cpu'
                    elif strategy == 'memory-based':
                        hpa_analysis['hpa_type'] = 'memory'
                    elif strategy in ['custom-metrics', 'hybrid']:
                        hpa_analysis['hpa_type'] = 'custom'
                    else:
                        hpa_analysis['hpa_type'] = 'unknown'
                    
                    # Count versions and strategies
                    version = hpa_analysis['hpa_version']
                    version_counts[version] = version_counts.get(version, 0) + 1
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                    
                    # Categorize by optimization score
                    if optimization_score < 0.7:
                        hpa_state['suboptimal_hpas'].append(hpa_analysis)
                    else:
                        hpa_state['existing_hpas'].append(hpa_analysis)
                        
                except Exception as e:
                    logger.error(f"❌ Error analyzing HPA {hpa.get('metadata', {}).get('name', 'unknown')}: {e}")
            
            # Find missing HPA candidates
            for key, mapping in hpa_state['deployment_mapping'].items():
                if not mapping['has_hpa'] and mapping.get('should_have_hpa', False):
                    hpa_state['missing_hpa_candidates'].append({
                        'deployment_name': mapping['target_name'],
                        'namespace': mapping['namespace'],
                        'priority_score': mapping['candidate_score'],
                        'recommendation_priority': mapping['recommendation_priority'],
                        'current_replicas': mapping.get('replicas', 1)
                    })
            
            # Build summary
            total_workloads = len(all_workloads)
            total_hpas = len(hpa_state['existing_hpas']) + len(hpa_state['suboptimal_hpas'])
            
            # Legacy type distribution for backward compatibility
            all_analyzed_hpas = hpa_state['existing_hpas'] + hpa_state['suboptimal_hpas']
            hpa_type_distribution = {
                'cpu': sum(1 for h in all_analyzed_hpas if h.get('hpa_type') == 'cpu'),
                'memory': sum(1 for h in all_analyzed_hpas if h.get('hpa_type') == 'memory'),
                'mixed': sum(1 for h in all_analyzed_hpas if h.get('hpa_type') == 'mixed'),
                'custom': sum(1 for h in all_analyzed_hpas if h.get('hpa_type') == 'custom')
            }
            
            # Calculate coverage properly
            if total_workloads > 0:
                hpa_coverage_percent = (total_hpas / total_workloads) * 100
                hpa_coverage_percent = min(100.0, hpa_coverage_percent)
            else:
                hpa_coverage_percent = 0.0
                logger.warning("⚠️ No workloads detected - HPA coverage is 0%")
            
            hpa_state['summary'] = {
                'total_workloads': total_workloads,
                'existing_hpas': len(hpa_state['existing_hpas']),
                'suboptimal_hpas': len(hpa_state['suboptimal_hpas']),
                'missing_candidates': len(hpa_state['missing_hpa_candidates']),
                'hpa_coverage_percent': hpa_coverage_percent,
                'optimization_potential': len(hpa_state['suboptimal_hpas']) + len(hpa_state['missing_hpa_candidates']),
                'hpa_type_distribution': hpa_type_distribution
            }
            
            # Store distributions at top level for chart generator access
            hpa_state['hpa_type_distribution'] = hpa_type_distribution
            hpa_state['version_distribution'] = version_counts
            hpa_state['strategy_distribution'] = strategy_counts
            
            # Log results
            logger.info(f"📊 HPA Analysis Summary:")
            logger.info(f"   • Total Workloads: {total_workloads}")
            logger.info(f"   • HPAs Found: {total_hpas}")
            logger.info(f"   • HPA Coverage: {hpa_coverage_percent:.1f}%")
            logger.info(f"   • HPA Candidates: {len(hpa_state['missing_hpa_candidates'])}")
            logger.info(f"   • Type Distribution: CPU={hpa_type_distribution.get('cpu', 0)}, "
                       f"Memory={hpa_type_distribution.get('memory', 0)}, "
                       f"Mixed={hpa_type_distribution.get('mixed', 0)}, "
                       f"Custom={hpa_type_distribution.get('custom', 0)}")
            
        except Exception as e:
            logger.error(f"❌ UNIFIED HPA Analysis failed: {e}")
            hpa_state['analysis_error'] = str(e)
        
        return hpa_state

# Convenience functions for backward compatibility
def detect_hpa_type(hpa: Dict) -> str:
    """Backward compatible simple type detection"""
    return HPAAnalyzer.detect_hpa_type(hpa)

def extract_cpu_target(hpa: Dict) -> int:
    """Extract CPU target from HPA metrics"""
    metrics_info = HPAAnalyzer.detect_hpa_metrics(hpa)
    cpu_info = metrics_info.get('cpu')
    if cpu_info and cpu_info.get('target_numeric'):
        return int(cpu_info['target_numeric'])
    return 70

def extract_memory_target(hpa: Dict) -> int:
    """Extract memory target from HPA metrics"""
    metrics_info = HPAAnalyzer.detect_hpa_metrics(hpa)
    memory_info = metrics_info.get('memory')
    if memory_info and memory_info.get('target_numeric'):
        return int(memory_info['target_numeric'])
    return 70

# Export main classes and functions
__all__ = [
    'HPAAnalyzer',
    'detect_hpa_type',
    'extract_cpu_target', 
    'extract_memory_target'
]