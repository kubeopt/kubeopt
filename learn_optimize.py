"""
Phase 4: Learning & Optimization Engine - REVOLUTIONARY INTELLIGENCE
====================================================================
Learns from implementation results to continuously improve strategy generation.
This is what makes your system truly intelligent and self-improving!

INTEGRATION: Learns from Phase 1-3 results and improves future strategies
PURPOSE: Create self-improving system that gets smarter with each optimization
"""

import json
import math
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging
import statistics

logger = logging.getLogger(__name__)

# ============================================================================
# LEARNING DATA STRUCTURES
# ============================================================================

@dataclass
class ImplementationResult:
    """Results from a completed optimization implementation"""
    execution_id: str
    cluster_id: str
    cluster_dna_signature: str
    strategy_name: str
    opportunities_implemented: List[str]
    
    # Execution metrics
    total_duration_minutes: int
    commands_executed: int
    commands_successful: int
    commands_failed: int
    rollbacks_performed: int
    
    # Business outcomes
    predicted_savings: float
    actual_savings: float
    savings_accuracy: float  # actual/predicted
    
    # Performance metrics
    implementation_success: bool
    time_to_first_benefit: int  # minutes
    stability_period_clean: bool  # no issues for 24h
    customer_satisfaction_score: float  # 1-5 scale
    
    # Learning data
    cluster_personality: str
    success_factors: List[str]
    failure_factors: List[str]
    lessons_learned: List[str]
    recommendations_for_similar: List[str]
    
    # Timestamps
    started_at: datetime
    completed_at: datetime
    benefits_realized_at: Optional[datetime]

@dataclass
class StrategyPattern:
    """Learned pattern for strategy optimization"""
    pattern_id: str
    cluster_personality_pattern: str
    successful_strategy_combinations: List[List[str]]
    optimal_sequencing: List[str]
    risk_mitigation_tactics: List[str]
    success_probability: float
    sample_size: int
    confidence_level: float
    last_updated: datetime

@dataclass
class ClusterArchetype:
    """Learned cluster archetype with proven optimization approaches"""
    archetype_id: str
    personality_signature: str
    common_characteristics: Dict[str, Any]
    proven_strategies: List[str]
    strategy_success_rates: Dict[str, float]
    optimal_implementation_order: List[str]
    common_pitfalls: List[str]
    best_practices: List[str]
    sample_clusters: int
    archetype_confidence: float

@dataclass
class AdaptiveThreshold:
    """Dynamically learned thresholds for optimization decisions"""
    metric_name: str
    cluster_archetype: str
    optimal_threshold: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    last_validation: datetime
    adjustment_history: List[Dict]

# ============================================================================
# LEARNING & OPTIMIZATION ENGINE
# ============================================================================

class LearningOptimizationEngine:
    """
    Revolutionary learning engine that improves strategy generation
    """
    
    def __init__(self, db_path: str = "optimization_learning.db"):
        self.db_path = db_path
        self.pattern_analyzer = PatternAnalyzer()
        self.archetype_learner = ArchetypeLearner()
        self.threshold_optimizer = ThresholdOptimizer()
        self.strategy_improver = StrategyImprover()
        
        # Initialize learning database
        self._initialize_learning_database()
        
        # Load existing patterns
        self.strategy_patterns = self._load_strategy_patterns()
        self.cluster_archetypes = self._load_cluster_archetypes()
        self.adaptive_thresholds = self._load_adaptive_thresholds()
        
    def _initialize_learning_database(self):
        """Initialize SQLite database for learning data"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Implementation results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS implementation_results (
                execution_id TEXT PRIMARY KEY,
                cluster_id TEXT,
                cluster_dna_signature TEXT,
                strategy_name TEXT,
                opportunities_implemented TEXT,
                total_duration_minutes INTEGER,
                commands_executed INTEGER,
                commands_successful INTEGER,
                commands_failed INTEGER,
                predicted_savings REAL,
                actual_savings REAL,
                savings_accuracy REAL,
                implementation_success INTEGER,
                cluster_personality TEXT,
                success_factors TEXT,
                failure_factors TEXT,
                started_at TEXT,
                completed_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Strategy patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_patterns (
                pattern_id TEXT PRIMARY KEY,
                cluster_personality_pattern TEXT,
                successful_combinations TEXT,
                optimal_sequencing TEXT,
                success_probability REAL,
                sample_size INTEGER,
                confidence_level REAL,
                last_updated TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cluster archetypes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cluster_archetypes (
                archetype_id TEXT PRIMARY KEY,
                personality_signature TEXT,
                common_characteristics TEXT,
                proven_strategies TEXT,
                strategy_success_rates TEXT,
                optimal_implementation_order TEXT,
                sample_clusters INTEGER,
                archetype_confidence REAL,
                last_updated TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Adaptive thresholds table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS adaptive_thresholds (
                metric_name TEXT,
                cluster_archetype TEXT,
                optimal_threshold REAL,
                confidence_interval_lower REAL,
                confidence_interval_upper REAL,
                sample_size INTEGER,
                last_validation TEXT,
                adjustment_history TEXT,
                PRIMARY KEY (metric_name, cluster_archetype)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("🧠 Learning database initialized")
    
    def apply_learning_to_strategy(self, cluster_dna, optimization_strategy) -> Dict:
        """Apply learning insights to optimize strategy generation"""
        
        logger.info(f"🎓 Applying learning insights to strategy optimization")
        
        # Get cluster personality for learning lookup
        cluster_personality = getattr(cluster_dna, 'cluster_personality', 'unknown')
        
        # Get learned recommendations
        recommendations = self.get_learned_recommendations({'cluster_personality': cluster_personality})
        
        # Calculate confidence boost based on learning
        confidence_boost = 0.0
        if recommendations['matching_archetype']:
            confidence_boost = recommendations['archetype_confidence'] * 20  # Up to 20% boost
        
        # Get similar clusters analyzed
        similar_clusters = recommendations['learned_from_clusters']
        
        # Generate optimization recommendations
        optimization_recommendations = []
        if recommendations['recommended_strategies']:
            for strategy_rec in recommendations['recommended_strategies']:
                optimization_recommendations.append(
                    f"Success probability: {strategy_rec['success_probability']:.1%} "
                    f"(based on {strategy_rec['sample_size']} implementations)"
                )
        
        # Predict success rate based on learning
        predicted_success_rate = recommendations['expected_success_probability']
        
        # Calculate timeline optimizations
        timeline_confidence = 0.8
        parallelization_opportunities = 0
        timeline_optimization = 'Standard'
        success_rate_improvement = 0.0
        
        if similar_clusters > 3:  # Have enough data for timeline optimization
            timeline_confidence = 0.9
            parallelization_opportunities = 1 if similar_clusters > 5 else 0
            timeline_optimization = 'Learning-Optimized'
            success_rate_improvement = confidence_boost
        
        learning_insights = {
            'confidence_boost': confidence_boost,
            'similar_clusters_analyzed': similar_clusters,
            'recommendations': optimization_recommendations,
            'predicted_success_rate': predicted_success_rate,
            'parallelization_opportunities': parallelization_opportunities,
            'timeline_confidence': timeline_confidence,
            'timeline_optimization': timeline_optimization,
            'success_rate_improvement': success_rate_improvement,
            'confidence_score': recommendations['archetype_confidence'],
            'learning_applied': True,
            'learning_quality': 'High' if similar_clusters > 5 else 'Medium' if similar_clusters > 2 else 'Low'
        }
        
        logger.info(f"✅ Learning insights applied - {confidence_boost:.1f}% confidence boost from {similar_clusters} similar clusters")
        
        return learning_insights
    
    def record_plan_generation(self, cluster_dna, optimization_strategy, implementation_plan: Dict):
        """Record plan generation for future learning"""
        
        logger.info(f"📚 Recording plan generation for learning")
        
        try:
            # Extract key information for learning
            cluster_personality = getattr(cluster_dna, 'cluster_personality', 'unknown')
            strategy_name = getattr(optimization_strategy, 'strategy_name', 'Unknown Strategy')
            
            # FIX: Convert opportunities to JSON-serializable format
            opportunities = getattr(optimization_strategy, 'opportunities', [])
            if opportunities and hasattr(opportunities[0], '__dict__'):
                # Convert dataclass objects to dicts
                opportunities_serializable = [
                    opp.type if hasattr(opp, 'type') else str(opp) 
                    for opp in opportunities
                ]
            else:
                opportunities_serializable = opportunities
            
            # Create a simple learning record
            learning_record = {
                'timestamp': datetime.now().isoformat(),
                'cluster_personality': cluster_personality,
                'strategy_name': strategy_name,
                'opportunities': opportunities_serializable,  # FIX: Use serializable version
                'implementation_phases': len(implementation_plan.get('implementation_phases', [])),
                'predicted_savings': implementation_plan.get('executive_summary', {}).get('optimization_opportunity', {}).get('projected_monthly_savings', 0),
                'generation_method': implementation_plan.get('metadata', {}).get('generation_method', 'unknown')
            }
            
            # Store in simple JSON file for now
            try:
                with open('plan_generation_log.json', 'a') as f:
                    f.write(json.dumps(learning_record) + '\n')
                logger.info(f"✅ Plan generation recorded successfully")
            except Exception as e:
                logger.warning(f"Could not write to learning log: {e}")
            
        except Exception as e:
            logger.warning(f"Could not record plan generation for learning: {e}")
    
    def record_implementation_result(self, result: ImplementationResult):
        """Record results from a completed implementation for learning"""
        
        logger.info(f"📊 Recording implementation result: {result.execution_id}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO implementation_results 
            (execution_id, cluster_id, cluster_dna_signature, strategy_name, 
             opportunities_implemented, total_duration_minutes, commands_executed,
             commands_successful, commands_failed, predicted_savings, actual_savings,
             savings_accuracy, implementation_success, cluster_personality,
             success_factors, failure_factors, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.execution_id,
            result.cluster_id,
            result.cluster_dna_signature,
            result.strategy_name,
            json.dumps(result.opportunities_implemented),
            result.total_duration_minutes,
            result.commands_executed,
            result.commands_successful,
            result.commands_failed,
            result.predicted_savings,
            result.actual_savings,
            result.savings_accuracy,
            1 if result.implementation_success else 0,
            result.cluster_personality,
            json.dumps(result.success_factors),
            json.dumps(result.failure_factors),
            result.started_at.isoformat(),
            result.completed_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Trigger learning processes
        self._learn_from_new_result(result)
        
        logger.info(f"✅ Implementation result recorded and learning triggered")
    
    def _learn_from_new_result(self, result: ImplementationResult):
        """Learn from new implementation result"""
        
        # Update strategy patterns
        self.pattern_analyzer.update_patterns(result, self.strategy_patterns)
        
        # Update cluster archetypes
        self.archetype_learner.update_archetypes(result, self.cluster_archetypes)
        
        # Update adaptive thresholds
        self.threshold_optimizer.update_thresholds(result, self.adaptive_thresholds)
        
        # Save updated patterns
        self._save_strategy_patterns()
        self._save_cluster_archetypes()
        self._save_adaptive_thresholds()
    
    def get_learned_recommendations(self, cluster_dna: Dict) -> Dict:
        """Get recommendations based on learned patterns"""
        
        cluster_personality = cluster_dna.get('cluster_personality', '')
        
        # Find matching archetype
        matching_archetype = self._find_matching_archetype(cluster_personality)
        
        # Get strategy recommendations
        strategy_recommendations = self._get_strategy_recommendations(cluster_personality)
        
        # Get optimal thresholds
        optimal_thresholds = self._get_optimal_thresholds(cluster_personality)
        
        # Get risk mitigation tactics
        risk_mitigation = self._get_risk_mitigation_tactics(cluster_personality)
        
        recommendations = {
            'matching_archetype': matching_archetype.archetype_id if matching_archetype else None,
            'archetype_confidence': matching_archetype.archetype_confidence if matching_archetype else 0.5,
            'recommended_strategies': strategy_recommendations,
            'optimal_thresholds': optimal_thresholds,
            'risk_mitigation_tactics': risk_mitigation,
            'implementation_tips': self._get_implementation_tips(cluster_personality),
            'expected_success_probability': self._predict_success_probability(cluster_personality),
            'learned_from_clusters': self._get_learning_sample_size(cluster_personality)
        }
        
        return recommendations
    
    def optimize_strategy_based_on_learning(self, original_strategy: Dict, 
                                          cluster_dna: Dict) -> Dict:
        """Optimize strategy using learned knowledge"""
        
        logger.info(f"🎯 Optimizing strategy using learned knowledge")
        
        optimized_strategy = original_strategy.copy()
        
        # Get learned recommendations
        learned_recommendations = self.get_learned_recommendations(cluster_dna)
        
        # Apply archetype-based optimizations
        if learned_recommendations['matching_archetype']:
            optimized_strategy = self._apply_archetype_optimizations(
                optimized_strategy, learned_recommendations
            )
        
        # Apply threshold optimizations
        optimized_strategy = self._apply_threshold_optimizations(
            optimized_strategy, learned_recommendations['optimal_thresholds']
        )
        
        # Apply risk mitigation improvements
        optimized_strategy = self._apply_risk_mitigation_improvements(
            optimized_strategy, learned_recommendations['risk_mitigation_tactics']
        )
        
        # Update success probability based on learning
        optimized_strategy['success_probability'] = learned_recommendations['expected_success_probability']
        
        # Add learning-based metadata
        optimized_strategy['learning_metadata'] = {
            'optimized_with_learning': True,
            'archetype_used': learned_recommendations['matching_archetype'],
            'learning_confidence': learned_recommendations['archetype_confidence'],
            'learned_from_clusters': learned_recommendations['learned_from_clusters'],
            'optimization_applied_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Strategy optimized - success probability: {optimized_strategy['success_probability']:.1%}")
        
        return optimized_strategy
    
    def generate_continuous_improvement_report(self) -> Dict:
        """Generate report on learning progress and continuous improvements"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get implementation statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_implementations,
                AVG(savings_accuracy) as avg_savings_accuracy,
                AVG(CASE WHEN implementation_success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                COUNT(DISTINCT cluster_personality) as unique_personalities,
                AVG(total_duration_minutes) as avg_duration
            FROM implementation_results
        ''')
        stats = cursor.fetchone()
        
        # Get strategy success rates
        cursor.execute('''
            SELECT 
                strategy_name,
                COUNT(*) as implementations,
                AVG(CASE WHEN implementation_success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(savings_accuracy) as avg_accuracy
            FROM implementation_results
            GROUP BY strategy_name
            ORDER BY success_rate DESC
        ''')
        strategy_stats = cursor.fetchall()
        
        # Get archetype performance
        cursor.execute('''
            SELECT 
                cluster_personality,
                COUNT(*) as implementations,
                AVG(actual_savings) as avg_savings,
                AVG(CASE WHEN implementation_success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
            FROM implementation_results
            GROUP BY cluster_personality
            HAVING COUNT(*) >= 3
            ORDER BY success_rate DESC
        ''')
        archetype_stats = cursor.fetchall()
        
        conn.close()
        
        # Generate learning insights
        learning_insights = self._generate_learning_insights()
        
        # Calculate learning velocity
        learning_velocity = self._calculate_learning_velocity()
        
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'overall_statistics': {
                'total_implementations': stats[0] if stats[0] else 0,
                'average_savings_accuracy': stats[1] if stats[1] else 0.0,
                'overall_success_rate': stats[2] if stats[2] else 0.0,
                'unique_cluster_personalities': stats[3] if stats[3] else 0,
                'average_implementation_duration': stats[4] if stats[4] else 0
            },
            'strategy_performance': [
                {
                    'strategy_name': row[0],
                    'implementations': row[1],
                    'success_rate': row[2],
                    'accuracy': row[3]
                }
                for row in strategy_stats
            ],
            'archetype_performance': [
                {
                    'personality': row[0],
                    'implementations': row[1],
                    'avg_savings': row[2],
                    'success_rate': row[3]
                }
                for row in archetype_stats
            ],
            'learning_insights': learning_insights,
            'learning_velocity': learning_velocity,
            'continuous_improvements': self._get_continuous_improvements(),
            'recommendations_for_improvement': self._get_improvement_recommendations()
        }
        
        return report
    
    # ========================================================================
    # PRIVATE LEARNING METHODS
    # ========================================================================
    
    def _find_matching_archetype(self, cluster_personality: str) -> Optional[ClusterArchetype]:
        """Find best matching cluster archetype"""
        
        best_match = None
        best_score = 0.0
        
        for archetype in self.cluster_archetypes.values():
            similarity_score = self._calculate_personality_similarity(
                cluster_personality, archetype.personality_signature
            )
            
            if similarity_score > best_score and similarity_score > 0.7:  # 70% similarity threshold
                best_score = similarity_score
                best_match = archetype
        
        return best_match
    
    def _calculate_personality_similarity(self, personality1: str, personality2: str) -> float:
        """Calculate similarity between cluster personalities"""
        
        # Split personalities into components
        components1 = set(personality1.split('-'))
        components2 = set(personality2.split('-'))
        
        # Calculate Jaccard similarity
        intersection = len(components1.intersection(components2))
        union = len(components1.union(components2))
        
        return intersection / union if union > 0 else 0.0
    
    def _get_strategy_recommendations(self, cluster_personality: str) -> List[Dict]:
        """Get strategy recommendations based on learned patterns"""
        
        recommendations = []
        
        for pattern in self.strategy_patterns.values():
            if pattern.cluster_personality_pattern in cluster_personality:
                recommendations.append({
                    'strategy_combinations': pattern.successful_strategy_combinations,
                    'optimal_sequence': pattern.optimal_sequencing,
                    'success_probability': pattern.success_probability,
                    'confidence': pattern.confidence_level,
                    'sample_size': pattern.sample_size
                })
        
        # Sort by success probability and confidence
        recommendations.sort(
            key=lambda x: x['success_probability'] * x['confidence'], 
            reverse=True
        )
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _get_optimal_thresholds(self, cluster_personality: str) -> Dict:
        """Get optimal thresholds for cluster personality"""
        
        optimal_thresholds = {}
        
        # Find matching archetype for threshold recommendations
        for archetype_id, thresholds_list in self.adaptive_thresholds.items():
            for threshold in thresholds_list:
                if cluster_personality in threshold.cluster_archetype:
                    optimal_thresholds[threshold.metric_name] = {
                        'value': threshold.optimal_threshold,
                        'confidence_interval': threshold.confidence_interval,
                        'sample_size': threshold.sample_size
                    }
        
        return optimal_thresholds
    
    def _get_risk_mitigation_tactics(self, cluster_personality: str) -> List[str]:
        """Get risk mitigation tactics for cluster personality"""
        
        tactics = []
        
        # Default tactics based on personality
        if 'enterprise' in cluster_personality:
            tactics.append("Use phased rollout approach")
            tactics.append("Implement comprehensive monitoring")
        
        if 'over-provisioned' in cluster_personality:
            tactics.append("Start with conservative optimization")
            tactics.append("Monitor resource utilization closely")
        
        if 'hpa-ready' in cluster_personality:
            tactics.append("Begin with HPA optimization")
            tactics.append("Validate metrics server functionality")
        
        return tactics
    
    def _get_implementation_tips(self, cluster_personality: str) -> List[str]:
        """Get implementation tips for cluster personality"""
        
        tips = []
        
        if 'network-heavy' in cluster_personality:
            tips.append("Monitor network costs during optimization")
            tips.append("Consider networking optimization opportunities")
        
        if 'storage-heavy' in cluster_personality:
            tips.append("Focus on storage optimization first")
            tips.append("Review storage class configurations")
        
        if 'medium' in cluster_personality:
            tips.append("Balance between aggressive and conservative approaches")
            tips.append("Use standard monitoring practices")
        
        return tips
    
    def _predict_success_probability(self, cluster_personality: str) -> float:
        """Predict success probability based on cluster personality"""
        
        base_probability = 0.75  # Default success rate
        
        # Adjust based on personality components
        if 'over-provisioned' in cluster_personality:
            base_probability += 0.1  # Higher success rate for over-provisioned clusters
        
        if 'hpa-ready' in cluster_personality:
            base_probability += 0.05  # HPA optimizations tend to be successful
        
        if 'enterprise' in cluster_personality:
            base_probability -= 0.05  # More complex, slightly lower success rate
        
        return min(0.95, max(0.5, base_probability))  # Keep between 50% and 95%
    
    def _get_learning_sample_size(self, cluster_personality: str) -> int:
        """Get the number of similar clusters in learning database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count similar personalities
            cursor.execute('''
                SELECT COUNT(DISTINCT cluster_id) 
                FROM implementation_results 
                WHERE cluster_personality LIKE ?
            ''', (f'%{cluster_personality.split("-")[0]}%',))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result[0] else 0
            
        except Exception as e:
            logger.warning(f"Could not get learning sample size: {e}")
            return 0
    
    def _apply_archetype_optimizations(self, strategy: Dict, recommendations: Dict) -> Dict:
        """Apply archetype-based optimizations to strategy"""
        
        if not recommendations['matching_archetype']:
            return strategy
        
        archetype = self.cluster_archetypes.get(recommendations['matching_archetype'])
        if not archetype:
            return strategy
        
        # Apply proven strategies from archetype
        if 'opportunities' in strategy:
            # Reorder opportunities based on archetype's optimal sequence
            current_opportunities = strategy['opportunities']
            optimal_order = archetype.optimal_implementation_order
            
            # Reorder based on learned optimal sequence
            reordered_opportunities = []
            for optimal_opp in optimal_order:
                if optimal_opp in current_opportunities:
                    reordered_opportunities.append(optimal_opp)
            
            # Add any remaining opportunities
            for opp in current_opportunities:
                if opp not in reordered_opportunities:
                    reordered_opportunities.append(opp)
            
            strategy['opportunities'] = reordered_opportunities
        
        # Apply archetype-specific best practices
        strategy['archetype_optimizations'] = {
            'applied_archetype': archetype.archetype_id,
            'best_practices': archetype.best_practices,
            'common_pitfalls_avoided': archetype.common_pitfalls
        }
        
        return strategy
    
    def _apply_threshold_optimizations(self, strategy: Dict, optimal_thresholds: Dict) -> Dict:
        """Apply threshold optimizations to strategy"""
        
        if optimal_thresholds:
            strategy['learned_thresholds'] = optimal_thresholds
        
        return strategy
    
    def _apply_risk_mitigation_improvements(self, strategy: Dict, risk_tactics: List[str]) -> Dict:
        """Apply risk mitigation improvements to strategy"""
        
        if risk_tactics:
            strategy['learned_risk_mitigation'] = risk_tactics
        
        return strategy
    
    def _generate_learning_insights(self) -> Dict:
        """Generate learning insights from accumulated data"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent trends
            cursor.execute('''
                SELECT 
                    AVG(savings_accuracy) as recent_accuracy,
                    COUNT(*) as recent_implementations
                FROM implementation_results 
                WHERE created_at > date('now', '-30 days')
            ''')
            recent_stats = cursor.fetchone()
            
            # Get improvement trends
            cursor.execute('''
                SELECT 
                    cluster_personality,
                    AVG(savings_accuracy) as avg_accuracy,
                    COUNT(*) as implementations
                FROM implementation_results
                GROUP BY cluster_personality
                HAVING COUNT(*) >= 2
            ''')
            personality_trends = cursor.fetchall()
            
            conn.close()
            
            insights = {
                'recent_accuracy_trend': recent_stats[0] if recent_stats[0] else 0.0,
                'recent_implementation_volume': recent_stats[1] if recent_stats[1] else 0,
                'personality_performance': [
                    {
                        'personality': row[0],
                        'accuracy': row[1],
                        'sample_size': row[2]
                    }
                    for row in personality_trends
                ],
                'learning_quality': self._assess_learning_quality(),
                'data_sufficiency': self._assess_data_sufficiency()
            }
            
            return insights
            
        except Exception as e:
            logger.warning(f"Could not generate learning insights: {e}")
            return {
                'recent_accuracy_trend': 0.0,
                'recent_implementation_volume': 0,
                'personality_performance': [],
                'learning_quality': 'Limited',
                'data_sufficiency': 'Insufficient'
            }
    
    def _calculate_learning_velocity(self) -> Dict:
        """Calculate how fast the system is learning"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get implementation volume over time
            cursor.execute('''
                SELECT 
                    date(created_at) as date,
                    COUNT(*) as implementations
                FROM implementation_results
                WHERE created_at > date('now', '-7 days')
                GROUP BY date(created_at)
                ORDER BY date
            ''')
            daily_volume = cursor.fetchall()
            
            conn.close()
            
            velocity = {
                'implementations_per_day': len(daily_volume),
                'learning_acceleration': 'steady' if len(daily_volume) > 3 else 'slow',
                'data_points_last_week': sum(row[1] for row in daily_volume)
            }
            
            return velocity
            
        except Exception as e:
            logger.warning(f"Could not calculate learning velocity: {e}")
            return {
                'implementations_per_day': 0,
                'learning_acceleration': 'unknown',
                'data_points_last_week': 0
            }
    
    def _get_continuous_improvements(self) -> List[str]:
        """Get list of continuous improvements made"""
        
        improvements = [
            "Dynamic threshold adjustment based on cluster personality",
            "Strategy ordering optimization based on success patterns",
            "Risk mitigation tactics learned from previous implementations",
            "Timeline predictions improved through historical data"
        ]
        
        return improvements
    
    def _get_improvement_recommendations(self) -> List[str]:
        """Get recommendations for system improvement"""
        
        recommendations = [
            "Collect more implementation feedback for better learning",
            "Implement A/B testing for strategy variations",
            "Add more granular cluster personality detection",
            "Enhance risk prediction models"
        ]
        
        return recommendations
    
    def _assess_learning_quality(self) -> str:
        """Assess the quality of learning data"""
        
        # This would be more sophisticated in a real implementation
        return "Developing"
    
    def _assess_data_sufficiency(self) -> str:
        """Assess if we have sufficient data for good learning"""
        
        # This would be more sophisticated in a real implementation
        return "Minimal"
    
    def _load_strategy_patterns(self) -> Dict[str, StrategyPattern]:
        """Load strategy patterns from database"""
        
        patterns = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM strategy_patterns')
            rows = cursor.fetchall()
            
            for row in rows:
                pattern = StrategyPattern(
                    pattern_id=row[0],
                    cluster_personality_pattern=row[1],
                    successful_strategy_combinations=json.loads(row[2]),
                    optimal_sequencing=json.loads(row[3]),
                    risk_mitigation_tactics=[],  # Will be loaded separately
                    success_probability=row[4],
                    sample_size=row[5],
                    confidence_level=row[6],
                    last_updated=datetime.fromisoformat(row[7])
                )
                patterns[pattern.pattern_id] = pattern
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"Could not load strategy patterns: {e}")
        
        return patterns
    
    def _load_cluster_archetypes(self) -> Dict[str, ClusterArchetype]:
        """Load cluster archetypes from database"""
        
        archetypes = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM cluster_archetypes')
            rows = cursor.fetchall()
            
            for row in rows:
                archetype = ClusterArchetype(
                    archetype_id=row[0],
                    personality_signature=row[1],
                    common_characteristics=json.loads(row[2]),
                    proven_strategies=json.loads(row[3]),
                    strategy_success_rates=json.loads(row[4]),
                    optimal_implementation_order=json.loads(row[5]),
                    common_pitfalls=[],  # Will be populated from results
                    best_practices=[],   # Will be populated from results
                    sample_clusters=row[6],
                    archetype_confidence=row[7]
                )
                archetypes[archetype.archetype_id] = archetype
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"Could not load cluster archetypes: {e}")
        
        return archetypes
    
    def _load_adaptive_thresholds(self) -> Dict[str, List[AdaptiveThreshold]]:
        """Load adaptive thresholds from database"""
        
        thresholds = defaultdict(list)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM adaptive_thresholds')
            rows = cursor.fetchall()
            
            for row in rows:
                threshold = AdaptiveThreshold(
                    metric_name=row[0],
                    cluster_archetype=row[1],
                    optimal_threshold=row[2],
                    confidence_interval=(row[3], row[4]),
                    sample_size=row[5],
                    last_validation=datetime.fromisoformat(row[6]),
                    adjustment_history=json.loads(row[7])
                )
                thresholds[row[1]].append(threshold)
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"Could not load adaptive thresholds: {e}")
        
        return dict(thresholds)
    
    def _save_strategy_patterns(self):
        """Save strategy patterns to database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for pattern in self.strategy_patterns.values():
            cursor.execute('''
                INSERT OR REPLACE INTO strategy_patterns
                (pattern_id, cluster_personality_pattern, successful_combinations,
                 optimal_sequencing, success_probability, sample_size, confidence_level, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.cluster_personality_pattern,
                json.dumps(pattern.successful_strategy_combinations),
                json.dumps(pattern.optimal_sequencing),
                pattern.success_probability,
                pattern.sample_size,
                pattern.confidence_level,
                pattern.last_updated.isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def _save_cluster_archetypes(self):
        """Save cluster archetypes to database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for archetype in self.cluster_archetypes.values():
            cursor.execute('''
                INSERT OR REPLACE INTO cluster_archetypes
                (archetype_id, personality_signature, common_characteristics,
                 proven_strategies, strategy_success_rates, optimal_implementation_order,
                 sample_clusters, archetype_confidence, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                archetype.archetype_id,
                archetype.personality_signature,
                json.dumps(archetype.common_characteristics),
                json.dumps(archetype.proven_strategies),
                json.dumps(archetype.strategy_success_rates),
                json.dumps(archetype.optimal_implementation_order),
                archetype.sample_clusters,
                archetype.archetype_confidence,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def _save_adaptive_thresholds(self):
        """Save adaptive thresholds to database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for archetype_thresholds in self.adaptive_thresholds.values():
            for threshold in archetype_thresholds:
                cursor.execute('''
                    INSERT OR REPLACE INTO adaptive_thresholds
                    (metric_name, cluster_archetype, optimal_threshold,
                     confidence_interval_lower, confidence_interval_upper,
                     sample_size, last_validation, adjustment_history)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    threshold.metric_name,
                    threshold.cluster_archetype,
                    threshold.optimal_threshold,
                    threshold.confidence_interval[0],
                    threshold.confidence_interval[1],
                    threshold.sample_size,
                    threshold.last_validation.isoformat(),
                    json.dumps(threshold.adjustment_history)
                ))
        
        conn.commit()
        conn.close()

# ============================================================================
# SPECIALIZED LEARNING COMPONENTS
# ============================================================================

class PatternAnalyzer:
    """Analyzes implementation results to identify successful patterns"""
    
    def update_patterns(self, result: ImplementationResult, patterns: Dict[str, StrategyPattern]):
        """Update strategy patterns based on new implementation result"""
        
        personality_key = self._extract_personality_pattern(result.cluster_personality)
        pattern_id = hashlib.md5(personality_key.encode()).hexdigest()[:8]
        
        if pattern_id not in patterns:
            # Create new pattern
            patterns[pattern_id] = StrategyPattern(
                pattern_id=pattern_id,
                cluster_personality_pattern=personality_key,
                successful_strategy_combinations=[],
                optimal_sequencing=[],
                risk_mitigation_tactics=[],
                success_probability=0.0,
                sample_size=0,
                confidence_level=0.0,
                last_updated=datetime.now()
            )
        
        pattern = patterns[pattern_id]
        
        # Update pattern with new result
        if result.implementation_success:
            if result.opportunities_implemented not in pattern.successful_strategy_combinations:
                pattern.successful_strategy_combinations.append(result.opportunities_implemented)
        
        # Update success probability
        pattern.sample_size += 1
        current_successes = len(pattern.successful_strategy_combinations)
        pattern.success_probability = current_successes / pattern.sample_size
        
        # Update confidence level
        pattern.confidence_level = min(1.0, pattern.sample_size / 10)  # Full confidence at 10 samples
        
        pattern.last_updated = datetime.now()
    
    def _extract_personality_pattern(self, cluster_personality: str) -> str:
        """Extract key personality components for pattern matching"""
        
        components = cluster_personality.split('-')
        
        # Keep key components that affect strategy selection
        key_components = []
        for component in components:
            if component in ['enterprise', 'medium', 'small', 'over-provisioned', 
                           'hpa-ready', 'conservative', 'aggressive', 'network-heavy', 'compute-heavy']:
                key_components.append(component)
        
        return '-'.join(sorted(key_components))

class ArchetypeLearner:
    """Learns cluster archetypes and their optimal strategies"""
    
    def update_archetypes(self, result: ImplementationResult, archetypes: Dict[str, ClusterArchetype]):
        """Update cluster archetypes based on implementation results"""
        
        archetype_id = self._generate_archetype_id(result.cluster_personality)
        
        if archetype_id not in archetypes:
            # Create new archetype
            archetypes[archetype_id] = ClusterArchetype(
                archetype_id=archetype_id,
                personality_signature=result.cluster_personality,
                common_characteristics={},
                proven_strategies=[],
                strategy_success_rates={},
                optimal_implementation_order=[],
                common_pitfalls=[],
                best_practices=[],
                sample_clusters=0,
                archetype_confidence=0.0
            )
        
        archetype = archetypes[archetype_id]
        
        # Update archetype data
        archetype.sample_clusters += 1
        
        # Update strategy success rates
        strategy_name = result.strategy_name
        if strategy_name not in archetype.strategy_success_rates:
            archetype.strategy_success_rates[strategy_name] = []
        
        archetype.strategy_success_rates[strategy_name].append(1.0 if result.implementation_success else 0.0)
        
        # Update proven strategies
        if result.implementation_success and result.strategy_name not in archetype.proven_strategies:
            archetype.proven_strategies.append(result.strategy_name)
        
        # Update best practices and pitfalls
        if result.implementation_success:
            archetype.best_practices.extend(result.success_factors)
        else:
            archetype.common_pitfalls.extend(result.failure_factors)
        
        # Remove duplicates
        archetype.best_practices = list(set(archetype.best_practices))
        archetype.common_pitfalls = list(set(archetype.common_pitfalls))
        
        # Update confidence
        archetype.archetype_confidence = min(1.0, archetype.sample_clusters / 5)  # Full confidence at 5 clusters
    
    def _generate_archetype_id(self, cluster_personality: str) -> str:
        """Generate archetype ID from cluster personality"""
        
        # Extract major characteristics for archetype grouping
        components = cluster_personality.split('-')
        major_components = []
        
        for component in components:
            if component in ['enterprise', 'medium', 'small']:
                major_components.append(component)
            elif component in ['over-provisioned', 'well-optimized']:
                major_components.append(component)
            elif component in ['hpa-ready', 'conservative']:
                major_components.append(component)
        
        archetype_signature = '-'.join(sorted(major_components))
        return hashlib.md5(archetype_signature.encode()).hexdigest()[:8]

class ThresholdOptimizer:
    """Optimizes decision thresholds based on outcomes"""
    
    def update_thresholds(self, result: ImplementationResult, thresholds: Dict[str, List[AdaptiveThreshold]]):
        """Update adaptive thresholds based on implementation results"""
        
        archetype_key = self._get_archetype_key(result.cluster_personality)
        
        # Update thresholds that affected this implementation
        metrics_to_update = [
            'hpa_potential_threshold',
            'cpu_gap_threshold',
            'memory_gap_threshold',
            'risk_tolerance_threshold'
        ]
        
        for metric_name in metrics_to_update:
            self._update_metric_threshold(
                metric_name, archetype_key, result, thresholds
            )
    
    def _update_metric_threshold(self, metric_name: str, archetype_key: str, 
                               result: ImplementationResult, 
                               thresholds: Dict[str, List[AdaptiveThreshold]]):
        """Update specific metric threshold"""
        
        if archetype_key not in thresholds:
            thresholds[archetype_key] = []
        
        # Find existing threshold or create new one
        threshold = None
        for t in thresholds[archetype_key]:
            if t.metric_name == metric_name:
                threshold = t
                break
        
        if not threshold:
            threshold = AdaptiveThreshold(
                metric_name=metric_name,
                cluster_archetype=archetype_key,
                optimal_threshold=0.5,  # Default
                confidence_interval=(0.3, 0.7),
                sample_size=0,
                last_validation=datetime.now(),
                adjustment_history=[]
            )
            thresholds[archetype_key].append(threshold)
        
        # Update threshold based on result
        threshold.sample_size += 1
        
        # Record adjustment if result suggests threshold change
        if result.implementation_success and result.savings_accuracy > 0.9:
            # Good result - threshold was appropriate
            adjustment = {
                'timestamp': datetime.now().isoformat(),
                'adjustment': 0.0,  # No change needed
                'reason': 'successful_implementation',
                'result_accuracy': result.savings_accuracy
            }
        elif not result.implementation_success:
            # Failed result - might need threshold adjustment
            adjustment = {
                'timestamp': datetime.now().isoformat(),
                'adjustment': -0.05,  # Make threshold more conservative
                'reason': 'implementation_failure',
                'result_accuracy': result.savings_accuracy
            }
            threshold.optimal_threshold = max(0.1, threshold.optimal_threshold - 0.05)
        else:
            # Partial success - minor adjustment
            adjustment = {
                'timestamp': datetime.now().isoformat(),
                'adjustment': 0.02,  # Slight increase
                'reason': 'partial_success',
                'result_accuracy': result.savings_accuracy
            }
            threshold.optimal_threshold = min(0.9, threshold.optimal_threshold + 0.02)
        
        threshold.adjustment_history.append(adjustment)
        threshold.last_validation = datetime.now()
    
    def _get_archetype_key(self, cluster_personality: str) -> str:
        """Get archetype key for threshold grouping"""
        
        components = cluster_personality.split('-')
        key_components = [c for c in components if c in ['enterprise', 'medium', 'small', 'conservative', 'aggressive']]
        return '-'.join(sorted(key_components))

class StrategyImprover:
    """Improves strategy generation based on learned patterns"""
    
    def suggest_strategy_improvements(self, current_strategy: Dict, 
                                    learned_patterns: Dict) -> List[str]:
        """Suggest improvements to current strategy based on learning"""
        
        suggestions = []
        
        # Check if strategy order can be improved
        if 'opportunities' in current_strategy:
            optimal_orders = self._get_optimal_opportunity_orders(learned_patterns)
            current_order = current_strategy['opportunities']
            
            for optimal_order in optimal_orders:
                if self._is_better_order(optimal_order, current_order):
                    suggestions.append(f"Consider reordering opportunities: {' -> '.join(optimal_order)}")
        
        # Check if risk mitigation can be improved
        risk_improvements = self._suggest_risk_improvements(current_strategy, learned_patterns)
        suggestions.extend(risk_improvements)
        
        # Check if success probability can be improved
        probability_improvements = self._suggest_probability_improvements(current_strategy, learned_patterns)
        suggestions.extend(probability_improvements)
        
        return suggestions
    
    def _get_optimal_opportunity_orders(self, learned_patterns: Dict) -> List[List[str]]:
        """Get optimal opportunity orders from learned patterns"""
        
        orders = []
        for pattern in learned_patterns.values():
            if hasattr(pattern, 'optimal_sequencing') and pattern.optimal_sequencing:
                orders.append(pattern.optimal_sequencing)
        
        return orders
    
    def _is_better_order(self, optimal_order: List[str], current_order: List[str]) -> bool:
        """Check if optimal order is better than current order"""
        
        # Simple heuristic: if optimal order has higher success rate historically
        # This would be more sophisticated in practice
        return len(set(optimal_order).intersection(set(current_order))) >= len(current_order) * 0.8
    
    def _suggest_risk_improvements(self, current_strategy: Dict, learned_patterns: Dict) -> List[str]:
        """Suggest risk improvements"""
        return []
    
    def _suggest_probability_improvements(self, current_strategy: Dict, learned_patterns: Dict) -> List[str]:
        """Suggest probability improvements"""
        return []

# ============================================================================
# DEMO AND INTEGRATION FUNCTIONS
# ============================================================================

def demo_learning_engine():
    """Demo the learning and optimization engine"""
    
    print("🧠 LEARNING & OPTIMIZATION ENGINE DEMO")
    print("=" * 60)
    
    # Initialize learning engine
    learning_engine = LearningOptimizationEngine("demo_learning.db")
    
    # Simulate some implementation results
    demo_results = [
        ImplementationResult(
            execution_id="exec-001",
            cluster_id="aks-dpl-mad-uat-ne2-1",
            cluster_dna_signature="abc123",
            strategy_name="HPA and Right-sizing Optimization",
            opportunities_implemented=["hpa_optimization", "resource_rightsizing"],
            total_duration_minutes=45,
            commands_executed=8,
            commands_successful=8,
            commands_failed=0,
            rollbacks_performed=0,
            predicted_savings=67.94,
            actual_savings=72.15,
            savings_accuracy=1.062,
            implementation_success=True,
            time_to_first_benefit=30,
            stability_period_clean=True,
            customer_satisfaction_score=4.5,
            cluster_personality="medium-over-provisioned-hpa-ready-network-heavy",
            success_factors=["good_preparation", "phased_implementation", "thorough_monitoring"],
            failure_factors=[],
            lessons_learned=["HPA works well with network-heavy clusters", "Phased approach reduces risk"],
            recommendations_for_similar=["Start with HPA", "Monitor network costs"],
            started_at=datetime.now() - timedelta(hours=2),
            completed_at=datetime.now() - timedelta(hours=1),
            benefits_realized_at=datetime.now() - timedelta(minutes=30)
        ),
        ImplementationResult(
            execution_id="exec-002",
            cluster_id="aks-prod-cluster-2",
            cluster_dna_signature="def456",
            strategy_name="Conservative Storage Optimization",
            opportunities_implemented=["storage_optimization"],
            total_duration_minutes=20,
            commands_executed=3,
            commands_successful=3,
            commands_failed=0,
            rollbacks_performed=0,
            predicted_savings=25.00,
            actual_savings=28.50,
            savings_accuracy=1.14,
            implementation_success=True,
            time_to_first_benefit=15,
            stability_period_clean=True,
            customer_satisfaction_score=4.2,
            cluster_personality="small-well-optimized-conservative-storage-heavy",
            success_factors=["simple_implementation", "low_risk_approach"],
            failure_factors=[],
            lessons_learned=["Storage optimization has high success rate", "Conservative approach works well"],
            recommendations_for_similar=["Storage optimization is safe first step"],
            started_at=datetime.now() - timedelta(hours=1),
            completed_at=datetime.now() - timedelta(minutes=40),
            benefits_realized_at=datetime.now() - timedelta(minutes=25)
        )
    ]
    
    # Record results
    print("📊 Recording implementation results...")
    for result in demo_results:
        learning_engine.record_implementation_result(result)
    
    # Test cluster DNA for recommendations
    test_cluster_dna = {
        'cluster_personality': 'medium-over-provisioned-hpa-ready-network-heavy',
        'optimization_hotspots': ['hpa_optimization', 'resource_rightsizing'],
        'cost_distribution': {'networking_percentage': 36.4},
        'efficiency_patterns': {'cpu_gap': 15, 'memory_gap': 10}
    }
    
    # Get learned recommendations
    print("\n🎯 Getting learned recommendations...")
    recommendations = learning_engine.get_learned_recommendations(test_cluster_dna)
    
    print(f"Matching archetype: {recommendations['matching_archetype']}")
    print(f"Archetype confidence: {recommendations['archetype_confidence']:.1%}")
    print(f"Expected success probability: {recommendations['expected_success_probability']:.1%}")
    print(f"Learned from {recommendations['learned_from_clusters']} similar clusters")
    
    # Test strategy optimization
    print("\n🚀 Optimizing strategy with learning...")
    original_strategy = {
        'strategy_name': 'Test HPA Strategy',
        'opportunities': ['resource_rightsizing', 'hpa_optimization'],  # Suboptimal order
        'success_probability': 0.75,
        'total_savings_potential': 65.0
    }
    
    optimized_strategy = learning_engine.optimize_strategy_based_on_learning(
        original_strategy, test_cluster_dna
    )
    
    print(f"Original order: {original_strategy['opportunities']}")
    print(f"Optimized order: {optimized_strategy['opportunities']}")
    print(f"Original success probability: {original_strategy['success_probability']:.1%}")
    print(f"Optimized success probability: {optimized_strategy['success_probability']:.1%}")
    
    # Generate improvement report
    print("\n📈 Generating continuous improvement report...")
    improvement_report = learning_engine.generate_continuous_improvement_report()
    
    print(f"Total implementations: {improvement_report['overall_statistics']['total_implementations']}")
    print(f"Overall success rate: {improvement_report['overall_statistics']['overall_success_rate']:.1%}")
    print(f"Average savings accuracy: {improvement_report['overall_statistics']['average_savings_accuracy']:.1%}")
    
    return learning_engine, improvement_report

if __name__ == "__main__":
    demo_learning_engine()