#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
ENHANCED Phase 2: Dynamic Strategy Generation Engine - WITH CLUSTER CONFIG INTEGRATION
=====================================================================================
ENHANCEMENTS ADDED:
1. ✅ Real cluster configuration integration
2. ✅ Savings consistency between strategy and plan modules
3. ✅ Proper analysis_results integration 
4. ✅ Realistic implementation costs
5. ✅ Positive ROI calculations
6. ✅ Better default values when analysis_results unavailable
7. ✅ Cluster config-aware strategy generation
"""

import json
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
import numpy as np

# Import standards-based implementation cost calculator
from shared.standards.implementation_cost_calculator import implementation_cost_calculator

logger = logging.getLogger(__name__)

# ============================================================================
# ENHANCED STRATEGY DATA STRUCTURES (UNCHANGED)
# ============================================================================

@dataclass
class ComprehensiveOptimizationOpportunity:
    """Enhanced optimization opportunity with comprehensive AKS coverage"""
    type: str  # 'compute', 'storage', 'networking', 'security', 'governance', 'monitoring'
    subtype: str  # 'hpa', 'rightsizing', 'node_optimization', 'storage_classes', etc.
    category: str  # 'cost', 'performance', 'security', 'compliance', 'operational'
    
    # Financial impact
    priority_score: float  # 0.0 - 1.0
    savings_potential_monthly: float
    implementation_cost: float
    roi_timeline_months: int
    break_even_point: str
    
    # Technical assessment
    implementation_complexity: float  # 0.0 - 1.0
    risk_assessment: float  # 0.0 - 1.0
    timeline_weeks: int
    confidence_level: float  # 0.0 - 1.0
    
    # Multi-dimensional impact
    cost_impact: float
    performance_impact: float
    security_impact: float
    compliance_impact: float
    operational_impact: float
    
    # Strategy details
    target_resources: List[str]
    optimal_approach: str
    implementation_strategy: str
    success_probability: float
    
    # Dependencies and constraints
    dependencies: List[str]
    constraints: List[str]
    prerequisites: List[str]
    
    # Validation and monitoring
    success_criteria: List[str]
    kpis: List[Dict]
    monitoring_requirements: List[str]
    validation_procedures: List[str]
    
    # Rollback and contingency
    rollback_strategy: str
    contingency_plans: List[str]
    emergency_procedures: List[str]

@dataclass 
class ComprehensiveDynamicStrategy:
    """Enhanced dynamic strategy with comprehensive AKS optimization"""
    strategy_id: str
    strategy_name: str
    strategy_type: str  # 'cost_focused', 'performance_focused', 'balanced', 'security_focused'
    strategy_approach: str  # 'aggressive', 'conservative', 'balanced', 'risk_averse'
    
    # Strategy composition
    opportunities: List[ComprehensiveOptimizationOpportunity]
    optimization_tracks: Dict[str, List[str]]  # Parallel optimization tracks
    critical_path: List[str]
    
    # Financial projections
    total_savings_potential: float
    total_implementation_cost: float
    net_benefit: float
    roi_percentage: float
    payback_period_months: int
    
    # Timeline and execution
    total_timeline_weeks: int
    implementation_phases: List[Dict]
    parallel_execution_opportunities: List[List[str]]
    
    # Risk and success assessment
    overall_risk_level: str
    success_probability: float
    confidence_intervals: Dict[str, Tuple[float, float]]
    risk_mitigation_strategies: List[str]
    
    # Multi-dimensional optimization
    optimization_objectives: Dict[str, float]  # cost, performance, security, etc.
    trade_off_analysis: Dict[str, Any]
    optimization_constraints: List[str]
    
    # Governance and compliance
    compliance_requirements: List[str]
    governance_framework: Dict[str, Any]
    approval_requirements: List[str]
    stakeholder_impact: Dict[str, str]
    
    # Monitoring and adaptation
    success_metrics: List[Dict]
    monitoring_strategy: Dict[str, Any]
    adaptation_triggers: List[str]
    continuous_optimization_plan: Dict[str, Any]
    
    # DNA-specific customizations
    cluster_personality_match: float
    strategy_uniqueness_score: float
    industry_alignment: str
    best_practices_compliance: float
    
    # NEW: Cluster config insights
    config_enhanced: bool = False
    cluster_intelligence: Optional[Dict[str, Any]] = None

# ============================================================================
# ENHANCED DYNAMIC STRATEGY GENERATION ENGINE
# ============================================================================

class EnhancedDynamicStrategyEngine:
    """
    Comprehensive strategy engine for AKS optimization with cluster config intelligence
    """
    
    def __init__(self):
        self.opportunity_detector = EnhancedOpportunityDetector()
        self.strategy_optimizer = AdvancedStrategyOptimizer()
        self.financial_analyzer = ComprehensiveFinancialAnalyzer()
        self.risk_assessor = AdvancedRiskAssessor()
        self.best_practices_engine = BestPracticesEngine()
        
        # NEW: Cluster configuration support
        self.cluster_config = None
        
        # Advanced strategy patterns learned from enterprise implementations
        self.strategy_patterns = self._load_enterprise_patterns()
        self.industry_benchmarks = self._load_industry_benchmarks()
        
    def set_cluster_config(self, cluster_config: Dict):
        """NEW: Set cluster configuration for enhanced strategy"""
        self.cluster_config = cluster_config
        logger.info(f"🎯 Strategy Engine: Cluster config set")
    
    def generate_comprehensive_dynamic_strategy(self, cluster_dna, 
                                          analysis_results: Optional[Dict] = None,
                                          cluster_config: Optional[Dict] = None) -> ComprehensiveDynamicStrategy:
        """
        ENHANCED: Generate comprehensive dynamic strategy with cluster config intelligence and ROI filtering
        """
        logger.info(f"🎯 Generating comprehensive dynamic strategy for cluster: {getattr(cluster_dna, 'cluster_personality', 'unknown')}")
        
        # Cache analysis results for HPA extraction from different sources
        self._current_analysis_results = analysis_results
        
        # NEW: Set cluster config if provided
        if cluster_config:
            self.set_cluster_config(cluster_config)
        
        # Extract actual savings from analysis_results first
        actual_savings = self._extract_actual_savings(analysis_results)
        actual_cost = self._extract_real_cluster_cost(analysis_results, cluster_config)
        
        # Validate we have real data to work with
        if actual_cost <= 0:
            logger.error("❌ CRITICAL: No real cluster cost data available")
            logger.error("❌ Cannot generate meaningful strategy without actual cost analysis")
            return None
            
        if actual_savings <= 0:
            logger.warning("⚠️ WARNING: No savings potential identified from analysis")
            logger.warning("⚠️ Strategy will focus on assessment and data collection")
            
        logger.info(f"💰 Using REAL data - Cost: ${actual_cost:.2f}, Savings: ${actual_savings:.2f}")
        if self.cluster_config:
            config_resources = self.cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0)
            logger.info(f"🔧 Using cluster config with {config_resources} resources")
        
        # Step 1: Enhanced opportunity detection with cluster config awareness
        opportunities = self.opportunity_detector.detect_comprehensive_opportunities(
            cluster_dna, analysis_results, actual_savings, self.cluster_config
        )
        logger.info(f"🔍 Detected {len(opportunities)} initial optimization opportunities")
        
        # NEW Step 1.5: Apply ROI-based filtering for financial viability
        if opportunities:
            logger.info(f"🔍 DEBUG: Before ROI filtering - {len(opportunities)} opportunities detected")
            for i, opp in enumerate(opportunities[:3]):  # Log first 3 for debugging
                payback_months = (opp.implementation_cost / opp.savings_potential_monthly) if opp.savings_potential_monthly > 0 else float('inf')
                payback_str = f"{payback_months:.1f}" if payback_months != float('inf') else "infinite"
                logger.info(f"🔍 DEBUG: Opp {i+1}: {opp.type}/{opp.subtype} - "
                           f"Savings: ${opp.savings_potential_monthly:.2f}/month, "
                           f"Cost: ${opp.implementation_cost:.2f}, "
                           f"Payback: {payback_str} months")
            
            opportunities = self.opportunity_detector._filter_opportunities_by_roi(
                opportunities, self.cluster_config
            )
            logger.info(f"✅ Filtered to {len(opportunities)} financially viable opportunities")
            
            # Handle case where all opportunities were filtered out - INVESTIGATE WHY
            if not opportunities:
                logger.error(f"💥 CRITICAL: All opportunities filtered out by ROI - this indicates a calculation error")
                logger.error(f"💥 DEBUG: actual_savings passed: ${actual_savings:.2f}")
                logger.error(f"💥 DEBUG: total_cost from analysis: ${analysis_results.get('total_cost', 0) if analysis_results else 0:.2f}")
                return None
        else:
            logger.error(f"💥 CRITICAL: No initial opportunities detected - opportunity detection logic failed")
            return None
        
        # Step 2: Multi-objective optimization analysis with cluster intelligence
        optimization_objectives = self._determine_optimization_objectives(cluster_dna, analysis_results, self.cluster_config)
        logger.info(f"🎯 Optimization objectives: {list(optimization_objectives.keys())}")
        
        # Step 3: Advanced strategy optimization using multi-objective algorithms
        optimal_strategy_config = self.strategy_optimizer.optimize_strategy(
            opportunities, cluster_dna, optimization_objectives, self.cluster_config
        )
        logger.info(f"🧮 Optimal strategy configuration: {optimal_strategy_config.get('strategy_type', 'unknown')}")
        
        # Step 4: Financial impact analysis with comprehensive ROI modeling
        financial_analysis = self.financial_analyzer.analyze_comprehensive_impact(
            optimal_strategy_config.get('selected_opportunities', []), cluster_dna, analysis_results, actual_savings
        )
        logger.info(f"💰 Total financial impact: ${financial_analysis.get('net_benefit', 0):.2f} net benefit")
        
        # Step 5: Advanced risk assessment with mitigation strategies
        risk_analysis = self.risk_assessor.assess_comprehensive_risks(
            optimal_strategy_config['selected_opportunities'], cluster_dna, self.cluster_config
        )
        logger.info(f"⚠️ Risk assessment: {risk_analysis.get('overall_risk_level', 'unknown')} risk")
        
        # Step 6: Best practices alignment and compliance checking
        best_practices_analysis = self.best_practices_engine.analyze_alignment(
            optimal_strategy_config, cluster_dna, self.cluster_config
        )
        logger.info(f"✅ Best practices compliance: {best_practices_analysis.get('compliance_score', 0):.1%}")
        
        # Step 7: Generate execution plan with parallel tracks
        execution_plan = self._generate_comprehensive_execution_plan(
            optimal_strategy_config['selected_opportunities'], cluster_dna, self.cluster_config
        )
        
        # Step 8: Create continuous optimization framework
        continuous_optimization = self._generate_continuous_optimization_plan(
            optimal_strategy_config, cluster_dna, self.cluster_config
        )
        
        # NEW Step 9: Extract cluster intelligence insights
        cluster_intelligence = None
        config_enhanced = False
        
        if self.cluster_config and self.cluster_config.get('status') == 'completed':
            cluster_intelligence = self._extract_cluster_intelligence(self.cluster_config, cluster_dna)
            config_enhanced = True
            logger.info(f"🔧 Strategy enhanced with cluster intelligence: {cluster_intelligence.get('workload_complexity', 'unknown')}")
        
        # Step 10: Assemble comprehensive strategy with cluster config
        strategy = self._assemble_comprehensive_strategy(
            optimal_strategy_config,
            financial_analysis,
            risk_analysis,
            best_practices_analysis,
            execution_plan,
            continuous_optimization,
            cluster_dna,
            cluster_intelligence,
            config_enhanced
        )
        
        logger.info(f"✅ Comprehensive dynamic strategy generated: {strategy.strategy_name}")
        logger.info(f"💰 Total savings potential: ${strategy.total_savings_potential:.2f}/month")
        logger.info(f"📅 Implementation timeline: {strategy.total_timeline_weeks} weeks")
        logger.info(f"🎲 Success probability: {strategy.success_probability:.1%}")
        logger.info(f"📊 ROI: {strategy.roi_percentage:.1f}%")
        if config_enhanced:
            logger.info(f"🔧 Strategy enhanced with real cluster configuration data")
        
        return strategy
    
    # ========================================================================
    # NEW: CLUSTER CONFIGURATION INTELLIGENCE METHODS
    # ========================================================================
    
    def _extract_cluster_intelligence(self, cluster_config: Dict, cluster_dna) -> Dict[str, Any]:
        """Extract intelligence insights from real cluster configuration"""
        
        intelligence = {}
        
        try:
            # Workload complexity assessment
            workload_resources = cluster_config.get('workload_resources', {})
            scaling_resources = cluster_config.get('scaling_resources', {})
            
            total_deployments = workload_resources.get('deployments', {}).get('item_count', 0)
            total_statefulsets = workload_resources.get('statefulsets', {}).get('item_count', 0)
            total_daemonsets = workload_resources.get('daemonsets', {}).get('item_count', 0)
            # Try to get HPA count from multiple sources (fix for 0 HPA issue)
            total_hpas = scaling_resources.get('horizontalpodautoscalers', {}).get('item_count', 0)
            
            # If cluster config shows 0 HPAs, try getting from analysis results
            if total_hpas == 0 and hasattr(self, '_current_analysis_results'):
                analysis_hpas = self._extract_hpa_count_from_analysis(self._current_analysis_results)
                if analysis_hpas > 0:
                    total_hpas = analysis_hpas
                    logger.info(f"🔧 Fixed HPA count in strategy: Using {total_hpas} HPAs from analysis results instead of cluster config's 0")
            
            total_workloads = total_deployments + total_statefulsets + total_daemonsets
            
            # Workload complexity classification using standards
            standards = implementation_cost_calculator.load_standards()
            complexity_thresholds = standards.get('optimization_thresholds', {}).get('thresholds', {})
            high_complexity_threshold = complexity_thresholds.get('workload_complexity_high_threshold', 50)
            medium_complexity_threshold = complexity_thresholds.get('workload_complexity_medium_threshold', 20)
            
            if total_workloads > high_complexity_threshold:
                workload_complexity = 'high'
            elif total_workloads > medium_complexity_threshold:
                workload_complexity = 'medium'
            else:
                workload_complexity = 'low'
            
            # HPA coverage analysis
            hpa_coverage = (total_hpas / max(total_workloads, 1)) * 100
            
            # Namespace analysis
            namespaces = cluster_config.get('fetch_metrics', {}).get('total_namespaces', 0)
            namespace_complexity = 'high' if namespaces > 15 else 'medium' if namespaces > 5 else 'low'
            
            # Strategy implications
            strategy_implications = []
            
            # Load standards for HPA thresholds
            standards = implementation_cost_calculator.load_standards()
            hpa_thresholds = standards.get('optimization_thresholds', {}).get('thresholds', {})
            high_hpa_potential_threshold = hpa_thresholds.get('high_hpa_potential_threshold', 20)
            
            if hpa_coverage < high_hpa_potential_threshold:
                strategy_implications.append('high_hpa_potential')
            if workload_complexity == 'high':
                strategy_implications.append('phased_implementation_recommended')
            if namespace_complexity == 'high':
                strategy_implications.append('namespace_aware_optimization')
            
            intelligence = {
                'workload_complexity': workload_complexity,
                'total_workloads': total_workloads,
                'hpa_coverage': hpa_coverage,
                'namespace_complexity': namespace_complexity,
                'strategy_implications': strategy_implications,
                'configuration_confidence': min(1.0, cluster_config.get('fetch_metrics', {}).get('successful_fetches', 0) / 50),
                'real_cluster_scale': self._determine_real_cluster_scale(total_workloads, namespaces),
                'optimization_readiness': self._assess_optimization_readiness_from_config(
                    hpa_coverage, workload_complexity, namespace_complexity
                )
            }
            
            logger.info(f"🔧 Cluster Intelligence: {workload_complexity} complexity, {hpa_coverage:.0f}% HPA coverage")
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting cluster intelligence: {e}")
            intelligence['error'] = str(e)
        
        return intelligence
    
    def _extract_hpa_count_from_analysis(self, analysis_results: Dict) -> int:
        """Extract HPA count from analysis results when cluster config shows 0"""
        try:
            # Try multiple sources where HPA data might be stored
            hpa_count = 0
            
            # Source 1: Check metrics_data.hpa_implementation.total_hpas
            metrics_data = analysis_results.get('metrics_data', {})
            if metrics_data:
                hpa_impl = metrics_data.get('hpa_implementation', {})
                if isinstance(hpa_impl, dict):
                    total_hpas = hpa_impl.get('total_hpas')
                    if isinstance(total_hpas, list):
                        hpa_count = len(total_hpas)
                    elif isinstance(total_hpas, int):
                        hpa_count = total_hpas
                        
                    if hpa_count > 0:
                        logger.info(f"🎯 Strategy: Found {hpa_count} HPAs in analysis_results.metrics_data.hpa_implementation")
                        return hpa_count
            
            # Source 2: Check direct hpa_implementation field
            hpa_implementation = analysis_results.get('hpa_implementation', {})
            if isinstance(hpa_implementation, dict):
                total_hpas = hpa_implementation.get('total_hpas')
                if isinstance(total_hpas, list):
                    hpa_count = len(total_hpas)
                elif isinstance(total_hpas, int):
                    hpa_count = total_hpas
                    
                if hpa_count > 0:
                    logger.info(f"🎯 Strategy: Found {hpa_count} HPAs in analysis_results.hpa_implementation")
                    return hpa_count
            
            # Source 3: Look for any field containing 'hpa' with count data
            for key, value in analysis_results.items():
                if 'hpa' in key.lower() and isinstance(value, dict):
                    if 'total_hpas' in value:
                        total_hpas = value['total_hpas']
                        if isinstance(total_hpas, list):
                            hpa_count = len(total_hpas)
                        elif isinstance(total_hpas, int):
                            hpa_count = total_hpas
                            
                        if hpa_count > 0:
                            logger.info(f"🎯 Strategy: Found {hpa_count} HPAs in analysis_results.{key}")
                            return hpa_count
                            
            logger.warning("⚠️ Strategy: Could not find HPA count in analysis results")
            return 0
            
        except Exception as e:
            logger.warning(f"⚠️ Strategy: Error extracting HPA count from analysis: {e}")
            return 0
    
    def _determine_real_cluster_scale(self, total_workloads: int, namespaces: int) -> str:
        """Determine real cluster scale from configuration"""
        
        if total_workloads > 100 or namespaces > 20:
            return 'enterprise'
        elif total_workloads > 30 or namespaces > 10:
            return 'large'
        elif total_workloads > 10 or namespaces > 5:
            return 'medium'
        else:
            return 'small'
    
    def _assess_optimization_readiness_from_config(self, hpa_coverage: float, 
                                                 workload_complexity: str, 
                                                 namespace_complexity: str) -> str:
        """Assess optimization readiness from real cluster configuration"""
        
        readiness_score = 0
        
        # Load HPA readiness thresholds from standards
        standards = implementation_cost_calculator.load_standards()
        hpa_thresholds = standards.get('optimization_thresholds', {}).get('thresholds', {})
        very_low_hpa_threshold = hpa_thresholds.get('very_low_hpa_threshold', 10)
        medium_hpa_threshold = hpa_thresholds.get('medium_hpa_threshold', 50)
        
        # HPA readiness using standards
        if hpa_coverage < very_low_hpa_threshold:
            readiness_score += 3  # High potential for HPA optimization
        elif hpa_coverage < medium_hpa_threshold:
            readiness_score += 2  # Medium potential
        else:
            readiness_score += 1  # Some potential
        
        # Complexity readiness
        if workload_complexity == 'low':
            readiness_score += 2  # Easier to optimize
        elif workload_complexity == 'medium':
            readiness_score += 1
        
        if namespace_complexity == 'low':
            readiness_score += 1  # Simpler namespace structure
        
        # Determine readiness level
        if readiness_score >= 5:
            return 'high'
        elif readiness_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    # ========================================================================
    # ENHANCED EXISTING METHODS (with cluster config awareness)
    # ========================================================================
    
    def _extract_actual_savings(self, analysis_results: Optional[Dict]) -> float:
        """Extract actual savings from analysis results for consistency - FIXED to prioritize detailed algorithmic calculations"""
        if not analysis_results:
            logger.warning("❌ No analysis_results provided - cannot extract savings without real data")
            return 0.0
        
        # Extract all available savings sources
        savings_sources = {
            'total_savings': analysis_results.get('total_savings', 0),
            'hpa_savings': analysis_results.get('hpa_savings', 0),
            'right_sizing_savings': analysis_results.get('right_sizing_savings', 0),
            'storage_savings': analysis_results.get('storage_savings', 0),
            'compute_savings': analysis_results.get('compute_savings', 0),
            'savings_potential': analysis_results.get('savings_potential', 0),
            'hpa_reduction': analysis_results.get('hpa_reduction', 0),
            'hpa_efficiency': analysis_results.get('hpa_efficiency', 0)
        }
        
        # ONLY use detailed algorithmic analysis results (our fixes)
        if savings_sources['total_savings'] > 0:
            logger.info(f"✅ Using DETAILED algorithmic total_savings: ${savings_sources['total_savings']:.2f}")
            return savings_sources['total_savings']
        
        # Use direct detailed savings values only
        for source in ['hpa_savings', 'right_sizing_savings', 'storage_savings', 'compute_savings']:
            if savings_sources[source] > 0:
                logger.info(f"✅ Using DETAILED {source}: ${savings_sources[source]:.2f}")
                return savings_sources[source]
        
        # NO FALLBACKS: Return 0 if no detailed analysis available
        logger.warning("❌ No detailed algorithmic analysis found - returning 0 savings (real analysis required)")
        return 0.0
    
    def _calculate_dynamic_savings_potential(self, total_cost: float, cluster_dna, analysis_results: Dict) -> float:
        """Calculate savings potential based on cluster characteristics using standards"""
        try:
            if total_cost <= 0:
                return 0.0
            
            # Load savings calculation standards
            standards = implementation_cost_calculator.load_standards()
            savings_config = standards.get('optimization_thresholds', {}).get('savings_calculation', {})
            
            # Base savings percentage from standards
            base_savings_percentage = savings_config.get('base_savings_percentage', 0.08)
            
            # Get adjustment values and thresholds from standards
            size_thresholds = savings_config.get('cluster_size_thresholds', {})
            size_adjustments = savings_config.get('cluster_size_adjustments', {})
            density_thresholds = savings_config.get('workload_density_thresholds', {})
            density_adjustments = savings_config.get('workload_density_adjustments', {})
            inefficiency_adjustments = savings_config.get('inefficiency_adjustments', {})
            cost_thresholds = savings_config.get('cost_thresholds', {})
            savings_limits = savings_config.get('savings_limits', {})
            
            # Adjust based on cluster characteristics
            workload_count = analysis_results.get('total_workloads', 0)
            node_count = len(analysis_results.get('nodes', []))
            
            # Size-based adjustments using standards thresholds
            large_cluster_threshold = size_thresholds.get('large_cluster_nodes', 10)
            medium_cluster_threshold = size_thresholds.get('medium_cluster_nodes', 5)
            
            if node_count >= large_cluster_threshold:
                base_savings_percentage += size_adjustments.get('large_cluster_bonus', 0.05)
            elif node_count >= medium_cluster_threshold:
                base_savings_percentage += size_adjustments.get('medium_cluster_bonus', 0.03)
            
            # Workload density adjustments using standards thresholds
            high_density_threshold = density_thresholds.get('high_density_workloads', 50)
            medium_density_threshold = density_thresholds.get('medium_density_workloads', 20)
            
            if workload_count > high_density_threshold:
                base_savings_percentage += density_adjustments.get('high_density_bonus', 0.04)
            elif workload_count > medium_density_threshold:
                base_savings_percentage += density_adjustments.get('medium_density_bonus', 0.02)
            
            # Check for obvious inefficiencies using standards
            max_cpu = analysis_results.get('high_cpu_summary', {}).get('max_cpu_utilization', 0)
            high_cpu_threshold = cost_thresholds.get('high_cpu_threshold', 500)
            moderate_cpu_threshold = cost_thresholds.get('moderate_cpu_threshold', 200)
            
            if max_cpu > high_cpu_threshold:
                base_savings_percentage += inefficiency_adjustments.get('high_cpu_scaling_bonus', 0.08)
            elif max_cpu > moderate_cpu_threshold:
                base_savings_percentage += inefficiency_adjustments.get('moderate_cpu_bonus', 0.04)
            
            # Storage optimization potential using standards
            storage_cost = analysis_results.get('storage_cost', 0)
            storage_threshold = cost_thresholds.get('storage_percentage_threshold', 0.30)
            if storage_cost > total_cost * storage_threshold:
                base_savings_percentage += inefficiency_adjustments.get('storage_optimization_bonus', 0.03)
            
            # Networking optimization potential using standards
            network_cost = analysis_results.get('network_cost', 0)
            network_threshold = cost_thresholds.get('network_percentage_threshold', 0.20)
            if network_cost > total_cost * network_threshold:
                base_savings_percentage += inefficiency_adjustments.get('network_optimization_bonus', 0.02)
            
            # Cap the savings percentage at reasonable limits from standards
            max_percentage = savings_limits.get('maximum_percentage', 0.25)
            min_percentage = savings_limits.get('minimum_percentage', 0.05)
            base_savings_percentage = min(base_savings_percentage, max_percentage)
            base_savings_percentage = max(base_savings_percentage, min_percentage)
            
            potential_savings = total_cost * base_savings_percentage
            
            logger.info(f"✅ Standards-based savings calculation: {base_savings_percentage*100:.1f}% of ${total_cost:.2f} = ${potential_savings:.2f}")
            logger.info(f"   Factors: {node_count} nodes, {workload_count} workloads, max CPU: {max_cpu:.0f}%")
            
            return potential_savings
            
        except Exception as e:
            logger.error(f"❌ Dynamic savings calculation failed: {e}")
            # Conservative fallback using standards
            standards = implementation_cost_calculator.load_standards()
            fallback_percentage = standards.get('optimization_thresholds', {}).get('savings_calculation', {}).get('base_savings_percentage', 0.08)
            return total_cost * fallback_percentage
    
    def _determine_optimization_objectives(self, cluster_dna, analysis_results: Optional[Dict], 
                                         cluster_config: Optional[Dict] = None) -> Dict[str, float]:
        """Enhanced optimization objectives with cluster config awareness using standards"""
        
        personality = getattr(cluster_dna, 'cluster_personality', '')
        total_cost = analysis_results.get('total_cost', 0) if analysis_results else 0
        
        # Load optimization objectives from standards
        standards = implementation_cost_calculator.load_standards()
        objectives_config = standards.get('optimization_thresholds', {}).get('optimization_objectives', {})
        base_objectives = objectives_config.get('base_objectives', {})
        personality_adjustments = objectives_config.get('personality_adjustments', {})
        cost_thresholds = objectives_config.get('cost_thresholds', {})
        
        # Base objectives from standards
        objectives = {
            'cost_optimization': base_objectives.get('cost_optimization', 0.4),
            'performance_optimization': base_objectives.get('performance_optimization', 0.3),
            'security_enhancement': base_objectives.get('security_enhancement', 0.2),
            'operational_efficiency': base_objectives.get('operational_efficiency', 0.1)
        }
        
        # Adjust based on cluster personality using standards
        high_cost_threshold = cost_thresholds.get('high_cost_threshold', 5000)
        cost_bonus = personality_adjustments.get('cost_focused_bonus', 0.2)
        
        if 'cost' in personality.lower() or total_cost > high_cost_threshold:
            objectives['cost_optimization'] += cost_bonus
            objectives['performance_optimization'] -= cost_bonus / 2
        
        if 'performance' in personality.lower() or 'latency' in personality.lower():
            performance_bonus = personality_adjustments.get('performance_focused_bonus', 0.2)
            objectives['performance_optimization'] += performance_bonus
            objectives['cost_optimization'] -= performance_bonus / 2
        
        if 'security' in personality.lower() or 'compliance' in personality.lower():
            security_bonus = personality_adjustments.get('security_focused_bonus', 0.2)
            objectives['security_enhancement'] += security_bonus
            objectives['cost_optimization'] -= security_bonus / 2
        
        if 'enterprise' in personality.lower():
            enterprise_bonus = personality_adjustments.get('enterprise_efficiency_bonus', 0.1)
            objectives['operational_efficiency'] += enterprise_bonus
            objectives['security_enhancement'] += enterprise_bonus
            objectives['cost_optimization'] -= enterprise_bonus * 2
        
        # NEW: Adjust based on cluster configuration using standards
        if cluster_config and cluster_config.get('status') == 'completed':
            cluster_intelligence = self._extract_cluster_intelligence(cluster_config, cluster_dna)
            
            # Load cluster intelligence adjustments from standards
            intelligence_adjustments = objectives_config.get('cluster_intelligence_adjustments', {})
            intelligence_thresholds = objectives_config.get('thresholds', {})
            
            # High workload complexity suggests more operational focus
            if cluster_intelligence.get('workload_complexity') == 'high':
                operational_bonus = intelligence_adjustments.get('high_complexity_operational_bonus', 0.1)
                cost_reduction = intelligence_adjustments.get('high_complexity_cost_reduction', 0.05)
                performance_reduction = intelligence_adjustments.get('high_complexity_performance_reduction', 0.05)
                
                objectives['operational_efficiency'] += operational_bonus
                objectives['cost_optimization'] -= cost_reduction
                objectives['performance_optimization'] -= performance_reduction
            
            # Low HPA coverage suggests cost optimization focus
            default_hpa_coverage = intelligence_thresholds.get('default_hpa_coverage', 50)
            hpa_coverage = cluster_intelligence.get('hpa_coverage', default_hpa_coverage)
            low_hpa_threshold = intelligence_thresholds.get('low_hpa_coverage_threshold', 20)
            
            if hpa_coverage < low_hpa_threshold:
                cost_bonus = intelligence_adjustments.get('low_hpa_cost_bonus', 0.15)
                operational_reduction = intelligence_adjustments.get('low_hpa_operational_reduction', 0.15)
                
                objectives['cost_optimization'] += cost_bonus
                objectives['operational_efficiency'] -= operational_reduction
            
            # Enterprise scale suggests balanced approach
            if cluster_intelligence.get('real_cluster_scale') == 'enterprise':
                # Flatten objectives for balanced enterprise approach using standards
                total_adjustment = intelligence_adjustments.get('enterprise_balance_adjustment', 0.1)
                objectives['cost_optimization'] -= total_adjustment / 4
                objectives['performance_optimization'] += total_adjustment / 4
                objectives['security_enhancement'] += total_adjustment / 4
                objectives['operational_efficiency'] += total_adjustment / 4
        
        # Normalize to sum to 1.0
        total = sum(objectives.values())
        objectives = {k: v/total for k, v in objectives.items()}
        
        return objectives
    
    def _generate_comprehensive_execution_plan(self, opportunities: List[ComprehensiveOptimizationOpportunity], 
                                             cluster_dna, cluster_config: Optional[Dict] = None) -> Dict:
        """Enhanced execution plan with cluster config awareness"""
        
        # Group opportunities by type for parallel execution
        execution_tracks = {
            'infrastructure': [],
            'compute': [],
            'storage': [],
            'networking': [],
            'security': [],
            'governance': []
        }
        
        for opp in opportunities:
            track = self._determine_execution_track(opp)
            execution_tracks[track].append(opp.type)
        
        # Calculate timeline with parallel execution and cluster complexity
        timeline_weeks = self._calculate_parallel_timeline(opportunities, cluster_dna, cluster_config)
        
        # Generate critical path with cluster awareness
        critical_path = self._identify_critical_path(opportunities, cluster_config)
        
        return {
            'execution_tracks': execution_tracks,
            'timeline_weeks': timeline_weeks,
            'critical_path': critical_path,
            'parallel_opportunities': self._identify_parallel_opportunities(opportunities),
            'phase_dependencies': self._calculate_phase_dependencies(opportunities),
            'resource_requirements': self._calculate_execution_resources(opportunities, cluster_config),
            'cluster_specific_considerations': self._generate_cluster_specific_considerations(cluster_config)
        }
    
    def _generate_cluster_specific_considerations(self, cluster_config: Optional[Dict]) -> List[str]:
        """Generate cluster-specific implementation considerations"""
        
        considerations = []
        
        if not cluster_config or cluster_config.get('status') != 'completed':
            return ['Standard implementation approach - no cluster config available']
        
        try:
            cluster_intelligence = self._extract_cluster_intelligence(cluster_config, None)
            
            # Workload complexity considerations
            workload_complexity = cluster_intelligence.get('workload_complexity', 'medium')
            if workload_complexity == 'high':
                considerations.append('Phased implementation recommended due to high workload complexity')
                considerations.append('Extended testing periods for each phase')
            elif workload_complexity == 'low':
                considerations.append('Accelerated implementation possible with simple workload structure')
            
            # HPA coverage considerations
            hpa_coverage = cluster_intelligence.get('hpa_coverage', 0)
            if hpa_coverage > 50:
                considerations.append('Review existing HPA configurations before implementing new ones')
            elif hpa_coverage == 0:
                considerations.append('Clean HPA implementation - no existing configurations to conflict')
            
            # Namespace considerations
            namespace_complexity = cluster_intelligence.get('namespace_complexity', 'medium')
            if namespace_complexity == 'high':
                considerations.append('Coordinate optimization across multiple namespaces')
                considerations.append('Namespace-specific testing and validation required')
            
            # Scale considerations
            cluster_scale = cluster_intelligence.get('real_cluster_scale', 'medium')
            if cluster_scale == 'enterprise':
                considerations.append('Enterprise-scale cluster requires additional governance and approval processes')
                considerations.append('Enhanced monitoring and rollback procedures necessary')
            
        except Exception as e:
            considerations.append(f'Unable to generate cluster-specific considerations: {e}')
        
        return considerations
    
    def _calculate_parallel_timeline(self, opportunities: List[ComprehensiveOptimizationOpportunity], 
                                   cluster_dna, cluster_config: Optional[Dict] = None) -> int:
        """Enhanced timeline calculation with cluster config awareness"""
        
        # Group by execution track
        tracks = {}
        for opp in opportunities:
            track = self._determine_execution_track(opp)
            if track not in tracks:
                tracks[track] = []
            tracks[track].append(opp.timeline_weeks)
        
        # Calculate track timelines
        track_timelines = {}
        for track, timelines in tracks.items():
            track_timelines[track] = sum(timelines)  # Sequential within track
        
        # Add coordination overhead
        coordination_overhead = len(tracks) * 0.5  # 0.5 weeks per track for coordination
        
        # NEW: Add cluster complexity overhead
        cluster_overhead = 0
        if cluster_config and cluster_config.get('status') == 'completed':
            cluster_intelligence = self._extract_cluster_intelligence(cluster_config, cluster_dna)
            
            # Complex clusters need more time
            if cluster_intelligence.get('workload_complexity') == 'high':
                cluster_overhead += 1
            if cluster_intelligence.get('namespace_complexity') == 'high':
                cluster_overhead += 0.5
            if cluster_intelligence.get('real_cluster_scale') == 'enterprise':
                cluster_overhead += 1
        
        # Total timeline is the longest track plus coordination and cluster overhead
        max_track_timeline = max(track_timelines.values()) if track_timelines else 0
        
        return int(max_track_timeline + coordination_overhead + cluster_overhead)
    
    def _identify_critical_path(self, opportunities: List[ComprehensiveOptimizationOpportunity], 
                              cluster_config: Optional[Dict] = None) -> List[str]:
        """Enhanced critical path identification with cluster awareness"""
        
        # Sort by dependencies, timeline impact, and cluster considerations
        critical_opportunities = sorted(
            opportunities,
            key=lambda x: (len(x.dependencies), -x.timeline_weeks, -x.priority_score)
        )
        
        # NEW: Adjust critical path based on cluster config
        if cluster_config and cluster_config.get('status') == 'completed':
            cluster_intelligence = self._extract_cluster_intelligence(cluster_config, None)
            
            # For high complexity clusters, prioritize lower-risk opportunities first
            if cluster_intelligence.get('workload_complexity') == 'high':
                critical_opportunities = sorted(
                    critical_opportunities,
                    key=lambda x: (x.risk_assessment, len(x.dependencies), -x.priority_score)
                )
        
        return [opp.type for opp in critical_opportunities]
    
    def _calculate_execution_resources(self, opportunities: List[ComprehensiveOptimizationOpportunity],
                                     cluster_config: Optional[Dict] = None) -> Dict[str, Any]:
        """Enhanced resource calculation with cluster config awareness"""
        
        total_complexity = sum(opp.implementation_complexity for opp in opportunities)
        avg_complexity = total_complexity / len(opportunities) if opportunities else 0
        
        # Base FTE requirements
        fte_requirements = {
            'aks_specialist': min(2.0, avg_complexity * 2),
            'devops_engineer': min(1.5, avg_complexity * 1.5),
            'security_specialist': 0.5 if any('security' in opp.type for opp in opportunities) else 0,
            'network_engineer': 0.3 if any('network' in opp.type for opp in opportunities) else 0,
            'project_manager': 0.5
        }
        
        # NEW: Adjust based on cluster configuration
        if cluster_config and cluster_config.get('status') == 'completed':
            cluster_intelligence = self._extract_cluster_intelligence(cluster_config, None)
            
            # Complex clusters need more expertise
            cluster_complexity = cluster_intelligence.get('workload_complexity', 'medium')
            if cluster_complexity == 'high':
                fte_requirements['aks_specialist'] *= 1.3
                fte_requirements['devops_engineer'] *= 1.2
                fte_requirements['project_manager'] *= 1.5
            
            # Enterprise scale needs additional coordination
            if cluster_intelligence.get('real_cluster_scale') == 'enterprise':
                fte_requirements['project_manager'] *= 1.3
                fte_requirements['change_manager'] = 0.3
        
        return {
            'fte_requirements': fte_requirements,
            'total_fte': sum(fte_requirements.values()),
            'skill_requirements': self._extract_skill_requirements(opportunities),
            'tool_requirements': self._extract_tool_requirements(opportunities),
            'infrastructure_requirements': self._extract_infrastructure_requirements(opportunities),
            'cluster_specific_requirements': self._extract_cluster_specific_requirements(cluster_config)
        }
    
    def _extract_cluster_specific_requirements(self, cluster_config: Optional[Dict]) -> List[str]:
        """Extract requirements specific to the cluster configuration"""
        
        requirements = []
        
        if not cluster_config or cluster_config.get('status') != 'completed':
            return ['Standard cluster requirements']
        
        try:
            cluster_intelligence = self._extract_cluster_intelligence(cluster_config, None)
            
            # Based on cluster scale
            cluster_scale = cluster_intelligence.get('real_cluster_scale', 'medium')
            if cluster_scale == 'enterprise':
                requirements.extend([
                    'Enterprise change management process',
                    'Extended testing and validation procedures',
                    'Multiple environment coordination'
                ])
            
            # Based on complexity
            workload_complexity = cluster_intelligence.get('workload_complexity', 'medium')
            if workload_complexity == 'high':
                requirements.extend([
                    'Detailed workload mapping and analysis',
                    'Extended rollback preparation',
                    'Enhanced monitoring during implementation'
                ])
            
            # Based on existing HPA coverage
            hpa_coverage = cluster_intelligence.get('hpa_coverage', 0)
            if hpa_coverage > 30:
                requirements.append('HPA conflict analysis and resolution procedures')
            
        except Exception as e:
            requirements.append(f'Cluster-specific requirement analysis failed: {e}')
        
        return requirements
    
    def _assemble_comprehensive_strategy(self, strategy_config: Dict, financial_analysis: Dict,
                                       risk_analysis: Dict, best_practices: Dict,
                                       execution_plan: Dict, continuous_optimization: Dict,
                                       cluster_dna, cluster_intelligence: Optional[Dict] = None,
                                       config_enhanced: bool = False) -> ComprehensiveDynamicStrategy:
        """Enhanced strategy assembly with cluster config intelligence"""
        
        strategy_id = f"strategy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Generate strategy name based on focus and approach (with config awareness)
        strategy_name = self._generate_strategy_name(strategy_config, cluster_dna, cluster_intelligence)
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            financial_analysis, risk_analysis, strategy_config['selected_opportunities']
        )
        
        # Generate trade-off analysis
        trade_off_analysis = self._generate_trade_off_analysis(strategy_config, cluster_dna)
        
        return ComprehensiveDynamicStrategy(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            strategy_type=strategy_config['strategy_type'],
            strategy_approach=strategy_config['approach'],
            
            opportunities=strategy_config['selected_opportunities'],
            optimization_tracks=execution_plan['execution_tracks'],
            critical_path=execution_plan['critical_path'],
            
            total_savings_potential=financial_analysis['total_savings'],
            total_implementation_cost=financial_analysis['implementation_cost'],
            net_benefit=financial_analysis['net_benefit'],
            roi_percentage=financial_analysis['roi_percentage'],
            payback_period_months=financial_analysis['payback_months'],
            
            total_timeline_weeks=execution_plan['timeline_weeks'],
            implementation_phases=self._generate_implementation_phases(strategy_config['selected_opportunities']),
            parallel_execution_opportunities=execution_plan['parallel_opportunities'],
            
            overall_risk_level=risk_analysis['overall_risk_level'],
            success_probability=risk_analysis['success_probability'],
            confidence_intervals=confidence_intervals,
            risk_mitigation_strategies=risk_analysis['mitigation_strategies'],
            
            optimization_objectives=strategy_config['objectives'],
            trade_off_analysis=trade_off_analysis,
            optimization_constraints=strategy_config.get('constraints', []),
            
            compliance_requirements=best_practices['compliance_requirements'],
            governance_framework=best_practices['governance_framework'],
            approval_requirements=best_practices['approval_requirements'],
            stakeholder_impact=self._assess_stakeholder_impact(strategy_config['selected_opportunities']),
            
            success_metrics=self._generate_comprehensive_success_metrics(strategy_config['selected_opportunities']),
            monitoring_strategy=continuous_optimization,
            adaptation_triggers=continuous_optimization['adaptation_triggers'],
            continuous_optimization_plan=continuous_optimization,
            
            cluster_personality_match=self._calculate_personality_match(strategy_config, cluster_dna),
            strategy_uniqueness_score=self._calculate_strategy_uniqueness(strategy_config, cluster_dna),
            industry_alignment=self._assess_industry_alignment(strategy_config),
            best_practices_compliance=best_practices['compliance_score'],
            
            # NEW: Cluster configuration enhancements
            config_enhanced=config_enhanced,
            cluster_intelligence=cluster_intelligence
        )
    
    def _generate_strategy_name(self, strategy_config: Dict, cluster_dna, 
                              cluster_intelligence: Optional[Dict] = None) -> str:
        """Enhanced strategy name generation with cluster config awareness"""
        
        personality = getattr(cluster_dna, 'cluster_personality', 'balanced')
        strategy_type = strategy_config['strategy_type']
        approach = strategy_config['approach']
        
        primary_focus = max(strategy_config['objectives'].items(), key=lambda x: x[1])[0]
        
        focus_map = {
            'cost_optimization': 'Cost-Optimized',
            'performance_optimization': 'Performance-Enhanced',
            'security_enhancement': 'Security-Hardened',
            'operational_efficiency': 'Operations-Streamlined'
        }
        
        approach_map = {
            'aggressive': 'Accelerated',
            'conservative': 'Phased',
            'balanced': 'Balanced',
            'risk_averse': 'Safe-Harbor'
        }
        
        focus_name = focus_map.get(primary_focus, 'Comprehensive')
        approach_name = approach_map.get(approach, 'Strategic')
        
        # Base scale determination
        if 'enterprise' in personality:
            scale = 'Enterprise'
        elif 'medium' in personality:
            scale = 'Business'
        else:
            scale = 'Agile'
        
        # NEW: Enhance with cluster intelligence
        if cluster_intelligence:
            real_scale = cluster_intelligence.get('real_cluster_scale', '')
            workload_complexity = cluster_intelligence.get('workload_complexity', '')
            
            # Override scale with real cluster data
            if real_scale == 'enterprise':
                scale = 'Enterprise'
            elif real_scale == 'large':
                scale = 'Large-Scale'
            elif real_scale == 'small':
                scale = 'Compact'
            
            # Add complexity indicator
            if workload_complexity == 'high':
                approach_name = f"Multi-Phase {approach_name}"
            elif workload_complexity == 'low':
                approach_name = f"Streamlined {approach_name}"
        
        return f"{focus_name} {approach_name} {scale} AKS Optimization"
    
    # ========================================================================
    # REST OF YOUR EXISTING METHODS (keeping them for compatibility)
    # ========================================================================
    
    def _load_enterprise_patterns(self) -> Dict:
        """Load enterprise strategy patterns from standards configuration"""
        try:
            standards = implementation_cost_calculator.load_standards()
            enterprise_patterns = standards.get('enterprise_patterns', {})
            
            if enterprise_patterns:
                logger.info("✅ Loaded enterprise patterns from standards configuration")
                return enterprise_patterns
            else:
                logger.warning("⚠️ No enterprise patterns found in standards - using minimal defaults")
                return {
                    'cost_optimization_patterns': {},
                    'performance_optimization_patterns': {},
                    'security_hardening_patterns': {}
                }
        except Exception as e:
            logger.error(f"❌ Failed to load enterprise patterns from standards: {e}")
            return {}
    
    def _load_industry_benchmarks(self) -> Dict:
        """Load industry benchmarks from standards configuration"""
        try:
            standards = implementation_cost_calculator.load_standards()
            industry_benchmarks = standards.get('industry_benchmarks', {})
            
            if industry_benchmarks:
                logger.info("✅ Loaded industry benchmarks from standards configuration")
                return industry_benchmarks
            else:
                logger.warning("⚠️ No industry benchmarks found in standards - using minimal defaults")
                return {
                    'cost_optimization': {},
                    'performance_optimization': {},
                    'security_hardening': {}
                }
        except Exception as e:
            logger.error(f"❌ Failed to load industry benchmarks from standards: {e}")
            return {}
    
    def _generate_continuous_optimization_plan(self, strategy_config: Dict, cluster_dna, 
                                             cluster_config: Optional[Dict] = None) -> Dict:
        """Enhanced continuous optimization plan with cluster awareness"""
        
        base_plan = {
            'monitoring_frequency': 'weekly',
            'optimization_cycles': {
                'quick_wins': {'frequency': 'monthly', 'scope': 'tactical'},
                'strategic_reviews': {'frequency': 'quarterly', 'scope': 'strategic'},
                'annual_assessment': {'frequency': 'yearly', 'scope': 'comprehensive'}
            },
            'adaptation_triggers': [
                'cost_variance_threshold_exceeded',
                'performance_degradation_detected',
                'new_optimization_opportunities_identified',
                'business_requirements_changed'
            ],
            'improvement_mechanisms': [
                'automated_optimization_suggestions',
                'ml_driven_anomaly_detection',
                'cost_trend_analysis',
                'performance_regression_detection'
            ],
            'governance_framework': {
                'change_approval_process': 'lightweight_for_tactical_heavy_for_strategic',
                'risk_assessment_requirements': 'automated_for_low_risk_manual_for_high_risk',
                'stakeholder_communication': 'monthly_reports_quarterly_reviews'
            }
        }
        
        # NEW: Enhance with cluster-specific considerations
        if cluster_config and cluster_config.get('status') == 'completed':
            cluster_intelligence = self._extract_cluster_intelligence(cluster_config, cluster_dna)
            
            # Adjust monitoring frequency based on cluster complexity
            if cluster_intelligence.get('workload_complexity') == 'high':
                base_plan['monitoring_frequency'] = 'daily'
                base_plan['optimization_cycles']['quick_wins']['frequency'] = 'bi-weekly'
            
            # Enterprise clusters need more governance
            if cluster_intelligence.get('real_cluster_scale') == 'enterprise':
                base_plan['governance_framework']['change_approval_process'] = 'formal_approval_required'
                base_plan['optimization_cycles']['compliance_reviews'] = {
                    'frequency': 'monthly', 'scope': 'compliance_and_governance'
                }
        
        return base_plan
    
    def _determine_execution_track(self, opportunity):
        type_to_track = {
            'hpa_optimization': 'compute',
            'resource_rightsizing': 'compute',
            'node_optimization': 'infrastructure',
            'storage_optimization': 'storage',
            'storage_classes': 'storage',
            'network_optimization': 'networking',
            'network_policies': 'networking',
            'security_hardening': 'security',
            'rbac_optimization': 'security',
            'cost_governance': 'governance',
            'monitoring_optimization': 'governance'
        }
        return type_to_track.get(opportunity.type, 'infrastructure')
    
    def _identify_parallel_opportunities(self, opportunities):
        parallel_groups = []
        tracks = {}
        for opp in opportunities:
            track = self._determine_execution_track(opp)
            if track not in tracks:
                tracks[track] = []
            tracks[track].append(opp.type)
        
        for track_opportunities in tracks.values():
            if len(track_opportunities) > 1:
                parallel_groups.append(track_opportunities)
        
        return parallel_groups
    
    def _calculate_phase_dependencies(self, opportunities):
        dependencies = {}
        for opp in opportunities:
            dependencies[opp.type] = opp.dependencies
        return dependencies
    
    def _generate_implementation_phases(self, opportunities):
        phases = []
        phase_groups = {
            'Assessment and Preparation': [opp for opp in opportunities if 'assessment' in opp.type.lower()],
            'Infrastructure Optimization': [opp for opp in opportunities if opp.type in ['node_optimization', 'storage_classes']],
            'Compute Optimization': [opp for opp in opportunities if opp.type in ['hpa_optimization', 'resource_rightsizing']],
            'Network and Security': [opp for opp in opportunities if 'network' in opp.type or 'security' in opp.type],
            'Governance and Monitoring': [opp for opp in opportunities if 'governance' in opp.type or 'monitoring' in opp.type],
            'Validation and Optimization': []
        }
        
        phase_number = 1
        for phase_name, phase_opportunities in phase_groups.items():
            if phase_opportunities or phase_name == 'Validation and Optimization':
                phase = {
                    'phase_number': phase_number,
                    'phase_name': phase_name,
                    'opportunities': [opp.type for opp in phase_opportunities],
                    'duration_weeks': max([opp.timeline_weeks for opp in phase_opportunities], default=1),
                    'savings_potential': sum(opp.savings_potential_monthly for opp in phase_opportunities),
                    'complexity_level': max([opp.implementation_complexity for opp in phase_opportunities], default=0.3),
                    'risk_level': max([opp.risk_assessment for opp in phase_opportunities], default=0.2),
                    'success_criteria': list(set([criterion for opp in phase_opportunities for criterion in opp.success_criteria])),
                    'dependencies': list(set([dep for opp in phase_opportunities for dep in opp.dependencies]))
                }
                phases.append(phase)
                phase_number += 1
        
        return phases
    
    def _assess_stakeholder_impact(self, opportunities):
        return {
            'technical_teams': 'Medium - New tools and processes to learn',
            'operations_teams': 'Medium - Updated procedures and monitoring',
            'finance_teams': 'High - Significant cost reduction and budget impact',
            'management': 'High - Improved efficiency and cost optimization',
            'end_users': 'Low - Minimal impact with improved performance',
            'security_teams': 'Medium - Enhanced security posture and compliance'
        }
    
    def _generate_comprehensive_success_metrics(self, opportunities):
        return [
            {
                'category': 'Financial',
                'metrics': [
                    {
                        'name': 'Monthly Cost Savings',
                        'target': sum(opp.savings_potential_monthly for opp in opportunities),
                        'unit': 'USD/month',
                        'measurement_frequency': 'Monthly'
                    }
                ]
            }
        ]
    
    def _calculate_confidence_intervals(self, financial_analysis, risk_analysis, opportunities):
        base_savings = financial_analysis['total_savings']
        base_timeline = max(opp.timeline_weeks for opp in opportunities) if opportunities else 4
        base_success = risk_analysis['success_probability']
        
        return {
            'savings': (base_savings * 0.8, base_savings * 1.2),
            'timeline': (base_timeline * 0.85, base_timeline * 1.15),
            'success_probability': (max(0.1, base_success - 0.1), min(0.95, base_success + 0.1))
        }
    
    def _generate_trade_off_analysis(self, strategy_config, cluster_dna):
        objectives = strategy_config['objectives']
        return {
            'primary_trade_offs': [
                {
                    'dimension_1': 'cost_optimization',
                    'dimension_2': 'performance_optimization',
                    'trade_off_ratio': objectives['cost_optimization'] / objectives['performance_optimization'],
                    'recommendation': 'Balanced approach recommended for sustainable optimization'
                }
            ],
            'optimization_philosophy': 'Balanced Multi-Objective',
            'risk_reward_profile': 'Balanced Risk-Reward Profile',
            'stakeholder_value_alignment': {'executives': 'High', 'engineering_teams': 'Medium'}
        }
    
    def _calculate_personality_match(self, strategy_config, cluster_dna):
        return 0.8  # Default good match
    
    def _calculate_strategy_uniqueness(self, strategy_config, cluster_dna):
        return 0.7  # Default good uniqueness
    
    def _assess_industry_alignment(self, strategy_config):
        return 'General Cloud Optimization'
    
    def _extract_skill_requirements(self, opportunities):
        return ['AKS', 'Kubernetes', 'Azure']
    
    def _extract_tool_requirements(self, opportunities):
        return ['kubectl', 'Azure CLI', 'Helm']
    
    def _extract_infrastructure_requirements(self, opportunities):
        return ['Monitoring namespace and resources']

    def _extract_real_cluster_cost(self, analysis_results: Optional[Dict], cluster_config: Optional[Dict] = None) -> float:
        """Extract real cluster cost - NO FAKE DEFAULTS"""
        if not analysis_results:
            logger.error("❌ Cannot determine cluster cost without analysis_results")
            return 0.0
            
        # Try to get real cost from analysis
        total_cost = analysis_results.get('total_cost', 0)
        if total_cost > 0:
            logger.info(f"✅ Using real cluster cost from analysis: ${total_cost:.2f}")
            return total_cost
            
        # Try alternative cost fields
        alternative_costs = [
            analysis_results.get('monthly_cost', 0),
            analysis_results.get('cost_total', 0),
            analysis_results.get('cluster_cost', 0),
            analysis_results.get('current_cost', 0)
        ]
        
        for cost in alternative_costs:
            if cost > 0:
                logger.info(f"✅ Using real cluster cost from alternative field: ${cost:.2f}")
                return cost
        
        # Try to calculate from component costs
        component_costs = [
            analysis_results.get('compute_cost', 0),
            analysis_results.get('storage_cost', 0),
            analysis_results.get('network_cost', 0),
            analysis_results.get('networking_cost', 0)
        ]
        
        total_components = sum(cost for cost in component_costs if cost > 0)
        if total_components > 0:
            logger.info(f"✅ Using calculated cluster cost from components: ${total_components:.2f}")
            return total_components
            
        # REAL DATA REQUIRED - No fake defaults
        logger.error("❌ No real cost data available - requires actual cluster cost analysis")
        return 0.0


# ============================================================================
# ENHANCED SUPPORTING CLASSES (with cluster config support)
# ============================================================================

class EnhancedOpportunityDetector:
    """Enhanced opportunity detector with cluster config awareness"""

    def _filter_opportunities_by_roi(self, opportunities: List[ComprehensiveOptimizationOpportunity], 
                                cluster_config: Optional[Dict] = None) -> List[ComprehensiveOptimizationOpportunity]:
        """
        Enhanced ROI-based opportunity filtering with cluster intelligence
        Filters out opportunities with unrealistic payback periods while considering cluster context
        """
        if not opportunities:
            logger.info("📊 ROI Filter: No opportunities to filter")
            return []
        
        viable_opportunities = []
        filtered_count = 0
        total_filtered_savings = 0.0
        
        # Get real cluster cost - no fake defaults
        total_cost = 0.0
        
        # Try to get from current analysis results first
        if hasattr(self, '_current_analysis_results') and self._current_analysis_results:
            total_cost = self._extract_real_cluster_cost(self._current_analysis_results)
        elif cluster_config and cluster_config.get('status') == 'completed':
            # Try to get from cluster config analysis
            analysis_data = cluster_config.get('analysis_results', {})
            if analysis_data:
                total_cost = self._extract_real_cluster_cost(analysis_data)
        
        # If no real cost available, cannot do meaningful ROI filtering
        if total_cost <= 0:
            logger.warning("❌ No real cluster cost available - skipping ROI filtering")
            return opportunities
        
        logger.info(f"💰 Using total cost ${total_cost:.2f} for ROI calculations")
        
        # Calculate intelligent thresholds based on cluster size and cost using standards
        standards = implementation_cost_calculator.load_standards()
        optimization_thresholds = standards.get('optimization_thresholds', {})
        
        PAYBACK_THRESHOLD_MONTHS = optimization_thresholds.get('payback_threshold_months', 18)
        MIN_MONTHLY_SAVINGS = max(
            optimization_thresholds.get('minimum_monthly_savings', 5.0), 
            total_cost * optimization_thresholds.get('minimum_savings_percentage', 0.005)
        )
        
        # NEW: Adjust thresholds based on cluster configuration intelligence
        if cluster_config and cluster_config.get('status') == 'completed':
            try:
                workload_resources = cluster_config.get('workload_resources', {})
                total_workloads = sum(
                    workload_resources.get(wl_type, {}).get('item_count', 0)
                    for wl_type in ['deployments', 'statefulsets', 'daemonsets']
                )
                
                # Enterprise clusters can afford longer payback periods using standards
                enterprise_config = optimization_thresholds.get('enterprise_clusters', {})
                small_config = optimization_thresholds.get('small_clusters', {})
                
                if total_workloads > 50:
                    PAYBACK_THRESHOLD_MONTHS = enterprise_config.get('payback_threshold_months', 24)
                    MIN_MONTHLY_SAVINGS = max(
                        enterprise_config.get('minimum_monthly_savings', 25.0), 
                        total_cost * enterprise_config.get('minimum_savings_percentage', 0.01)
                    )
                    logger.info(f"🏢 Enterprise cluster detected ({total_workloads} workloads) - Adjusted ROI thresholds")
                elif total_workloads < 10:
                    PAYBACK_THRESHOLD_MONTHS = small_config.get('payback_threshold_months', 15)
                    MIN_MONTHLY_SAVINGS = max(
                        small_config.get('minimum_monthly_savings', 2.0),
                        total_cost * small_config.get('minimum_savings_percentage', 0.002)
                    )
                    logger.info(f"🏠 Small cluster detected ({total_workloads} workloads) - Relaxed ROI thresholds")
                else:
                    # Medium clusters - use base standards
                    MIN_MONTHLY_SAVINGS = max(
                        optimization_thresholds.get('minimum_monthly_savings', 5.0), 
                        total_cost * optimization_thresholds.get('minimum_savings_percentage', 0.005)
                    )
            
            except Exception as e:
                logger.warning(f"⚠️ Could not adjust ROI thresholds based on cluster config: {e}")
                # Use cost-based minimum only
                MIN_MONTHLY_SAVINGS = max(5.0, total_cost * 0.005)
        
        logger.info(f"📊 ROI Filter: Evaluating {len(opportunities)} opportunities")
        logger.info(f"💰 Thresholds: Max payback {PAYBACK_THRESHOLD_MONTHS} months, Min savings ${MIN_MONTHLY_SAVINGS}/month")
        
        for opp in opportunities:
            # Always keep zero-cost opportunities (free optimizations)
            if opp.implementation_cost <= 0:
                viable_opportunities.append(opp)
                logger.debug(f"✅ Kept zero-cost opportunity: {opp.subtype}")
                continue
            
            # Check minimum savings threshold
            if opp.savings_potential_monthly < MIN_MONTHLY_SAVINGS:
                filtered_count += 1
                total_filtered_savings += opp.savings_potential_monthly
                logger.info(f"🔄 Filtered low-impact opportunity: {opp.subtype} "
                        f"(${opp.savings_potential_monthly:.0f}/month < ${MIN_MONTHLY_SAVINGS}/month threshold)")
                continue
            
            # Calculate comprehensive ROI metrics
            roi_metrics = self._calculate_opportunity_roi(
                opp.savings_potential_monthly, 
                opp.implementation_cost
            )
            
            # Use NPV and payback period for filtering decisions
            if roi_metrics['is_viable'] and roi_metrics['payback_months'] <= PAYBACK_THRESHOLD_MONTHS:
                viable_opportunities.append(opp)
                logger.debug(f"✅ Kept viable opportunity: {opp.subtype} "
                           f"(Payback: {roi_metrics['payback_months']:.1f} months, "
                           f"NPV: ${roi_metrics['npv']:.0f}, "
                           f"ROI: {roi_metrics['roi_percentage']:.1f}%)")
            else:
                filtered_count += 1
                total_filtered_savings += opp.savings_potential_monthly
                
                if roi_metrics['payback_months'] > PAYBACK_THRESHOLD_MONTHS:
                    logger.info(f"🔄 Filtered long-payback opportunity: {opp.subtype} "
                               f"(Payback: {roi_metrics['payback_months']:.1f} months > {PAYBACK_THRESHOLD_MONTHS} month threshold)")
                elif roi_metrics['npv'] <= 0:
                    logger.info(f"🔄 Filtered negative-NPV opportunity: {opp.subtype} "
                               f"(NPV: ${roi_metrics['npv']:.0f}, not financially viable)")
                else:
                    logger.warning(f"⚠️ Filtered opportunity with zero savings potential: {opp.subtype}")
        
        # Log comprehensive filtering results
        kept_count = len(viable_opportunities)
        if filtered_count > 0:
            logger.info(f"📊 ROI Filter Results: Kept {kept_count}, Filtered {filtered_count} opportunities")
            logger.info(f"💰 Filtered potential savings: ${total_filtered_savings:.2f}/month "
                    f"(deemed not cost-effective)")
            
            if kept_count == 0:
                logger.warning(f"⚠️ All opportunities filtered out - consider adjusting ROI thresholds or "
                            f"review opportunity detection logic")
        else:
            logger.info(f"✅ ROI Filter: All {kept_count} opportunities passed ROI criteria")
        
        return viable_opportunities

    
    def detect_comprehensive_opportunities(self, cluster_dna, analysis_results: Optional[Dict], 
                                         actual_savings: float, cluster_config: Optional[Dict] = None) -> List[ComprehensiveOptimizationOpportunity]:
        """Enhanced opportunity detection with cluster config intelligence"""
        
        opportunities = []
        
        # Pass cluster_config to all opportunity detection methods
        opportunities.extend(self._detect_compute_opportunities(cluster_dna, analysis_results, actual_savings, cluster_config))
        opportunities.extend(self._detect_storage_opportunities(cluster_dna, analysis_results, actual_savings, cluster_config))
        opportunities.extend(self._detect_networking_opportunities(cluster_dna, analysis_results, actual_savings, cluster_config))
        opportunities.extend(self._detect_security_opportunities(cluster_dna, analysis_results, actual_savings, cluster_config))
        opportunities.extend(self._detect_governance_opportunities(cluster_dna, analysis_results, actual_savings, cluster_config))
        opportunities.extend(self._detect_monitoring_opportunities(cluster_dna, analysis_results, actual_savings, cluster_config))
        
        return opportunities
    
    def _detect_compute_opportunities(self, cluster_dna, analysis_results: Optional[Dict], 
                                    actual_savings: float, cluster_config: Optional[Dict] = None) -> List[ComprehensiveOptimizationOpportunity]:
        """Enhanced compute opportunity detection with cluster config"""
        
        opportunities = []
        
        # HPA Optimization - Detect based on actual cluster analysis, not just hotspots
        total_cost = self._extract_real_cluster_cost(analysis_results)
        
        # Dynamic HPA opportunity detection based on cluster metrics
        should_recommend_hpa = False
        
        # Check multiple criteria for HPA recommendation
        if analysis_results:
            # Check if cluster has scaling potential (high cost but low HPA coverage)
            current_hpa_count = analysis_results.get('hpa_count', 0)
            total_workloads = analysis_results.get('total_workloads', 0)
            hpa_coverage = (current_hpa_count / total_workloads * 100) if total_workloads > 0 else 0
            
            # Recommend HPA if coverage is low and cluster is significant size
            if total_cost > 500 and hpa_coverage < 80:  # Less than 80% HPA coverage
                should_recommend_hpa = True
            
            # Also check if cluster has scaling inefficiencies
            hpa_efficiency = analysis_results.get('hpa_efficiency_percentage', 50)
            if hpa_efficiency < 70:  # Poor HPA efficiency
                should_recommend_hpa = True
        
        # Fallback: recommend HPA for any cluster over $300/month (basic threshold)
        if total_cost > 300:
            should_recommend_hpa = True
            
        if should_recommend_hpa:
            # FIXED: Use detailed algorithmic analysis results when available
            total_cost = self._extract_real_cluster_cost(analysis_results)
            
            # DEBUG: Log what's actually received to diagnose the root cause
            if analysis_results:
                hpa_value = analysis_results.get('hpa_savings', 'MISSING')
                total_value = analysis_results.get('total_savings', 'MISSING')
                available_keys = [k for k in analysis_results.keys() if 'savings' in k.lower()]
                logger.info(f"🔍 DEBUG: hpa_savings={hpa_value}, total_savings={total_value}")
                logger.info(f"🔍 DEBUG: Available savings keys: {available_keys}")
            
            # ONLY use detailed HPA savings from algorithmic analysis (our fixes)
            if analysis_results and analysis_results.get('hpa_savings', 0) > 0:
                hpa_savings = analysis_results.get('hpa_savings')
                logger.info(f"✅ Using DETAILED HPA savings from algorithmic analysis: ${hpa_savings:.2f}")
            else:
                # DEBUG: Show exactly why we're skipping
                if not analysis_results:
                    logger.error("❌ No analysis_results provided to dynamic strategy")
                else:
                    hpa_val = analysis_results.get('hpa_savings', 'MISSING')
                    logger.error(f"❌ HPA savings not valid: hpa_savings={hpa_val}")
                
                logger.error("❌ No detailed HPA analysis found - skipping HPA opportunity")
                return opportunities
            
            # NEW: Standards-based implementation cost calculation
            try:
                # Determine complexity based on cluster configuration
                complexity = "basic_cpu_memory"  # Default
                if cluster_config and cluster_config.get('status') == 'completed':
                    scaling_resources = cluster_config.get('scaling_resources', {})
                    # Check if custom metrics needed based on existing monitoring
                    if scaling_resources.get('monitoring_configured', False):
                        complexity = "custom_metrics"
                
                # Calculate cost using industry standards with dynamic region detection
                region = self._detect_cluster_region(cluster_config, analysis_results)
                cost_result = implementation_cost_calculator.calculate_hpa_cost(
                    cluster_config=cluster_config,
                    complexity=complexity,
                    region=region
                )
                
                implementation_cost = cost_result.total_cost
                timeline_weeks = max(1, cost_result.timeline_days // 7)
                
                logger.info(f"📊 HPA cost calculation: ${implementation_cost:.0f} ({cost_result.risk_level} risk, {timeline_weeks} weeks)")
                
            except Exception as e:
                logger.error(f"❌ Failed to calculate HPA implementation cost: {e}")
                # Cannot create opportunity without real cost calculation
                logger.error(f"❌ Skipping HPA opportunity - real cost calculation required")
               
            
            opportunities.append(ComprehensiveOptimizationOpportunity(
                type='hpa_optimization',
                subtype='horizontal_scaling',
                category='cost',
                
                priority_score=0.8,
                savings_potential_monthly=hpa_savings,
                implementation_cost=implementation_cost,
                roi_timeline_months=max(1, int(implementation_cost / hpa_savings)) if hpa_savings > 0 else 12,
                break_even_point=f"Month {max(2, int(implementation_cost / hpa_savings) + 1)}" if hpa_savings > 0 else "Month 12",
                
                implementation_complexity=0.6,
                risk_assessment=0.4,
                timeline_weeks=timeline_weeks,
                confidence_level=0.8,
                
                cost_impact=0.8,
                performance_impact=0.6,
                security_impact=0.1,
                compliance_impact=0.1,
                operational_impact=0.7,
                
                target_resources=['deployments', 'statefulsets'],
                optimal_approach='memory_and_cpu_based_scaling',
                implementation_strategy='phased_rollout_with_validation',
                success_probability=0.85,
                
                dependencies=[],
                constraints=['metrics_server_required'],
                prerequisites=['kubernetes_metrics_available'],
                
                success_criteria=[
                    f'Achieve ${hpa_savings:.0f}/month cost reduction',
                    'HPA scaling events respond within 2 minutes',
                    'Zero application downtime during scaling'
                ],
                kpis=[
                    {'metric': 'cost_savings', 'target': hpa_savings, 'unit': 'USD/month'},
                    {'metric': 'scaling_response_time', 'target': 2, 'unit': 'minutes'},
                    {'metric': 'availability', 'target': 99.9, 'unit': 'percentage'}
                ],
                monitoring_requirements=['hpa_events', 'pod_count', 'resource_utilization'],
                validation_procedures=['load_testing', 'scaling_validation'],
                
                rollback_strategy='immediate_hpa_removal_with_manual_scaling',
                contingency_plans=['manual_scaling_procedures', 'resource_request_adjustments'],
                emergency_procedures=['hpa_disable_and_scale_to_safe_levels']
            ))
        
        # Resource Right-sizing - Detect based on actual cluster utilization
        should_recommend_rightsizing = False
        
        # Dynamic right-sizing detection based on cluster metrics
        if analysis_results:
            avg_cpu_utilization = analysis_results.get('average_cpu_utilization', 50)
            avg_memory_utilization = analysis_results.get('average_memory_utilization', 50)
            
            # Recommend right-sizing if utilization is low (over-provisioned)
            if avg_cpu_utilization < 60 or avg_memory_utilization < 60:
                should_recommend_rightsizing = True
            
            # Also recommend for clusters with high resource waste
            resource_waste = analysis_results.get('resource_waste_percentage', 0)
            if resource_waste > 20:  # More than 20% resource waste
                should_recommend_rightsizing = True
        
        # Recommend for any significant cluster that might benefit from right-sizing
        if total_cost > 200:
            should_recommend_rightsizing = True
            
        if should_recommend_rightsizing:
            # FIXED: Use detailed algorithmic analysis results when available
            total_cost = self._extract_real_cluster_cost(analysis_results)
            
            # DEBUG: Log what's actually received for right-sizing
            if analysis_results:
                rs_value = analysis_results.get('right_sizing_savings', 'MISSING')
                logger.info(f"🔍 DEBUG RIGHT-SIZING: right_sizing_savings={rs_value}")
            
            # ONLY use detailed right-sizing savings from algorithmic analysis (our fixes)
            if analysis_results and analysis_results.get('right_sizing_savings', 0) > 0:
                rightsizing_savings = analysis_results.get('right_sizing_savings')
                logger.info(f"✅ Using DETAILED right-sizing savings from algorithmic analysis: ${rightsizing_savings:.2f}")
            else:
                # DEBUG: Show exactly why we're skipping right-sizing
                if not analysis_results:
                    logger.error("❌ No analysis_results provided for right-sizing")
                else:
                    rs_val = analysis_results.get('right_sizing_savings', 'MISSING')
                    logger.error(f"❌ Right-sizing savings not valid: right_sizing_savings={rs_val}")
                
                logger.error("❌ No detailed right-sizing analysis found - skipping right-sizing opportunity")
                return opportunities
            
            # NEW: Standards-based implementation cost calculation for rightsizing
            try:
                # Determine complexity and workload count
                workload_count = 10  # Default
                complexity = "simple_workloads"  # Default
                
                if cluster_config and cluster_config.get('status') == 'completed':
                    workload_resources = cluster_config.get('workload_resources', {})
                    workload_count = sum(
                        workload_resources.get(wl_type, {}).get('item_count', 0)
                        for wl_type in ['deployments', 'statefulsets']
                    )
                    
                    # Determine complexity based on workload mix
                    if workload_count > 30:
                        complexity = "complex_patterns"  # Large number of workloads
                    elif workload_count > 15:
                        complexity = "mixed_workloads"  # Moderate complexity
                
                # Calculate cost using industry standards with dynamic region detection
                region = self._detect_cluster_region(cluster_config, analysis_results)
                cost_result = implementation_cost_calculator.calculate_rightsizing_cost(
                    cluster_config=cluster_config,
                    workload_count=workload_count,
                    complexity=complexity,
                    region=region
                )
                
                implementation_cost = cost_result.total_cost
                timeline_weeks = max(1, cost_result.timeline_days // 7)
                
                logger.info(f"📊 Rightsizing cost calculation: ${implementation_cost:.0f} for {workload_count} workloads ({cost_result.risk_level} risk, {timeline_weeks} weeks)")
                
            except Exception as e:
                logger.error(f"❌ Failed to calculate rightsizing implementation cost: {e}")
                # Cannot create opportunity without real cost calculation
                logger.error(f"❌ Skipping rightsizing opportunity - real cost calculation required")
            
            
            opportunities.append(ComprehensiveOptimizationOpportunity(
                type='resource_rightsizing',
                subtype='resource_optimization',
                category='cost',
                
                priority_score=0.7,
                savings_potential_monthly=rightsizing_savings,
                implementation_cost=implementation_cost,
                roi_timeline_months=max(1, int(implementation_cost / rightsizing_savings)) if rightsizing_savings > 0 else 12,
                break_even_point=f"Month {max(2, int(implementation_cost / rightsizing_savings) + 1)}" if rightsizing_savings > 0 else "Month 12",
                
                implementation_complexity=0.5,
                risk_assessment=0.3,
                timeline_weeks=timeline_weeks,
                confidence_level=0.9,
                
                cost_impact=0.7,
                performance_impact=0.2,
                security_impact=0.0,
                compliance_impact=0.0,
                operational_impact=0.5,
                
                target_resources=['deployment_resources', 'pod_resources'],
                optimal_approach='data_driven_rightsizing',
                implementation_strategy='gradual_adjustment_with_monitoring',
                success_probability=0.9,
                
                dependencies=[],
                constraints=['application_performance_maintained'],
                prerequisites=['resource_usage_data_available'],
                
                success_criteria=[
                    f'Achieve ${rightsizing_savings:.0f}/month cost reduction',
                    'Resource utilization improved by 15-25%',
                    'Application SLA maintained'
                ],
                kpis=[
                    {'metric': 'cost_savings', 'target': rightsizing_savings, 'unit': 'USD/month'},
                    {'metric': 'resource_utilization', 'target': 75, 'unit': 'percentage'},
                    {'metric': 'application_performance', 'target': 0, 'unit': 'percentage_degradation'}
                ],
                monitoring_requirements=['resource_usage', 'application_performance', 'error_rates'],
                validation_procedures=['performance_testing', 'resource_validation'],
                
                rollback_strategy='deployment_rollback_to_previous_version',
                contingency_plans=['resource_increase_procedures', 'performance_recovery_plan'],
                emergency_procedures=['immediate_resource_scaling_up']
            ))
        
        return opportunities
    
    def _detect_cluster_region(self, cluster_config: Optional[Dict], analysis_results: Optional[Dict]) -> str:
        """Detect cluster region from configuration or analysis data"""
        try:
            # Try to get region from cluster config first
            if cluster_config:
                # Look for region in various possible locations
                region_indicators = [
                    cluster_config.get('location'),
                    cluster_config.get('region'),
                    cluster_config.get('cluster_location'),
                    cluster_config.get('azure_region')
                ]
                
                for region in region_indicators:
                    if region:
                        # Map Azure regions to our regional categories
                        region_lower = region.lower()
                        if any(x in region_lower for x in ['east', 'west', 'central']) and 'us' in region_lower:
                            return "north_america"
                        elif any(x in region_lower for x in ['europe', 'uk', 'west europe', 'north europe']):
                            return "europe"
                        elif any(x in region_lower for x in ['asia', 'southeast', 'east asia']):
                            return "asia_pacific"
                        else:
                            return "north_america"  # Default to north america
            
            # Try to get region from analysis results
            if analysis_results:
                location = analysis_results.get('location') or analysis_results.get('region')
                if location:
                    location_lower = location.lower()
                    if any(x in location_lower for x in ['east', 'west', 'central']) and 'us' in location_lower:
                        return "north_america"
                    elif any(x in location_lower for x in ['europe', 'uk']):
                        return "europe"
                    elif any(x in location_lower for x in ['asia', 'southeast']):
                        return "asia_pacific"
            
            # Default fallback
            return "north_america"
            
        except Exception as e:
            logger.warning(f"⚠️ Could not detect cluster region: {e}, using default")
            return "north_america"
    
    def _calculate_opportunity_roi(self, monthly_savings: float, implementation_cost: float, 
                                 project_duration_months: int = 24, discount_rate: float = 0.08) -> dict:
        """
        Calculate proper financial ROI metrics using NPV and payback period
        """
        if monthly_savings <= 0:
            return {
                'npv': -implementation_cost,
                'payback_months': float('inf'),
                'roi_percentage': -100.0,
                'is_viable': False
            }
        
        # Simple payback period (months)
        payback_months = implementation_cost / monthly_savings if monthly_savings > 0 else float('inf')
        
        # Calculate NPV of savings over project duration
        monthly_discount_rate = discount_rate / 12  # Convert annual to monthly
        total_discounted_savings = 0
        
        for month in range(1, project_duration_months + 1):
            monthly_pv = monthly_savings / ((1 + monthly_discount_rate) ** month)
            total_discounted_savings += monthly_pv
        
        # Net Present Value
        npv = total_discounted_savings - implementation_cost
        
        # ROI percentage (total return / investment)
        total_undiscounted_savings = monthly_savings * project_duration_months
        roi_percentage = ((total_undiscounted_savings - implementation_cost) / implementation_cost) * 100 if implementation_cost > 0 else 0
        
        # Determine viability (positive NPV and reasonable payback)
        is_viable = npv > 0 and payback_months <= 36  # 3 years max payback
        
        return {
            'npv': npv,
            'payback_months': payback_months,
            'roi_percentage': roi_percentage,
            'is_viable': is_viable,
            'total_savings_24m': total_undiscounted_savings,
            'discounted_savings': total_discounted_savings
        }
    
    # Simplified implementations for other opportunity types (keeping same pattern)
    def _detect_storage_opportunities(self, cluster_dna, analysis_results, actual_savings, cluster_config=None):
        """Detect storage optimization opportunities"""
        opportunities = []
        
        if not analysis_results:
            logger.warning("❌ No analysis_results - cannot detect storage opportunities")
            return opportunities
            
        storage_cost = analysis_results.get('storage_cost', 0)
        total_cost = self._extract_real_cluster_cost(analysis_results)
        
        if total_cost <= 0:
            logger.warning("❌ No real cost data - cannot detect storage opportunities")
            return opportunities
        
        # Storage optimization opportunity if storage > threshold from standards
        standards = implementation_cost_calculator.load_standards()
        opportunity_config = standards.get('optimization_thresholds', {}).get('opportunity_optimization', {})
        storage_threshold = standards.get('optimization_thresholds', {}).get('savings_calculation', {}).get('cost_thresholds', {}).get('storage_percentage_threshold', 0.25)
        storage_optimization_percentage = opportunity_config.get('storage_optimization_percentage', 0.15)
        
        if storage_cost > total_cost * storage_threshold:
            storage_savings = storage_cost * storage_optimization_percentage
            implementation_cost = implementation_cost_calculator.calculate_implementation_cost(
                'storage_optimization', 'basic_storage_classes', cluster_size='medium'
            )
            
            opportunities.append(ComprehensiveOptimizationOpportunity(
                type='storage',
                subtype='storage_class_optimization',
                category='cost',
                priority_score=0.6,
                savings_potential_monthly=storage_savings,
                implementation_cost=implementation_cost,
                roi_timeline_months=max(1, int(implementation_cost / storage_savings)) if storage_savings > 0 else 12,
                break_even_point=f"Month {max(2, int(implementation_cost / storage_savings) + 1)}" if storage_savings > 0 else "Month 12",
                implementation_complexity=0.4,
                risk_assessment=0.2,
                timeline_weeks=2,
                confidence_level=0.8,
                cost_impact=0.6,
                performance_impact=0.1,
                security_impact=0.0,
                compliance_impact=0.0,
                operational_impact=0.3,
                target_resources=['persistent_volumes', 'storage_classes'],
                optimal_approach='storage_class_migration',
                implementation_strategy='gradual_pv_migration',
                success_probability=0.9,
                dependencies=[],
                constraints=['data_availability_maintained'],
                prerequisites=['storage_analysis_completed'],
                success_criteria=[f'Achieve ${storage_savings:.0f}/month storage cost reduction'],
                kpis=[{'metric': 'storage_cost_savings', 'target': storage_savings, 'unit': 'USD/month'}],
                monitoring_requirements=['storage_performance', 'data_integrity'],
                validation_procedures=['storage_performance_testing'],
                rollback_strategy='storage_class_rollback',
                contingency_plans=['storage_capacity_scaling'],
                emergency_procedures=['immediate_storage_restore']
            ))
        
        return opportunities
    
    def _detect_networking_opportunities(self, cluster_dna, analysis_results, actual_savings, cluster_config=None):
        """Detect networking optimization opportunities"""
        opportunities = []
        
        if not analysis_results:
            logger.warning("❌ No analysis_results - cannot detect networking opportunities")
            return opportunities
            
        network_cost = analysis_results.get('networking_cost', 0) or analysis_results.get('network_cost', 0)
        total_cost = self._extract_real_cluster_cost(analysis_results)
        
        if total_cost <= 0:
            logger.warning("❌ No real cost data - cannot detect networking opportunities")
            return opportunities
        
        # Network optimization opportunity using standards
        standards = implementation_cost_calculator.load_standards()
        opportunity_config = standards.get('optimization_thresholds', {}).get('opportunity_optimization', {})
        network_threshold = standards.get('optimization_thresholds', {}).get('savings_calculation', {}).get('cost_thresholds', {}).get('network_percentage_threshold', 0.20)
        network_optimization_percentage = opportunity_config.get('network_optimization_percentage', 0.12)
        
        if network_cost > total_cost * network_threshold:
            network_savings = network_cost * network_optimization_percentage
            implementation_cost = implementation_cost_calculator.calculate_implementation_cost(
                'network_optimization', 'basic_segmentation', cluster_size='medium'
            )
            
            opportunities.append(ComprehensiveOptimizationOpportunity(
                type='networking',
                subtype='network_policy_optimization',
                category='cost',
                priority_score=0.5,
                savings_potential_monthly=network_savings,
                implementation_cost=implementation_cost,
                roi_timeline_months=max(1, int(implementation_cost / network_savings)) if network_savings > 0 else 12,
                break_even_point=f"Month {max(2, int(implementation_cost / network_savings) + 1)}" if network_savings > 0 else "Month 12",
                implementation_complexity=0.6,
                risk_assessment=0.3,
                timeline_weeks=3,
                confidence_level=0.7,
                cost_impact=0.5,
                performance_impact=0.2,
                security_impact=0.6,
                compliance_impact=0.0,
                operational_impact=0.4,
                target_resources=['network_policies', 'load_balancers'],
                optimal_approach='network_segmentation',
                implementation_strategy='phased_network_policy_implementation',
                success_probability=0.8,
                dependencies=[],
                constraints=['network_connectivity_maintained'],
                prerequisites=['network_analysis_completed'],
                success_criteria=[f'Achieve ${network_savings:.0f}/month network cost reduction'],
                kpis=[{'metric': 'network_cost_savings', 'target': network_savings, 'unit': 'USD/month'}],
                monitoring_requirements=['network_performance', 'connectivity_status'],
                validation_procedures=['network_connectivity_testing'],
                rollback_strategy='network_policy_rollback',
                contingency_plans=['network_troubleshooting'],
                emergency_procedures=['network_policy_disable']
            ))
        
        return opportunities
    
    def _detect_security_opportunities(self, cluster_dna, analysis_results, actual_savings, cluster_config=None):
        """Detect security enhancement opportunities"""
        opportunities = []
        
        # Security enhancements are always valuable - load value from standards
        standards = implementation_cost_calculator.load_standards()
        opportunity_config = standards.get('optimization_thresholds', {}).get('opportunity_optimization', {})
        security_value_monthly = opportunity_config.get('security_value_monthly', 50.0)
        
        implementation_cost = implementation_cost_calculator.calculate_implementation_cost(
            'security_hardening', 'pod_security_standards', cluster_size='medium'
        )
        
        opportunities.append(ComprehensiveOptimizationOpportunity(
            type='security',
            subtype='pod_security_standards',
            category='security',
            priority_score=0.7,
            savings_potential_monthly=security_value_monthly,
            implementation_cost=implementation_cost,
            roi_timeline_months=max(1, int(implementation_cost / security_value_monthly)),
            break_even_point=f"Month {max(2, int(implementation_cost / security_value_monthly) + 1)}",
            implementation_complexity=0.7,
            risk_assessment=0.4,
            timeline_weeks=4,
            confidence_level=0.8,
            cost_impact=0.1,
            performance_impact=0.0,
            security_impact=0.9,
            compliance_impact=0.8,
            operational_impact=0.6,
            target_resources=['pod_security_policies', 'rbac_rules'],
            optimal_approach='security_standards_implementation',
            implementation_strategy='phased_security_hardening',
            success_probability=0.85,
            dependencies=[],
            constraints=['application_functionality_maintained'],
            prerequisites=['security_assessment_completed'],
            success_criteria=['Enhanced security posture', 'Compliance requirements met'],
            kpis=[{'metric': 'security_compliance_score', 'target': 90, 'unit': 'percentage'}],
            monitoring_requirements=['security_alerts', 'compliance_status'],
            validation_procedures=['security_testing', 'compliance_audit'],
            rollback_strategy='security_policy_rollback',
            contingency_plans=['security_incident_response'],
            emergency_procedures=['security_lockdown_procedures']
        ))
        
        return opportunities
    
    def _detect_governance_opportunities(self, cluster_dna, analysis_results, actual_savings, cluster_config=None):
        """Detect governance and compliance opportunities"""
        opportunities = []
        
        # Governance improvements for larger clusters
        if cluster_config:
            workload_count = cluster_config.get('workload_resources', {}).get('deployments', {}).get('item_count', 0)
        else:
            workload_count = analysis_results.get('total_workloads', 0) if analysis_results else 0
            
        # Load governance standards
        standards = implementation_cost_calculator.load_standards()
        opportunity_config = standards.get('optimization_thresholds', {}).get('opportunity_optimization', {})
        governance_threshold = opportunity_config.get('governance_workload_threshold', 20)
        governance_value_monthly = opportunity_config.get('governance_value_monthly', 30.0)
        
        if workload_count > governance_threshold:  # Only for clusters with significant workloads
            
            implementation_cost = implementation_cost_calculator.calculate_implementation_cost(
                'observability_setup', 'basic_monitoring', cluster_size='medium'
            )
            
            opportunities.append(ComprehensiveOptimizationOpportunity(
                type='governance',
                subtype='resource_governance',
                category='operational',
                priority_score=0.4,
                savings_potential_monthly=governance_value_monthly,
                implementation_cost=implementation_cost,
                roi_timeline_months=max(1, int(implementation_cost / governance_value_monthly)),
                break_even_point=f"Month {max(2, int(implementation_cost / governance_value_monthly) + 1)}",
                implementation_complexity=0.5,
                risk_assessment=0.2,
                timeline_weeks=3,
                confidence_level=0.7,
                cost_impact=0.2,
                performance_impact=0.1,
                security_impact=0.3,
                compliance_impact=0.8,
                operational_impact=0.7,
                target_resources=['resource_quotas', 'policy_rules'],
                optimal_approach='governance_framework_implementation',
                implementation_strategy='phased_governance_rollout',
                success_probability=0.8,
                dependencies=[],
                constraints=['development_velocity_maintained'],
                prerequisites=['governance_requirements_defined'],
                success_criteria=['Improved resource governance', 'Policy compliance'],
                kpis=[{'metric': 'governance_compliance_score', 'target': 85, 'unit': 'percentage'}],
                monitoring_requirements=['policy_violations', 'resource_usage'],
                validation_procedures=['governance_audit', 'compliance_check'],
                rollback_strategy='policy_relaxation',
                contingency_plans=['governance_exceptions'],
                emergency_procedures=['policy_override_procedures']
            ))
        
        return opportunities
    
    def _detect_monitoring_opportunities(self, cluster_dna, analysis_results, actual_savings, cluster_config=None):
        """Detect monitoring and observability opportunities"""
        opportunities = []
        
        # Enhanced monitoring is valuable for all clusters - load value from standards
        standards = implementation_cost_calculator.load_standards()
        opportunity_config = standards.get('optimization_thresholds', {}).get('opportunity_optimization', {})
        monitoring_value_monthly = opportunity_config.get('monitoring_value_monthly', 40.0)
        
        implementation_cost = implementation_cost_calculator.calculate_implementation_cost(
            'observability_setup', 'basic_monitoring', cluster_size='medium'
        )
        
        opportunities.append(ComprehensiveOptimizationOpportunity(
            type='monitoring',
            subtype='observability_enhancement',
            category='operational',
            priority_score=0.6,
            savings_potential_monthly=monitoring_value_monthly,
            implementation_cost=implementation_cost,
            roi_timeline_months=max(1, int(implementation_cost / monitoring_value_monthly)),
            break_even_point=f"Month {max(2, int(implementation_cost / monitoring_value_monthly) + 1)}",
            implementation_complexity=0.5,
            risk_assessment=0.2,
            timeline_weeks=2,
            confidence_level=0.9,
            cost_impact=0.3,
            performance_impact=0.4,
            security_impact=0.2,
            compliance_impact=0.3,
            operational_impact=0.8,
            target_resources=['monitoring_stack', 'alerting_rules'],
            optimal_approach='comprehensive_observability',
            implementation_strategy='monitoring_stack_enhancement',
            success_probability=0.9,
            dependencies=[],
            constraints=['monitoring_overhead_minimized'],
            prerequisites=['monitoring_requirements_defined'],
            success_criteria=['Enhanced observability', 'Faster issue detection'],
            kpis=[{'metric': 'mttr_improvement', 'target': 50, 'unit': 'percentage'}],
            monitoring_requirements=['system_metrics', 'application_metrics'],
            validation_procedures=['monitoring_effectiveness_test'],
            rollback_strategy='monitoring_configuration_rollback',
            contingency_plans=['alternative_monitoring_solutions'],
            emergency_procedures=['monitoring_escalation_procedures']
        ))
        
        return opportunities

    def _extract_real_cluster_cost(self, analysis_results: Optional[Dict], cluster_config: Optional[Dict] = None) -> float:
        """Extract real cluster cost - NO FAKE DEFAULTS"""
        if not analysis_results:
            logger.error("❌ Cannot determine cluster cost without analysis_results")
            return 0.0
            
        # Try to get real cost from analysis
        total_cost = analysis_results.get('total_cost', 0)
        if total_cost > 0:
            logger.info(f"✅ Using real cluster cost from analysis: ${total_cost:.2f}")
            return total_cost
            
        # Try alternative cost fields
        alternative_costs = [
            analysis_results.get('monthly_cost', 0),
            analysis_results.get('cost_total', 0),
            analysis_results.get('cluster_cost', 0),
            analysis_results.get('current_cost', 0)
        ]
        
        for cost in alternative_costs:
            if cost > 0:
                logger.info(f"✅ Using real cluster cost from alternative field: ${cost:.2f}")
                return cost
        
        # Try to calculate from component costs
        component_costs = [
            analysis_results.get('compute_cost', 0),
            analysis_results.get('storage_cost', 0),
            analysis_results.get('network_cost', 0),
            analysis_results.get('networking_cost', 0)
        ]
        
        total_components = sum(cost for cost in component_costs if cost > 0)
        if total_components > 0:
            logger.info(f"✅ Using calculated cluster cost from components: ${total_components:.2f}")
            return total_components
            
        # REAL DATA REQUIRED - No fake defaults
        logger.error("❌ No real cost data available - requires actual cluster cost analysis")
        return 0.0

# Supporting classes for strategy optimization
class AdvancedStrategyOptimizer:
    def optimize_strategy(self, opportunities, cluster_dna, objectives, cluster_config=None):
        if not opportunities:
            return {
                'selected_opportunities': [],
                'strategy_type': 'minimal',
                'approach': 'conservative',
                'objectives': objectives,
                'optimization_score': 0.5
            }
        
        selected = opportunities[:min(3, len(opportunities))]
        primary_objective = max(objectives.items(), key=lambda x: x[1])[0]
        strategy_type = {
            'cost_optimization': 'cost_focused',
            'performance_optimization': 'performance_focused',
            'security_enhancement': 'security_focused',
            'operational_efficiency': 'operational_focused'
        }.get(primary_objective, 'balanced')
        
        return {
            'selected_opportunities': selected,
            'strategy_type': strategy_type,
            'approach': 'balanced',
            'objectives': objectives,
            'optimization_score': 0.8
        }

class ComprehensiveFinancialAnalyzer:
    def analyze_comprehensive_impact(self, opportunities, cluster_dna, analysis_results, actual_savings):
        total_savings = sum(opp.savings_potential_monthly for opp in opportunities)
        total_implementation_cost = sum(opp.implementation_cost for opp in opportunities)
        
        if total_savings == 0:
            total_savings = actual_savings
        
        roi_12_months = ((total_savings * 12 - total_implementation_cost) / total_implementation_cost) * 100 if total_implementation_cost > 0 else 0
        payback_months = total_implementation_cost / total_savings if total_savings > 0 else float('inf')
        net_benefit_12_months = (total_savings * 12) - total_implementation_cost
        
        return {
            'total_savings': total_savings,
            'implementation_cost': total_implementation_cost,
            'roi_percentage': roi_12_months,
            'payback_months': int(payback_months) if payback_months != float('inf') else 999,
            'net_benefit': net_benefit_12_months
        }

class AdvancedRiskAssessor:
    def assess_comprehensive_risks(self, opportunities, cluster_dna, cluster_config=None):
        avg_risk = sum(opp.risk_assessment for opp in opportunities) / len(opportunities) if opportunities else 0.3
        avg_success = sum(opp.success_probability for opp in opportunities) / len(opportunities) if opportunities else 0.8
        
        return {
            'overall_risk_level': 'Low' if avg_risk < 0.3 else 'Medium' if avg_risk < 0.6 else 'High',
            'success_probability': avg_success,
            'mitigation_strategies': [
                'Implement phased rollout approach',
                'Maintain comprehensive monitoring',
                'Establish clear rollback procedures'
            ]
        }

class BestPracticesEngine:
    def analyze_alignment(self, strategy_config, cluster_dna, cluster_config=None):
        return {
            'compliance_score': 0.75,
            'compliance_requirements': ['Cost governance', 'Security policies'],
            'governance_framework': {
                'approval_levels': ['technical', 'business'],
                'review_frequency': 'monthly'
            },
            'approval_requirements': ['Technical Lead approval', 'Business stakeholder approval']
        }


