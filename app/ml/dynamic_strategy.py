"""
Phase 2: Dynamic Strategy Generation Engine - STARTER CODE
==========================================================
Takes your cluster DNA and generates completely dynamic optimization strategies.
This is where the magic happens - turning DNA into executable plans!

INTEGRATION: Works with Phase 1 (Cluster DNA Analyzer)
PURPOSE: Generate unique strategies for each cluster personality
"""

import json
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Import from Phase 1
from app.ml.dna_analyzer import ClusterDNA, analyze_cluster_dna_from_analysis

logger = logging.getLogger(__name__)

# ============================================================================
# STRATEGY DATA STRUCTURES
# ============================================================================

@dataclass
class OptimizationOpportunity:
    """Dynamic optimization opportunity discovered from DNA"""
    type: str  # 'hpa_optimization', 'resource_rightsizing', 'storage_optimization', etc.
    priority_score: float  # 0.0 - 1.0
    savings_potential_monthly: float  # Dollar amount
    implementation_complexity: float  # 0.0 - 1.0
    risk_assessment: float  # 0.0 - 1.0
    timeline_weeks: int
    confidence_level: float  # 0.0 - 1.0
    
    # Strategy-specific data
    target_workloads: List[str]
    optimal_approach: str
    executable_commands: List[str]
    success_criteria: List[str]
    rollback_plan: List[str]

@dataclass 
class DynamicStrategy:
    """Complete dynamic strategy generated for specific cluster DNA"""
    strategy_name: str
    strategy_type: str  # 'conservative', 'aggressive', 'balanced'
    opportunities: List[OptimizationOpportunity]
    total_savings_potential: float
    total_timeline_weeks: int
    overall_risk_level: str
    success_probability: float
    
    # Execution plan
    implementation_phases: List[Dict]
    monitoring_requirements: List[str]
    success_metrics: List[str]
    
    # DNA-specific customizations
    cluster_personality_match: float
    strategy_uniqueness_score: float

# ============================================================================
# DYNAMIC STRATEGY GENERATION ENGINE
# ============================================================================

class DynamicStrategyEngine:
    """
    Main engine that generates unique strategies from cluster DNA
    NO TEMPLATES - Everything generated algorithmically
    """
    
    def __init__(self):
        self.opportunity_detector = OpportunityDetector()
        self.strategy_optimizer = StrategyOptimizer()
        self.command_generator = ExecutableCommandGenerator()
        self.success_predictor = SuccessPredictor()
        
        # Strategy generation patterns (learned from successful implementations)
        self.success_patterns = self._load_success_patterns()
        
    def generate_dynamic_strategy(self, cluster_dna: ClusterDNA, analysis_results: Optional[Dict] = None) -> DynamicStrategy:
        """
        MAIN METHOD: Generate completely dynamic strategy from cluster DNA
        """
        logger.info(f"🎯 Generating dynamic strategy for cluster personality: {cluster_dna.cluster_personality}")
        
        # Step 1: Detect optimization opportunities based on DNA
        opportunities = self.opportunity_detector.detect_opportunities_from_dna(cluster_dna)
        logger.info(f"🔍 Detected {len(opportunities)} optimization opportunities")
        
        # Step 2: Optimize opportunity combination using algorithms
        optimal_combination = self.strategy_optimizer.find_optimal_combination(opportunities, cluster_dna)
        logger.info(f"🧮 Optimal combination: {[opp.type for opp in optimal_combination]}")
        
        # Step 3: Generate executable commands for each opportunity
        for opportunity in optimal_combination:
            opportunity.executable_commands = self.command_generator.generate_commands(opportunity, cluster_dna)
            opportunity.success_criteria = self.command_generator.generate_success_criteria(opportunity, cluster_dna)
            opportunity.rollback_plan = self.command_generator.generate_rollback_plan(opportunity, cluster_dna)
        
        # Step 4: Create unified strategy
        strategy = self._assemble_unified_strategy(optimal_combination, cluster_dna)
        
        # Step 5: Predict success probability
        strategy.success_probability = self.success_predictor.predict_success(strategy, cluster_dna)
        
        logger.info(f"✅ Dynamic strategy generated: {strategy.strategy_name}")
        logger.info(f"💰 Total savings potential: ${strategy.total_savings_potential:.2f}/month")
        logger.info(f"📅 Timeline: {strategy.total_timeline_weeks} weeks")
        logger.info(f"🎲 Success probability: {strategy.success_probability:.1%}")
        
        return strategy
    
    def _load_success_patterns(self) -> Dict:
        """Load patterns from successful implementations (this would grow over time)"""
        return {
            'conservative_clusters': {
                'preferred_strategies': ['gradual_hpa', 'conservative_rightsizing'],
                'success_factors': ['high_monitoring', 'phased_rollout', 'extensive_testing'],
                'risk_tolerance': 0.3
            },
            'aggressive_clusters': {
                'preferred_strategies': ['aggressive_hpa', 'massive_rightsizing', 'node_optimization'],
                'success_factors': ['parallel_execution', 'automated_monitoring', 'rapid_iteration'],
                'risk_tolerance': 0.7
            },
            'network_heavy_clusters': {
                'preferred_strategies': ['compute_optimization', 'traffic_consolidation'],
                'success_factors': ['network_aware_scheduling', 'locality_optimization'],
                'risk_tolerance': 0.4
            }
        }
    
    def _assemble_unified_strategy(self, opportunities: List[OptimizationOpportunity], 
                                 cluster_dna: ClusterDNA) -> DynamicStrategy:
        """Assemble opportunities into unified strategy"""
        
        # Calculate strategy metadata
        total_savings = sum(opp.savings_potential_monthly for opp in opportunities)
        total_timeline = max(opp.timeline_weeks for opp in opportunities)  # Parallel execution
        avg_risk = sum(opp.risk_assessment for opp in opportunities) / len(opportunities)
        
        # Determine strategy type based on cluster DNA
        if 'conservative' in cluster_dna.cluster_personality:
            strategy_type = 'conservative'
            strategy_name = f"Conservative {self._get_primary_optimization_type(opportunities)} Optimization"
        elif 'aggressive' in cluster_dna.cluster_personality:
            strategy_type = 'aggressive'
            strategy_name = f"Aggressive Multi-Phase {self._get_primary_optimization_type(opportunities)}"
        else:
            strategy_type = 'balanced'
            strategy_name = f"Balanced {self._get_primary_optimization_type(opportunities)} Approach"
        
        # Generate implementation phases
        implementation_phases = self._generate_implementation_phases(opportunities, cluster_dna)
        
        # Generate monitoring requirements
        monitoring_requirements = self._generate_monitoring_requirements(opportunities, cluster_dna)
        
        # Generate success metrics
        success_metrics = self._generate_success_metrics(opportunities, total_savings)
        
        # Calculate personality match score
        personality_match = self._calculate_personality_match(opportunities, cluster_dna)
        
        # Calculate uniqueness score
        uniqueness_score = self._calculate_strategy_uniqueness(opportunities, cluster_dna)
        
        return DynamicStrategy(
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            opportunities=opportunities,
            total_savings_potential=total_savings,
            total_timeline_weeks=total_timeline,
            overall_risk_level=self._risk_score_to_level(avg_risk),
            success_probability=0.0,  # Will be calculated later
            implementation_phases=implementation_phases,
            monitoring_requirements=monitoring_requirements,
            success_metrics=success_metrics,
            cluster_personality_match=personality_match,
            strategy_uniqueness_score=uniqueness_score
        )
    
    def _get_primary_optimization_type(self, opportunities: List[OptimizationOpportunity]) -> str:
        """Get primary optimization type from opportunities"""
        if not opportunities:
            return "General"
        
        # Find opportunity with highest savings potential
        primary_opp = max(opportunities, key=lambda x: x.savings_potential_monthly)
        
        type_map = {
            'hpa_optimization': 'HPA',
            'resource_rightsizing': 'Right-sizing',
            'storage_optimization': 'Storage',
            'system_pool_optimization': 'System Pool'
        }
        
        return type_map.get(primary_opp.type, 'Multi-Component')
    
    def _generate_implementation_phases(self, opportunities: List[OptimizationOpportunity], 
                                      cluster_dna: ClusterDNA) -> List[Dict]:
        """Generate implementation phases with proper sequencing"""
        phases = []
        
        # Sort opportunities by priority and risk (low risk first for conservative)
        if 'conservative' in cluster_dna.cluster_personality:
            sorted_opportunities = sorted(opportunities, key=lambda x: (x.risk_assessment, -x.priority_score))
        else:
            sorted_opportunities = sorted(opportunities, key=lambda x: (-x.priority_score, x.risk_assessment))
        
        for i, opportunity in enumerate(sorted_opportunities):
            phase = {
                'phase_number': i + 1,
                'name': f"Phase {i + 1}: {opportunity.type.replace('_', ' ').title()}",
                'opportunity_type': opportunity.type,
                'duration_weeks': opportunity.timeline_weeks,
                'savings_potential': opportunity.savings_potential_monthly,
                'risk_level': self._risk_score_to_level(opportunity.risk_assessment),
                'target_workloads': opportunity.target_workloads,
                'executable_commands': opportunity.executable_commands,
                'success_criteria': opportunity.success_criteria,
                'rollback_plan': opportunity.rollback_plan
            }
            phases.append(phase)
        
        return phases
    
    def _generate_monitoring_requirements(self, opportunities: List[OptimizationOpportunity], 
                                        cluster_dna: ClusterDNA) -> List[str]:
        """Generate monitoring requirements based on opportunities and cluster DNA"""
        requirements = []
        
        # Base monitoring
        requirements.append("Monitor cluster-wide cost trends daily")
        requirements.append("Track resource utilization changes")
        
        # Opportunity-specific monitoring
        for opportunity in opportunities:
            if opportunity.type == 'hpa_optimization':
                requirements.append("Monitor HPA scaling events and pod count changes")
                requirements.append("Track application performance during scaling")
            elif opportunity.type == 'resource_rightsizing':
                requirements.append("Monitor resource utilization after right-sizing")
                requirements.append("Track application error rates and response times")
            elif opportunity.type == 'storage_optimization':
                requirements.append("Monitor storage I/O performance")
                requirements.append("Track storage cost reductions")
        
        # Cluster personality-specific monitoring
        if 'conservative' in cluster_dna.cluster_personality:
            requirements.append("Implement conservative alerting with low thresholds")
            requirements.append("Daily review of all optimization metrics")
        elif 'aggressive' in cluster_dna.cluster_personality:
            requirements.append("Implement automated monitoring with quick recovery")
            requirements.append("Real-time performance tracking")
        
        return requirements
    
    def _generate_success_metrics(self, opportunities: List[OptimizationOpportunity], 
                                total_savings: float) -> List[str]:
        """Generate success metrics for the strategy"""
        metrics = [
            f"Achieve ${total_savings:.2f}/month cost reduction",
            "Maintain application SLA > 99.9%",
            "Zero critical incidents during implementation",
            "Resource utilization improvement > 15%"
        ]
        
        # Add opportunity-specific metrics
        for opportunity in opportunities:
            if opportunity.type == 'hpa_optimization':
                metrics.append("HPA scaling events responding to load within 2 minutes")
            elif opportunity.type == 'resource_rightsizing':
                metrics.append("Application performance degradation < 5%")
        
        return metrics
    
    def _calculate_personality_match(self, opportunities: List[OptimizationOpportunity], 
                                   cluster_dna: ClusterDNA) -> float:
        """Calculate how well the strategy matches cluster personality"""
        match_factors = []
        
        personality = cluster_dna.cluster_personality
        
        # Conservative cluster personality matching
        if 'conservative' in personality:
            avg_risk = sum(opp.risk_assessment for opp in opportunities) / len(opportunities)
            match_factors.append(1.0 - avg_risk)  # Lower risk = better match
        
        # HPA-ready personality matching
        if 'hpa-ready' in personality:
            hpa_opportunities = [opp for opp in opportunities if opp.type == 'hpa_optimization']
            match_factors.append(len(hpa_opportunities) / len(opportunities))
        
        # Network-heavy personality matching
        if 'network-heavy' in personality:
            # Strategy should focus on compute optimization, not network changes
            compute_opportunities = [opp for opp in opportunities if 'resource' in opp.type or 'hpa' in opp.type]
            match_factors.append(len(compute_opportunities) / len(opportunities))
        
        return sum(match_factors) / len(match_factors) if match_factors else 0.7
    
    def _calculate_strategy_uniqueness(self, opportunities: List[OptimizationOpportunity], 
                                     cluster_dna: ClusterDNA) -> float:
        """Calculate how unique this strategy is"""
        uniqueness_factors = []
        
        # Opportunity combination uniqueness
        opp_types = sorted([opp.type for opp in opportunities])
        combination_hash = hash(tuple(opp_types))
        uniqueness_factors.append((combination_hash % 1000) / 1000)  # Normalize hash
        
        # Cluster DNA uniqueness contribution
        uniqueness_factors.append(cluster_dna.uniqueness_score)
        
        # Timeline uniqueness
        total_timeline = sum(opp.timeline_weeks for opp in opportunities)
        timeline_uniqueness = min(1.0, abs(total_timeline - 6) / 10)  # Deviation from average
        uniqueness_factors.append(timeline_uniqueness)
        
        return sum(uniqueness_factors) / len(uniqueness_factors)
    
    def _risk_score_to_level(self, risk_score: float) -> str:
        """Convert risk score to level string"""
        if risk_score > 0.7:
            return "High"
        elif risk_score > 0.4:
            return "Medium"
        else:
            return "Low"

# ============================================================================
# OPPORTUNITY DETECTOR
# ============================================================================

class OpportunityDetector:
    """Detects optimization opportunities from cluster DNA patterns"""
    
    def detect_opportunities_from_dna(self, cluster_dna: ClusterDNA) -> List[OptimizationOpportunity]:
        """Main method to detect opportunities from cluster DNA"""
        opportunities = []
        
        # Detect HPA opportunities
        hpa_opp = self._detect_hpa_opportunity(cluster_dna)
        if hpa_opp:
            opportunities.append(hpa_opp)
        
        # Detect right-sizing opportunities
        rightsizing_opp = self._detect_rightsizing_opportunity(cluster_dna)
        if rightsizing_opp:
            opportunities.append(rightsizing_opp)
        
        # Detect storage opportunities
        storage_opp = self._detect_storage_opportunity(cluster_dna)
        if storage_opp:
            opportunities.append(storage_opp)
        
        # Detect system pool opportunities
        system_opp = self._detect_system_pool_opportunity(cluster_dna)
        if system_opp:
            opportunities.append(system_opp)
        
        return opportunities
    
    def _detect_hpa_opportunity(self, cluster_dna: ClusterDNA) -> Optional[OptimizationOpportunity]:
        """Detect HPA optimization opportunity from DNA"""
        
        if 'hpa_optimization' not in cluster_dna.optimization_hotspots:
            return None
        
        # Calculate opportunity parameters from DNA
        auto_scaling_potential = cluster_dna.scaling_characteristics.get('auto_scaling_potential', 0.5)
        
        if auto_scaling_potential < 0.3:
            return None
        
        # Determine optimal approach based on cluster personality
        if 'conservative' in cluster_dna.cluster_personality:
            optimal_approach = 'memory_focused_conservative_hpa'
            risk_assessment = 0.3
            timeline_weeks = 3
        elif 'variable-workload' in cluster_dna.cluster_personality:
            optimal_approach = 'aggressive_dual_metric_hpa'
            risk_assessment = 0.6
            timeline_weeks = 2
        else:
            optimal_approach = 'balanced_memory_cpu_hpa'
            risk_assessment = 0.4
            timeline_weeks = 3
        
        # Calculate savings potential (this would come from the original analysis)
        savings_potential = cluster_dna.cost_distribution.get('compute_percentage', 20) * 0.15  # 15% of compute costs
        
        # Priority based on savings potential and auto-scaling readiness
        priority_score = (auto_scaling_potential * 0.6) + (min(savings_potential / 100, 1.0) * 0.4)
        
        return OptimizationOpportunity(
            type='hpa_optimization',
            priority_score=priority_score,
            savings_potential_monthly=savings_potential,
            implementation_complexity=0.4,
            risk_assessment=risk_assessment,
            timeline_weeks=timeline_weeks,
            confidence_level=cluster_dna.optimization_readiness_score,
            target_workloads=self._identify_hpa_target_workloads(cluster_dna),
            optimal_approach=optimal_approach,
            executable_commands=[],  # Will be generated later
            success_criteria=[],     # Will be generated later
            rollback_plan=[]         # Will be generated later
        )
    
    def _detect_rightsizing_opportunity(self, cluster_dna: ClusterDNA) -> Optional[OptimizationOpportunity]:
        """Detect right-sizing opportunity from DNA"""
        
        if 'resource_rightsizing' not in cluster_dna.optimization_hotspots:
            return None
        
        # Calculate waste from efficiency patterns
        cpu_gap = cluster_dna.efficiency_patterns.get('cpu_gap', 0)
        memory_gap = cluster_dna.efficiency_patterns.get('memory_gap', 0)
        avg_gap = (cpu_gap + memory_gap) / 2
        
        if avg_gap < 10:  # Less than 10% waste
            return None
        
        # Determine approach based on waste pattern
        if cpu_gap > memory_gap + 15:
            optimal_approach = 'cpu_focused_rightsizing'
        elif memory_gap > cpu_gap + 15:
            optimal_approach = 'memory_focused_rightsizing'
        else:
            optimal_approach = 'balanced_rightsizing'
        
        # Calculate parameters
        savings_potential = avg_gap * 2  # Estimate 2% savings per 1% waste
        priority_score = min(1.0, avg_gap / 50)  # Normalize to 50% max waste
        risk_assessment = min(0.8, avg_gap / 100)  # Higher waste = higher risk
        
        return OptimizationOpportunity(
            type='resource_rightsizing',
            priority_score=priority_score,
            savings_potential_monthly=savings_potential,
            implementation_complexity=0.3,
            risk_assessment=risk_assessment,
            timeline_weeks=2,
            confidence_level=cluster_dna.optimization_readiness_score,
            target_workloads=self._identify_rightsizing_target_workloads(cluster_dna),
            optimal_approach=optimal_approach,
            executable_commands=[],
            success_criteria=[],
            rollback_plan=[]
        )
    
    def _detect_storage_opportunity(self, cluster_dna: ClusterDNA) -> Optional[OptimizationOpportunity]:
        """Detect storage optimization opportunity from DNA"""
        
        storage_percentage = cluster_dna.cost_distribution.get('storage_percentage', 0)
        
        if storage_percentage < 10:  # Less than 10% of costs
            return None
        
        savings_potential = storage_percentage * 0.3  # 30% of storage costs optimizable
        
        if savings_potential < 5:  # Less than $5 savings
            return None
        
        return OptimizationOpportunity(
            type='storage_optimization',
            priority_score=0.6,
            savings_potential_monthly=savings_potential,
            implementation_complexity=0.2,
            risk_assessment=0.2,
            timeline_weeks=1,
            confidence_level=0.8,
            target_workloads=[],
            optimal_approach='storage_class_optimization',
            executable_commands=[],
            success_criteria=[],
            rollback_plan=[]
        )
    
    def _detect_system_pool_opportunity(self, cluster_dna: ClusterDNA) -> Optional[OptimizationOpportunity]:
        """Detect system pool optimization opportunity from DNA"""
        
        if 'system_pool_optimization' not in cluster_dna.optimization_hotspots:
            return None
        
        system_efficiency = cluster_dna.scaling_characteristics.get('system_efficiency', 1.0)
        
        if system_efficiency > 0.5:  # System pool is efficient enough
            return None
        
        # Calculate savings potential
        waste_percentage = (1.0 - system_efficiency) * 100
        savings_potential = waste_percentage * 0.5  # Conservative estimate
        
        return OptimizationOpportunity(
            type='system_pool_optimization',
            priority_score=0.8,  # High priority for obvious waste
            savings_potential_monthly=savings_potential,
            implementation_complexity=0.5,
            risk_assessment=0.4,  # Medium risk for system components
            timeline_weeks=2,
            confidence_level=0.9,
            target_workloads=[],
            optimal_approach='system_node_consolidation',
            executable_commands=[],
            success_criteria=[],
            rollback_plan=[]
        )
    
    def _identify_hpa_target_workloads(self, cluster_dna: ClusterDNA) -> List[str]:
        """Identify workloads suitable for HPA based on DNA"""
        # This would analyze workload patterns from the DNA
        # For now, return top cost workloads
        return ['high-cost-workload-1', 'variable-load-workload-2']
    
    def _identify_rightsizing_target_workloads(self, cluster_dna: ClusterDNA) -> List[str]:
        """Identify workloads suitable for right-sizing based on DNA"""
        # This would analyze resource waste patterns
        return ['over-provisioned-workload-1', 'wasteful-workload-2']

# ============================================================================
# STRATEGY OPTIMIZER
# ============================================================================

class StrategyOptimizer:
    """Optimizes combination of opportunities using algorithmic approaches"""
    
    def find_optimal_combination(self, opportunities: List[OptimizationOpportunity], 
                               cluster_dna: ClusterDNA) -> List[OptimizationOpportunity]:
        """Find optimal combination of opportunities using constraint optimization"""
        
        if not opportunities:
            return []
        
        # Generate all feasible combinations
        feasible_combinations = self._generate_feasible_combinations(opportunities, cluster_dna)
        
        # Score each combination
        scored_combinations = []
        for combination in feasible_combinations:
            score = self._score_combination(combination, cluster_dna)
            scored_combinations.append((score, combination))
        
        # Return best combination
        if scored_combinations:
            best_score, best_combination = max(scored_combinations, key=lambda x: x[0])
            logger.info(f"🎯 Optimal combination score: {best_score:.3f}")
            return best_combination
        
        return opportunities  # Fallback to all opportunities
    
    def _generate_feasible_combinations(self, opportunities: List[OptimizationOpportunity], 
                                      cluster_dna: ClusterDNA) -> List[List[OptimizationOpportunity]]:
        """Generate all feasible combinations of opportunities"""
        combinations = []
        
        # Single opportunities
        for opp in opportunities:
            combinations.append([opp])
        
        # Pairs
        for i, opp1 in enumerate(opportunities):
            for j, opp2 in enumerate(opportunities[i+1:], i+1):
                if self._are_compatible(opp1, opp2, cluster_dna):
                    combinations.append([opp1, opp2])
        
        # Triples (if cluster can handle complexity)
        if self._can_handle_complex_strategy(cluster_dna):
            for i, opp1 in enumerate(opportunities):
                for j, opp2 in enumerate(opportunities[i+1:], i+1):
                    for k, opp3 in enumerate(opportunities[j+1:], j+1):
                        if (self._are_compatible(opp1, opp2, cluster_dna) and 
                            self._are_compatible(opp1, opp3, cluster_dna) and
                            self._are_compatible(opp2, opp3, cluster_dna)):
                            combinations.append([opp1, opp2, opp3])
        
        return combinations
    
    def _are_compatible(self, opp1: OptimizationOpportunity, opp2: OptimizationOpportunity, 
                       cluster_dna: ClusterDNA) -> bool:
        """Check if two opportunities can be implemented together"""
        
        # Risk compatibility
        combined_risk = (opp1.risk_assessment + opp2.risk_assessment) / 2
        if 'conservative' in cluster_dna.cluster_personality and combined_risk > 0.5:
            return False
        
        # Timeline compatibility
        if abs(opp1.timeline_weeks - opp2.timeline_weeks) > 3:
            return False  # Too different timelines
        
        # Resource conflict check
        if (opp1.type == 'hpa_optimization' and opp2.type == 'resource_rightsizing' and
            any(workload in opp2.target_workloads for workload in opp1.target_workloads)):
            return False  # Same workloads targeted by both
        
        return True
    
    def _can_handle_complex_strategy(self, cluster_dna: ClusterDNA) -> bool:
        """Check if cluster can handle complex multi-opportunity strategies"""
        
        # Conservative clusters prefer simpler strategies
        if 'conservative' in cluster_dna.cluster_personality:
            return False
        
        # Enterprise clusters can handle complexity
        if 'enterprise' in cluster_dna.cluster_personality:
            return True
        
        # High automation readiness can handle complexity
        if cluster_dna.automation_readiness_category == 'automation_ready':
            return True
        
        return False
    
    def _score_combination(self, combination: List[OptimizationOpportunity], 
                          cluster_dna: ClusterDNA) -> float:
        """Score a combination of opportunities"""
        
        if not combination:
            return 0.0
        
        # Calculate component scores
        total_savings = sum(opp.savings_potential_monthly for opp in combination)
        avg_priority = sum(opp.priority_score for opp in combination) / len(combination)
        avg_risk = sum(opp.risk_assessment for opp in combination) / len(combination)
        avg_confidence = sum(opp.confidence_level for opp in combination) / len(combination)
        
        # Calculate synergy bonus
        synergy_bonus = self._calculate_synergy_bonus(combination)
        
        # Calculate personality match
        personality_match = self._calculate_combination_personality_match(combination, cluster_dna)
        
        # Weighted score calculation
        score = (
            (total_savings / 100) * 0.3 +     # Savings impact
            avg_priority * 0.25 +              # Priority
            (1 - avg_risk) * 0.2 +             # Risk (inverted)
            avg_confidence * 0.15 +            # Confidence
            synergy_bonus * 0.05 +             # Synergy
            personality_match * 0.05           # Personality match
        )
        
        return score
    
    def _calculate_synergy_bonus(self, combination: List[OptimizationOpportunity]) -> float:
        """Calculate synergy bonus for opportunity combinations"""
        if len(combination) <= 1:
            return 0.0
        
        synergy = 0.0
        
        # HPA + Right-sizing synergy
        has_hpa = any(opp.type == 'hpa_optimization' for opp in combination)
        has_rightsizing = any(opp.type == 'resource_rightsizing' for opp in combination)
        if has_hpa and has_rightsizing:
            synergy += 0.2
        
        # Storage + any other optimization
        has_storage = any(opp.type == 'storage_optimization' for opp in combination)
        if has_storage and len(combination) > 1:
            synergy += 0.1
        
        return synergy
    
    def _calculate_combination_personality_match(self, combination: List[OptimizationOpportunity], 
                                               cluster_dna: ClusterDNA) -> float:
        """Calculate how well combination matches cluster personality"""
        
        personality = cluster_dna.cluster_personality
        match_factors = []
        
        # Conservative personality matching
        if 'conservative' in personality:
            avg_risk = sum(opp.risk_assessment for opp in combination) / len(combination)
            match_factors.append(1.0 - avg_risk)
        
        # HPA-ready personality matching
        if 'hpa-ready' in personality:
            hpa_count = sum(1 for opp in combination if opp.type == 'hpa_optimization')
            match_factors.append(hpa_count / len(combination))
        
        # Enterprise personality matching
        if 'enterprise' in personality:
            # Enterprise clusters can handle more complex combinations
            complexity_bonus = min(1.0, len(combination) / 3)
            match_factors.append(complexity_bonus)
        
        return sum(match_factors) / len(match_factors) if match_factors else 0.5

# ============================================================================
# EXECUTABLE COMMAND GENERATOR
# ============================================================================

class ExecutableCommandGenerator:
    """Generates executable kubectl/az commands from opportunities"""
    
    def generate_commands(self, opportunity: OptimizationOpportunity, 
                         cluster_dna: ClusterDNA) -> List[str]:
        """Generate executable commands for opportunity"""
        
        if opportunity.type == 'hpa_optimization':
            return self._generate_hpa_commands(opportunity, cluster_dna)
        elif opportunity.type == 'resource_rightsizing':
            return self._generate_rightsizing_commands(opportunity, cluster_dna)
        elif opportunity.type == 'storage_optimization':
            return self._generate_storage_commands(opportunity, cluster_dna)
        elif opportunity.type == 'system_pool_optimization':
            return self._generate_system_pool_commands(opportunity, cluster_dna)
        else:
            return []
    
    def _generate_hpa_commands(self, opportunity: OptimizationOpportunity, 
                              cluster_dna: ClusterDNA) -> List[str]:
        """Generate HPA-specific commands"""
        
        commands = []
        
        # Calculate targets based on cluster DNA
        if 'conservative' in cluster_dna.cluster_personality:
            memory_target = 75
            cpu_target = 70
        else:
            memory_target = 65
            cpu_target = 60
        
        for workload in opportunity.target_workloads:
            commands.extend([
                f"# Deploy HPA for {workload}",
                f"kubectl apply -f {workload}-hpa.yaml",
                f"kubectl get hpa {workload}-hpa -n production -w --timeout=300s",
                f"kubectl describe hpa {workload}-hpa -n production",
                ""
            ])
        
        return commands
    
    def _generate_rightsizing_commands(self, opportunity: OptimizationOpportunity, 
                                     cluster_dna: ClusterDNA) -> List[str]:
        """Generate right-sizing commands"""
        
        commands = []
        
        # Calculate reduction factors based on approach
        if opportunity.optimal_approach == 'cpu_focused_rightsizing':
            cpu_factor = 0.7
            memory_factor = 0.9
        elif opportunity.optimal_approach == 'memory_focused_rightsizing':
            cpu_factor = 0.9
            memory_factor = 0.7
        else:
            cpu_factor = 0.8
            memory_factor = 0.8
        
        for workload in opportunity.target_workloads:
            commands.extend([
                f"# Right-size {workload}",
                f"kubectl patch deployment {workload} -n production -p '{{...}}'",
                f"kubectl rollout status deployment/{workload} -n production",
                f"kubectl get deployment {workload} -n production -o yaml | grep resources",
                ""
            ])
        
        return commands
    
    def _generate_storage_commands(self, opportunity: OptimizationOpportunity, 
                                  cluster_dna: ClusterDNA) -> List[str]:
        """Generate storage optimization commands"""
        
        return [
            "# Create optimized storage class",
            "kubectl apply -f optimized-storage-class.yaml",
            "kubectl get storageclass",
            "kubectl patch storageclass optimized-ssd -p '{\"metadata\":{\"annotations\":{\"storageclass.kubernetes.io/is-default-class\":\"true\"}}}'",
            ""
        ]
    
    def _generate_system_pool_commands(self, opportunity: OptimizationOpportunity, 
                                     cluster_dna: ClusterDNA) -> List[str]:
        """Generate system pool optimization commands"""
        
        return [
            "# System pool optimization",
            "kubectl get nodes -l node-role=system",
            "kubectl cordon <underutilized-system-node>",
            "kubectl drain <underutilized-system-node> --ignore-daemonsets",
            "kubectl get pods -o wide | grep <underutilized-system-node>",
            ""
        ]
    
    def generate_success_criteria(self, opportunity: OptimizationOpportunity, 
                                cluster_dna: ClusterDNA) -> List[str]:
        """Generate success criteria for opportunity"""
        
        criteria = [
            f"Achieve ${opportunity.savings_potential_monthly:.2f}/month cost reduction",
            "Maintain application SLA > 99.9%",
            "Implementation completes without incidents"
        ]
        
        if opportunity.type == 'hpa_optimization':
            criteria.append("HPA scaling events respond within 2 minutes")
        elif opportunity.type == 'resource_rightsizing':
            criteria.append("Application performance degradation < 5%")
        
        return criteria
    
    def generate_rollback_plan(self, opportunity: OptimizationOpportunity, 
                              cluster_dna: ClusterDNA) -> List[str]:
        """Generate rollback plan for opportunity"""
        
        if opportunity.type == 'hpa_optimization':
            return [
                "kubectl delete hpa <workload>-hpa -n production",
                "kubectl scale deployment <workload> --replicas=<original-count> -n production",
                "Monitor for 15 minutes to ensure stability"
            ]
        elif opportunity.type == 'resource_rightsizing':
            return [
                "kubectl rollout undo deployment/<workload> -n production",
                "kubectl rollout status deployment/<workload> -n production",
                "Verify application performance returns to baseline"
            ]
        else:
            return [
                "Revert configuration changes",
                "Monitor system for 15 minutes",
                "Validate service restoration"
            ]

# ============================================================================
# SUCCESS PREDICTOR
# ============================================================================

class SuccessPredictor:
    """Predicts success probability of strategies using algorithmic models"""
    
    def predict_success(self, strategy: DynamicStrategy, cluster_dna: ClusterDNA) -> float:
        """Predict probability of successful strategy implementation"""
        
        success_factors = []
        
        # Data quality factor
        data_quality = cluster_dna.optimization_readiness_score
        success_factors.append(data_quality)
        
        # Risk factor (lower risk = higher success probability)
        avg_risk = sum(opp.risk_assessment for opp in strategy.opportunities) / len(strategy.opportunities)
        risk_factor = 1.0 - avg_risk
        success_factors.append(risk_factor)
        
        # Complexity factor
        complexity = sum(opp.implementation_complexity for opp in strategy.opportunities) / len(strategy.opportunities)
        complexity_factor = 1.0 - complexity
        success_factors.append(complexity_factor)
        
        # Personality match factor
        personality_match = strategy.cluster_personality_match
        success_factors.append(personality_match)
        
        # Timeline realism factor
        timeline_realism = self._assess_timeline_realism(strategy)
        success_factors.append(timeline_realism)
        
        # Calculate weighted success probability
        success_probability = sum(success_factors) / len(success_factors)
        
        # Apply conservative bounds
        return max(0.3, min(0.95, success_probability))
    
    def _assess_timeline_realism(self, strategy: DynamicStrategy) -> float:
        """Assess if timeline is realistic"""
        
        # Baseline: 6 weeks is optimal
        optimal_timeline = 6
        actual_timeline = strategy.total_timeline_weeks
        
        # Calculate realism score
        if actual_timeline == optimal_timeline:
            return 1.0
        else:
            deviation = abs(actual_timeline - optimal_timeline)
            return max(0.5, 1.0 - (deviation / 10))

# ============================================================================
# DEMO FUNCTION WITH YOUR ACTUAL DATA
# ============================================================================

def demo_dynamic_strategy_generation():
    """
    DEMO: Generate dynamic strategy using your actual cluster DNA
    """
    
    print("🚀 DYNAMIC STRATEGY GENERATION DEMO")
    print("=" * 50)
    
    # Use your actual analysis data from Phase 1
    your_actual_data = {
        'cluster_name': 'aks-dpl-mad-uat-ne2-1',
        'resource_group': 'rg-dpl-mad-uat-ne2-2',
        'total_cost': 1864.43,
        'node_cost': 325.93,
        'storage_cost': 158.63,
        'networking_cost': 678.59,
        'control_plane_cost': 171.26,
        'registry_cost': 41.96,
        'other_cost': 366.28,
        'total_savings': 71.11,
        'hpa_savings': 46.61,
        'right_sizing_savings': 21.33,
        'storage_savings': 3.17,
        'cpu_gap': 15.0,
        'memory_gap': 10.0,
        'analysis_confidence': 0.88,
        'current_usage_analysis': {
            'nodes': [
                {'name': 'aks-appusrpool-20297217-vmss000000', 'cpu_usage_pct': 63.7, 'memory_usage_pct': 80.3},
                {'name': 'aks-appusrpool-20297217-vmss000001', 'cpu_usage_pct': 80.3, 'memory_usage_pct': 73.1},
                {'name': 'aks-appusrpool-20297217-vmss000002', 'cpu_usage_pct': 95.4, 'memory_usage_pct': 78.1},
                {'name': 'aks-systempool-14902933-vmss000000', 'cpu_usage_pct': 11.8, 'memory_usage_pct': 67.1},
                {'name': 'aks-systempool-14902933-vmss000001', 'cpu_usage_pct': 11.5, 'memory_usage_pct': 63.9}
            ]
        },
        'namespace_costs': {
            'madapi-preprod': 282.95,
            'argocd': 15.50,
            'kube-system': 8.30
        }
    }
    
    # Step 1: Generate cluster DNA
    cluster_dna = analyze_cluster_dna_from_analysis(your_actual_data)
    print(f"🧬 Cluster DNA: {cluster_dna.cluster_personality}")
    
    # Step 2: Generate dynamic strategy
    strategy_engine = DynamicStrategyEngine()
    dynamic_strategy = strategy_engine.generate_dynamic_strategy(cluster_dna)
    
    # Step 3: Display results
    print(f"\n🎯 GENERATED STRATEGY: {dynamic_strategy.strategy_name}")
    print(f"💰 Total Savings Potential: ${dynamic_strategy.total_savings_potential:.2f}/month")
    print(f"📅 Timeline: {dynamic_strategy.total_timeline_weeks} weeks")
    print(f"⚠️ Risk Level: {dynamic_strategy.overall_risk_level}")
    print(f"🎲 Success Probability: {dynamic_strategy.success_probability:.1%}")
    
    print(f"\n📋 IMPLEMENTATION PHASES:")
    for phase in dynamic_strategy.implementation_phases:
        print(f"  {phase['name']}: ${phase['savings_potential']:.2f} savings, {phase['duration_weeks']} weeks")
    
    print(f"\n🛠️ EXECUTABLE COMMANDS (Sample):")
    for opportunity in dynamic_strategy.opportunities[:1]:  # Show first opportunity
        print(f"  {opportunity.type}:")
        for cmd in opportunity.executable_commands[:3]:  # Show first 3 commands
            if cmd.strip():
                print(f"    {cmd}")
    
    print(f"\n✅ SUCCESS CRITERIA:")
    for criterion in dynamic_strategy.success_metrics[:3]:
        print(f"  • {criterion}")
    
    return dynamic_strategy

if __name__ == "__main__":
    demo_dynamic_strategy_generation()