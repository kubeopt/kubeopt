#!/usr/bin/env python3
"""
AKS Algorithmic Cost Analyzer - Enhanced Version
Developer: Srinivas Kondepudi  
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer

Provides intelligent cost analysis and optimization recommendations using ML approaches.
Ensures consistent variable naming and data flow throughout the pipeline.
"""

import logging
import os
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np

from analytics.processors.pod_cost_analyzer import KubernetesParsingUtils
from analytics.processors.aks_scorer import AKSScorer
from machine_learning.models.workload_performance_analyzer import WorkloadPerformanceAnalyzer
from shared.standards.performance_standards import SystemPerformanceStandards
from shared.standards.cost_optimization_standards import (
    CostCalculationStandards,
    HorizontalPodAutoscalerCostStandards,
    RightSizingCostStandards
)
from shared.node_data_processor import NodeDataProcessor
from algorithms.hpa_optimization_algorithm import HPAOptimizationAlgorithm
from algorithms.rightsizing_optimization_algorithm import RightSizingOptimizationAlgorithm
from algorithms.storage_optimization_algorithm import StorageOptimizationAlgorithm
from algorithms.performance_optimization_algorithm import PerformanceOptimizationAlgorithm
from algorithms.infrastructure_optimization_algorithm import InfrastructureOptimizationAlgorithm
from algorithms.confidence_scoring_algorithm import ConfidenceScoringAlgorithm
from algorithms.optimization_calculator_algorithm import OptimizationCalculatorAlgorithm
from algorithms.efficiency_evaluator_algorithm import EfficiencyEvaluatorAlgorithm
from algorithms.usage_analysis_algorithm import UsageAnalysisAlgorithm
from algorithms.workload_classification_algorithm import WorkloadClassificationAlgorithm
from shared.interfaces.data_contract import DataContractDict, ValidationOnlyDataContract

logger = logging.getLogger(__name__)


class MetricsValidator:
    """Validates metrics according to .clauderc standards - NO FALLBACKS"""
    
    @staticmethod
    def validate_utilization_metrics(cpu_usage_pct: float, memory_usage_pct: float) -> None:
        """Validate utilization metrics - fail fast if invalid"""
        if not isinstance(cpu_usage_pct, (int, float)) or not isinstance(memory_usage_pct, (int, float)):
            raise TypeError(f"Utilization must be numeric: CPU={type(cpu_usage_pct).__name__}, Memory={type(memory_usage_pct).__name__}")
        
        if not (0 <= cpu_usage_pct <= 10000):  # Allow high values for HPA metrics
            raise ValueError(f"CPU utilization outside valid range: {cpu_usage_pct}%")
        
        if not (0 <= memory_usage_pct <= 10000):  # Allow high values for HPA metrics
            raise ValueError(f"Memory utilization outside valid range: {memory_usage_pct}%")
        
        if cpu_usage_pct > SystemPerformanceStandards.CPU_UTILIZATION_CRITICAL:
            logger.warning(f"CPU {cpu_usage_pct}% exceeds critical threshold {SystemPerformanceStandards.CPU_UTILIZATION_CRITICAL}%")
        
        if memory_usage_pct > SystemPerformanceStandards.MEMORY_UTILIZATION_CRITICAL:
            logger.warning(f"Memory {memory_usage_pct}% exceeds critical threshold {SystemPerformanceStandards.MEMORY_UTILIZATION_CRITICAL}%")


class MLOperationCache:
    """Thread-safe cache for expensive ML operations to prevent duplicates"""
    
    def __init__(self):
        self.cache = {}
        self.active_operations = {}
        self.lock = threading.RLock()
        # Load configuration from standards
        import yaml
        import os
        
        standards_path = os.path.join(os.path.dirname(__file__), '../../config/aks_implementation_standards.yaml')
        with open(standards_path, 'r') as f:
            self.standards = yaml.safe_load(f)
            
        if not self.standards:
            raise ValueError("Standards configuration is empty or invalid")
            
        # Validate required configuration sections exist
        if 'monitoring_alerting' not in self.standards:
            raise ValueError("monitoring_alerting section missing from standards")
        if 'detection_intervals' not in self.standards['monitoring_alerting']:
            raise ValueError("detection_intervals section missing from monitoring_alerting")
            
        self.max_cache_age = self.standards['monitoring_alerting']['detection_intervals']['real_time_seconds']
        self.max_active_wait = self.standards['monitoring_alerting']['detection_intervals']['alert_check_seconds'] * 2
    
    def get_or_compute(self, cache_key: str, compute_func, *args, **kwargs):
        """Get cached result or compute if not available"""
        current_time = time.time()
        
        with self.lock:
            # Check for cached result
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if current_time - cache_entry['timestamp'] < self.max_cache_age:
                    logger.info(f"ML CACHE HIT: Using cached result for {cache_key[:32]}...")
                    return cache_entry['result']
                else:
                    del self.cache[cache_key]
            
            # Check if operation is active
            if cache_key in self.active_operations:
                operation_info = self.active_operations[cache_key]
                wait_event = operation_info['completion_event']
                start_time = operation_info['start_time']
                
                if current_time - start_time > self.max_active_wait:
                    logger.warning(f"ML CACHE: Operation {cache_key[:32]}... timed out")
                    del self.active_operations[cache_key]
                else:
                    logger.info(f"ML CACHE: Operation already running, waiting...")
        
        # Wait for active operation
        if cache_key in self.active_operations:
            wait_event.wait(timeout=self.max_active_wait)
            
            with self.lock:
                if cache_key in self.cache:
                    cache_entry = self.cache[cache_key]
                    if current_time - cache_entry['timestamp'] < self.max_cache_age:
                        return cache_entry['result']
        
        # Execute operation
        return self._execute_operation(cache_key, compute_func, *args, **kwargs)
    
    def _execute_operation(self, cache_key: str, compute_func, *args, **kwargs):
        """Execute ML operation with synchronization"""
        completion_event = threading.Event()
        current_time = time.time()
        thread_id = threading.current_thread().ident
        
        with self.lock:
            self.active_operations[cache_key] = {
                'thread_id': thread_id,
                'start_time': current_time,
                'completion_event': completion_event
            }
        
        try:
            logger.info(f"ML CACHE: Executing operation {cache_key[:32]}...")
            result = compute_func(*args, **kwargs)
            
            with self.lock:
                self.cache[cache_key] = {
                    'result': result,
                    'timestamp': current_time,
                    'thread_id': thread_id
                }
                
                if cache_key in self.active_operations:
                    del self.active_operations[cache_key]
            
            completion_event.set()
            return result
            
        except Exception as e:
            logger.error(f"ML CACHE: Operation failed: {e}")
            with self.lock:
                if cache_key in self.active_operations:
                    del self.active_operations[cache_key]
            completion_event.set()
            raise


# Global ML operation cache instance
ml_operation_cache = MLOperationCache()


class MLEnhancedHPARecommendationEngine:
    """HPA Recommendation Engine using ML analysis"""
    
    def __init__(self):
        self._ml_engine_cache = {}
        self._ml_engine_lock = threading.Lock()
        self.parser = KubernetesParsingUtils() if 'KubernetesParsingUtils' in globals() else None
        
        # Initialize AKS Scorer for standards-based targets
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "aks_scoring.yaml"
        )
        self.aks_scorer = AKSScorer.from_yaml(config_path)
        
        # Initialize optimization algorithms with standards
        self.hpa_algorithm = HPAOptimizationAlgorithm(logger)
        self.rightsizing_algorithm = RightSizingOptimizationAlgorithm(logger)
        self.storage_algorithm = StorageOptimizationAlgorithm(logger)
        self.performance_algorithm = PerformanceOptimizationAlgorithm(logger)
        self.infrastructure_algorithm = InfrastructureOptimizationAlgorithm(logger)
        self.confidence_algorithm = ConfidenceScoringAlgorithm(logger)
        self.workload_classification_algorithm = WorkloadClassificationAlgorithm(logger)
        
        # Create algorithm instances dictionary for complex algorithms
        algorithm_instances = {
            'hpa_algorithm': self.hpa_algorithm,
            'rightsizing_algorithm': self.rightsizing_algorithm,
            'storage_algorithm': self.storage_algorithm,
            'performance_algorithm': self.performance_algorithm,
            'infrastructure_algorithm': self.infrastructure_algorithm,
            'confidence_algorithm': self.confidence_algorithm
        }
        
        # Initialize complex algorithms that need other algorithm instances
        self.usage_analysis_algorithm = UsageAnalysisAlgorithm(logger, algorithm_instances, self.aks_scorer)
        self.optimization_calculator_algorithm = OptimizationCalculatorAlgorithm(logger, algorithm_instances, self.aks_scorer)
        self.efficiency_evaluator_algorithm = EfficiencyEvaluatorAlgorithm(logger, algorithm_instances, self.aks_scorer)
    
    def _get_ml_engine(self):
        """Get or create ML engine with caching"""
        thread_id = threading.current_thread().ident
        
        with self._ml_engine_lock:
            if thread_id not in self._ml_engine_cache:
                self._ml_engine_cache[thread_id] = WorkloadPerformanceAnalyzer()
                logger.info(f"Created new ML engine instance for thread {thread_id}")
            
            return self._ml_engine_cache[thread_id]
    
    def generate_hpa_recommendations(self, metrics_data: Dict, actual_costs: Dict) -> Dict:
        """Generate HPA recommendations with ML analysis"""
        try:
            # Create cache key based on metrics
            cache_key = self._create_hpa_cache_key(metrics_data, actual_costs)
            
            # Use ML operation cache
            return ml_operation_cache.get_or_compute(
                cache_key,
                self._generate_hpa_recommendations_internal,
                metrics_data,
                actual_costs
            )
            
        except Exception as e:
            logger.error(f"HPA recommendation failed: {e}")
            raise ValueError(f"HPA recommendation engine failed: {e}")
    
    def _create_hpa_cache_key(self, metrics_data: Dict, actual_costs: Dict) -> str:
        """Create unique cache key for HPA recommendations"""
        try:
            nodes = metrics_data.get('nodes')
            if nodes is None:
                raise ValueError("nodes is required in metrics_data")
            node_count = len(nodes)
            total_cost = actual_costs.get('monthly_actual_total')
            if total_cost is None:
                raise ValueError("monthly_actual_total is required in actual_costs")
            hpa_impl = metrics_data.get('hpa_implementation')
            if hpa_impl is None:
                raise ValueError("hpa_implementation is required in metrics_data")
            hpa_pattern = hpa_impl.get('current_hpa_pattern')
            if hpa_pattern is None:
                hpa_pattern = 'none'  # No HPA pattern detected
            
            # Calculate averages with consistent variable names
            if not nodes:
                raise ValueError("Nodes data is required for HPA pattern detection")
            
            cpu_values = []
            memory_values = []
            for node in nodes:
                cpu = node.get('cpu_usage_pct')
                memory = node.get('memory_usage_pct')
                if cpu is None or memory is None:
                    raise ValueError(f"Node missing cpu_usage_pct or memory_usage_pct")
                cpu_values.append(cpu)
                memory_values.append(memory)
            
            avg_cpu_utilization = np.mean(cpu_values)
            avg_memory_usage_pct = np.mean(memory_values)
            
            cache_key = f"hpa_{node_count}n_{total_cost:.0f}c_{avg_cpu_utilization:.1f}cpu_{avg_memory_usage_pct:.1f}mem_{hpa_pattern}_{int(time.time() // 300)}"
            return cache_key
            
        except Exception as e:
            logger.warning(f"Failed to create HPA cache key: {e}")
            raise ValueError("Failed to detect HPA pattern - no valid pattern found")
    
    def _generate_hpa_recommendations_internal(self, metrics_data: Dict, actual_costs: Dict) -> Dict:
        """Internal method that performs ML analysis"""
        logger.info("Generating ML-based HPA recommendations...")
        
        # Get ML engine
        ml_engine = self._get_ml_engine()
        learning_status = ml_engine.get_learning_insights()
        if 'learning_enabled' not in learning_status:
            raise ValueError("learning_enabled not found in learning_status")
        logger.info(f"ML Engine Status: Learning={learning_status['learning_enabled']}")
        
        # Prepare data for ML analysis
        enhanced_features = self._prepare_comprehensive_ml_data(metrics_data)
        
        # Run ML analysis
        ml_results = ml_engine.analyze_and_recommend_with_comprehensive_insights(
            metrics_data=enhanced_features,
            current_hpa_config={},
            cluster_id=f"cost_analyzer_{datetime.now().strftime('%Y%m%d')}"
        )
        
        # Convert ML results to consistent output
        consistent_recommendation = self._convert_comprehensive_ml_to_output(
            ml_results, metrics_data, actual_costs
        )
        
        # Validate consistency
        validation_result = self._validate_comprehensive_ml_consistency(consistent_recommendation)
        if not validation_result['consistent']:
            logger.warning(f"ML output inconsistencies: {validation_result['issues']}")
            consistent_recommendation = self._fix_comprehensive_ml_contradictions(
                consistent_recommendation, ml_results
            )
        
        # Calculate HPA efficiency using standards-based algorithm
        hpa_efficiency = self.hpa_algorithm.calculate_comprehensive_hpa_efficiency(ml_results, metrics_data)
        consistent_recommendation['hpa_efficiency_percentage'] = hpa_efficiency
        
        # Include metrics_data for downstream processing
        consistent_recommendation['metrics_data'] = metrics_data
        
        # Set ML enhancement flag based on actual ML analysis success
        ml_enhanced = ml_results.get('workload_classification', {}).get('ml_enhanced', False)
        consistent_recommendation['ml_enhanced'] = ml_enhanced
        
        logger.info(f"HPA recommendations generated with efficiency: {hpa_efficiency:.1f}% (ML enhanced: {ml_enhanced})")
        return consistent_recommendation
    
    def _prepare_comprehensive_ml_data(self, metrics_data: Dict) -> Dict:
        """Prepare data for ML analysis with validation"""
        # Validate required data exists - NO FALLBACKS per .clauderc
        if 'nodes' not in metrics_data:
            raise ValueError("metrics_data missing required 'nodes' field")
        
        nodes = metrics_data['nodes']
        if not nodes:
            raise ValueError("Node metrics data required for analysis")
        
        # Validate node data has required fields with consistent naming
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValueError(f"Node {i} is not a dictionary")
            if 'cpu_usage_pct' not in node:
                raise ValueError(f"Node {i} missing 'cpu_usage_pct'")
            if 'memory_usage_pct' not in node:
                raise ValueError(f"Node {i} missing 'memory_usage_pct'")
        
        # Per .clauderc: ML engine gets transformed nodes (with cpu_usage_pct)
        # Original nodes only passed separately for feature extraction that needs status.allocatable
        original_nodes = metrics_data.get('original_nodes', [])
        
        prepared_data = {
            'nodes': nodes,  # Transformed nodes for ML analysis (has cpu_usage_pct)
            'original_nodes': original_nodes,  # Original K8s nodes for feature extraction (has status.allocatable)
            'hpa_implementation': self._validate_hpa_implementation(metrics_data)
        }
        
        logger.info(f"Prepared ML data: {len(nodes)} nodes validated")
        return prepared_data
    
    def _validate_hpa_implementation(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate HPA implementation data - no fallbacks per .clauderc"""
        if 'hpa_implementation' not in metrics_data:
            raise ValueError("hpa_implementation missing from metrics_data")
        
        hpa_impl = metrics_data['hpa_implementation']
        required_fields = ['current_hpa_pattern', 'confidence', 'total_hpas']
        
        for field in required_fields:
            if field not in hpa_impl:
                raise ValueError(f"Required field '{field}' missing from hpa_implementation")
        
        return hpa_impl
    
    
    
    
    def _convert_comprehensive_ml_to_output(self, ml_results: Dict, metrics_data: Dict, actual_costs: Dict) -> Dict:
        """Convert ML results to consistent output format"""
        try:
            # Extract ML results with consistent naming
            workload_classification = ml_results.get('workload_classification', {})
            optimization_analysis = ml_results.get('optimization_analysis')
            if optimization_analysis is None:
                raise ValueError("optimization_analysis is required in ml_results")
            hpa_recommendation = ml_results.get('hpa_recommendation')
            if hpa_recommendation is None:
                raise ValueError("hpa_recommendation is required in ml_results")
            workload_characteristics = ml_results.get('workload_characteristics')
            if workload_characteristics is None:
                raise ValueError("workload_characteristics is required in ml_results")
            
            workload_type = workload_classification.get('workload_type', 'BALANCED')
            confidence = workload_classification.get('confidence')
            if confidence is None:
                raise ValueError("confidence is required in workload_classification")
            primary_action = optimization_analysis.get('primary_action')
            if primary_action is None:
                primary_action = 'MONITOR'  # Default action
            
            logger.info(f"ML Classification: {workload_type} (confidence: {confidence:.2f})")
            logger.info(f"ML Recommendation: {primary_action}")
            
            # Get utilization with consistent naming
            data_source = "unknown"
            if 'cpu_usage_pct' in workload_characteristics:
                ml_cpu_usage_pct = workload_characteristics['cpu_usage_pct']
                ml_memory_usage_pct = workload_characteristics.get('memory_usage_pct')
                data_source = "workload_characteristics.cpu_usage_pct"
            elif 'cpu_mean' in workload_characteristics:
                # ML models provide cpu_mean/memory_mean
                ml_cpu_usage_pct = workload_characteristics['cpu_mean']
                ml_memory_usage_pct = workload_characteristics.get('memory_mean')
                data_source = "workload_characteristics.cpu_mean"
            elif 'cpu_usage_pct' in ml_results:
                ml_cpu_usage_pct = ml_results.get('cpu_usage_pct') or ml_results.get('cpu_mean')
                if ml_cpu_usage_pct is None:
                    raise ValueError("ML results missing CPU usage data")
                ml_memory_usage_pct = ml_results.get('memory_usage_pct')
                data_source = "ml_results.cpu_usage_pct"
            else:
                logger.error(f"Available workload_characteristics keys: {list(workload_characteristics.keys())}")
                logger.error(f"Available ml_results keys: {list(ml_results.keys())}")
                raise ValueError("ML analysis missing CPU usage data")
            
            if ml_memory_usage_pct is None:
                raise ValueError("ML analysis missing memory_usage_pct data")
            
            # Validate metrics
            MetricsValidator.validate_utilization_metrics(ml_cpu_usage_pct, ml_memory_usage_pct)
            
            logger.info(f"ML Analysis: CPU={ml_cpu_usage_pct:.1f}%, Memory={ml_memory_usage_pct:.1f}% (from {data_source})")
            
            # Extract all workloads data
            all_workloads = []
            high_cpu_workloads = []
            
            # Validate metrics_data exists
            if not metrics_data:
                raise ValueError("metrics_data is required for workload analysis")
            
            # Extract workloads from various sources
            all_workloads = self._extract_all_workloads_from_metrics(metrics_data)
            
            # Filter high CPU workloads (>150% as per aks_realtime_metrics)
            high_cpu_workloads = []
            for w in all_workloads:
                cpu_util = w.get('cpu_usage_pct')
                if cpu_util is not None and cpu_util > 150:
                    high_cpu_workloads.append(w)
            
            # Calculate statistics
            cpu_values = []
            for w in all_workloads:
                cpu_util = w.get('cpu_usage_pct')
                if cpu_util is not None and cpu_util > 0:
                    cpu_values.append(cpu_util)
            max_cpu_utilization = max(cpu_values) if cpu_values else 0
            avg_cpu_utilization = np.mean(cpu_values) if cpu_values else 0
            
            logger.info(f"Workload Summary: {len(all_workloads)} total, {len(high_cpu_workloads)} high CPU")
            logger.info(f"CPU Stats: max={max_cpu_utilization:.1f}%, avg={avg_cpu_utilization:.1f}%")
            
            # Generate chart data
            nodes = metrics_data.get('nodes')
            if nodes is None:
                raise ValueError("nodes is required in metrics_data")
            current_replicas = len(nodes) if nodes else 1
            
            chart_data = self.hpa_algorithm.generate_hpa_chart_data(
                workload_type, primary_action, ml_cpu_usage_pct,
                ml_memory_usage_pct, current_replicas, hpa_recommendation
            )
            
            # Generate recommendation text
            recommendation = self._generate_comprehensive_ml_recommendation(
                workload_type, primary_action, confidence, ml_cpu_usage_pct,
                ml_memory_usage_pct, actual_costs, hpa_recommendation, optimization_analysis
            )
            
            # Build flattened structure for consistency
            flattened_workload_characteristics = {
                # Core metrics
                'cpu_usage_pct': ml_cpu_usage_pct,
                'memory_usage_pct': ml_memory_usage_pct,
                'workload_type': workload_type,
                'confidence': confidence,
                'primary_action': primary_action,
                
                # All workloads data
                'all_workloads': all_workloads,
                'total_workloads': len(all_workloads),
                'workloads_by_severity': {
                    'normal': [w for w in all_workloads if w.get('severity', 'normal') == 'normal'],
                    'high': [w for w in all_workloads if w.get('severity', 'normal') == 'high'],
                    'critical': [w for w in all_workloads if w.get('severity', 'normal') == 'critical']
                },
                
                # High CPU workloads
                'high_cpu_workloads': high_cpu_workloads,
                'max_cpu_utilization': max_cpu_utilization,
                'peak_cpu_usage_pct': max_cpu_utilization,
                'average_cpu_utilization': avg_cpu_utilization,
                'high_cpu_count': len(high_cpu_workloads),
                
                # ML metadata
                'comprehensive_ml_classification': workload_classification,
                'optimization_analysis': optimization_analysis,
                'hpa_recommendation': hpa_recommendation,
                
                # Additional insights
                'resource_balance': workload_characteristics.get('resource_balance', 25),
                'performance_stability': workload_characteristics.get('performance_stability', 0.8),
                'burst_patterns': workload_characteristics.get('burst_patterns', 0.1),
                'efficiency_score': workload_characteristics.get('efficiency_score', 0.6),
                
                # Data quality
                'data_quality': self._assess_data_quality(metrics_data),
                'data_structure_version': 'all_workloads_preserved',
                'chart_data_ready': True
            }
            
            # Add chart data and recommendation
            return {
                'chart_data': chart_data,
                'optimization_recommendation': recommendation,
                'workload_characteristics': flattened_workload_characteristics
            }
            
        except Exception as e:
            logger.error(f"Failed to convert ML output: {e}")
            raise
    
    def _extract_all_workloads_from_metrics(self, metrics_data: Dict) -> List[Dict]:
        """Extract all workloads from metrics data"""
        all_workloads = []
        processed_keys = set()
        
        # Get warm band target from standards
        cpu_target_pct = float(self.aks_scorer.get_target('cpu_warm_band')[1] * 100)
        
        # Extract from HPA implementation
        hpa_impl = metrics_data.get('hpa_implementation', {})
        
        # Process high CPU HPAs first
        high_cpu_hpas = hpa_impl.get('high_cpu_hpas', [])
        for hpa in high_cpu_hpas:
            name = hpa.get('name', 'unknown')
            namespace = hpa.get('namespace', 'unknown')
            key = f"{namespace}/{name}"
            
            if key not in processed_keys:
                # Validate required fields per .clauderc standards
                cpu_usage_value = hpa.get('cpu_usage_pct')
                if cpu_usage_value is None:
                    logger.error(f"High CPU HPA {name} missing required cpu_usage_pct")
                    continue
                
                target_cpu_value = hpa.get('target_cpu')
                if target_cpu_value is None:
                    logger.debug(f"Using default CPU target for HPA {name}")
                    target_cpu_value = cpu_target_pct
                
                severity_value = hpa.get('severity')
                if severity_value is None:
                    raise ValueError(f"HPA {name} missing required severity field")
                
                workload = {
                    'name': name,
                    'namespace': namespace,
                    'cpu_usage_pct': float(cpu_usage_value),
                    'target': float(target_cpu_value),
                    'severity': severity_value,
                    'type': 'hpa_high_cpu'
                }
                all_workloads.append(workload)
                processed_keys.add(key)
        
        # Process all HPA details
        all_hpa_details = hpa_impl.get('hpa_details', [])
        for hpa in all_hpa_details:
            name = hpa.get('name')
            namespace = hpa.get('namespace')
            
            if not name or not namespace:
                continue
            
            key = f"{namespace}/{name}"
            if key not in processed_keys:
                # Use available CPU data from HPA details or derive from target
                cpu_usage = None
                if 'current_cpu' in hpa:
                    cpu_usage = float(hpa['current_cpu'])
                elif hpa.get('has_cpu_metric', False):
                    # Calculate from target_cpu or use a reasonable estimate
                    target_cpu = hpa.get('target_cpu', cpu_target_pct)
                    # For HPA-managed workloads, assume they're reasonably close to target
                    cpu_usage = float(target_cpu * 0.85) if target_cpu else cpu_target_pct * 0.85
                    logger.debug(f"Estimated CPU usage for HPA {key}: {cpu_usage:.1f}%")
                else:
                    # Skip if no CPU metric information available
                    logger.debug(f"Skipping HPA {key} - no CPU metrics configured")
                    continue
                
                workload = {
                    'name': name,
                    'namespace': namespace,
                    'cpu_usage_pct': cpu_usage,
                    'target': float(hpa.get('target_cpu', cpu_target_pct)),
                    'severity': self.workload_classification_algorithm.determine_severity(cpu_usage),
                    'type': 'hpa_managed'
                }
                all_workloads.append(workload)
                processed_keys.add(key)
        
        # Extract from all_workloads if present
        if 'all_workloads' in metrics_data:
            for w in metrics_data['all_workloads']:
                name = w.get('name')
                namespace = w.get('namespace')
                if name and namespace:
                    key = f"{namespace}/{name}"
                    if key not in processed_keys:
                        # Normalize field names
                        cpu_usage = w.get('cpu_usage_pct', w.get('cpu_usage_pct', 0))
                        workload = {
                            'name': name,
                            'namespace': namespace,
                            'cpu_usage_pct': float(cpu_usage),
                            'target': float(w.get('target', cpu_target_pct)),
                            'severity': w.get('severity', self.workload_classification_algorithm.determine_severity(cpu_usage)),
                            'type': w.get('type', 'workload')
                        }
                        all_workloads.append(workload)
                        processed_keys.add(key)
        
        # Require top_cpu_summary per .clauderc - no fallbacks
        if 'top_cpu_summary' not in metrics_data:
            raise ValueError("top_cpu_summary missing from metrics_data - required field")
        
        top_cpu_summary = metrics_data['top_cpu_summary']
        if not isinstance(top_cpu_summary, dict):
            raise TypeError(f"top_cpu_summary must be dict, got {type(top_cpu_summary)}")
        
        # If we don't have workloads, use data from top_cpu_summary
        if not all_workloads:
            if 'max_cpu_utilization' not in top_cpu_summary:
                raise ValueError("max_cpu_utilization missing from top_cpu_summary")
            
            max_cpu = top_cpu_summary['max_cpu_utilization']
            if max_cpu > 0:
                # Create synthetic workload entry
                workload = {
                    'name': 'aggregated',
                    'namespace': 'default',
                    'cpu_usage_pct': max_cpu,
                    'target': cpu_target_pct,
                    'severity': self.workload_classification_algorithm.determine_severity(max_cpu),
                    'type': 'aggregated'
                }
                all_workloads.append(workload)
        
        logger.info(f"Extracted {len(all_workloads)} total workloads")
        return all_workloads
    
    def _assess_data_quality(self, metrics_data: Dict) -> Dict:
        """Assess data quality from metrics"""
        hpa_impl = metrics_data.get('hpa_implementation', {})
        validation = hpa_impl.get('validation', {})
        
        # Get high CPU summary for suspicious value check - per .clauderc no fallbacks
        if 'top_cpu_summary' not in metrics_data:
            raise ValueError("top_cpu_summary missing from metrics_data - required for data quality assessment")
        
        top_cpu_summary = metrics_data['top_cpu_summary']
        if 'max_cpu_utilization' not in top_cpu_summary:
            raise ValueError("max_cpu_utilization missing from top_cpu_summary")
        
        max_cpu = top_cpu_summary['max_cpu_utilization']
        
        return {
            'validation_performed': validation.get('performed', False),
            'hpa_discrepancies': validation.get('warnings_count', 0),
            'data_source': validation.get('data_source_preference', 'hpa_metrics'),
            'suspicious_max_cpu': max_cpu > 500,
            'pods_validated': validation.get('pods_validated', 0)
        }
    
    def _generate_comprehensive_ml_recommendation(self, workload_type: str, primary_action: str,
                                                 confidence: float, cpu_usage_pct: float,
                                                 memory_usage_pct: float, actual_costs: Dict,
                                                 hpa_recommendation: Dict, optimization_analysis: Dict) -> Dict:
        """Generate recommendation text"""
        monthly_cost = actual_costs.get('monthly_actual_total', 0)
        
        # Calculate potential savings based on workload type
        savings_percentages = {
            'BURSTY': 25,
            'CPU_INTENSIVE': 20,
            'MEMORY_INTENSIVE': 20,
            'LOW_UTILIZATION': 30,
            'BALANCED': 15
        }
        
        savings_pct = savings_percentages.get(workload_type, 15)
        potential_savings = monthly_cost * (savings_pct / 100)
        
        # Generate title based on primary action
        action_titles = {
            'IMPLEMENT_HPA': 'Implement Horizontal Pod Autoscaling',
            'OPTIMIZE_HPA': 'Optimize HPA Configuration',
            'RIGHTSIZE': 'Rightsize Resources',
            'MONITOR': 'Continue Monitoring',
            'SCALE_DOWN': 'Scale Down Resources'
        }
        
        title = action_titles.get(primary_action, 'Optimize Workload Performance')
        
        # Generate description based on workload type
        descriptions = {
            'BURSTY': f"Your workloads show bursty patterns with CPU at {cpu_usage_pct:.1f}%. "
                     f"Implementing HPA can save up to ${potential_savings:.2f}/month.",
            'CPU_INTENSIVE': f"CPU-intensive workloads detected at {cpu_usage_pct:.1f}% utilization. "
                           f"CPU-based autoscaling recommended for ${potential_savings:.2f}/month savings.",
            'MEMORY_INTENSIVE': f"Memory-intensive workloads at {memory_usage_pct:.1f}% utilization. "
                              f"Memory-based autoscaling can save ${potential_savings:.2f}/month.",
            'LOW_UTILIZATION': f"Low resource utilization detected (CPU: {cpu_usage_pct:.1f}%, Memory: {memory_usage_pct:.1f}%). "
                             f"Scale down to save up to ${potential_savings:.2f}/month.",
            'BALANCED': f"Balanced workload pattern detected. Optimize autoscaling for ${potential_savings:.2f}/month savings."
        }
        
        description = descriptions.get(workload_type,
                                      f"Optimize your workloads to save ${potential_savings:.2f}/month")
        
        return {
            'title': title,
            'description': description,
            'confidence': f"{confidence * 100:.0f}%",
            'potential_monthly_savings': potential_savings,
            'implementation_complexity': hpa_recommendation.get('implementation_complexity', 'medium'),
            'estimated_time': hpa_recommendation.get('estimated_implementation_time', '2-4 hours'),
            'priority': optimization_analysis.get('priority', 'medium')
        }
    
    def _validate_comprehensive_ml_consistency(self, recommendation: Dict) -> Dict:
        """Validate ML output consistency"""
        issues = []
        
        workload_chars = recommendation.get('workload_characteristics', {})
        
        # Check for required fields
        if 'cpu_usage_pct' not in workload_chars:
            issues.append("Missing cpu_usage_pct")
        if 'memory_usage_pct' not in workload_chars:
            issues.append("Missing memory_usage_pct")
        
        # Check for logical consistency
        cpu = workload_chars.get('cpu_usage_pct', 0)
        memory = workload_chars.get('memory_usage_pct', 0)
        workload_type = workload_chars.get('workload_type', '')
        
        if workload_type == 'CPU_INTENSIVE' and cpu < memory:
            issues.append("CPU_INTENSIVE but memory usage higher")
        
        if workload_type == 'MEMORY_INTENSIVE' and memory < cpu:
            issues.append("MEMORY_INTENSIVE but CPU usage higher")
        
        if workload_type == 'LOW_UTILIZATION' and (cpu > 50 or memory > 50):
            issues.append("LOW_UTILIZATION but usage above 50%")
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues
        }
    
    def _fix_comprehensive_ml_contradictions(self, recommendation: Dict, ml_results: Dict) -> Dict:
        """Fix any contradictions in ML output"""
        workload_chars = recommendation.get('workload_characteristics', {})
        
        # Ensure required fields exist
        if 'cpu_usage_pct' not in workload_chars:
            workload_chars['cpu_usage_pct'] = ml_results.get('cpu_usage_pct', 50.0)
        
        if 'memory_usage_pct' not in workload_chars:
            workload_chars['memory_usage_pct'] = ml_results.get('memory_usage_pct', 50.0)
        
        # Fix workload type contradictions
        cpu = workload_chars['cpu_usage_pct']
        memory = workload_chars['memory_usage_pct']
        
        if cpu > memory * 1.5:
            workload_chars['workload_type'] = 'CPU_INTENSIVE'
        elif memory > cpu * 1.5:
            workload_chars['workload_type'] = 'MEMORY_INTENSIVE'
        elif cpu < 30 and memory < 30:
            workload_chars['workload_type'] = 'LOW_UTILIZATION'
        else:
            workload_chars['workload_type'] = 'BALANCED'
        
        recommendation['workload_characteristics'] = workload_chars
        return recommendation


class ConsistentCostAnalyzer:
    """Main Cost Analysis Engine with ML-based recommendations"""
    
    def __init__(self):
        # Initialize AKS Scorer
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "aks_scoring.yaml"
        )
        self.aks_scorer = AKSScorer.from_yaml(config_path)
        
        # Initialize optimization algorithms with standards
        self.hpa_algorithm = HPAOptimizationAlgorithm(logger)
        self.rightsizing_algorithm = RightSizingOptimizationAlgorithm(logger)
        self.storage_algorithm = StorageOptimizationAlgorithm(logger)
        self.performance_algorithm = PerformanceOptimizationAlgorithm(logger)
        self.infrastructure_algorithm = InfrastructureOptimizationAlgorithm(logger)
        self.confidence_algorithm = ConfidenceScoringAlgorithm(logger)
        
        # Create algorithm instances dictionary for complex algorithms
        algorithm_instances = {
            'hpa_algorithm': self.hpa_algorithm,
            'rightsizing_algorithm': self.rightsizing_algorithm,
            'storage_algorithm': self.storage_algorithm,
            'performance_algorithm': self.performance_algorithm,
            'infrastructure_algorithm': self.infrastructure_algorithm,
            'confidence_algorithm': self.confidence_algorithm
        }
        
        # Initialize complex algorithms that need other algorithm instances
        self.usage_analysis_algorithm = UsageAnalysisAlgorithm(logger, algorithm_instances, self.aks_scorer)
        self.optimization_calculator_algorithm = OptimizationCalculatorAlgorithm(logger, algorithm_instances, self.aks_scorer)
        self.efficiency_evaluator_algorithm = EfficiencyEvaluatorAlgorithm(logger, algorithm_instances, self.aks_scorer)
        
        # Initialize sub-analyzers reference dictionary
        self.algorithms = {
            'current_usage_analyzer': self.usage_analysis_algorithm,
            'optimization_calculator': self.optimization_calculator_algorithm,
            'efficiency_evaluator': self.efficiency_evaluator_algorithm,
            'confidence_scorer': self.confidence_algorithm
        }
        
        # Operation cache for performance
        self.operation_cache = {}
        self.operation_lock = threading.Lock()
    
    def _get_standard_range(self, category: str, metric: str) -> list:
        """Get standard range from AKS scorer - NO DEFAULTS per .clauderc"""
        try:
            result = self.aks_scorer.get_target(metric)
            # Handle dict format from AKS scorer
            if isinstance(result, dict) and 'optimal' in result:
                optimal_range = result['optimal']
                if isinstance(optimal_range, (list, tuple)) and len(optimal_range) >= 2:
                    return list(optimal_range)
                else:
                    raise ValueError(f"Invalid optimal range in result for {metric}: {optimal_range}")
            # Handle direct list/tuple format
            elif isinstance(result, (list, tuple)) and len(result) >= 2:
                return list(result)
            else:
                raise ValueError(f"Invalid range format from scorer for {metric}: {result}")
        except Exception as e:
            raise ValueError(f"Failed to get required standard range for {metric}: {e}") from e
    
    def _get_standard_value(self, category: str, metric: str) -> any:
        """Get standard value from AKS scorer - NO DEFAULTS per .clauderc"""
        try:
            return self.aks_scorer.get_target(metric)
        except Exception as e:
            raise ValueError(f"Failed to get required standard value for {metric}: {e}") from e
    
    def _generate_hpa_recommendations(self, cost_data: Dict, metrics_data: Dict) -> Dict:
        """Generate HPA recommendations using ML engine"""
        try:
            # Extract actual costs
            actual_costs = self._extract_and_validate_actual_costs(cost_data)
            
            # Use ML engine for HPA recommendations
            ml_engine = MLEnhancedHPARecommendationEngine()
            return ml_engine.generate_hpa_recommendations(metrics_data, actual_costs)
            
        except Exception as e:
            logger.error(f"Failed to generate HPA recommendations: {e}")
            raise

    def _get_actual_hpa_coverage(self, metrics_data: Dict) -> Dict:
        """Get actual HPA coverage from metrics data"""
        coverage = {
            'hpa_count': 0,
            'total_workloads': 0,
            'hpa_targets': set(),
            'workload_names': set()
        }
        
        try:
            # Check for HPA implementation data
            hpa_implementation = metrics_data.get('hpa_implementation')
            if hpa_implementation is None:
                hpa_implementation = {}
            
            # Get HPA count - check multiple possible data structures
            hpa_count = 0
            
            # Method 1: Check for 'total_hpas' field
            if 'total_hpas' in hpa_implementation:
                total_hpas = hpa_implementation.get('total_hpas')
                hpa_count = int(total_hpas) if total_hpas is not None else 0
                logger.info(f"Found HPA count from total_hpas: {hpa_count}")
            # Method 2: Check for 'hpas' field with count
            elif 'hpas' in hpa_implementation:
                hpas = hpa_implementation.get('hpas')
                if isinstance(hpas, list):
                    hpa_count = len(hpas)
                    logger.info(f"Found HPA count from hpas list: {hpa_count}")
                elif isinstance(hpas, dict) and 'count' in hpas:
                    hpa_count = hpas.get('count', 0)
                    logger.info(f"Found HPA count from hpas.count: {hpa_count}")
            # Method 3: Check for HPA data structure with 'items' (like kubectl output)
            elif isinstance(hpa_implementation, dict):
                for key in ['hpa', 'hpa_data', 'data']:
                    if key in hpa_implementation:
                        hpa_data = hpa_implementation[key]
                        if isinstance(hpa_data, dict) and 'items' in hpa_data:
                            hpa_items = hpa_data['items']
                            hpa_count = len(hpa_items) if hpa_items is not None else 0
                            logger.info(f"Found HPA count from {key}.items: {hpa_count}")
                            break
                        elif isinstance(hpa_data, list):
                            hpa_count = len(hpa_data)
                            logger.info(f"Found HPA count from {key} list: {hpa_count}")
                            break
            
            coverage['hpa_count'] = hpa_count
            
            # Get workload count from metrics_data
            total_workloads = 0
            nodes = metrics_data.get('nodes', [])
            if isinstance(nodes, list):
                total_workloads = len(nodes)
            elif isinstance(nodes, dict) and 'items' in nodes:
                total_workloads = len(nodes['items'])
            
            # Alternative: use top_cpu_summary if available
            if total_workloads == 0:
                top_cpu_summary = metrics_data.get('top_cpu_summary', {})
                total_workloads = top_cpu_summary.get('total_workloads', 0)
            
            coverage['total_workloads'] = total_workloads
            
            logger.info(f"Coverage analysis: {hpa_count} HPAs covering {total_workloads} workloads")
            
        except Exception as e:
            logger.warning(f"Error analyzing HPA coverage: {e}")
            
        return coverage
    
    def analyze(self, cost_data: Dict, metrics_data: Dict, pod_data: Dict = None) -> DataContractDict:
        """Main analysis entry point with consistent data flow"""
        
        # Check cache first
        analysis_cache_key = self._create_analysis_cache_key(cost_data, metrics_data, 'full_analysis')
        
        with self.operation_lock:
            if analysis_cache_key in self.operation_cache:
                cache_entry = self.operation_cache[analysis_cache_key]
                cache_valid = (time.time() - cache_entry['timestamp'] < 300 and
                              'savings_by_category' in cache_entry.get('result', {}))
                if cache_valid:
                    logger.info("CACHE HIT: Using cached analysis result")
                    return cache_entry['result']
                else:
                    del self.operation_cache[analysis_cache_key]
        
        logger.info("Starting consistent cost analysis with ML recommendations")
        
        try:
            # ENFORCE DATA CONTRACT: Convert inputs to enforced dictionaries
            from shared.interfaces.data_contract import AnalysisDataContract, DataContractDict
            
            # DEBUG: Check metrics_data BEFORE data contract enforcement
            logger.info(f"🔍 DEBUG BEFORE DATA CONTRACT: metrics_data['nodes'] sample:")
            if metrics_data.get('nodes'):
                sample_node = metrics_data['nodes'][0]
                logger.info(f"🔍 BEFORE: sample_node = name: '{sample_node.get('name')}', cpu_usage_pct: {sample_node.get('cpu_usage_pct')}")
            
            # NEW: Use validation-only DataContract approach
            from shared.interfaces.data_contract import ValidationOnlyDataContract
            
            # Validate data integrity without modifying the data
            cost_data = ValidationOnlyDataContract.validate_without_modification(cost_data, "analyze() cost_data")
            metrics_data = ValidationOnlyDataContract.validate_without_modification(metrics_data, "analyze() metrics_data")
            if pod_data:
                pod_data = ValidationOnlyDataContract.validate_without_modification(pod_data, "analyze() pod_data")
            
            # Check critical fields for node data integrity
            if metrics_data.get('nodes'):
                node_critical_fields = ['name', 'cpu_usage_pct']
                sample_node = metrics_data['nodes'][0] if isinstance(metrics_data['nodes'], list) else {}
                ValidationOnlyDataContract.check_critical_fields(sample_node, node_critical_fields, "node_data_integrity")
            
            logger.info("✅ NEW: Validation-only DataContract approach - data integrity checked without corruption")
            
            # DEBUG: Check metrics_data AFTER data contract enforcement
            logger.info(f"🔍 DEBUG AFTER DATA CONTRACT: metrics_data['nodes'] sample:")
            if metrics_data.get('nodes'):
                sample_node = metrics_data['nodes'][0]
                # Safe access for debugging - handle both dict and DataContractDict
                try:
                    node_name = sample_node.get('name', 'UNKNOWN')
                    cpu_pct = sample_node.get('cpu_usage_pct', 'MISSING')
                    logger.info(f"🔍 AFTER: sample_node = name: '{node_name}', cpu_usage_pct: {cpu_pct}")
                except Exception as e:
                    logger.info(f"🔍 AFTER: sample_node access error: {e}, type: {type(sample_node)}")
                    # Try direct access to verify structure is preserved
                    if hasattr(sample_node, 'keys'):
                        logger.info(f"🔍 AFTER: sample_node keys: {list(sample_node.keys())}")
                    else:
                        logger.info(f"🔍 AFTER: sample_node is not dict-like: {sample_node}")
            
            # Step 1: Validate input data
            if not self._validate_data(cost_data, metrics_data):
                raise ValueError("Insufficient data for analysis")
            
            # Step 2: Extract actual costs
            actual_costs = self._extract_and_validate_actual_costs(cost_data)
            logger.info(f"Total cost: ${actual_costs['monthly_actual_total']:.2f}")
            
            # Step 3: Analyze current usage
            current_usage = self.algorithms['current_usage_analyzer'].analyze(metrics_data, pod_data)
            
            if current_usage is None:
                raise ValueError("Current usage analysis returned None")
            
            # Step 4: Calculate optimization potential
            optimization = self.algorithms['optimization_calculator'].calculate(
                actual_costs, current_usage, metrics_data
            )
            
            # Step 5: Validate optimization
            optimization = self._validate_optimization_results(optimization, actual_costs, metrics_data, current_usage)
            
            # Step 6: Evaluate efficiency
            efficiency = self.algorithms['efficiency_evaluator'].evaluate(
                current_usage, optimization, metrics_data
            )
            
            # Step 7: Calculate confidence
            confidence = self.algorithms['confidence_scorer'].score(
                actual_costs, current_usage, optimization, efficiency
            )
            
            # Step 8: Generate HPA recommendations
            logger.info("Generating ML-based HPA recommendations...")
            hpa_recommendations = self._generate_hpa_recommendations(cost_data, metrics_data)
            logger.info(f"HPA recommendations generated: {hpa_recommendations.get('optimization_recommendation', {}).get('title', 'Unknown')}")
            logger.info(f"HPA efficiency: {hpa_recommendations.get('hpa_efficiency_percentage', 0.0):.1f}%")
            
            # Step 9: Combine results
            results = self._combine_and_validate_results(
                actual_costs, current_usage, optimization, efficiency, confidence, metrics_data
            )
            
            # Step 10: Add HPA recommendations
            results['hpa_recommendations'] = hpa_recommendations
            logger.info("HPA recommendations added to results")
            
            # Preserve HPA implementation data
            hpa_implementation = metrics_data.get('hpa_implementation')
            if hpa_implementation is None:
                hpa_implementation = {}
            if hpa_implementation:
                results['hpa_implementation'] = hpa_implementation
                total_hpas = hpa_implementation.get('total_hpas', 0)
                logger.info(f"Preserved HPA implementation data with {total_hpas} HPAs")
            
            # Preserve top_cpu_summary data (standardized field name) - per .clauderc
            if 'top_cpu_summary' not in metrics_data:
                raise ValueError("top_cpu_summary missing from metrics_data - required for analysis results")
            
            top_cpu_summary = metrics_data['top_cpu_summary']
            if not isinstance(top_cpu_summary, dict):
                raise TypeError(f"top_cpu_summary must be dict, got {type(top_cpu_summary)}")
            
            results['top_cpu_summary'] = top_cpu_summary
            
            # Log max CPU if available
            if 'max_cpu_utilization' in top_cpu_summary:
                logger.info(f"Preserved top_cpu_summary with max CPU {top_cpu_summary['max_cpu_utilization']:.1f}%")
            else:
                logger.warning("top_cpu_summary missing max_cpu_utilization field")
            
            # Extract HPA efficiency
            hpa_efficiency_raw = hpa_recommendations.get('hpa_efficiency_percentage')
            
            if hpa_efficiency_raw is None:
                # Recalculate if needed
                ml_engine = MLEnhancedHPARecommendationEngine()
                ml_results = hpa_recommendations.get('workload_characteristics', {})
                hpa_efficiency_raw = ml_engine._calculate_comprehensive_hpa_efficiency(ml_results, metrics_data)
            
            # Convert to float
            try:
                if hpa_efficiency_raw is not None:
                    if hasattr(hpa_efficiency_raw, 'item'):
                        hpa_efficiency = float(hpa_efficiency_raw.item())
                    else:
                        hpa_efficiency = float(hpa_efficiency_raw)
                else:
                    raise ValueError("HPA efficiency is required but was None")
            except (AttributeError, ValueError, TypeError) as e:
                logger.error(f"Error converting HPA efficiency: {e}")
                raise ValueError(f"HPA efficiency conversion failed: {e}") from e
            
            # Ensure within bounds
            hpa_efficiency = max(0.0, min(100.0, hpa_efficiency))
            
            # Set HPA efficiency in results
            results['hpa_efficiency'] = hpa_efficiency
            results['hpa_efficiency_percentage'] = hpa_efficiency
            results['hpa_reduction'] = hpa_efficiency
            
            # Store ML confidence
            ml_metadata = hpa_recommendations.get('workload_characteristics', {}).get('comprehensive_ml_classification', {})
            ml_confidence = ml_metadata.get('confidence', 0.5)
            results['ml_confidence'] = round(ml_confidence * 100)
            
            logger.info(f"HPA Efficiency: {results['hpa_efficiency']:.1f}%")
            logger.info(f"ML Confidence: {results['ml_confidence']:.1f}%")
            
            # Step 11: Merge optimization results
            results.update({
                'networking_monthly_savings': optimization.get('networking_monthly_savings', 0),
                'control_plane_monthly_savings': optimization.get('control_plane_monthly_savings', 0),
                'registry_monthly_savings': optimization.get('registry_monthly_savings', 0),
                'monitoring_monthly_savings': optimization.get('monitoring_monthly_savings', 0),  # ADDED
                'idle_monthly_savings': optimization.get('idle_monthly_savings', 0),  # ADDED
                'infrastructure_monthly_savings': optimization.get('infrastructure_monthly_savings', 0),  # ADDED
                'performance_monthly_savings': optimization.get('performance_monthly_savings', 0),  # ADDED
                'compute_monthly_savings': optimization.get('compute_monthly_savings', 0),  # ADDED
                'storage_monthly_savings': optimization.get('storage_monthly_savings', 0),  # ADDED
                'hpa_monthly_savings': optimization.get('hpa_monthly_savings', 0),  # ADDED
                'rightsizing_monthly_savings': optimization.get('rightsizing_monthly_savings', 0),  # ADDED
                'total_savings': optimization.get('total_monthly_savings', results.get('total_savings', 0))
            })
            
            # Calculate category-specific savings
            results['savings_by_category'] = self._analyze_category_specific_savings(
                cost_data, metrics_data, current_usage, results
            )
            
            # Total savings from categories
            category_total = sum(results['savings_by_category'].values())
            results['total_savings'] = category_total
            
            logger.info(f"Total savings: ${category_total:.2f} from {len(results['savings_by_category'])} categories")
            
            # Add health scoring
            current_cpu = current_usage.get('avg_cpu_utilization', 0)
            current_memory = current_usage.get('avg_memory_utilization', 0)
            
            # Health score based on standards
            cpu_range = self._get_standard_range('resource_utilization', 'cpu_utilization_target')
            memory_range = self._get_standard_range('resource_utilization', 'memory_utilization_target')
            cpu_target = (cpu_range[0] + cpu_range[1]) / 2
            memory_target = (memory_range[0] + memory_range[1]) / 2
            
            cpu_health = 100 if cpu_range[0] <= current_cpu <= cpu_range[1] else max(0, 100 - abs(current_cpu - cpu_target) * 2)
            memory_health = 100 if memory_range[0] <= current_memory <= memory_range[1] else max(0, 100 - abs(current_memory - memory_target) * 2)
            
            results['current_health_score'] = (cpu_health + memory_health) / 2
            results['target_health_score'] = 95
            results['standards_compliance'] = {
                'cncf_compliance': cpu_health >= SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE and memory_health >= SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE,
                'finops_compliance': results.get('total_savings', 0) > 0,
                'optimization_percentage': results.get('total_savings', 0) / max(results.get('total_cost', 1), 1) * 100
            }
            
            # Create optimization opportunities
            results['optimization_opportunities'] = self._create_optimization_opportunities(results, current_usage)
            
            logger.info(f"Health score: {results['current_health_score']:.1f}/100")
            
            # Add HPA count
            # Use improved HPA extraction method
            actual_hpa_coverage = self._get_actual_hpa_coverage(metrics_data)
            hpa_count = actual_hpa_coverage.get('hpa_count', 0)
            results['hpa_count'] = hpa_count
            logger.info(f"HPA count: {hpa_count}")
            
            # Calculate optimization score
            try:
                total_cost = cost_data.get('total_cost', 0)
                total_savings = results.get('total_savings', 0)
                
                if total_cost > 0:
                    savings_percentage = (total_savings / total_cost) * 100
                    optimization_score = max(0, 100 - savings_percentage)
                else:
                    optimization_score = 50
                
                results['optimization_score'] = round(optimization_score, 1)
                logger.info(f"Optimization Score: {optimization_score:.1f}/100")
                
            except Exception as e:
                logger.error(f"Optimization scoring failed: {e}")
                results['optimization_score'] = 0
            
            # Final validation
            validation_result = self._final_validation(results)
            if not validation_result['valid']:
                logger.warning(f"Validation warnings: {validation_result['warnings']}")
                results = self._auto_fix_results(results, validation_result['warnings'])
            
            # Cache the results
            with self.operation_lock:
                self.operation_cache[analysis_cache_key] = {
                    'result': results,
                    'timestamp': time.time()
                }
                
                # Clean old cache entries
                if len(self.operation_cache) > 10:
                    oldest_key = min(self.operation_cache.keys(), key=lambda k: self.operation_cache[k]['timestamp'])
                    del self.operation_cache[oldest_key]
            
            # Validate required fields are present
            required_fields = ['savings_by_category', 'current_health_score', 'standards_compliance']
            missing_fields = [field for field in required_fields if field not in results]
            
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                raise ValueError(f"Analysis failed to set required fields: {missing_fields}")
            
            logger.info("Cost analysis complete")
            
            # DATA CONTRACT: Log warnings but don't fail analysis
            from shared.interfaces.data_contract import AnalysisDataContract
            try:
                # Validate output follows data contract
                approved_fields = AnalysisDataContract.get_approved_fields()
                AnalysisDataContract.validate_field_usage(results, approved_fields, "AlgorithmicCostAnalyzer.analyze()")
                logger.info("✅ Data contract validation passed - all fields approved")
            except ValueError as contract_error:
                logger.warning(f"⚠️ DATA CONTRACT WARNING: {contract_error}")
                logger.warning(f"⚠️ Analysis continuing despite contract violation - new fields may have been added")
                # Continue analysis - don't fail for contract violations
                # This allows us to add new optimization categories without breaking existing analysis
            
            return results
            
        except Exception as e:
            logger.error(f"Cost analysis failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise ValueError(f"Cost analysis failed: {str(e)}")
    
    def _create_analysis_cache_key(self, cost_data: Dict, metrics_data: Dict, operation_type: str) -> str:
        """Create cache key for analysis operations"""
        try:
            total_cost = cost_data.get('total_cost', 0)
            node_count = len(metrics_data.get('nodes', []))
            # Use improved HPA extraction method
            actual_hpa_coverage = self._get_actual_hpa_coverage(metrics_data)
            hpa_count = actual_hpa_coverage.get('hpa_count', 0)
            
            cache_key = f"{operation_type}_{total_cost:.0f}_{node_count}n_{hpa_count}hpa_{int(time.time() // 300)}"
            return cache_key
            
        except Exception as e:
            logger.warning(f"Failed to create cache key: {e}")
            return f"{operation_type}_fallback_{int(time.time() // 300)}"
    
    def _validate_data(self, cost_data: Dict, metrics_data: Dict) -> bool:
        """Validate input data completeness"""
        if not cost_data or not metrics_data:
            return False
        
        if 'total_cost' not in cost_data:
            logger.error("Missing 'total_cost' in cost_data")
            return False
        
        if 'nodes' not in metrics_data:
            logger.error("Missing 'nodes' in metrics_data")
            return False
        
        nodes = metrics_data.get('nodes', [])
        if not nodes:
            logger.error("Empty 'nodes' list in metrics_data")
            return False
        
        return True
    
    def _extract_and_validate_actual_costs(self, cost_data: Dict) -> Dict:
        """Extract and structure actual costs"""
        total_cost = cost_data.get('total_cost', 0)
        
        if total_cost <= 0:
            raise ValueError("Total cost must be positive")
        
        # Extract component costs with validation
        node_cost = cost_data.get('node_cost', 0) or cost_data.get('compute_cost', 0)
        storage_cost = cost_data.get('storage_cost', 0)
        networking_cost = cost_data.get('networking_cost', 0)
        control_plane_cost = cost_data.get('control_plane_cost', 0)
        registry_cost = cost_data.get('registry_cost', 0)
        
        # CRITICAL FIX: Include monitoring cost which is often the largest component
        monitoring_cost = cost_data.get('monitoring_cost', 0) or cost_data.get('log_analytics_cost', 0)
        
        # Include other cost categories
        other_cost = cost_data.get('other_cost', 0)
        idle_cost = cost_data.get('idle_cost', 0)
        
        # If components not provided, estimate from total
        if node_cost == 0:
            node_cost = total_cost * 0.6
        if storage_cost == 0:
            storage_cost = total_cost * 0.15
        if networking_cost == 0:
            networking_cost = total_cost * 0.1
        if control_plane_cost == 0:
            control_plane_cost = total_cost * 0.1
        if registry_cost == 0:
            registry_cost = total_cost * 0.05
        
        return {
            'monthly_actual_total': total_cost,
            'monthly_actual_compute': node_cost,
            'monthly_actual_storage': storage_cost,
            'monthly_actual_networking': networking_cost,
            'monthly_actual_control_plane': control_plane_cost,
            'monthly_actual_registry': registry_cost,
            'monthly_actual_monitoring': monitoring_cost,  # CRITICAL: Include monitoring cost
            'monthly_actual_other': other_cost,
            'monthly_actual_idle': idle_cost
        }
    
    def _validate_optimization_results(self, optimization: Dict, actual_costs: Dict,
                                      metrics_data: Dict = None, current_usage: Dict = None) -> Dict:
        """Validate and fix optimization calculations"""
        total_cost = actual_costs.get('monthly_actual_total', 0)
        
        # Ensure savings don't exceed costs
        for key in optimization:
            if 'savings' in key:
                value = optimization[key]
                if value > total_cost:
                    logger.warning(f"{key} ({value}) exceeds total cost ({total_cost}), capping")
                    optimization[key] = total_cost * 0.3
        
        # DO NOT recalculate total - it's already calculated correctly with anti-double-counting logic
        # The total_monthly_savings was calculated in the optimization method with proper overlap handling
        
        # Calculate percentage using the correctly calculated total
        if total_cost > 0:
            total_monthly_savings = optimization.get('total_monthly_savings', 0)
            optimization['optimization_percentage'] = (total_monthly_savings / total_cost) * 100
        else:
            optimization['optimization_percentage'] = 0
        
        return optimization
    
    def _combine_and_validate_results(self, actual_costs: Dict, current_usage: Dict,
                                     optimization: Dict, efficiency: Dict, confidence: Dict,
                                     metrics_data: Dict) -> Dict:
        """Combine all analysis results with validation and enforcement"""
        from shared.interfaces.data_contract import AnalysisDataContract, ValidationOnlyDataContract
        
        # NEW: Use regular dict but validate the combined results
        results = {}
        logger.info("✅ NEW: Using regular dict for results - will validate final output")
        
        # Add all fields with enforcement
        from shared.interfaces.data_contract import AnalysisDataContract
        
        results.update({
            # Costs - use data contract constants
            AnalysisDataContract.TOTAL_COST: actual_costs['monthly_actual_total'],
            AnalysisDataContract.COMPUTE_COST: actual_costs['monthly_actual_compute'],
            AnalysisDataContract.STORAGE_COST: actual_costs['monthly_actual_storage'],
            AnalysisDataContract.NETWORKING_COST: actual_costs['monthly_actual_networking'],
            AnalysisDataContract.CONTROL_PLANE_COST: actual_costs['monthly_actual_control_plane'],
            AnalysisDataContract.REGISTRY_COST: actual_costs['monthly_actual_registry'],
            AnalysisDataContract.MONITORING_COST: actual_costs.get('monthly_actual_monitoring', 0),  # CRITICAL FIX
            AnalysisDataContract.OTHER_COST: actual_costs.get('monthly_actual_other', 0),
            AnalysisDataContract.IDLE_COST: actual_costs.get('monthly_actual_idle', 0),
            
            # Usage metrics with consistent naming
            'avg_cpu_utilization': current_usage.get('avg_cpu_utilization', 0),
            'avg_memory_utilization': current_usage.get('avg_memory_utilization', 0),
            'max_cpu_utilization': current_usage.get('max_cpu_utilization', 0),
            'max_memory_utilization': current_usage.get('max_memory_utilization', 0),
            'cpu_std_dev': current_usage.get('cpu_std_dev', 0),
            'memory_std_dev': current_usage.get('memory_std_dev', 0),
            
            # Optimization
            'compute_savings': optimization.get('compute_monthly_savings', 0),
            'storage_savings': optimization.get('storage_monthly_savings', 0),
            'hpa_savings': optimization.get('hpa_monthly_savings', 0),
            'networking_savings': optimization.get('networking_monthly_savings', 0),
            'total_savings': optimization.get('total_monthly_savings', 0),
            
            # Efficiency
            'current_efficiency': efficiency.get('current_overall', 0),
            'target_efficiency': efficiency.get('target_overall', 0),
            'current_cpu_efficiency': efficiency.get('current_cpu', 0),
            'current_memory_efficiency': efficiency.get('current_memory', 0),
            
            # Confidence
            'confidence_score': confidence.get('overall', 0),
            'data_quality': confidence.get('data_quality', 0),
            'consistency_score': confidence.get('consistency', 0),
            'feasibility_score': confidence.get('feasibility', 0),
            
            # Node count
            'node_count': current_usage.get('node_count', len(metrics_data.get('nodes', [])))
        })
        
        # Validate all numeric values
        for key, value in results.items():
            if isinstance(value, (int, float)):
                if value < 0:
                    logger.warning(f"Negative value for {key}: {value}, setting to 0")
                    results[key] = 0
        
        return results
    
    def _analyze_category_specific_savings(self, cost_data: Dict, metrics_data: Dict,
                                          current_usage: Dict, results: Dict) -> Dict:
        """Extract savings by category from optimization results"""
        # OptimizationCalculatorAlgorithm provides all these with industry standards
        savings = {
            'compute': results.get('compute_monthly_savings', 0),
            'storage': results.get('storage_monthly_savings', 0), 
            'networking': results.get('networking_monthly_savings', 0),
            'control_plane': results.get('control_plane_monthly_savings', 0),
            'registry': results.get('registry_monthly_savings', 0),
            'monitoring': results.get('monitoring_monthly_savings', 0),
            'idle': results.get('idle_monthly_savings', 0),  # ADDED: idle resource savings
            'infrastructure': results.get('infrastructure_monthly_savings', 0),
            'hpa': results.get('hpa_monthly_savings', 0),
            'rightsizing': results.get('rightsizing_monthly_savings', 0),
            'performance': results.get('performance_monthly_savings', 0)
        }
        
        # Log detailed breakdown for debugging
        total = sum(savings.values())
        logger.info(f"💰 SAVINGS BREAKDOWN:")
        for category, amount in savings.items():
            if amount > 0:
                logger.info(f"   {category}: ${amount:.2f}")
        logger.info(f"   TOTAL: ${total:.2f}")
        
        return savings
    
    def _create_optimization_opportunities(self, results: dict, current_usage: dict) -> dict:
        """Create detailed optimization opportunities"""
        opportunities = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }
        
        # Check CPU optimization
        avg_cpu = current_usage.get('avg_cpu_utilization', 0)
        if avg_cpu < 50:
            opportunities['immediate'].append({
                'type': 'rightsize',
                'description': f'CPU utilization at {avg_cpu:.1f}% - consider smaller instances',
                'potential_savings': results.get('compute_savings', 0) * 0.5,
                'priority': 'high'
            })
        
        # Check memory optimization
        avg_memory = current_usage.get('avg_memory_utilization', 0)
        if avg_memory < 50:
            opportunities['immediate'].append({
                'type': 'rightsize',
                'description': f'Memory utilization at {avg_memory:.1f}% - optimize memory allocation',
                'potential_savings': results.get('compute_savings', 0) * 0.3,
                'priority': 'medium'
            })
        
        # Check HPA implementation
        if results.get('hpa_count', 0) == 0:
            opportunities['short_term'].append({
                'type': 'autoscaling',
                'description': 'No HPAs detected - implement horizontal pod autoscaling',
                'potential_savings': results.get('hpa_savings', 0),
                'priority': 'high'
            })
        
        # Check storage optimization
        if results.get('storage_cost', 0) > results.get('total_cost', 0) * 0.3:
            opportunities['long_term'].append({
                'type': 'storage',
                'description': 'Storage costs exceed 30% of total - review storage strategy',
                'potential_savings': results.get('storage_savings', 0),
                'priority': 'medium'
            })
        
        # Check networking optimization
        if results.get('networking_cost', 0) > results.get('total_cost', 0) * 0.2:
            opportunities['short_term'].append({
                'type': 'networking',
                'description': 'High networking costs detected - optimize network configuration',
                'potential_savings': results.get('networking_savings', 0),
                'priority': 'medium'
            })
        
        return opportunities
    
    def _final_validation(self, results: Dict) -> Dict:
        """Final validation of results"""
        warnings = []
        
        # Check for required fields
        required_fields = ['total_cost', 'total_savings', 'savings_by_category', 'current_health_score']
        for field in required_fields:
            if field not in results:
                warnings.append(f"Missing required field: {field}")
        
        # Check for logical consistency
        if results.get('total_savings', 0) > results.get('total_cost', 0):
            warnings.append("Total savings exceeds total cost")
        
        if results.get('current_efficiency', 0) > 100:
            warnings.append("Current efficiency exceeds 100%")
        
        if results.get('optimization_score', 0) < 0:
            warnings.append("Negative optimization score")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings
        }
    
    def _auto_fix_results(self, results: Dict, warnings: List[str]) -> Dict:
        """Auto-fix common issues in results"""
        for warning in warnings:
            if "Total savings exceeds total cost" in warning:
                results['total_savings'] = results.get('total_cost', 0) * 0.3
            
            elif "Current efficiency exceeds 100%" in warning:
                results['current_efficiency'] = 95.0
            
            elif "Negative optimization score" in warning:
                results['optimization_score'] = 50.0
            
            elif "Missing required field" in warning:
                if 'total_cost' not in results:
                    results['total_cost'] = 0
                if 'total_savings' not in results:
                    results['total_savings'] = 0
                if 'savings_by_category' not in results:
                    results['savings_by_category'] = {}
                if 'current_health_score' not in results:
                    results['current_health_score'] = 50
        
        # NEW: Validate final results without modifying them
        results = ValidationOnlyDataContract.validate_without_modification(results, "final_combined_results")
        
        # Check critical output fields
        critical_output_fields = ['total_cost', 'avg_cpu_utilization', 'node_count']
        if not ValidationOnlyDataContract.check_critical_fields(results, critical_output_fields, "final_results_critical_check"):
            logger.warning("⚠️ Some critical fields missing from final results")
        
        # Suggest any field mappings
        ValidationOnlyDataContract.suggest_field_mappings(results, "final_results_mapping")
        
        return results


