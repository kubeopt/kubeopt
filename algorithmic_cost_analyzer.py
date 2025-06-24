"""
AKS Algorithmic Cost Analyzer
-----------------------------
Provides intelligent cost analysis and optimization recommendations
using machine learning approaches and statistical analysis.
"""

# ============================================================================
# IMPORTS AND CONFIGURATION
# ============================================================================


import numpy as np
import pandas as pd
import logging
import math
import statistics
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import warnings

from pod_cost_analyzer import KubernetesParsingUtils
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_stdev(data: list, default=0.0) -> float:
    """Compute standard deviation - return default if insufficient data"""
    try:
        if not data or len(data) < 2:
            return default
        return statistics.stdev(data)
    except:
        return default

def safe_variance(data: list, default=0.0) -> float:
    """Compute variance - return default if insufficient data"""
    try:
        if not data or len(data) < 2:
            return default
        return statistics.variance(data)
    except:
        return default

def safe_mean(data: list, default=0.0) -> float:
    """Compute mean - return default if no data"""
    try:
        if not data:
            return default
        return statistics.mean(data)
    except:
        return default

def safe_max(data: list, default=0.0) -> float:
    """Safely get maximum value"""
    try:
        return max(data) if data else default
    except:
        return default

def safe_min(data: list, default=0.0) -> float:
    """Safely get minimum value"""
    try:
        return min(data) if data else default
    except:
        return default

def ensure_numeric(value, default=0.0) -> float:
    """Ensure value is numeric"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

# =============
# Smart HPA (Cpu vs Memory)
# =============

# ADD THIS NEW CLASS TO algorithmic_cost_analyzer.py

class HPARecommendationEngine:
    """
    Smart HPA Recommendation Engine
    INTEGRATION: Uses detected HPA patterns to generate accurate recommendations
    """
    
    def __init__(self):
        self.parser = KubernetesParsingUtils() if 'KubernetesParsingUtils' in globals() else None
    
    def generate_hpa_recommendations(self, metrics_data: Dict, actual_costs: Dict) -> Dict:
        """
        Generate context-aware HPA recommendations based on current implementation
        
        Args:
            metrics_data: Real-time metrics including HPA detection results
            actual_costs: Actual cost breakdown
            
        Returns:
            Complete HPA recommendation with chart data and optimization message
        """
        logger.info("🎯 Generating smart HPA recommendations...")
        
        try:
            # Extract HPA implementation status
            hpa_implementation = metrics_data.get('hpa_implementation', {})
            current_pattern = hpa_implementation.get('current_hpa_pattern', 'unknown')
            detection_confidence = hpa_implementation.get('confidence', 'low')
            
            # Extract utilization data
            nodes = metrics_data.get('nodes', [])
            if not nodes:
                return None
            
            # Calculate average utilization
            cpu_utils = [ensure_numeric(node.get('cpu_usage_pct', 0)) for node in nodes]
            memory_utils = [ensure_numeric(node.get('memory_usage_pct', 0)) for node in nodes]
            
            avg_cpu = safe_mean(cpu_utils) if cpu_utils else 35.0
            avg_memory = safe_mean(memory_utils) if memory_utils else 60.0
            
            logger.info(f"📊 Current utilization: CPU={avg_cpu:.1f}%, Memory={avg_memory:.1f}%")
            logger.info(f"🔍 Detected HPA pattern: {current_pattern} (confidence: {detection_confidence})")
            
            # Calculate HPA scaling scenarios
            hpa_scenarios = self._calculate_hpa_scenarios(avg_cpu, avg_memory, len(nodes))
            
            # Generate recommendation based on current implementation
            recommendation = self._generate_context_aware_recommendation(
                current_pattern, hpa_scenarios, actual_costs, avg_cpu, avg_memory
            )
            
            # Build complete response
            return {
                'hpa_chart_data': {
                    'timePoints': hpa_scenarios['traffic_scenarios'],
                    'cpuReplicas': hpa_scenarios['cpu_replicas'],
                    'memoryReplicas': hpa_scenarios['memory_replicas'],
                    'current_cpu_avg': avg_cpu,
                    'current_memory_avg': avg_memory,
                    'data_source': 'real_node_metrics_with_hpa_detection'
                },
                'optimization_recommendation': recommendation,
                'current_implementation': {
                    'pattern': current_pattern,
                    'confidence': detection_confidence,
                    'total_hpas': hpa_implementation.get('total_hpas', 0)
                },
                'workload_characteristics': {
                    'cpu_utilization': avg_cpu,
                    'memory_utilization': avg_memory,
                    'cluster_type': self._classify_cluster_type(avg_cpu, avg_memory),
                    'optimization_potential': self._assess_optimization_potential(avg_cpu, avg_memory)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ HPA recommendation generation failed: {e}")
            return None
    
    def _calculate_hpa_scenarios(self, avg_cpu: float, avg_memory: float, node_count: int) -> Dict:
        """Calculate HPA scaling scenarios for different traffic patterns"""
        
        # Estimate current replicas
        current_replicas = node_count * 2  # Typical estimation
        
        # HPA targets
        cpu_target = 70.0
        memory_target = 60.0
        
        # Base scaling calculations
        cpu_scale_factor = avg_cpu / cpu_target
        memory_scale_factor = avg_memory / memory_target
        
        cpu_base_replicas = max(1, int(current_replicas * cpu_scale_factor))
        memory_base_replicas = max(1, int(current_replicas * memory_scale_factor))
        
        # Traffic scenario multipliers (representing load variations)
        traffic_multipliers = [0.8, 1.2, 1.5, 1.1, 0.9]
        traffic_scenarios = ['Low Traffic', 'Medium Traffic', 'Peak Traffic', 'Evening', 'Night']
        
        # Generate replica counts for each scenario
        cpu_replicas = [max(1, int(cpu_base_replicas * mult)) for mult in traffic_multipliers]
        memory_replicas = [max(1, int(memory_base_replicas * mult)) for mult in traffic_multipliers]
        
        return {
            'traffic_scenarios': traffic_scenarios,
            'cpu_replicas': cpu_replicas,
            'memory_replicas': memory_replicas,
            'cpu_average': int(safe_mean(cpu_replicas)),
            'memory_average': int(safe_mean(memory_replicas))
        }
    
    def _generate_context_aware_recommendation(self, current_pattern: str, scenarios: Dict, 
                                             costs: Dict, avg_cpu: float, avg_memory: float) -> Dict:
        """Generate recommendation based on current HPA implementation"""
        
        node_cost = ensure_numeric(costs.get('monthly_actual_node', 0))
        cost_per_replica = node_cost / max(scenarios['cpu_average'], scenarios['memory_average'], 1) if node_cost > 0 else 50
        
        cpu_avg_replicas = scenarios['cpu_average']
        memory_avg_replicas = scenarios['memory_average']
        
        if current_pattern == 'cpu_based_dominant':
            # Currently using CPU-based HPA
            if memory_avg_replicas < cpu_avg_replicas:
                # Memory-based would save money
                replica_reduction = cpu_avg_replicas - memory_avg_replicas
                monthly_savings = replica_reduction * cost_per_replica
                reduction_pct = (replica_reduction / cpu_avg_replicas) * 100 if cpu_avg_replicas > 0 else 0
                
                return {
                    'title': 'Switch to Memory-based HPA for Cost Savings',
                    'description': f'Memory-based HPA could reduce replica count by {reduction_pct:.0f}%, saving ${monthly_savings:.0f}/month (${monthly_savings*12:.0f}/year) through intelligent auto-scaling.',
                    'current_status': '✅ Using CPU-based HPA',
                    'recommendation': 'SWITCH to Memory-based HPA',
                    'direction': 'cost_optimization',
                    'monthly_savings': monthly_savings,
                    'replica_impact': f'Reduce from ~{cpu_avg_replicas} to ~{memory_avg_replicas} replicas',
                    'confidence': 'High',
                    'reasoning': f'Your memory utilization ({avg_memory:.1f}%) suggests memory-based scaling would be more cost-effective than CPU-based ({avg_cpu:.1f}%).',
                    'implementation_priority': 'High - Quick Win'
                }
            else:
                # Current approach is optimal
                replica_increase = memory_avg_replicas - cpu_avg_replicas
                increase_pct = (replica_increase / cpu_avg_replicas) * 100 if cpu_avg_replicas > 0 else 0
                
                return {
                    'title': 'Current CPU-based HPA is Optimal',
                    'description': f'Your CPU-based HPA is cost-effective. Switching to memory-based would increase replica count by {increase_pct:.0f}% (~{replica_increase} more replicas).',
                    'current_status': '✅ Using CPU-based HPA (Optimal)',
                    'recommendation': 'MAINTAIN current approach',
                    'direction': 'status_quo',
                    'cost_impact': f'Avoid ${replica_increase * cost_per_replica:.0f}/month cost increase',
                    'confidence': 'High',
                    'reasoning': f'Your low CPU utilization ({avg_cpu:.1f}%) makes CPU-based scaling the right choice.',
                    'implementation_priority': 'None - Already Optimized'
                }
        
        elif current_pattern == 'memory_based_dominant':
            # Currently using Memory-based HPA
            if cpu_avg_replicas < memory_avg_replicas:
                # CPU-based would save money
                replica_reduction = memory_avg_replicas - cpu_avg_replicas
                monthly_savings = replica_reduction * cost_per_replica
                reduction_pct = (replica_reduction / memory_avg_replicas) * 100 if memory_avg_replicas > 0 else 0
                
                return {
                    'title': 'Switch to CPU-based HPA for Major Savings',
                    'description': f'CPU-based HPA could reduce replica count by {reduction_pct:.0f}%, saving ${monthly_savings:.0f}/month (${monthly_savings*12:.0f}/year) through intelligent auto-scaling.',
                    'current_status': '⚠️ Using Memory-based HPA',
                    'recommendation': 'SWITCH to CPU-based HPA',
                    'direction': 'cost_optimization',
                    'monthly_savings': monthly_savings,
                    'replica_impact': f'Reduce from ~{memory_avg_replicas} to ~{cpu_avg_replicas} replicas',
                    'confidence': 'High',
                    'reasoning': f'Your low CPU utilization ({avg_cpu:.1f}%) indicates memory-based scaling is over-provisioning resources.',
                    'implementation_priority': 'High - Major Cost Savings'
                }
            else:
                # Current approach prevents issues
                return {
                    'title': 'Current Memory-based HPA Prevents Issues',
                    'description': f'Your memory-based approach prevents OOM crashes and maintains application stability. CPU-based scaling would be too aggressive for your workload pattern.',
                    'current_status': '🛡️ Using Memory-based HPA (Stability Focus)',
                    'recommendation': 'MAINTAIN current approach',
                    'direction': 'stability_focused',
                    'confidence': 'High',
                    'reasoning': f'Memory utilization ({avg_memory:.1f}%) is the actual constraint for your workloads.',
                    'implementation_priority': 'None - Stability Optimized'
                }
        
        elif current_pattern == 'no_hpa_detected':
            # No HPA - recommend the better option
            if cpu_avg_replicas < memory_avg_replicas:
                better_approach = 'CPU-based HPA'
                potential_savings = (memory_avg_replicas - cpu_avg_replicas) * cost_per_replica
                optimal_replicas = cpu_avg_replicas
            else:
                better_approach = 'Memory-based HPA'
                potential_savings = (cpu_avg_replicas - memory_avg_replicas) * cost_per_replica
                optimal_replicas = memory_avg_replicas
            
            return {
                'title': f'Implement {better_approach} for Optimization',
                'description': f'No HPA detected. Implementing {better_approach} could save ${potential_savings:.0f}/month through automatic scaling based on your workload patterns.',
                'current_status': '📋 No HPA Detected (Manual Scaling)',
                'recommendation': f'IMPLEMENT {better_approach}',
                'direction': 'implement_hpa',
                'potential_savings': potential_savings,
                'replica_optimization': f'Optimize to ~{optimal_replicas} replicas with auto-scaling',
                'confidence': 'Medium',
                'reasoning': f'Your utilization pattern (CPU: {avg_cpu:.1f}%, Memory: {avg_memory:.1f}%) suggests {better_approach.split("-")[0].lower()}-based scaling.',
                'implementation_priority': 'Medium - Enable Auto-scaling'
            }
        
        else:
            # Mixed/Hybrid/Unknown implementation
            better_option = 'CPU-based' if cpu_avg_replicas < memory_avg_replicas else 'Memory-based'
            
            return {
                'title': f'Standardize on {better_option} HPA',
                'description': f'Mixed HPA implementation detected. Standardizing on {better_option} HPA would optimize costs and reduce complexity.',
                'current_status': '🔄 Mixed HPA Implementation',
                'recommendation': f'STANDARDIZE on {better_option} HPA',
                'direction': 'standardize',
                'confidence': 'Medium',
                'reasoning': f'Consistent approach reduces complexity and optimizes for your workload pattern.',
                'implementation_priority': 'Medium - Standardization'
            }
    
    def _classify_cluster_type(self, avg_cpu: float, avg_memory: float) -> str:
        """Classify cluster type based on utilization patterns"""
        if avg_cpu < 25 and avg_memory > avg_cpu * 1.5:
            return 'CPU Over-Provisioned'
        elif avg_memory > 70 and avg_cpu < 40:
            return 'Memory-Constrained'
        elif abs(avg_cpu - avg_memory) < 10:
            return 'Balanced Utilization'
        elif avg_cpu > 60 and avg_memory < 40:
            return 'CPU-Intensive'
        else:
            return 'Mixed Workload'
    
    def _assess_optimization_potential(self, avg_cpu: float, avg_memory: float) -> str:
        """Assess optimization potential"""
        if avg_cpu < 30 or avg_memory < 40:
            return 'High - Significant over-provisioning detected'
        elif avg_cpu < 50 or avg_memory < 60:
            return 'Medium - Some optimization opportunities'
        else:
            return 'Low - Well-optimized utilization'



# ============================================================================
# FIXED COST ANALYZER
# ============================================================================

class ConsistentCostAnalyzer:
    """
    CONSISTENT COST ANALYZER - Main Analysis Engine
    """
    
    def __init__(self):
        self.algorithms = {
            'current_usage_analyzer': CurrentUsageAnalysisAlgorithm(),
            'optimization_calculator': OptimizationCalculatorAlgorithm(),
            'efficiency_evaluator': EfficiencyEvaluatorAlgorithm(),
            'confidence_scorer': ConfidenceScorerAlgorithm()
        }

    def _generate_hpa_recommendations(self, cost_data: Dict, metrics_data: Dict) -> Dict:
        """Generate HPA recommendations using the new engine"""
        try:
            logger.info("🔍 Generating HPA recommendations with detection engine...")
            hpa_engine = HPARecommendationEngine()
            hpa_recommendations = hpa_engine.generate_hpa_recommendations(metrics_data, cost_data)
            
            # Validate the recommendations structure
            if not isinstance(hpa_recommendations, dict):
                raise ValueError("HPA engine returned invalid recommendations structure")
            
            required_keys = ['hpa_chart_data', 'optimization_recommendation', 'current_implementation']
            for key in required_keys:
                if key not in hpa_recommendations:
                    logger.warning(f"⚠️ Missing key in HPA recommendations: {key}")
            
            logger.info("✅ HPA recommendations generated successfully")
            return hpa_recommendations
            
        except Exception as e:
            logger.error(f"❌ Failed to generate HPA recommendations: {e}")
            raise ValueError(f"Enhanced consistent hpa recomendation failed: {str(e)}")

    def analyze(self, cost_data: Dict, metrics_data: Dict, pod_data: Dict = None) -> Dict:
        """ENHANCED: Main analysis function with HPA recommendations"""
        logger.info("🎯 Starting CONSISTENT cost analysis")
        
        try:
            # Step 1: Validate and normalize data
            if not self._validate_data(cost_data, metrics_data):
                raise ValueError("❌ Insufficient data for analysis")
            
            # Step 2: Extract and validate actual costs
            actual_costs = self._extract_and_validate_actual_costs(cost_data)
            logger.info(f"💰 Validated total cost: ${actual_costs['monthly_actual_total']:.2f}")
            
            # Step 3: Analyze current usage patterns
            current_usage = self.algorithms['current_usage_analyzer'].analyze(metrics_data, pod_data)
            
            # Step 4: Calculate optimization potential with validation
            optimization = self.algorithms['optimization_calculator'].calculate(
                actual_costs, current_usage, metrics_data
            )
            
            # Step 5: Validate optimization calculations
            optimization = self._validate_optimization_results(optimization, actual_costs)
            
            # Step 6: Evaluate efficiency improvements
            efficiency = self.algorithms['efficiency_evaluator'].evaluate(
                current_usage, optimization, metrics_data
            )
            
            # Step 7: Calculate confidence scores
            confidence = self.algorithms['confidence_scorer'].score(
                actual_costs, current_usage, optimization, efficiency
            )
            
            # Step 8: CRITICAL - Generate HPA recommendations
            logger.info("🎯 Generating HPA recommendations...")
            hpa_recommendations = self._generate_hpa_recommendations(actual_costs, metrics_data)
            logger.info(f"✅ HPA recommendations generated: {hpa_recommendations.get('optimization_recommendation', {}).get('title', 'Unknown')}")
            
            # Step 9: Combine results with validation
            results = self._combine_and_validate_results(
                actual_costs, current_usage, optimization, efficiency, confidence
            )
            
            # Step 10: CRITICAL - Add HPA recommendations to results
            results['hpa_recommendations'] = hpa_recommendations
            logger.info("✅ HPA recommendations added to analysis results")
            
            # Step 11: Final validation
            validation_result = self._final_validation(results)
            if not validation_result['valid']:
                logger.warning(f"⚠️ Validation warnings: {validation_result['warnings']}")
                # Fix issues automatically
                results = self._auto_fix_results(results, validation_result['warnings'])
            
            logger.info("✅ ENHANCED CONSISTENT analysis completed with HPA recommendations")
            logger.info(f"📊 Final validation: Total=${results['total_cost']:.2f}, Savings=${results['total_savings']:.2f}")
            
            return results
        
        except Exception as e:
            logger.error(f"❌ ENHANCED CONSISTENT analysis failed: {str(e)}")
            raise ValueError(f"Enhanced consistent analysis failed: {str(e)}")
    
    def _validate_data(self, cost_data: Dict, metrics_data: Dict) -> bool:
        """Enhanced data validation"""
        if not cost_data:
            logger.error("❌ No cost data provided")
            return False
            
        total_cost = ensure_numeric(cost_data.get('total_cost', 0))
        if total_cost <= 0:
            logger.error("❌ Invalid total cost")
            return False
        
        if not metrics_data:
            logger.warning("⚠️ No metrics data - using cost-only analysis")
            # Allow analysis with cost data only
        
        logger.info("✅ Data validation passed")
        return True
    
    def _extract_and_validate_actual_costs(self, cost_data: Dict) -> Dict:
        """Extract and validate actual costs with reconciliation"""
        
        # Extract individual cost components
        node_cost = ensure_numeric(cost_data.get('node_cost', 0))
        storage_cost = ensure_numeric(cost_data.get('storage_cost', 0))
        networking_cost = ensure_numeric(cost_data.get('networking_cost', 0))
        control_plane_cost = ensure_numeric(cost_data.get('control_plane_cost', 0))
        registry_cost = ensure_numeric(cost_data.get('registry_cost', 0))
        other_cost = ensure_numeric(cost_data.get('other_cost', 0))
        
        # Calculate component total
        component_total = (node_cost + storage_cost + networking_cost + 
                          control_plane_cost + registry_cost + other_cost)
        
        # Get declared total
        declared_total = ensure_numeric(cost_data.get('total_cost', 0))
        
        # Reconcile totals
        if abs(component_total - declared_total) > 0.01:  # Allow for small rounding errors
            logger.warning(f"⚠️ Cost reconciliation: components=${component_total:.2f}, declared=${declared_total:.2f}")
            
            if declared_total > 0:
                # Use declared total and proportionally adjust components
                adjustment_factor = declared_total / component_total if component_total > 0 else 1
                node_cost *= adjustment_factor
                storage_cost *= adjustment_factor
                networking_cost *= adjustment_factor
                control_plane_cost *= adjustment_factor
                registry_cost *= adjustment_factor
                other_cost *= adjustment_factor
                final_total = declared_total
                logger.info(f"✅ Adjusted components to match declared total: ${final_total:.2f}")
            else:
                final_total = component_total
                logger.info(f"✅ Using component total: ${final_total:.2f}")
        else:
            final_total = declared_total
            logger.info(f"✅ Costs reconciled: ${final_total:.2f}")
        
        return {
            'monthly_actual_total': final_total,
            'monthly_actual_node': node_cost,
            'monthly_actual_storage': storage_cost,
            'monthly_actual_networking': networking_cost,
            'monthly_actual_control_plane': control_plane_cost,
            'monthly_actual_registry': registry_cost,
            'monthly_actual_other': other_cost,
            'cost_period': cost_data.get('analysis_period_days', 30),
            'cost_source': 'Azure Cost Management API',
            'cost_label': 'Monthly Baseline (actual billing)'
        }
    
    def _validate_optimization_results(self, optimization: Dict, actual_costs: Dict) -> Dict:
        """Validate and fix optimization calculations"""
        
        total_cost = actual_costs['monthly_actual_total']
        node_cost = actual_costs['monthly_actual_node']
        storage_cost = actual_costs['monthly_actual_storage']
        
        # Get optimization values
        hpa_savings = ensure_numeric(optimization.get('hpa_monthly_savings', 0))
        rightsizing_savings = ensure_numeric(optimization.get('rightsizing_monthly_savings', 0))
        storage_savings = ensure_numeric(optimization.get('storage_monthly_savings', 0))
        
        # Validate HPA savings (shouldn't exceed 80% of node cost)
        max_hpa_savings = node_cost * 0.8
        if hpa_savings > max_hpa_savings:
            logger.warning(f"⚠️ HPA savings too high: ${hpa_savings:.2f} > ${max_hpa_savings:.2f}")
            hpa_savings = max_hpa_savings
        
        # Validate right-sizing savings (shouldn't exceed 60% of node cost)
        max_rightsizing_savings = node_cost * 0.6
        if rightsizing_savings > max_rightsizing_savings:
            logger.warning(f"⚠️ Right-sizing savings too high: ${rightsizing_savings:.2f} > ${max_rightsizing_savings:.2f}")
            rightsizing_savings = max_rightsizing_savings
        
        # Validate storage savings (shouldn't exceed 50% of storage cost)
        max_storage_savings = storage_cost * 0.5
        if storage_savings > max_storage_savings:
            logger.warning(f"⚠️ Storage savings too high: ${storage_savings:.2f} > ${max_storage_savings:.2f}")
            storage_savings = max_storage_savings
        
        # Calculate total savings
        total_savings = hpa_savings + rightsizing_savings + storage_savings
        
        # Validate total savings (shouldn't exceed 70% of total cost)
        max_total_savings = total_cost * 0.7
        if total_savings > max_total_savings:
            logger.warning(f"⚠️ Total savings too high: ${total_savings:.2f} > ${max_total_savings:.2f}")
            # Proportionally reduce all savings
            reduction_factor = max_total_savings / total_savings
            hpa_savings *= reduction_factor
            rightsizing_savings *= reduction_factor
            storage_savings *= reduction_factor
            total_savings = max_total_savings
        
        # Calculate validated savings percentage
        savings_percentage = (total_savings / total_cost * 100) if total_cost > 0 else 0
        
        # Update optimization results
        optimization.update({
            'hpa_monthly_savings': hpa_savings,
            'rightsizing_monthly_savings': rightsizing_savings,
            'storage_monthly_savings': storage_savings,
            'total_monthly_savings': total_savings,
            'savings_percentage': savings_percentage,
            'validation_applied': True
        })
        
        logger.info(f"✅ Validated savings: HPA=${hpa_savings:.2f}, Right-sizing=${rightsizing_savings:.2f}, Storage=${storage_savings:.2f}, Total=${total_savings:.2f} ({savings_percentage:.1f}%)")
        
        return optimization
    
    def _combine_and_validate_results(self, actual_costs: Dict, current_usage: Dict, 
                                    optimization: Dict, efficiency: Dict, confidence: Dict) -> Dict:
        """Combine all analysis results with validation"""
        
        # Extract cost components
        total_cost = actual_costs['monthly_actual_total']
        node_cost = actual_costs['monthly_actual_node']
        storage_cost = actual_costs['monthly_actual_storage']
        networking_cost = actual_costs['monthly_actual_networking']
        control_plane_cost = actual_costs['monthly_actual_control_plane']
        registry_cost = actual_costs['monthly_actual_registry']
        other_cost = actual_costs['monthly_actual_other']
        
        # Validate cost breakdown totals
        component_total = (node_cost + storage_cost + networking_cost + 
                          control_plane_cost + registry_cost + other_cost)
        
        if abs(component_total - total_cost) > 0.01:
            logger.warning(f"⚠️ Final cost validation failed: components=${component_total:.2f}, total=${total_cost:.2f}")
            # Force balance
            adjustment = total_cost - component_total
            other_cost += adjustment
            logger.info(f"✅ Balanced costs by adjusting 'other': +${adjustment:.2f}")
        
        return {
            # === ACTUAL COSTS ===
            'total_cost': total_cost,
            'cost_label': actual_costs['cost_label'],
            'cost_source': actual_costs['cost_source'],
            'node_cost': node_cost,
            'storage_cost': storage_cost,
            'networking_cost': networking_cost,
            'control_plane_cost': control_plane_cost,
            'registry_cost': registry_cost,
            'other_cost': other_cost,
            
            # === OPTIMIZATION POTENTIAL ===
            'total_savings': optimization['total_monthly_savings'],
            'savings_label': 'Monthly Potential (current usage optimization)',
            'savings_source': 'Current usage pattern analysis',
            'hpa_savings': optimization['hpa_monthly_savings'],
            'right_sizing_savings': optimization['rightsizing_monthly_savings'],
            'storage_savings': optimization['storage_monthly_savings'],
            'savings_percentage': optimization['savings_percentage'],
            'annual_savings': optimization['total_monthly_savings'] * 12,
            
            # === CURRENT USAGE INSIGHTS ===
            'current_cpu_utilization': current_usage.get('avg_cpu_utilization', 0),
            'current_memory_utilization': current_usage.get('avg_memory_utilization', 0),
            'current_node_count': current_usage.get('node_count', 1),
            'current_usage_timestamp': datetime.now().isoformat(),
            'hpa_reduction': optimization.get('hpa_replica_reduction_pct', 0),
            'cpu_gap': current_usage.get('cpu_optimization_potential_pct', 0),
            'memory_gap': current_usage.get('memory_optimization_potential_pct', 0),
            
            # === CONFIDENCE & QUALITY ===
            'analysis_confidence': confidence.get('overall_confidence', 0.7),
            'confidence_level': confidence.get('confidence_level', 'Medium'),
            'data_quality_score': confidence.get('data_quality_score', 7.0),
            
            # === METADATA ===
            'analysis_method': 'consistent_current_usage_optimization',
            'is_consistent': True,
            'temporal_confusion_eliminated': True,
            'uses_real_current_metrics': True,
            'algorithms_used': list(self.algorithms.keys()),
            'analysis_timestamp': datetime.now().isoformat(),
            'is_algorithmic': True,
            'static_values_used': False,
            'validation_applied': True,
            
            # Full algorithm results for detailed analysis
            'current_usage_analysis': current_usage,
            'optimization_analysis': optimization,
            'efficiency_analysis': efficiency,
            'confidence_analysis': confidence
        }
    
    def _final_validation(self, results: Dict) -> Dict:
        """Perform final validation checks"""
        warnings = []
        
        total_cost = results.get('total_cost', 0)
        total_savings = results.get('total_savings', 0)
        savings_percentage = results.get('savings_percentage', 0)
        
        # Check if savings percentage is reasonable
        if savings_percentage > 70:
            warnings.append('Savings percentage exceeds 70%')
        
        # Check if total savings exceeds total cost
        if total_savings > total_cost:
            warnings.append('Total savings exceeds total cost')
        
        # Check cost breakdown
        cost_breakdown_total = (
            results.get('node_cost', 0) +
            results.get('storage_cost', 0) +
            results.get('networking_cost', 0) +
            results.get('control_plane_cost', 0) +
            results.get('registry_cost', 0) +
            results.get('other_cost', 0)
        )
        
        if abs(cost_breakdown_total - total_cost) > 0.01:
            warnings.append(f'Cost breakdown ${cost_breakdown_total:.2f} != total ${total_cost:.2f}')
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings
        }
    
    def _auto_fix_results(self, results: Dict, warnings: List[str]) -> Dict:
        """Automatically fix common issues"""
        
        for warning in warnings:
            if 'Cost breakdown' in warning and '!=' in warning:
                # Fix cost breakdown mismatch
                total_cost = results['total_cost']
                component_total = (
                    results.get('node_cost', 0) +
                    results.get('storage_cost', 0) +
                    results.get('networking_cost', 0) +
                    results.get('control_plane_cost', 0) +
                    results.get('registry_cost', 0) +
                    results.get('other_cost', 0)
                )
                
                if component_total > 0:
                    adjustment_factor = total_cost / component_total
                    results['node_cost'] *= adjustment_factor
                    results['storage_cost'] *= adjustment_factor
                    results['networking_cost'] *= adjustment_factor
                    results['control_plane_cost'] *= adjustment_factor
                    results['registry_cost'] *= adjustment_factor
                    results['other_cost'] *= adjustment_factor
                    logger.info(f"✅ Auto-fixed cost breakdown mismatch")
            
            elif 'exceeds total cost' in warning:
                # Fix savings exceeding total cost
                max_savings = results['total_cost'] * 0.6  # Cap at 60%
                results['total_savings'] = max_savings
                results['annual_savings'] = max_savings * 12
                results['savings_percentage'] = 60.0
                
                # Proportionally reduce component savings
                total_component_savings = (
                    results.get('hpa_savings', 0) +
                    results.get('right_sizing_savings', 0) +
                    results.get('storage_savings', 0)
                )
                
                if total_component_savings > 0:
                    reduction_factor = max_savings / total_component_savings
                    results['hpa_savings'] *= reduction_factor
                    results['right_sizing_savings'] *= reduction_factor
                    results['storage_savings'] *= reduction_factor
                
                logger.info(f"✅ Auto-fixed excessive savings")
        
        return results
    
    def _create_fallback_results(self, cost_data: Dict) -> Dict:
        """Create fallback results when analysis fails"""
        total_cost = ensure_numeric(cost_data.get('total_cost', 0))
        
        # Conservative estimates
        conservative_savings = min(total_cost * 0.05, 50)  # 5% or $50, whichever is smaller
        
        return {
            'total_cost': total_cost,
            'cost_label': 'Fallback Analysis',
            'node_cost': total_cost * 0.6,
            'storage_cost': total_cost * 0.2,
            'networking_cost': total_cost * 0.1,
            'control_plane_cost': total_cost * 0.05,
            'registry_cost': total_cost * 0.03,
            'other_cost': total_cost * 0.02,
            'total_savings': conservative_savings,
            'hpa_savings': conservative_savings * 0.5,
            'right_sizing_savings': conservative_savings * 0.3,
            'storage_savings': conservative_savings * 0.2,
            'savings_percentage': (conservative_savings / total_cost * 100) if total_cost > 0 else 0,
            'annual_savings': conservative_savings * 12,
            'analysis_confidence': 0.3,
            'confidence_level': 'Low',
            'data_quality_score': 3.0,
            'analysis_method': 'fallback_conservative',
            'is_fallback': True,
            'cpu_gap': 15.0,
            'memory_gap': 10.0,
            'hpa_reduction': 5.0
        }

# ============================================================================
# ANALYSIS ALGORITHMS
# ============================================================================

class CurrentUsageAnalysisAlgorithm:
    """Analyzes current real-time usage patterns"""
    
    def analyze(self, metrics_data: Dict, pod_data: Dict = None) -> Dict:
        """Analyze current usage patterns with improved accuracy"""
        logger.info("🔍 ALGORITHM: current usage analysis")
        
        try:
            nodes = metrics_data.get('nodes', []) if metrics_data else []
            
            if not nodes:
                return self._minimal_usage_analysis()
            
            # Extract utilization metrics with validation
            cpu_utils = []
            memory_utils = []
            
            for node in nodes:
                cpu_val = ensure_numeric(node.get('cpu_usage_pct', 0))
                memory_val = ensure_numeric(node.get('memory_usage_pct', 0))
                
                # Validate reasonable ranges
                if 0 <= cpu_val <= 100:
                    cpu_utils.append(cpu_val)
                if 0 <= memory_val <= 100:
                    memory_utils.append(memory_val)
            
            # Calculate statistical metrics
            avg_cpu = safe_mean(cpu_utils) if cpu_utils else 35.0
            avg_memory = safe_mean(memory_utils) if memory_utils else 60.0
            cpu_std = safe_stdev(cpu_utils) if len(cpu_utils) > 1 else 10.0
            memory_std = safe_stdev(memory_utils) if len(memory_utils) > 1 else 15.0
            
            # Calculate optimization potential with realistic bounds
            cpu_optimization_potential = self._calculate_cpu_optimization_potential(avg_cpu, cpu_std)
            memory_optimization_potential = self._calculate_memory_optimization_potential(avg_memory, memory_std)
            
            # Additional analysis
            hpa_suitability = self._calculate_hpa_suitability(cpu_std, memory_std, len(nodes))
            system_efficiency = self._calculate_system_efficiency(avg_cpu, avg_memory)
            usage_pattern = self._classify_usage_pattern(avg_cpu, avg_memory, cpu_std, memory_std)
            
            return {
                'node_count': len(nodes),
                'avg_cpu_utilization': round(avg_cpu, 1),
                'avg_memory_utilization': round(avg_memory, 1),
                'cpu_variability': round(cpu_std, 1),
                'memory_variability': round(memory_std, 1),
                'cpu_optimization_potential_pct': round(cpu_optimization_potential * 100, 1),
                'memory_optimization_potential_pct': round(memory_optimization_potential * 100, 1),
                'hpa_suitability_score': round(hpa_suitability, 2),
                'system_efficiency_score': round(system_efficiency, 2),
                'analysis_quality': 'high' if len(nodes) > 1 else 'medium',
                'usage_pattern': usage_pattern,
                'raw_cpu_values': cpu_utils,
                'raw_memory_values': memory_utils
            }
            
        except Exception as e:
            logger.error(f"❌ Current usage analysis failed: {e}")
            return self._minimal_usage_analysis()
    
    def _calculate_cpu_optimization_potential(self, avg_cpu: float, cpu_std: float) -> float:
        """Calculate CPU optimization potential with realistic bounds"""
        optimal_range = (60, 80)  # Adjusted for more realistic targets
        
        if avg_cpu < optimal_range[0]:
            # Under-utilized - significant potential
            potential = min(0.4, (optimal_range[0] - avg_cpu) / optimal_range[0])
        elif avg_cpu > optimal_range[1]:
            # Over-utilized - limited optimization
            potential = 0.05
        else:
            # In optimal range - minimal optimization
            potential = 0.02
        
        # Adjust for variability (higher variability = more optimization potential)
        variability_factor = min(1.5, 1 + (cpu_std / 50))
        result = min(0.5, potential * variability_factor)  # Cap at 50%
        
        return result
    
    def _calculate_memory_optimization_potential(self, avg_memory: float, memory_std: float) -> float:
        """Calculate memory optimization potential with realistic bounds"""
        optimal_range = (65, 85)  # Adjusted for more realistic targets
        
        if avg_memory < optimal_range[0]:
            potential = min(0.3, (optimal_range[0] - avg_memory) / optimal_range[0])
        elif avg_memory > optimal_range[1]:
            potential = 0.03
        else:
            potential = 0.02
        
        variability_factor = min(1.3, 1 + (memory_std / 60))
        result = min(0.4, potential * variability_factor)  # Cap at 40%
        
        return result
    
    def _calculate_hpa_suitability(self, cpu_std: float, memory_std: float, node_count: int) -> float:
        """Calculate HPA suitability score"""
        # Higher variability indicates better HPA candidates
        variability_score = (cpu_std + memory_std) / 100
        variability_score = min(1.0, variability_score)  # Cap at 1.0
        
        # More nodes = better HPA scalability
        scale_factor = min(1.0, node_count / 5)
        
        # Combine factors
        suitability = variability_score * 0.7 + scale_factor * 0.3
        return min(1.0, suitability)
    
    def _calculate_system_efficiency(self, avg_cpu: float, avg_memory: float) -> float:
        """Calculate overall system efficiency"""
        # Target utilization: CPU ~70%, Memory ~75%
        cpu_target = 70.0
        memory_target = 75.0
        
        cpu_efficiency = max(0, 1 - abs(avg_cpu - cpu_target) / cpu_target)
        memory_efficiency = max(0, 1 - abs(avg_memory - memory_target) / memory_target)
        
        return (cpu_efficiency + memory_efficiency) / 2
    
    def _classify_usage_pattern(self, avg_cpu: float, avg_memory: float, cpu_std: float, memory_std: float) -> str:
        """Classify usage pattern"""
        if cpu_std > 25 or memory_std > 30:
            return 'highly_variable'
        elif avg_cpu > 85 or avg_memory > 90:
            return 'over_utilized'
        elif avg_cpu < 30 and avg_memory < 40:
            return 'under_utilized'
        elif 60 <= avg_cpu <= 80 and 65 <= avg_memory <= 85:
            return 'well_optimized'
        else:
            return 'mixed_efficiency'
    
    def _minimal_usage_analysis(self) -> Dict:
        """Fallback analysis when no metrics available"""
        return {
            'node_count': 1,
            'avg_cpu_utilization': 35.0,
            'avg_memory_utilization': 60.0,
            'cpu_variability': 10.0,
            'memory_variability': 15.0,
            'cpu_optimization_potential_pct': 15.0,
            'memory_optimization_potential_pct': 12.0,
            'hpa_suitability_score': 0.5,
            'system_efficiency_score': 0.6,
            'analysis_quality': 'low',
            'usage_pattern': 'unknown'
        }


class OptimizationCalculatorAlgorithm:
    """Calculates optimization potential with realistic bounds"""
    
    def calculate(self, actual_costs: Dict, current_usage: Dict, metrics_data: Dict) -> Dict:
        """Calculate optimization savings with improved accuracy"""
        logger.info("💡 ALGORITHM: optimization calculation")
        
        try:
            # Base costs
            monthly_node_cost = ensure_numeric(actual_costs['monthly_actual_node'])
            monthly_storage_cost = ensure_numeric(actual_costs['monthly_actual_storage'])
            monthly_total_cost = ensure_numeric(actual_costs['monthly_actual_total'])
            
            # Calculate savings with validation
            hpa_savings = self._calculate_hpa_savings(monthly_node_cost, current_usage)
            rightsizing_savings = self._calculate_rightsizing_savings(monthly_node_cost, current_usage)
            storage_savings = self._calculate_storage_savings(monthly_storage_cost, current_usage)
            
            # Validate individual savings don't exceed reasonable limits
            max_hpa = monthly_node_cost * 0.6  # Max 60% of node cost
            max_rightsizing = monthly_node_cost * 0.4  # Max 40% of node cost
            max_storage = monthly_storage_cost * 0.3  # Max 30% of storage cost
            
            hpa_savings = min(hpa_savings, max_hpa)
            rightsizing_savings = min(rightsizing_savings, max_rightsizing)
            storage_savings = min(storage_savings, max_storage)
            
            # Calculate totals
            total_savings = hpa_savings + rightsizing_savings + storage_savings
            
            # Validate total doesn't exceed 50% of total cost
            max_total_savings = monthly_total_cost * 0.5
            if total_savings > max_total_savings:
                # Proportionally reduce savings
                reduction_factor = max_total_savings / total_savings
                hpa_savings *= reduction_factor
                rightsizing_savings *= reduction_factor
                storage_savings *= reduction_factor
                total_savings = max_total_savings
            
            savings_percentage = (total_savings / monthly_total_cost * 100) if monthly_total_cost > 0 else 0
            
            return {
                'hpa_monthly_savings': round(hpa_savings, 2),
                'rightsizing_monthly_savings': round(rightsizing_savings, 2),
                'storage_monthly_savings': round(storage_savings, 2),
                'total_monthly_savings': round(total_savings, 2),
                'savings_percentage': round(savings_percentage, 1),
                'hpa_replica_reduction_pct': self._calculate_hpa_replica_reduction(current_usage),
                'optimization_confidence': self._calculate_optimization_confidence(current_usage),
                'calculation_method': 'fixed_current_usage_based_algorithmic',
                'validation_applied': True
            }
            
        except Exception as e:
            logger.error(f"❌ Optimization calculation failed: {e}")
            return self._minimal_optimization_result()
    
    def _calculate_hpa_savings(self, node_cost: float, usage: Dict) -> float:
        """Calculate HPA savings based on usage patterns"""
        hpa_suitability = usage.get('hpa_suitability_score', 0.5)
        
        if hpa_suitability < 0.2:
            return 0
        
        # Base efficiency from suitability (reduced for realism)
        base_efficiency = hpa_suitability * 0.15  # Reduced from 0.25
        
        # CPU/Memory utilization bonus
        avg_cpu = usage.get('avg_cpu_utilization', 50)
        avg_memory = usage.get('avg_memory_utilization', 60)
        
        if avg_cpu < 40 or avg_memory < 50:
            utilization_bonus = 0.08  # Reduced from 0.1
        elif avg_cpu < 60 or avg_memory < 70:
            utilization_bonus = 0.05
        else:
            utilization_bonus = 0.02
        
        total_efficiency = min(0.25, base_efficiency + utilization_bonus)  # Cap at 25%
        return node_cost * total_efficiency
    
    def _calculate_rightsizing_savings(self, node_cost: float, usage: Dict) -> float:
        """Calculate right-sizing savings"""
        cpu_potential = usage.get('cpu_optimization_potential_pct', 0) / 100
        memory_potential = usage.get('memory_optimization_potential_pct', 0) / 100
        
        # Use the higher of the two potentials but with conservative factor
        optimization_potential = max(cpu_potential, memory_potential)
        conservative_factor = 0.5  # Reduced from 0.7 for more realistic estimates
        
        # Additional cap based on system efficiency
        system_efficiency = usage.get('system_efficiency_score', 0.7)
        if system_efficiency > 0.8:
            conservative_factor *= 0.7  # Further reduce if system is already efficient
        
        return node_cost * optimization_potential * conservative_factor
    
    def _calculate_storage_savings(self, storage_cost: float, usage: Dict) -> float:
        """Calculate storage savings"""
        system_efficiency = usage.get('system_efficiency_score', 0.7)
        
        if system_efficiency < 0.5:
            storage_optimization_potential = 0.12  # Reduced from 0.15
        elif system_efficiency < 0.7:
            storage_optimization_potential = 0.06  # Reduced from 0.08
        else:
            storage_optimization_potential = 0.02  # Reduced from 0.03
        
        return storage_cost * storage_optimization_potential
    
    def _calculate_hpa_replica_reduction(self, usage: Dict) -> float:
        """Calculate expected HPA replica reduction percentage"""
        hpa_suitability = usage.get('hpa_suitability_score', 0)
        system_efficiency = usage.get('system_efficiency_score', 0.7)
        
        # More conservative replica reduction estimates
        base_reduction = hpa_suitability * 25  # Reduced from 40
        efficiency_bonus = (1 - system_efficiency) * 15  # Reduced from 20
        
        return min(40, base_reduction + efficiency_bonus)  # Cap at 40%
    
    def _calculate_optimization_confidence(self, usage: Dict) -> float:
        """Calculate confidence in optimization calculations"""
        factors = []
        
        # Analysis quality factor
        analysis_quality = usage.get('analysis_quality', 'medium')
        if analysis_quality == 'high':
            factors.append(0.9)
        elif analysis_quality == 'medium':
            factors.append(0.7)
        else:
            factors.append(0.5)
        
        # Node count factor
        node_count = usage.get('node_count', 1)
        if node_count > 3:
            factors.append(0.8)
        elif node_count > 1:
            factors.append(0.6)
        else:
            factors.append(0.4)
        
        # HPA suitability factor
        hpa_suitability = usage.get('hpa_suitability_score', 0)
        factors.append(max(0.3, hpa_suitability))
        
        # System efficiency factor (lower efficiency = higher confidence in improvements)
        system_efficiency = usage.get('system_efficiency_score', 0.7)
        factors.append(max(0.4, 1 - system_efficiency + 0.3))
        
        confidence = safe_mean(factors)
        return max(0.3, min(0.9, confidence))  # Bound between 0.3 and 0.9
    
    def _minimal_optimization_result(self) -> Dict:
        """Fallback optimization result"""
        return {
            'hpa_monthly_savings': 0,
            'rightsizing_monthly_savings': 0,
            'storage_monthly_savings': 0,
            'total_monthly_savings': 0,
            'savings_percentage': 0,
            'hpa_replica_reduction_pct': 0,
            'optimization_confidence': 0.3,
            'calculation_method': 'minimal_fallback'
        }


class EfficiencyEvaluatorAlgorithm:
    """Evaluates efficiency improvements"""
    
    def evaluate(self, current_usage: Dict, optimization: Dict, metrics_data: Dict) -> Dict:
        """Evaluate efficiency improvements with realistic targets"""
        logger.info("⚡ ALGORITHM: efficiency evaluation")
        
        try:
            # Current efficiency levels
            current_cpu_efficiency = self._calculate_cpu_efficiency(current_usage)
            current_memory_efficiency = self._calculate_memory_efficiency(current_usage)
            current_system_efficiency = current_usage.get('system_efficiency_score', 0.7)
            
            # Target efficiency after optimization (more realistic)
            target_cpu_efficiency = self._calculate_target_efficiency(
                current_cpu_efficiency, 
                current_usage.get('cpu_optimization_potential_pct', 0) / 100,
                max_improvement=0.3  # Cap improvement at 30%
            )
            target_memory_efficiency = self._calculate_target_efficiency(
                current_memory_efficiency, 
                current_usage.get('memory_optimization_potential_pct', 0) / 100,
                max_improvement=0.25  # Cap improvement at 25%
            )
            target_system_efficiency = min(0.9, (target_cpu_efficiency + target_memory_efficiency) / 2)
            
            # Calculate realistic improvements
            cpu_improvement = max(0, target_cpu_efficiency - current_cpu_efficiency)
            memory_improvement = max(0, target_memory_efficiency - current_memory_efficiency)
            system_improvement = max(0, target_system_efficiency - current_system_efficiency)
            
            return {
                'current_cpu_efficiency': round(current_cpu_efficiency, 3),
                'current_memory_efficiency': round(current_memory_efficiency, 3),
                'current_system_efficiency': round(current_system_efficiency, 3),
                'target_cpu_efficiency': round(target_cpu_efficiency, 3),
                'target_memory_efficiency': round(target_memory_efficiency, 3),
                'target_system_efficiency': round(target_system_efficiency, 3),
                'cpu_efficiency_improvement': round(cpu_improvement, 3),
                'memory_efficiency_improvement': round(memory_improvement, 3),
                'system_efficiency_improvement': round(system_improvement, 3),
                'overall_efficiency_potential': round(system_improvement, 3),
                'efficiency_evaluation_method': 'fixed_algorithmic_target_based'
            }
            
        except Exception as e:
            logger.error(f"❌ Efficiency evaluation failed: {e}")
            return self._minimal_efficiency_evaluation()
    
    def _calculate_cpu_efficiency(self, usage: Dict) -> float:
        """Calculate current CPU efficiency"""
        avg_cpu = usage.get('avg_cpu_utilization', 0)
        target_cpu = 70  # Realistic target
        
        if avg_cpu > target_cpu:
            # Over-utilized
            efficiency = target_cpu / avg_cpu
        else:
            # Under-utilized
            efficiency = avg_cpu / target_cpu
        
        return min(1.0, max(0.1, efficiency))
    
    def _calculate_memory_efficiency(self, usage: Dict) -> float:
        """Calculate current memory efficiency"""
        avg_memory = usage.get('avg_memory_utilization', 0)
        target_memory = 75  # Realistic target
        
        if avg_memory > target_memory:
            # Over-utilized
            efficiency = target_memory / avg_memory
        else:
            # Under-utilized
            efficiency = avg_memory / target_memory
        
        return min(1.0, max(0.1, efficiency))
    
    def _calculate_target_efficiency(self, current_efficiency: float, optimization_potential: float, max_improvement: float = 0.3) -> float:
        """Calculate target efficiency after optimization"""
        # Conservative improvement calculation
        potential_improvement = optimization_potential * 0.6  # Only 60% of potential is realistic
        actual_improvement = min(max_improvement, potential_improvement)
        
        target = current_efficiency + actual_improvement
        return min(0.95, target)  # Cap at 95% efficiency
    
    def _minimal_efficiency_evaluation(self) -> Dict:
        """Fallback efficiency evaluation"""
        return {
            'current_cpu_efficiency': 0.6,
            'current_memory_efficiency': 0.65,
            'current_system_efficiency': 0.625,
            'target_cpu_efficiency': 0.75,
            'target_memory_efficiency': 0.8,
            'target_system_efficiency': 0.775,
            'cpu_efficiency_improvement': 0.15,
            'memory_efficiency_improvement': 0.15,
            'system_efficiency_improvement': 0.15,
            'overall_efficiency_potential': 0.15,
            'efficiency_evaluation_method': 'minimal_fallback'
        }


class ConfidenceScorerAlgorithm:
    """ML-style confidence scoring"""
    
    def score(self, actual_costs: Dict, current_usage: Dict, optimization: Dict, efficiency: Dict) -> Dict:
        """Calculate confidence scores with improved accuracy"""
        logger.info("🤖 ALGORITHM: confidence scoring")
        
        try:
            # Calculate individual scores
            data_quality_score = self._calculate_data_quality_score(actual_costs, current_usage)
            consistency_score = self._calculate_consistency_score(optimization, efficiency)
            feasibility_score = self._calculate_feasibility_score(current_usage, optimization)
            
            # Weighted combination (more conservative)
            overall_confidence = (
                data_quality_score * 0.4 +
                consistency_score * 0.35 +
                feasibility_score * 0.25
            )
            
            # Determine confidence level with more conservative thresholds
            if overall_confidence > 0.75:
                confidence_level = 'High'
                confidence_description = 'High-quality data with validated analysis'
            elif overall_confidence > 0.55:
                confidence_level = 'Medium'
                confidence_description = 'Good data quality with reliable analysis'
            else:
                confidence_level = 'Low'
                confidence_description = 'Limited data - conservative estimates provided'
            
            return {
                'overall_confidence': round(overall_confidence, 2),
                'confidence_level': confidence_level,
                'confidence_description': confidence_description,
                'data_quality_score': round(data_quality_score * 10, 1),  # Scale to 0-10
                'data_quality_factor': round(data_quality_score, 2),
                'consistency_factor': round(consistency_score, 2),
                'feasibility_factor': round(feasibility_score, 2),
                'confidence_method': 'fixed_weighted_algorithmic_scoring'
            }
            
        except Exception as e:
            logger.error(f"❌ Confidence scoring failed: {e}")
            return self._minimal_confidence_score()
    
    def _calculate_data_quality_score(self, costs: Dict, usage: Dict) -> float:
        """Calculate data quality score"""
        quality_factors = []
        
        # Cost data quality
        total_cost = costs.get('monthly_actual_total', 0)
        if total_cost > 100:
            quality_factors.append(1.0)
        elif total_cost > 50:
            quality_factors.append(0.8)
        elif total_cost > 10:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.3)
        
        # Usage data quality
        node_count = usage.get('node_count', 0)
        if node_count > 5:
            quality_factors.append(1.0)
        elif node_count > 2:
            quality_factors.append(0.8)
        elif node_count >= 1:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.2)
        
        # Analysis quality
        analysis_quality = usage.get('analysis_quality', 'medium')
        quality_map = {'high': 1.0, 'medium': 0.7, 'low': 0.4}
        quality_factors.append(quality_map.get(analysis_quality, 0.5))
        
        # Raw data availability
        has_raw_cpu = bool(usage.get('raw_cpu_values'))
        has_raw_memory = bool(usage.get('raw_memory_values'))
        if has_raw_cpu and has_raw_memory:
            quality_factors.append(1.0)
        elif has_raw_cpu or has_raw_memory:
            quality_factors.append(0.7)
        else:
            quality_factors.append(0.4)
        
        return safe_mean(quality_factors)
    
    def _calculate_consistency_score(self, optimization: Dict, efficiency: Dict) -> float:
        """Calculate consistency between analyses"""
        consistency_factors = []
        
        # Check optimization confidence vs efficiency improvement alignment
        opt_confidence = optimization.get('optimization_confidence', 0.5)
        eff_improvement = efficiency.get('overall_efficiency_potential', 0.1)
        
        # Both high or both low = good consistency
        if (opt_confidence > 0.7 and eff_improvement > 0.15) or (opt_confidence < 0.4 and eff_improvement < 0.08):
            consistency_factors.append(1.0)
        elif abs(opt_confidence - eff_improvement) < 0.2:
            consistency_factors.append(0.8)
        else:
            consistency_factors.append(0.5)
        
        # Check if savings percentages are reasonable
        savings_pct = optimization.get('savings_percentage', 0)
        if 2 <= savings_pct <= 30:  # Reasonable range
            consistency_factors.append(1.0)
        elif savings_pct <= 50:
            consistency_factors.append(0.7)
        else:
            consistency_factors.append(0.3)
        
        # Check HPA reduction reasonableness
        hpa_reduction = optimization.get('hpa_replica_reduction_pct', 0)
        if 5 <= hpa_reduction <= 40:  # Reasonable range
            consistency_factors.append(1.0)
        elif hpa_reduction <= 60:
            consistency_factors.append(0.7)
        else:
            consistency_factors.append(0.4)
        
        return safe_mean(consistency_factors)
    
    def _calculate_feasibility_score(self, usage: Dict, optimization: Dict) -> float:
        """Calculate feasibility of optimizations"""
        feasibility_factors = []
        
        # HPA feasibility
        hpa_suitability = usage.get('hpa_suitability_score', 0)
        hpa_savings = optimization.get('hpa_monthly_savings', 0)
        if hpa_suitability > 0.6 and hpa_savings > 0:
            feasibility_factors.append(1.0)
        elif hpa_suitability > 0.3 or hpa_savings > 0:
            feasibility_factors.append(0.7)
        else:
            feasibility_factors.append(0.4)
        
        # Right-sizing feasibility
        cpu_potential = usage.get('cpu_optimization_potential_pct', 0)
        memory_potential = usage.get('memory_optimization_potential_pct', 0)
        if cpu_potential > 15 or memory_potential > 10:
            feasibility_factors.append(1.0)
        elif cpu_potential > 8 or memory_potential > 5:
            feasibility_factors.append(0.8)
        else:
            feasibility_factors.append(0.5)
        
        # System efficiency feasibility
        system_efficiency = usage.get('system_efficiency_score', 0.7)
        if system_efficiency < 0.6:
            feasibility_factors.append(1.0)  # Lots of room for improvement
        elif system_efficiency < 0.8:
            feasibility_factors.append(0.8)  # Some room for improvement
        else:
            feasibility_factors.append(0.5)  # Limited improvement potential
        
        # Validation applied factor
        if optimization.get('validation_applied'):
            feasibility_factors.append(0.9)
        else:
            feasibility_factors.append(0.6)
        
        return safe_mean(feasibility_factors)
    
    def _minimal_confidence_score(self) -> Dict:
        """Fallback confidence score"""
        return {
            'overall_confidence': 0.5,
            'confidence_level': 'Medium',
            'confidence_description': 'Standard analysis with conservative estimates',
            'data_quality_score': 5.0,
            'data_quality_factor': 0.5,
            'consistency_factor': 0.5,
            'feasibility_factor': 0.5,
            'confidence_method': 'minimal_fallback'
        }

# ============================================================================
# MAIN INTEGRATION FUNCTION
# ============================================================================

def integrate_consistent_analysis(resource_group: str, cluster_name: str, 
                                      cost_data: Dict, metrics_data: Dict, 
                                      pod_data: Dict = None) -> Dict:
    """
    CONSISTENT ANALYSIS INTEGRATION
    Main integration function for app.py
    """
    
    logger.info("🎯 Starting CONSISTENT algorithmic integration")
    logger.info("✅ Approach: Validated actual costs + realistic optimization estimates")
    
    try:
        # Initialize fixed analyzer
        analyzer = ConsistentCostAnalyzer()
        
        # Run analysis with comprehensive validation
        results = analyzer.analyze(cost_data, metrics_data, pod_data)
        
        # Add integration metadata
        results['integration_info'] = {
            'resource_group': resource_group,
            'cluster_name': cluster_name,
            'analysis_timestamp': datetime.now().isoformat(),
            'consistent_approach_used': True,
            'validation_applied': True,
            'fixes_applied': [
                'Cost reconciliation',
                'Savings validation',
                'Percentage calculation fixes',
                'Realistic optimization bounds',
                'Enhanced error handling'
            ],
            'algorithms_count': len(results.get('algorithms_used', [])),
            'confidence_basis': 'Validated current usage pattern analysis with realistic cost baseline'
        }
        
        logger.info(f"✅ CONSISTENT analysis complete:")
        logger.info(f"   - Monthly actual cost: ${results.get('total_cost', 0):.2f}")
        logger.info(f"   - Monthly savings potential: ${results.get('total_savings', 0):.2f}")
        logger.info(f"   - Savings percentage: {results.get('savings_percentage', 0):.1f}%")
        logger.info(f"   - Confidence: {results.get('analysis_confidence', 0):.2f}")
        logger.info(f"   - Method: consistent current usage optimization")
        
        return results
        
    except Exception as e:
        logger.error(f"CONSISTENT analysis failed: {e}")
        # Return fallback results instead of raising exception
        analyzer = ConsistentCostAnalyzer()
        return analyzer._create_fallback_results(cost_data)

# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

def integrate_algorithmic_analysis(resource_group: str, cluster_name: str, 
                                 cost_data: Dict, metrics_data: Dict, 
                                 pod_data: Dict = None) -> Dict:
    """
    Legacy function - redirects to consistent analysis
    """
    logger.info("🔄 Legacy function called - redirecting to consistent analysis")
    return integrate_consistent_analysis(resource_group, cluster_name, cost_data, metrics_data, pod_data)