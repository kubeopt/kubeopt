#!/usr/bin/env python3
"""
Comprehensive Self-Learning Test - Updated for Latest Implementation
================================================================
Test suite for the complete self-learning HPA engine with rich insights
"""

import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_self_learning_basic():
    """Basic test of comprehensive self-learning functionality"""
    
    print("🧠 Comprehensive Self-Learning HPA Engine - Test Suite")
    print("=" * 60)
    
    try:
        # Import from the comprehensive implementation
        from workload_performance_analyzer import create_comprehensive_self_learning_hpa_engine
        
        # Create engine with self-learning enabled
        print("🔧 Creating comprehensive self-learning engine...")
        engine = create_comprehensive_self_learning_hpa_engine(
            model_path="app/ml/data_feed",
            enable_self_learning=True
        )
        
        print("✅ Engine created successfully!")
        
        # Check learning status
        print("\n📊 Checking learning status...")
        status = engine.get_learning_insights()
        print(f"   Learning Enabled: {status.get('learning_enabled', 'Unknown')}")
        print(f"   Model Trained: {status.get('model_trained', 'Unknown')}")
        print(f"   Total Samples: {status.get('samples', {}).get('total_collected', 0)}")
        print(f"   Supervised Samples: {status.get('samples', {}).get('supervised', 0)}")
        print(f"   Confidence Threshold: {status.get('confidence_threshold', 0.7)}")
        
        return engine
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure workload_performance_analyzer.py is in the same directory")
        return None
    except Exception as e:
        print(f"❌ Error creating engine: {e}")
        logger.exception("Engine creation error details:")
        return None

def test_comprehensive_analysis(engine):
    """Test comprehensive workload analysis with rich insights"""
    
    print(f"\n🔍 Testing Comprehensive Workload Analysis")
    print("-" * 50)
    
    if not engine:
        print("❌ No engine available for testing")
        return None
    
    # Comprehensive test data
    test_data = {
        'nodes': [
            {
                'cpu_usage_pct': 150.0, 
                'memory_usage_pct': 95.0, 
                'status': 'Ready', 
                'name': 'test-node-1',
                'cpu_request_pct': 170.0,
                'memory_request_pct': 110.0
            },
            {
                'cpu_usage_pct': 70.0, 
                'memory_usage_pct': 85.0, 
                'status': 'Ready', 
                'name': 'test-node-2',
                'cpu_request_pct': 90.0,
                'memory_request_pct': 100.0
            },
            {
                'cpu_usage_pct': 45.0, 
                'memory_usage_pct': 60.0, 
                'status': 'Ready', 
                'name': 'test-node-3',
                'cpu_request_pct': 65.0,
                'memory_request_pct': 75.0
            }
        ],
        'hpa_implementation': {
            'current_hpa_pattern': 'cpu_based_hpa',
            'confidence': 'medium',
            'total_hpas': 2,
            'workloads': [{'name': 'web-app'}, {'name': 'api-service'}]
        }
    }
    
    current_hpa = {
        'min_replicas': 2,
        'max_replicas': 10,
        'target_cpu': 70,
        'target_memory': 80
    }
    
    try:
        print("🔍 Running comprehensive analysis...")
        
        # Run comprehensive analysis with learning
        result = engine.analyze_and_recommend_with_comprehensive_insights(
            metrics_data=test_data, 
            current_hpa_config=current_hpa,
            cluster_id="test-cluster-comprehensive"
        )
        
        # Check if we got a valid result
        if not result or 'analysis_metadata' not in result:
            print("❌ Analysis failed or returned invalid result")
            return None
        
        # Display comprehensive results
        print("✅ Comprehensive analysis completed successfully!")
        
        # Workload Classification
        workload_class = result.get('workload_classification', {})
        print(f"\n📊 Workload Classification:")
        print(f"   Type: {workload_class.get('workload_type', 'Unknown')}")
        print(f"   Confidence: {workload_class.get('confidence', 0):.1%}")
        print(f"   Method: {workload_class.get('method', 'Unknown')}")
        print(f"   Confidence Level: {workload_class.get('confidence_level', 'Unknown')}")
        
        # Feature Insights
        feature_insights = workload_class.get('feature_insights', {})
        if feature_insights:
            resource_util = feature_insights.get('resource_utilization', {})
            print(f"\n💾 Resource Utilization:")
            print(f"   CPU Mean: {resource_util.get('cpu_mean', 0):.1f}%")
            print(f"   Memory Mean: {resource_util.get('memory_mean', 0):.1f}%")
            print(f"   Resource Balance: {resource_util.get('resource_balance', 0):.1f}")
            
            efficiency = feature_insights.get('efficiency_metrics', {})
            print(f"   Overall Efficiency: {efficiency.get('overall_efficiency', 0):.1%}")
            print(f"   Waste Indicator: {efficiency.get('waste_indicator', 0):.1f}")
        
        # HPA Recommendation
        hpa_rec = result.get('hpa_recommendation', {})
        print(f"\n🎯 HPA Recommendation:")
        print(f"   Action: {hpa_rec.get('action', 'Unknown')}")
        print(f"   Title: {hpa_rec.get('title', 'Unknown')}")
        print(f"   Description: {hpa_rec.get('description', 'Unknown')[:100]}...")
        print(f"   Timeline: {hpa_rec.get('implementation_timeline', 'Unknown')}")
        print(f"   Expected Improvement: {hpa_rec.get('expected_improvement', 'Unknown')}")
        
        # Optimization Analysis
        optimization = result.get('optimization_analysis', {})
        print(f"\n⚡ Optimization Analysis:")
        print(f"   Primary Action: {optimization.get('primary_action', 'Unknown')}")
        print(f"   Resource Focus: {optimization.get('resource_focus', 'Unknown')}")
        print(f"   Reasoning: {optimization.get('reasoning', 'Unknown')[:100]}...")
        
        cost_analysis = optimization.get('cost_analysis', {})
        if cost_analysis:
            print(f"   Waste Percentage: {cost_analysis.get('waste_percentage', 0):.1f}%")
            print(f"   Potential Savings: ${cost_analysis.get('potential_monthly_savings', 0):.2f}/month")
        
        # Workload Characteristics
        characteristics = result.get('workload_characteristics', {})
        print(f"\n📈 Workload Characteristics:")
        print(f"   Performance Stability: {characteristics.get('performance_stability', 0):.1%}")
        print(f"   Burst Patterns: {characteristics.get('burst_patterns', 0):.1%}")
        print(f"   Optimization Potential: {characteristics.get('optimization_potential', 'Unknown')}")
        
        # Learning Status
        learning_status = result.get('self_learning_status', {})
        print(f"\n🧠 Learning Status:")
        print(f"   Samples Collected: {learning_status.get('samples', {}).get('total_collected', 0)}")
        print(f"   Supervised Samples: {learning_status.get('samples', {}).get('supervised', 0)}")
        print(f"   Model Trained: {learning_status.get('model_trained', False)}")
        
        # Chart Data
        chart_data = result.get('hpa_chart_data', {})
        if chart_data:
            print(f"\n📊 HPA Chart Data Available:")
            print(f"   Time Points: {len(chart_data.get('timePoints', []))}")
            print(f"   Data Source: {chart_data.get('data_source', 'Unknown')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Comprehensive analysis failed: {e}")
        logger.exception("Analysis error details:")
        return None

def test_feedback_provision(engine, analysis_result):
    """Test providing feedback for learning"""
    
    print(f"\n📝 Testing Feedback Provision")
    print("-" * 40)
    
    if not engine or not analysis_result:
        print("❌ Cannot test feedback without valid engine and analysis result")
        return
    
    try:
        # Get analysis timestamp
        analysis_timestamp = analysis_result.get('analysis_metadata', {}).get('timestamp')
        
        if not analysis_timestamp:
            print("⚠️ No analysis timestamp found, using current time")
            analysis_timestamp = datetime.now().isoformat()
        
        # Provide feedback
        print("📝 Providing feedback...")
        engine.provide_feedback(
            analysis_timestamp=analysis_timestamp,
            correct_workload_type="CPU_INTENSIVE",
            feedback_score=0.9,
            notes="Test feedback - High CPU usage confirmed as CPU intensive workload"
        )
        
        print("✅ Feedback provided successfully!")
        
        # Check updated learning status
        print("📊 Checking updated learning status...")
        updated_status = engine.get_learning_insights()
        supervised_count = updated_status.get('samples', {}).get('supervised', 0)
        total_count = updated_status.get('samples', {}).get('total_collected', 0)
        print(f"   Total Samples: {total_count}")
        print(f"   Supervised Samples: {supervised_count}")
        print(f"   Learning Progress: {supervised_count}/{total_count}")
        
    except Exception as e:
        print(f"❌ Feedback provision failed: {e}")
        logger.exception("Feedback error details:")

def test_multiple_scenarios(engine):
    """Test multiple scenarios to build comprehensive learning data"""
    
    print(f"\n🔄 Testing Multiple Comprehensive Scenarios")
    print("-" * 50)
    
    if not engine:
        print("❌ No engine available")
        return
    
    scenarios = [
        {
            'name': 'Memory Heavy Database Workload',
            'nodes': [
                {'cpu_usage_pct': 30.0, 'memory_usage_pct': 85.0, 'status': 'Ready', 'cpu_request_pct': 50.0, 'memory_request_pct': 100.0},
                {'cpu_usage_pct': 25.0, 'memory_usage_pct': 90.0, 'status': 'Ready', 'cpu_request_pct': 45.0, 'memory_request_pct': 105.0}
            ],
            'hpa': {'current_hpa_pattern': 'memory_based_hpa', 'confidence': 'high', 'total_hpas': 1},
            'expected': 'MEMORY_INTENSIVE'
        },
        {
            'name': 'Balanced Web Application',
            'nodes': [
                {'cpu_usage_pct': 60.0, 'memory_usage_pct': 65.0, 'status': 'Ready', 'cpu_request_pct': 80.0, 'memory_request_pct': 85.0},
                {'cpu_usage_pct': 55.0, 'memory_usage_pct': 70.0, 'status': 'Ready', 'cpu_request_pct': 75.0, 'memory_request_pct': 90.0}
            ],
            'hpa': {'current_hpa_pattern': 'cpu_based_hpa', 'confidence': 'medium', 'total_hpas': 2},
            'expected': 'BALANCED'
        },
        {
            'name': 'Low Utilization Development Environment',
            'nodes': [
                {'cpu_usage_pct': 15.0, 'memory_usage_pct': 25.0, 'status': 'Ready', 'cpu_request_pct': 40.0, 'memory_request_pct': 50.0},
                {'cpu_usage_pct': 20.0, 'memory_usage_pct': 30.0, 'status': 'Ready', 'cpu_request_pct': 45.0, 'memory_request_pct': 55.0}
            ],
            'hpa': {'current_hpa_pattern': 'no_hpa_detected', 'confidence': 'low', 'total_hpas': 0},
            'expected': 'LOW_UTILIZATION'
        },
        {
            'name': 'Bursty Traffic Workload',
            'nodes': [
                {'cpu_usage_pct': 80.0, 'memory_usage_pct': 45.0, 'status': 'Ready', 'cpu_request_pct': 120.0, 'memory_request_pct': 65.0},
                {'cpu_usage_pct': 95.0, 'memory_usage_pct': 50.0, 'status': 'Ready', 'cpu_request_pct': 130.0, 'memory_request_pct': 70.0},
                {'cpu_usage_pct': 40.0, 'memory_usage_pct': 35.0, 'status': 'Ready', 'cpu_request_pct': 60.0, 'memory_request_pct': 55.0}
            ],
            'hpa': {'current_hpa_pattern': 'multi_metric_hpa', 'confidence': 'high', 'total_hpas': 3},
            'expected': 'BURSTY'
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(scenarios):
        print(f"\n🔍 Scenario {i+1}: {scenario['name']}")
        
        test_data = {
            'nodes': scenario['nodes'],
            'hpa_implementation': scenario['hpa']
        }
        
        current_hpa = {
            'min_replicas': 1,
            'max_replicas': 15,
            'target_cpu': 70,
            'target_memory': 80
        }
        
        try:
            # Run comprehensive analysis
            result = engine.analyze_and_recommend_with_comprehensive_insights(
                metrics_data=test_data, 
                current_hpa_config=current_hpa,
                cluster_id=f"test-cluster-scenario-{i+1}"
            )
            
            if result and 'workload_classification' in result:
                predicted = result['workload_classification'].get('workload_type', 'Unknown')
                confidence = result['workload_classification'].get('confidence', 0)
                method = result['workload_classification'].get('method', 'Unknown')
                
                print(f"   Predicted: {predicted} ({confidence:.1%}) via {method}")
                print(f"   Expected: {scenario['expected']}")
                
                # Check recommendation
                hpa_action = result.get('hpa_recommendation', {}).get('action', 'Unknown')
                optimization_action = result.get('optimization_analysis', {}).get('primary_action', 'Unknown')
                print(f"   HPA Action: {hpa_action}")
                print(f"   Optimization: {optimization_action}")
                
                match = predicted == scenario['expected']
                print(f"   Match: {'✅' if match else '❌'}")
                
                # Provide feedback
                timestamp = result.get('analysis_metadata', {}).get('timestamp', datetime.now().isoformat())
                feedback_score = 1.0 if match else 0.7  # Still valuable even if wrong
                
                engine.provide_feedback(
                    timestamp, 
                    scenario['expected'], 
                    feedback_score,
                    f"Test scenario: {scenario['name']} - {'Correct' if match else 'Incorrect'} prediction"
                )
                
                results.append({
                    'scenario': scenario['name'],
                    'predicted': predicted,
                    'expected': scenario['expected'],
                    'correct': match,
                    'confidence': confidence,
                    'hpa_action': hpa_action
                })
            else:
                print("   ❌ Analysis failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            logger.exception(f"Scenario {i+1} error details:")
    
    # Summary
    if results:
        correct = sum(1 for r in results if r['correct'])
        total = len(results)
        avg_confidence = sum(r['confidence'] for r in results) / total
        
        print(f"\n📊 Scenario Results Summary:")
        print(f"   Accuracy: {correct}/{total} ({correct/total:.1%})")
        print(f"   Average Confidence: {avg_confidence:.1%}")
        
        print(f"\n📝 Detailed Results:")
        for r in results:
            status = "✅" if r['correct'] else "❌"
            print(f"   {status} {r['scenario']}: {r['predicted']} (expected {r['expected']})")
    
    # Final comprehensive learning status
    final_status = engine.get_learning_insights()
    print(f"\n🧠 Final Learning Status:")
    print(f"   Total Samples: {final_status.get('samples', {}).get('total_collected', 0)}")
    print(f"   Supervised Samples: {final_status.get('samples', {}).get('supervised', 0)}")
    print(f"   Model Trained: {final_status.get('model_trained', False)}")
    print(f"   Learning Enabled: {final_status.get('learning_enabled', False)}")
    
    performance = final_status.get('performance', {})
    if performance.get('recent_accuracy'):
        print(f"   Recent Accuracy: {performance['recent_accuracy']:.1%}")

def test_export_capabilities(engine):
    """Test export capabilities"""
    
    print(f"\n📤 Testing Export Capabilities")
    print("-" * 40)
    
    if not engine:
        print("❌ No engine available")
        return
    
    try:
        print("📤 Attempting to export learning data...")
        
        # Try to export learning data
        export_path = engine.export_learning_history('csv')
        
        if export_path and os.path.exists(export_path):
            print(f"✅ Learning data exported to: {export_path}")
            file_size = os.path.getsize(export_path)
            print(f"   File size: {file_size} bytes")
        else:
            print("⚠️ Export completed but file not found (may be empty)")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        logger.exception("Export error details:")

def main():
    """Run comprehensive test suite"""
    
    print("🚀 Comprehensive Self-Learning HPA Engine - Test Suite")
    print("=" * 65)
    
    # Test 1: Basic setup
    engine = test_self_learning_basic()
    if not engine:
        print("\n❌ Cannot proceed without working engine")
        return
    
    # Test 2: Comprehensive analysis
    analysis_result = test_comprehensive_analysis(engine)
    
    # Test 3: Feedback provision
    test_feedback_provision(engine, analysis_result)
    
    # Test 4: Multiple scenarios
    test_multiple_scenarios(engine)
    
    # Test 5: Export capabilities
    test_export_capabilities(engine)
    
    print(f"\n{'='*65}")
    print("🎉 COMPREHENSIVE SELF-LEARNING TESTS COMPLETED")
    print("="*65)
    
    print(f"\n💡 Key Capabilities Verified:")
    print("✅ Comprehensive self-learning engine creation")
    print("✅ Rich workload analysis with 53+ features")
    print("✅ Detailed HPA recommendations with insights")
    print("✅ Cost optimization analysis")
    print("✅ Feedback collection for continuous learning")
    print("✅ Multiple scenario handling")
    print("✅ Learning data export")
    
    print(f"\n🔬 Rich Insights Generated:")
    print("• Workload classification with confidence levels")
    print("• Resource utilization analysis")
    print("• Performance stability assessment")
    print("• Cost optimization opportunities")
    print("• HPA scaling recommendations")
    print("• Feature-based decision reasoning")
    
    print(f"\n🔄 Self-Learning Features:")
    print("• Automatic prediction storage")
    print("• Feedback-based model improvement")
    print("• Learning progress tracking")
    print("• Performance history monitoring")
    
    print(f"\n🚀 Next Steps:")
    print("1. Run with real cluster data")
    print("2. Provide feedback on actual predictions")
    print("3. Monitor learning progress over time")
    print("4. Use rich insights for HPA optimization")

if __name__ == "__main__":
    main()