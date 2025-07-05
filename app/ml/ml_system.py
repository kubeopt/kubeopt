"""
FIXED ML SYSTEM INTEGRATION
===========================
Fixed import paths and made it work with your actual project structure.
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Optional

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

logger = logging.getLogger(__name__)

# ============================================================================
# LEARNING INTEGRATION CLASSES (Fixed)
# ============================================================================

class MLLearningIntegrationMixin:
    """Add learning integration to existing classes"""
    
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
        logger.debug(f"📊 Feedback: {feedback_type} from {component}")

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
        else:
            logger.warning(f"⚠️ {name} doesn't support learning integration")
    
    def learn_from_implementation_result(self, result: Dict):
        """Learn from results"""
        try:
            if self.learning_engine and hasattr(self.learning_engine, 'record_enhanced_implementation_result'):
                enhanced_result = self._convert_to_enhanced_result(result)
                self.learning_engine.record_enhanced_implementation_result(enhanced_result)
                logger.info(f"🧠 Learning recorded for {result.get('execution_id', 'unknown')}")
            else:
                logger.info(f"📊 Learning result logged: {result.get('execution_id', 'unknown')}")
        except Exception as e:
            logger.warning(f"⚠️ Learning failed: {e}")
    
    def _convert_to_enhanced_result(self, result: Dict):
        """Convert to enhanced result format"""
        # Try to import the actual class, fallback to simple object
        try:
            from learn_optimize import EnhancedImplementationResult
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
        except ImportError:
            # Fallback to simple object
            class SimpleEnhancedResult:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
                    # Set required attributes
                    self.execution_id = data.get('execution_id', f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    self.implementation_success = data.get('success', True)
                    self.actual_savings = data.get('actual_savings', 0)
                    self.predicted_savings = data.get('predicted_savings', 0)
            
            return SimpleEnhancedResult(result)

# ============================================================================
# MOCK COMPONENTS (for testing when your components aren't available)
# ============================================================================

class MockLearningEngine:
    """Mock learning engine for testing"""
    def __init__(self):
        self.models_trained = True
        logger.info("🤖 Mock learning engine initialized")
    
    def apply_enhanced_learning_to_strategy(self, cluster_dna, strategy):
        """Mock learning application"""
        return {
            'confidence_boost': 15.0,
            'ml_prediction_confidence': 0.85,
            'learning_applied': True,
            'recommendations': ['Use phased approach', 'Monitor closely'],
            'learning_quality': 'Good'
        }
    
    def record_enhanced_implementation_result(self, result):
        """Mock result recording"""
        logger.info(f"🧠 Mock learning recorded: {getattr(result, 'execution_id', 'unknown')}")

class MockImplementationGenerator(MLLearningIntegrationMixin):
    """Mock implementation generator for testing"""
    
    def __init__(self):
        super().__init__()
        logger.info("🎯 Mock implementation generator initialized")
    
    def generate_implementation_plan(self, analysis_results: Dict) -> Dict:
        """Mock plan generation with learning integration"""
        
        cluster_name = analysis_results.get('cluster_name', 'unknown')
        total_savings = analysis_results.get('total_savings', 0)
        
        # Mock learning integration
        if self._learning_enabled:
            self.report_outcome_for_learning('plan_generated', {
                'cluster_name': cluster_name,
                'total_savings': total_savings,
                'phases_count': 5
            })
        
        return {
            'implementation_phases': [
                {'title': 'Assessment', 'savings': 0},
                {'title': 'HPA Implementation', 'savings': analysis_results.get('hpa_savings', 0)},
                {'title': 'Right-sizing', 'savings': analysis_results.get('right_sizing_savings', 0)},
                {'title': 'Storage Optimization', 'savings': analysis_results.get('storage_savings', 0)},
                {'title': 'Validation', 'savings': 0}
            ],
            'total_savings': total_savings,
            'learning_enhanced': self._learning_enabled
        }

class MockDNAAnalyzer(MLLearningIntegrationMixin):
    """Mock DNA analyzer for testing"""
    
    def __init__(self):
        super().__init__()
        logger.info("🧬 Mock DNA analyzer initialized")
    
    def analyze_cluster_dna(self, analysis_results: Dict):
        """Mock DNA analysis with learning integration"""
        
        cluster_name = analysis_results.get('cluster_name', 'unknown')
        total_cost = analysis_results.get('total_cost', 0)
        
        # Create mock DNA
        class MockDNA:
            def __init__(self):
                self.cluster_personality = 'production-stable'
                self.uniqueness_score = 0.75
                self.optimization_readiness_score = 0.85
        
        dna = MockDNA()
        
        # Mock learning integration
        if self._learning_enabled:
            self.report_outcome_for_learning('dna_analysis_completed', {
                'cluster_name': cluster_name,
                'cluster_personality': dna.cluster_personality,
                'uniqueness_score': dna.uniqueness_score
            })
        
        return dna

# ============================================================================
# INTEGRATION FUNCTIONS (Fixed)
# ============================================================================

def create_integrated_ml_system():
    """Create integrated system with proper error handling"""
    
    print("🚀 Creating integrated ML system...")
    
    # Try to import your actual components, fallback to mocks
    learning_engine = None
    implementation_generator = None
    dna_analyzer = None
    
    # Try to import your actual learning engine
    try:
        from learn_optimize import create_enhanced_learning_engine
        learning_engine = create_enhanced_learning_engine()
        print("✅ Loaded your actual learning engine")
    except ImportError as e:
        print(f"⚠️ Could not import learning engine ({e}), using mock")
        learning_engine = MockLearningEngine()
    
    # Try to import your actual implementation generator
    try:
        from implementation_generator import FixedAKSImplementationGenerator
        implementation_generator = FixedAKSImplementationGenerator()
        print("✅ Loaded your actual implementation generator")
    except ImportError as e:
        print(f"⚠️ Could not import implementation generator ({e}), using mock")
        implementation_generator = MockImplementationGenerator()
    
    # Try to import your actual DNA analyzer
    try:
        from dna_analyzer import ClusterDNAAnalyzer
        dna_analyzer = ClusterDNAAnalyzer()
        print("✅ Loaded your actual DNA analyzer")
    except ImportError as e:
        print(f"⚠️ Could not import DNA analyzer ({e}), using mock")
        dna_analyzer = MockDNAAnalyzer()
    
    # Create orchestrator
    orchestrator = MLSystemOrchestrator(learning_engine)
    
    # Connect components
    orchestrator.connect_component('implementation_generator', implementation_generator)
    orchestrator.connect_component('dna_analyzer', dna_analyzer)
    
    return {
        'orchestrator': orchestrator,
        'learning_engine': learning_engine,
        'implementation_generator': implementation_generator,
        'dna_analyzer': dna_analyzer
    }

def test_your_integrated_system():
    """Test the integrated system"""
    
    print("🧪 TESTING YOUR INTEGRATED SYSTEM")
    print("=" * 50)
    
    # Create integrated system
    system = create_integrated_ml_system()
    
    # Your actual data
    analysis_results = {
        'cluster_name': 'aks-dpl-mad-uat-ne2-1',
        'resource_group': 'rg-dpl-mad-uat-ne2-2', 
        'total_cost': 1864.43,
        'total_savings': 71.11,
        'hpa_savings': 46.61,
        'right_sizing_savings': 21.33,
        'storage_savings': 3.17
    }
    
    # Test DNA analyzer with learning
    print("\n🧬 Testing DNA analyzer with learning...")
    dna = system['dna_analyzer'].analyze_cluster_dna(analysis_results)
    print(f"✅ DNA analyzed: {dna.cluster_personality}")
    
    # Test implementation generator with learning
    print("\n🎯 Testing implementation generator with learning...")
    plan = system['implementation_generator'].generate_implementation_plan(analysis_results)
    print(f"✅ Plan generated: {len(plan.get('implementation_phases', []))} phases")
    print(f"   Learning enhanced: {plan.get('learning_enhanced', False)}")
    
    # Test learning from results
    print("\n🧠 Testing learning from implementation results...")
    result = {
        'execution_id': 'test-001',
        'cluster_name': 'aks-dpl-mad-uat-ne2-1',
        'success': True,
        'actual_savings': 65.0,
        'predicted_savings': 71.11,
        'cluster_personality': dna.cluster_personality
    }
    system['orchestrator'].learn_from_implementation_result(result)
    print("✅ Learning result recorded")
    
    # Show learning status
    print(f"\n📊 Connected components: {len(system['orchestrator'].connected_components)}")
    print(f"📊 Feedback items: {len(system['orchestrator'].learning_feedback.feedback_buffer)}")
    
    print("\n" + "=" * 50)
    print("✅ INTEGRATION TEST COMPLETE!")
    
    if any('Mock' in str(type(component)) for component in [
        system['learning_engine'], 
        system['implementation_generator'], 
        system['dna_analyzer']
    ]):
        print("⚠️  Some components using mocks - update your imports once you add the integration mixin")
        print("\n🔧 TO USE YOUR ACTUAL COMPONENTS:")
        print("1. Add MLLearningIntegrationMixin to your existing classes")
        print("2. Add super().__init__() to their __init__ methods")
        print("3. Run this test again")
    else:
        print("🎯 ALL YOUR ACTUAL COMPONENTS CONNECTED WITH LEARNING!")
    
    return system

def demonstrate_learning_flow():
    """Demonstrate the learning flow"""
    
    print("\n🧠 DEMONSTRATING LEARNING FLOW")
    print("=" * 40)
    
    system = create_integrated_ml_system()
    
    # Simulate multiple optimizations to show learning
    scenarios = [
        {
            'cluster_name': 'prod-cluster-1',
            'total_cost': 2000,
            'total_savings': 150,
            'actual_result': {'success': True, 'actual_savings': 145}
        },
        {
            'cluster_name': 'dev-cluster-1', 
            'total_cost': 500,
            'total_savings': 50,
            'actual_result': {'success': True, 'actual_savings': 48}
        },
        {
            'cluster_name': 'test-cluster-1',
            'total_cost': 800,
            'total_savings': 80,
            'actual_result': {'success': False, 'actual_savings': 20}
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i}: {scenario['cluster_name']} ---")
        
        # Generate plan
        analysis = {
            'cluster_name': scenario['cluster_name'],
            'total_cost': scenario['total_cost'],
            'total_savings': scenario['total_savings'],
            'hpa_savings': scenario['total_savings'] * 0.6,
            'right_sizing_savings': scenario['total_savings'] * 0.4
        }
        
        plan = system['implementation_generator'].generate_implementation_plan(analysis)
        print(f"  📋 Plan generated: {scenario['total_savings']} savings predicted")
        
        # Simulate execution result
        result = {
            'execution_id': f'exec-{i}',
            'cluster_name': scenario['cluster_name'],
            'predicted_savings': scenario['total_savings'],
            **scenario['actual_result']
        }
        
        system['orchestrator'].learn_from_implementation_result(result)
        print(f"  🧠 Learning recorded: {result['actual_savings']} actual vs {result['predicted_savings']} predicted")
    
    print(f"\n📊 Total learning items collected: {len(system['orchestrator'].learning_feedback.feedback_buffer)}")
    print("✅ Learning flow demonstrated!")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run tests
    test_your_integrated_system()
    demonstrate_learning_flow()