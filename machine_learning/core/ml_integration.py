#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

import logging
from machine_learning.core.enterprise_metrics import create_enterprise_metrics
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class MLLearningIntegrationMixin:
    """
    Add this mixin to your existing classes (no other changes needed)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ml_orchestrator = None
        self.learning_feedback = None
        self._learning_enabled = False
    
    def enable_learning_integration(self, ml_orchestrator):
        """Enable learning - called by orchestrator"""
        self.ml_orchestrator = ml_orchestrator
        self.learning_feedback = ml_orchestrator.learning_feedback
        self._learning_enabled = True
        logger.info(f"✅ Learning enabled for {self.__class__.__name__}")
    
    def report_outcome_for_learning(self, outcome_type: str, data: Dict):
        """Report outcome for learning"""
        if self._learning_enabled and self.learning_feedback:
            self.learning_feedback.add_feedback(
                component=self.__class__.__name__,
                feedback_type=outcome_type,
                data=data
            )

class LearningFeedbackSystem:
    """Simple feedback collector"""
    def __init__(self):
        self.feedback_buffer = []
    
    def add_feedback(self, component: str, feedback_type: str, data: Dict):
        self.feedback_buffer.append({
            'component': component,
            'type': feedback_type,
            'data': data,
            'timestamp': datetime.now()
        })

class MLSystemOrchestrator:
    """Simple orchestrator to connect everything"""
    def __init__(self, learning_engine):
        self.learning_engine = learning_engine
        self.learning_feedback = LearningFeedbackSystem()
        self.connected_components = {}
    
    def connect_component(self, name: str, component):
        if hasattr(component, 'enable_learning_integration'):
            component.enable_learning_integration(self)
            self.connected_components[name] = component
            logger.info(f"🔗 Connected {name}")
    
    def learn_from_implementation_result(self, result: Dict):
        """Learn from results"""
        if self.learning_engine:
            # Convert simple result to your learning engine format
            enhanced_result = self._convert_to_enhanced_result(result)
            self.learning_engine.record_enhanced_implementation_result(enhanced_result)
    
    def _convert_to_enhanced_result(self, result: Dict):
        """Convert to your EnhancedImplementationResult format"""
        from machine_learning.core.learn_optimize import EnhancedImplementationResult
        from datetime import datetime
        
        return EnhancedImplementationResult(
            execution_id=result.get('execution_id', f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            cluster_id=result.get('cluster_name', 'unknown'),
            cluster_dna_signature=result.get('cluster_dna_signature', 'unknown'),
            strategy_name=result.get('strategy_name', 'optimization'),
            opportunities_implemented=result.get('opportunities', []),
            total_duration_minutes=result.get('duration_minutes', 60),
            commands_executed=result.get('commands_executed', 10),
            commands_successful=result.get('commands_successful', 9),
            commands_failed=result.get('commands_failed', 1),
            rollbacks_performed=result.get('rollbacks', 0),
            predicted_savings=result.get('predicted_savings', 0),
            actual_savings=result.get('actual_savings', 0),
            savings_accuracy=result.get('actual_savings', 0) / max(result.get('predicted_savings', 1), 1),
            implementation_success=result.get('success', True),
            time_to_first_benefit=30,
            stability_period_clean=result.get('success', True),
            customer_satisfaction_score=4.5 if result.get('success', True) else 3.0,
            cluster_features=result.get('cluster_features', {}),
            environmental_factors=result.get('environmental_factors', {}),
            execution_context=result.get('execution_context', {}),
            post_implementation_metrics=result.get('post_metrics', {}),
            cluster_personality=result.get('cluster_personality', 'unknown'),
            success_factors=result.get('success_factors', []),
            failure_factors=result.get('failure_factors', []),
            lessons_learned=result.get('lessons_learned', []),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            benefits_realized_at=None
        )

# For backward compatibility
MLIntegrationMixin = MLLearningIntegrationMixin