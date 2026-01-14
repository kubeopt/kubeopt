#!/usr/bin/env python3
"""
HPA Analyzer Module - Consistent and Simplified
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer

Comprehensive HPA analysis with consistent variable naming.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess
import json

# Import performance standards
try:
    from shared.standards.performance_standards import (
        SystemPerformanceStandards as SysPerf
    )
except ImportError:
    # Standards must be available - fail explicitly
    raise ImportError("Performance standards are required but not found")

logger = logging.getLogger(__name__)


class HPAAnalyzer:
    """Comprehensive HPA analyzer with consistent data flow"""
    
    @staticmethod
    def analyze_hpa_state(k8s_cache, **kwargs) -> Dict[str, Any]:
        """
        Main HPA state analysis using single data source
        
        Args:
            k8s_cache: KubernetesDataCache instance (single source of truth)
            
        Returns:
            Comprehensive HPA analysis results
        """
        logger.info("Starting unified HPA analysis")
        
        hpa_state = {
            'existing_hpas': [],
            'suboptimal_hpas': [],
            'missing_hpa_candidates': [],
            'deployment_mapping': {},
            'summary': {},
            'version_distribution': {},
            'strategy_distribution': {},
            'hpa_type_distribution': {}
        }
        
        try:
            # Get data from kubernetes cache
            hpa_data = k8s_cache.get_hpa_data()
            
            # Extract workloads
            all_workloads = []
            
            # Add deployments
            deployments_data = hpa_data.get('deployments')
            if deployments_data is None:
                deployments_data = {}
            if deployments_data and 'items' in deployments_data:
                all_workloads.extend(deployments_data['items'])
                logger.info(f"Found {len(deployments_data['items'])} deployments")
            
            # Add statefulsets  
            statefulsets_data = hpa_data.get('statefulsets')
            if statefulsets_data is None:
                statefulsets_data = {}
            if statefulsets_data and 'items' in statefulsets_data:
                all_workloads.extend(statefulsets_data['items'])
                logger.info(f"Found {len(statefulsets_data['items'])} statefulsets")
            
            # Extract HPAs
            hpa_json_data = hpa_data.get('hpa')
            if hpa_json_data is None:
                hpa_json_data = {}
            existing_hpas = []
            
            if hpa_json_data and 'items' in hpa_json_data:
                existing_hpas = hpa_json_data['items']
                logger.info(f"Found {len(existing_hpas)} HPAs")
            else:
                logger.info("No HPAs found in cluster")
            
            # Create deployment-HPA mapping
            hpa_state['deployment_mapping'] = HPAAnalyzer._create_deployment_mapping(
                existing_hpas, all_workloads
            )
            
            # Analyze each HPA
            version_counts = {}
            strategy_counts = {}
            
            for hpa in existing_hpas:
                try:
                    hpa_analysis = HPAAnalyzer._analyze_single_hpa(hpa)
                    
                    # Count versions and strategies
                    version = hpa_analysis['hpa_version']
                    strategy = hpa_analysis['metrics_info']['scaling_strategy']
                    
                    current_count = version_counts.get(version)
                    version_counts[version] = (current_count + 1) if current_count else 1
                    current_strat_count = strategy_counts.get(strategy)
                    strategy_counts[strategy] = (current_strat_count + 1) if current_strat_count else 1
                    
                    # Categorize by optimization score
                    if hpa_analysis['optimization_score'] < 0.7:
                        hpa_state['suboptimal_hpas'].append(hpa_analysis)
                    else:
                        hpa_state['existing_hpas'].append(hpa_analysis)
                        
                except Exception as e:
                    logger.error(f"Error analyzing HPA: {e}")
            
            # Find missing HPA candidates
            for key, mapping in hpa_state['deployment_mapping'].items():
                should_have = mapping.get('should_have_hpa')
                if not mapping['has_hpa'] and should_have:
                    hpa_state['missing_hpa_candidates'].append({
                        'deployment_name': mapping['target_name'],
                        'namespace': mapping['namespace'],
                        'priority_score': mapping['candidate_score'],
                        'recommendation_priority': mapping['recommendation_priority'],
                        'current_replicas': mapping.get('replicas') or 1
                    })
            
            # Build summary
            total_workloads = len(all_workloads)
            total_hpas = len(hpa_state['existing_hpas']) + len(hpa_state['suboptimal_hpas'])
            
            # Type distribution
            all_analyzed_hpas = hpa_state['existing_hpas'] + hpa_state['suboptimal_hpas']
            hpa_type_distribution = {
                'cpu': sum(1 for h in all_analyzed_hpas if h.get('hpa_type') == 'cpu'),
                'memory': sum(1 for h in all_analyzed_hpas if h.get('hpa_type') == 'memory'),
                'mixed': sum(1 for h in all_analyzed_hpas if h.get('hpa_type') == 'mixed'),
                'custom': sum(1 for h in all_analyzed_hpas if h.get('hpa_type') == 'custom')
            }
            
            # Calculate coverage
            if total_workloads > 0:
                hpa_coverage_percent = min(100.0, (total_hpas / total_workloads) * 100)
            else:
                hpa_coverage_percent = 0.0
            
            hpa_state['summary'] = {
                'total_workloads': total_workloads,
                'existing_hpas': len(hpa_state['existing_hpas']),
                'suboptimal_hpas': len(hpa_state['suboptimal_hpas']),
                'missing_candidates': len(hpa_state['missing_hpa_candidates']),
                'hpa_coverage_percent': hpa_coverage_percent,
                'optimization_potential': len(hpa_state['suboptimal_hpas']) + len(hpa_state['missing_hpa_candidates']),
                'hpa_type_distribution': hpa_type_distribution
            }
            
            # Store distributions
            hpa_state['hpa_type_distribution'] = hpa_type_distribution
            hpa_state['version_distribution'] = version_counts
            hpa_state['strategy_distribution'] = strategy_counts
            
            logger.info(f"HPA Analysis: {total_hpas} HPAs, {hpa_coverage_percent:.1f}% coverage, "
                       f"{len(hpa_state['missing_hpa_candidates'])} candidates")
            
        except Exception as e:
            logger.error(f"HPA Analysis failed: {e}")
            hpa_state['analysis_error'] = str(e)
        
        return hpa_state
    
    @staticmethod
    def _analyze_single_hpa(hpa: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single HPA configuration"""
        metrics_info = HPAAnalyzer._detect_metrics(hpa)
        optimization_score = HPAAnalyzer._calculate_optimization_score(hpa, metrics_info)
        
        hpa_analysis = {
            'name': hpa.get('metadata', {}).get('name') if hpa.get('metadata') else None,
            'namespace': hpa.get('metadata', {}).get('namespace') if hpa.get('metadata') else None,
            'target': hpa.get('spec', {}).get('scaleTargetRef', {}).get('name') if hpa.get('spec', {}).get('scaleTargetRef') else None,
            'target_kind': hpa.get('spec', {}).get('scaleTargetRef', {}).get('kind'),
            'optimization_score': optimization_score,
            'hpa_version': HPAAnalyzer._get_version(hpa),
            'metrics_info': metrics_info,
            'min_replicas': hpa.get('spec', {}).get('minReplicas', 1),
            'max_replicas': hpa.get('spec', {}).get('maxReplicas', 10),
            'current_replicas': hpa.get('status', {}).get('currentReplicas', 0),
            'desired_replicas': hpa.get('status', {}).get('desiredReplicas', 0)
        }
        
        # Map strategy to type for compatibility
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
        
        return hpa_analysis
    
    @staticmethod
    def _detect_metrics(hpa: Dict[str, Any]) -> Dict[str, Any]:
        """Detect HPA metrics configuration"""
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
            metrics_info['has_multiple'] = len(metrics) > 1
            
            for idx, metric in enumerate(metrics):
                if metric.get('type') == 'Resource':
                    resource_name = metric.get('resource', {}).get('name', '')
                    target = metric.get('resource', {}).get('target', {})
                    
                    # Extract target value
                    target_value = None
                    target_numeric = None
                    
                    if 'averageUtilization' in target:
                        target_value = f"{target['averageUtilization']}%"
                        target_numeric = target['averageUtilization']
                    elif 'averageValue' in target:
                        target_value = target['averageValue']
                        target_numeric = KubernetesParsingUtils.parse_cpu_safe(str(target['averageValue'])) / 1000  # Convert to cores
                    
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
                    
                    if idx == 0:
                        metrics_info['primary_metric'] = resource_name
                        
                elif metric.get('type') in ['Pods', 'Object', 'External']:
                    custom_metric = {
                        'type': metric['type'],
                        'name': 'unknown',
                        'target': 'unknown',
                        'target_type': 'unknown'
                    }
                    
                    # Extract custom metric details based on type
                    if metric['type'] == 'Pods':
                        pods_metric = metric.get('pods', {})
                        custom_metric['name'] = pods_metric.get('metric', {}).get('name', 'unknown')
                        target = pods_metric.get('target', {})
                    elif metric['type'] == 'Object':
                        object_metric = metric.get('object', {})
                        custom_metric['name'] = object_metric.get('metric', {}).get('name', 'unknown')
                        target = object_metric.get('target', {})
                    elif metric['type'] == 'External':
                        external_metric = metric.get('external', {})
                        custom_metric['name'] = external_metric.get('metric', {}).get('name', 'unknown')
                        target = external_metric.get('target', {})
                    
                    # Extract target value
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
            metrics_info['scaling_strategy'] = HPAAnalyzer._classify_strategy(metrics_info)
            
        except Exception as e:
            logger.error(f"Error detecting metrics: {e}")
            metrics_info['error'] = str(e)
        
        return metrics_info
    
    @staticmethod
    def _classify_strategy(metrics_info: Dict[str, Any]) -> str:
        """Classify the scaling strategy based on metrics"""
        has_cpu = metrics_info['cpu'] is not None
        has_memory = metrics_info['memory'] is not None
        has_custom = len(metrics_info['custom']) > 0
        
        if metrics_info['has_multiple']:
            if has_cpu and has_memory:
                if has_custom:
                    return 'hybrid'
                else:
                    return 'balanced'
            elif (has_cpu or has_memory) and has_custom:
                return 'hybrid'
            elif has_custom:
                return 'custom-metrics'
        
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
    def _get_version(hpa: Dict[str, Any]) -> str:
        """Get HPA API version"""
        api_version = hpa.get('apiVersion', '').lower()
        
        if 'v2beta2' in api_version:
            return 'v2beta2'
        elif 'v2beta1' in api_version:
            return 'v2beta1'
        elif 'v2' in api_version:
            return 'v2'
        elif 'v1' in api_version:
            return 'v1'
        else:
            return 'unknown'
    
    @staticmethod
    def _calculate_optimization_score(hpa: Dict[str, Any], metrics_info: Dict[str, Any]) -> float:
        """Calculate HPA optimization score"""
        score_factors = []
        
        try:
            # Metrics configuration scoring
            strategy = metrics_info['scaling_strategy']
            if strategy == 'balanced':
                score_factors.append(0.9)
            elif strategy in ['cpu-based', 'memory-based']:
                score_factors.append(0.7)
            elif strategy == 'hybrid':
                score_factors.append(0.8)
            elif strategy == 'custom-metrics':
                score_factors.append(0.6)
            else:
                score_factors.append(0.3)
            
            # API version scoring
            version = metrics_info['api_version']
            if 'v2' in version:
                score_factors.append(0.9)
            elif 'v1' in version:
                score_factors.append(0.6)
            else:
                score_factors.append(0.5)
            
            # Replica configuration scoring
            min_replicas = hpa.get('spec', {}).get('minReplicas', 1)
            max_replicas = hpa.get('spec', {}).get('maxReplicas', 10)
            
            if min_replicas >= 2 and max_replicas >= min_replicas * 3:
                score_factors.append(0.9)
            elif min_replicas >= 1 and max_replicas >= min_replicas * 2:
                score_factors.append(0.7)
            else:
                score_factors.append(0.4)
            
            # Target configuration scoring using standards
            cpu_info = metrics_info.get('cpu')
            if cpu_info and cpu_info.get('target_numeric'):
                cpu_target = cpu_info.get('target_numeric')
                if cpu_target is None:
                    raise ValueError("CPU target cannot be None when cpu_info exists")
                
                # Use standards for optimal range
                optimal_min = SysPerf.CPU_UTILIZATION_OPTIMAL - 10
                optimal_max = SysPerf.CPU_UTILIZATION_HIGH_PERFORMANCE
                
                if optimal_min <= cpu_target <= optimal_max:
                    score_factors.append(0.9)
                elif (SysPerf.CPU_UTILIZATION_OPTIMAL * 0.71) <= cpu_target <= SysPerf.CPU_UTILIZATION_STRESS:
                    score_factors.append(0.7)
                else:
                    score_factors.append(0.4)
            
            # Behavior configuration
            if hpa.get('spec', {}).get('behavior'):
                score_factors.append(0.9)
            else:
                score_factors.append(0.5)
            
            # Calculate final score
            if score_factors:
                final_score = sum(score_factors) / len(score_factors)
            else:
                final_score = 0.0
            
        except Exception as e:
            logger.error(f"Error calculating optimization score: {e}")
            final_score = 0.0
        
        return final_score
    
    @staticmethod
    def _create_deployment_mapping(hpa_list: List[Dict], deployments: List[Dict]) -> Dict[str, Dict]:
        """Map deployments to their HPAs"""
        hpa_map = {}
        
        try:
            # Map existing HPAs
            for hpa in hpa_list:
                try:
                    target = hpa.get('spec', {}).get('scaleTargetRef', {})
                    target_kind = target.get('kind', '')
                    target_name = target.get('name', '')
                    namespace = hpa.get('metadata', {}).get('namespace', 'default')
                    
                    if target_kind in ['Deployment', 'StatefulSet', 'ReplicaSet', 'ReplicationController']:
                        key = f"{namespace}/{target_name}"
                        
                        metrics_info = HPAAnalyzer._detect_metrics(hpa)
                        
                        hpa_info = {
                            'hpa_name': hpa.get('metadata', {}).get('name'),
                            'target_kind': target_kind,
                            'target_name': target_name,
                            'namespace': namespace,
                            'has_hpa': True,
                            'hpa_version': HPAAnalyzer._get_version(hpa),
                            'metrics_info': metrics_info,
                            'optimization_score': HPAAnalyzer._calculate_optimization_score(hpa, metrics_info),
                            'min_replicas': hpa.get('spec', {}).get('minReplicas', 1),
                            'max_replicas': hpa.get('spec', {}).get('maxReplicas', 10),
                            'current_replicas': hpa.get('status', {}).get('currentReplicas', 0),
                            'desired_replicas': hpa.get('status', {}).get('desiredReplicas', 0),
                            'last_scale_time': hpa.get('status', {}).get('lastScaleTime'),
                            'conditions': hpa.get('status', {}).get('conditions', [])
                        }
                        
                        # Add type for compatibility
                        strategy = metrics_info['scaling_strategy']
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
                        
                except Exception as e:
                    logger.warning(f"Error processing HPA: {e}")
            
            # Identify workloads without HPA
            for deployment in deployments:
                try:
                    name = deployment.get('metadata', {}).get('name', '')
                    namespace = deployment.get('metadata', {}).get('namespace', 'default')
                    key = f"{namespace}/{name}"
                    
                    if key not in hpa_map:
                        candidate_score = HPAAnalyzer._calculate_candidate_score(deployment)
                        
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
                            'recommendation_priority': HPAAnalyzer._get_priority(candidate_score)
                        }
                        
                except Exception as e:
                    logger.warning(f"Error processing deployment: {e}")
            
        except Exception as e:
            logger.error(f"Error creating deployment mapping: {e}")
        
        return hpa_map
    
    @staticmethod
    def _calculate_candidate_score(deployment: Dict[str, Any]) -> float:
        """Calculate HPA candidate score for deployment"""
        # Load scoring weights from standards configuration
        import yaml
        import os
        
        standards_path = os.path.join(os.path.dirname(__file__), '../../config/aks_implementation_standards.yaml')
        with open(standards_path, 'r') as f:
            standards = yaml.safe_load(f)
            
        if 'optimization_thresholds' not in standards:
            raise ValueError("optimization_thresholds section missing from standards")
        if 'priority_thresholds' not in standards['optimization_thresholds']:
            raise ValueError("priority_thresholds section missing from optimization_thresholds")
        
        # Use thresholds to calculate dynamic scores
        score_weights = {
            'base_score': 0.5,
            'high_replica_bonus': 0.3,
            'medium_replica_bonus': 0.2,
            'resource_request_bonus': 0.1,
            'resource_limit_bonus': 0.1,
            'complete_resources_bonus': 0.1,
            'prod_namespace_bonus': 0.1,
            'stage_namespace_bonus': 0.05
        }
        
        score = score_weights['base_score']
        
        try:
            # Replica analysis
            replicas = deployment.get('spec', {}).get('replicas')
            if replicas is None:
                raise ValueError("Deployment replicas not specified")
            
            if replicas >= 3:
                score += score_weights['high_replica_bonus']
            elif replicas >= 2:
                score += score_weights['medium_replica_bonus']
            
            # Resource configuration analysis
            containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
            has_requests = False
            has_limits = False
            
            for container in containers:
                resources = container.get('resources')
                if resources is None:
                    continue
                    
                if resources.get('requests'):
                    has_requests = True
                    score += score_weights['resource_request_bonus']
                if resources.get('limits'):
                    has_limits = True
                    score += score_weights['resource_limit_bonus']
            
            if has_requests and has_limits:
                score += score_weights['complete_resources_bonus']
            
            # Namespace analysis
            namespace = deployment.get('metadata', {}).get('namespace')
            if namespace is None:
                raise ValueError("Deployment namespace not specified")
                
            if namespace in ['production', 'prod', 'default']:
                score += score_weights['prod_namespace_bonus']
            elif namespace in ['staging', 'stage']:
                score += score_weights['stage_namespace_bonus']
            
            # Labels analysis
            labels = deployment.get('metadata', {}).get('labels', {})
            if 'app' in labels or 'application' in labels:
                score += 0.05
            
        except Exception as e:
            logger.warning(f"Error calculating candidate score: {e}")
        
        return min(1.0, max(0.0, score))
    
    @staticmethod
    def _get_priority(score: float) -> str:
        """Get priority level based on score"""
        if score >= 0.8:
            return 'high'
        elif score >= 0.6:
            return 'medium'
        elif score >= 0.4:
            return 'low'
        else:
            return 'minimal'
    
    
    @staticmethod
    def detect_hpa_metrics(hpa: Dict) -> Dict:
        """Public method for metric detection (compatibility)"""
        return HPAAnalyzer._detect_metrics(hpa)
    
    @staticmethod
    def get_hpa_version(hpa: Dict) -> str:
        """Public method for version detection (compatibility)"""
        return HPAAnalyzer._get_version(hpa)
    
    @staticmethod
    def get_deployment_hpa_mapping(hpa_list: List[Dict], deployments: List[Dict]) -> Dict:
        """Public method for deployment mapping (compatibility)"""
        return HPAAnalyzer._create_deployment_mapping(hpa_list, deployments)
    
    @staticmethod
    def calculate_optimization_score(hpa: Dict, metrics_info: Optional[Dict] = None) -> float:
        """Public method for optimization score (compatibility)"""
        if metrics_info is None:
            metrics_info = HPAAnalyzer._detect_metrics(hpa)
        return HPAAnalyzer._calculate_optimization_score(hpa, metrics_info)
    
    @staticmethod
    def calculate_candidate_score(deployment: Dict) -> float:
        """Public method for candidate score (compatibility)"""
        return HPAAnalyzer._calculate_candidate_score(deployment)


# Compatibility functions
def detect_hpa_type(hpa: Dict) -> str:
    """Backward compatible simple type detection"""
    metrics_info = HPAAnalyzer._detect_metrics(hpa)
    strategy = metrics_info['scaling_strategy']
    
    if strategy == 'balanced':
        return 'mixed'
    elif strategy == 'cpu-based':
        return 'cpu'
    elif strategy == 'memory-based':
        return 'memory'
    elif strategy in ['custom-metrics', 'hybrid']:
        return 'custom'
    else:
        return 'unknown'


def extract_cpu_target(hpa: Dict) -> int:
    """Extract CPU target from HPA metrics"""
    metrics_info = HPAAnalyzer._detect_metrics(hpa)
    cpu_info = metrics_info.get('cpu')
    if cpu_info and cpu_info.get('target_numeric'):
        return int(cpu_info['target_numeric'])
    raise ValueError("No CPU target found in HPA")


def extract_memory_target(hpa: Dict) -> int:
    """Extract memory target from HPA metrics"""
    metrics_info = HPAAnalyzer._detect_metrics(hpa)
    memory_info = metrics_info.get('memory')
    if memory_info and memory_info.get('target_numeric'):
        return int(memory_info['target_numeric'])
    raise ValueError("No memory target found in HPA")


# Export main classes and functions
__all__ = [
    'HPAAnalyzer',
    'detect_hpa_type',
    'extract_cpu_target',
    'extract_memory_target'
]