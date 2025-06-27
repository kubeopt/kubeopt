#!/usr/bin/env python3
"""
ML Model Testing and Validation Script
=====================================
Test your trained models with real or synthetic data
"""

import numpy as np
import pandas as pd
import json
import joblib
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLModelTester:
    """
    Comprehensive testing suite for trained ML models
    """
    
    def __init__(self):
        self.pattern_classifier = None
        self.scaler = None
        self.model_info = None
        self.is_loaded = False
        
    def load_models(self):
        """Load the trained models"""
        try:
            logger.info("📥 Loading trained models...")
            
            # Load models
            self.pattern_classifier = joblib.load('workload_pattern_classifier.pkl')
            self.scaler = joblib.load('workload_feature_scaler.pkl')
            
            # Load model info
            with open('model_info.json', 'r') as f:
                self.model_info = json.load(f)
            
            self.is_loaded = True
            logger.info("✅ Models loaded successfully")
            logger.info(f"📊 Model supports {len(self.model_info['classes'])} classes: {self.model_info['classes']}")
            
            return True
            
        except FileNotFoundError as e:
            logger.error(f"❌ Model files not found: {e}")
            logger.error("💡 Run the training script first: python ml_trainer.py")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            return False
    
    def test_with_sample_data(self):
        """Test with various sample scenarios"""
        if not self.is_loaded:
            logger.error("❌ Models not loaded")
            return
        
        logger.info("🧪 Testing with sample scenarios...")
        
        # Define test scenarios
        test_scenarios = [
            {
                'name': 'High CPU Web Server',
                'nodes': [
                    {'cpu_usage_pct': 85.0, 'memory_usage_pct': 45.0, 'ready': True},
                    {'cpu_usage_pct': 88.0, 'memory_usage_pct': 42.0, 'ready': True},
                    {'cpu_usage_pct': 82.0, 'memory_usage_pct': 48.0, 'ready': True}
                ],
                'hpa_implementation': {
                    'current_hpa_pattern': 'cpu_based_dominant',
                    'confidence': 'high',
                    'total_hpas': 2
                },
                'expected': 'CPU_INTENSIVE'
            },
            {
                'name': 'Memory-Heavy Database',
                'nodes': [
                    {'cpu_usage_pct': 35.0, 'memory_usage_pct': 85.0, 'ready': True},
                    {'cpu_usage_pct': 38.0, 'memory_usage_pct': 82.0, 'ready': True},
                    {'cpu_usage_pct': 32.0, 'memory_usage_pct': 88.0, 'ready': True}
                ],
                'hpa_implementation': {
                    'current_hpa_pattern': 'memory_based_dominant',
                    'confidence': 'high',
                    'total_hpas': 3
                },
                'expected': 'MEMORY_INTENSIVE'
            },
            {
                'name': 'Balanced Application',
                'nodes': [
                    {'cpu_usage_pct': 55.0, 'memory_usage_pct': 60.0, 'ready': True},
                    {'cpu_usage_pct': 58.0, 'memory_usage_pct': 62.0, 'ready': True},
                    {'cpu_usage_pct': 52.0, 'memory_usage_pct': 58.0, 'ready': True}
                ],
                'hpa_implementation': {
                    'current_hpa_pattern': 'hybrid_approach',
                    'confidence': 'medium',
                    'total_hpas': 2
                },
                'expected': 'BALANCED'
            },
            {
                'name': 'Bursty Traffic Pattern',
                'nodes': [
                    {'cpu_usage_pct': 25.0, 'memory_usage_pct': 40.0, 'ready': True},
                    {'cpu_usage_pct': 85.0, 'memory_usage_pct': 45.0, 'ready': True},
                    {'cpu_usage_pct': 30.0, 'memory_usage_pct': 42.0, 'ready': True},
                    {'cpu_usage_pct': 90.0, 'memory_usage_pct': 48.0, 'ready': True}
                ],
                'hpa_implementation': {
                    'current_hpa_pattern': 'mixed_implementation',
                    'confidence': 'medium',
                    'total_hpas': 1
                },
                'expected': 'BURSTY'
            },
            {
                'name': 'Low Utilization Idle',
                'nodes': [
                    {'cpu_usage_pct': 15.0, 'memory_usage_pct': 25.0, 'ready': True},
                    {'cpu_usage_pct': 18.0, 'memory_usage_pct': 28.0, 'ready': True},
                    {'cpu_usage_pct': 12.0, 'memory_usage_pct': 22.0, 'ready': True}
                ],
                'hpa_implementation': {
                    'current_hpa_pattern': 'no_hpa_detected',
                    'confidence': 'low',
                    'total_hpas': 0
                },
                'expected': 'LOW_UTILIZATION'
            }
        ]
        
        # Test each scenario
        results = []
        for scenario in test_scenarios:
            logger.info(f"\n🔍 Testing: {scenario['name']}")
            
            result = self.test_single_scenario(scenario)
            results.append(result)
            
            # Print results
            predicted = result['prediction']['workload_type']
            confidence = result['prediction']['confidence']
            expected = scenario['expected']
            
            status = "✅ CORRECT" if predicted == expected else "❌ INCORRECT"
            logger.info(f"   Expected: {expected}")
            logger.info(f"   Predicted: {predicted} (confidence: {confidence:.3f})")
            logger.info(f"   Status: {status}")
        
        # Summary
        correct = sum(1 for r in results if r['correct'])
        total = len(results)
        accuracy = correct / total
        
        logger.info(f"\n📊 SUMMARY: {correct}/{total} correct ({accuracy:.1%} accuracy)")
        
        return results
    
    def test_single_scenario(self, scenario):
        """Test a single scenario"""
        try:
            # Import the analyzer
            from workload_performance_analyzer import WorkloadPatternClassifier
            
            # Create instance
            classifier = WorkloadPatternClassifier()
            
            # Extract features
            metrics_data = {
                'nodes': scenario['nodes'],
                'hpa_implementation': scenario['hpa_implementation']
            }
            
            features = classifier.extract_advanced_features(metrics_data)
            
            # Classify
            prediction = classifier.classify_workload_type(features)
            
            return {
                'scenario': scenario['name'],
                'prediction': prediction,
                'expected': scenario['expected'],
                'correct': prediction['workload_type'] == scenario['expected'],
                'features_shape': features.shape
            }
            
        except Exception as e:
            logger.error(f"❌ Test failed for {scenario['name']}: {e}")
            return {
                'scenario': scenario['name'],
                'prediction': {'workload_type': 'ERROR', 'confidence': 0.0},
                'expected': scenario['expected'],
                'correct': False,
                'error': str(e)
            }
    
    def test_with_your_data(self, nodes_data, hpa_data=None):
        """
        Test with your actual data
        
        Args:
            nodes_data: List of node dictionaries with cpu_usage_pct, memory_usage_pct, ready
            hpa_data: Optional HPA implementation data
        """
        logger.info("🔬 Testing with your custom data...")
        
        if not nodes_data:
            logger.error("❌ No nodes data provided")
            return None
        
        # Default HPA data if not provided
        if not hpa_data:
            hpa_data = {
                'current_hpa_pattern': 'no_hpa_detected',
                'confidence': 'low',
                'total_hpas': 0
            }
        
        try:
            # Import the analyzer
            from workload_performance_analyzer import WorkloadPatternClassifier
            
            # Create instance
            classifier = WorkloadPatternClassifier()
            
            # Prepare data
            metrics_data = {
                'nodes': nodes_data,
                'hpa_implementation': hpa_data
            }
            
            # Extract features
            features = classifier.extract_advanced_features(metrics_data)
            logger.info(f"📊 Extracted {features.shape[1]} features from {len(nodes_data)} nodes")
            
            # Classify
            prediction = classifier.classify_workload_type(features)
            
            # Detailed analysis
            logger.info(f"\n🎯 ANALYSIS RESULTS:")
            logger.info(f"   Workload Type: {prediction['workload_type']}")
            logger.info(f"   Confidence: {prediction['confidence']:.3f}")
            logger.info(f"   Method: {prediction['method']}")
            
            if 'feature_importance' in prediction:
                logger.info(f"   Key Factors:")
                for factor, value in prediction['feature_importance'].items():
                    logger.info(f"     - {factor}: {value:.2f}")
            
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Custom data test failed: {e}")
            return None
    
    def benchmark_performance(self, n_tests=100):
        """Benchmark model performance"""
        if not self.is_loaded:
            logger.error("❌ Models not loaded")
            return
        
        logger.info(f"⚡ Running performance benchmark ({n_tests} tests)...")
        
        # Generate random test data
        from ml_trainer import MLModelTrainer
        trainer = MLModelTrainer()
        
        # Generate small dataset for benchmarking
        test_df = trainer.generate_synthetic_training_data(n_samples=n_tests)
        
        import time
        times = []
        
        try:
            # Import the analyzer
            from workload_performance_analyzer import WorkloadPatternClassifier
            classifier = WorkloadPatternClassifier()
            
            for i in range(n_tests):
                # Create test scenario
                nodes = [
                    {
                        'cpu_usage_pct': float(test_df.iloc[i]['cpu_mean']),
                        'memory_usage_pct': float(test_df.iloc[i]['memory_mean']),
                        'ready': True
                    }
                ]
                
                metrics_data = {
                    'nodes': nodes,
                    'hpa_implementation': {
                        'current_hpa_pattern': 'cpu_based_dominant',
                        'confidence': 'medium',
                        'total_hpas': 1
                    }
                }
                
                # Time the classification
                start_time = time.time()
                features = classifier.extract_advanced_features(metrics_data)
                prediction = classifier.classify_workload_type(features)
                end_time = time.time()
                
                times.append(end_time - start_time)
            
            # Calculate statistics
            avg_time = np.mean(times)
            median_time = np.median(times)
            max_time = np.max(times)
            min_time = np.min(times)
            
            logger.info(f"⚡ PERFORMANCE RESULTS:")
            logger.info(f"   Average time: {avg_time*1000:.2f}ms")
            logger.info(f"   Median time: {median_time*1000:.2f}ms")
            logger.info(f"   Min time: {min_time*1000:.2f}ms")
            logger.info(f"   Max time: {max_time*1000:.2f}ms")
            logger.info(f"   Throughput: {1/avg_time:.1f} predictions/second")
            
            return {
                'avg_time_ms': avg_time * 1000,
                'median_time_ms': median_time * 1000,
                'throughput_per_sec': 1/avg_time,
                'all_times': times
            }
            
        except Exception as e:
            logger.error(f"❌ Benchmark failed: {e}")
            return None
    
    def validate_model_files(self):
        """Validate model files and their integrity"""
        logger.info("🔍 Validating model files...")
        
        files_to_check = [
            'workload_pattern_classifier.pkl',
            'workload_feature_scaler.pkl',
            'model_info.json'
        ]
        
        validation_results = {}
        
        for file_name in files_to_check:
            try:
                if file_name.endswith('.pkl'):
                    model = joblib.load(file_name)
                    validation_results[file_name] = {
                        'exists': True,
                        'loadable': True,
                        'size_mb': os.path.getsize(file_name) / (1024*1024),
                        'type': str(type(model))
                    }
                elif file_name.endswith('.json'):
                    with open(file_name, 'r') as f:
                        data = json.load(f)
                    validation_results[file_name] = {
                        'exists': True,
                        'loadable': True,
                        'size_mb': os.path.getsize(file_name) / (1024*1024),
                        'keys': list(data.keys())
                    }
                
                logger.info(f"✅ {file_name}: OK")
                
            except FileNotFoundError:
                validation_results[file_name] = {'exists': False, 'loadable': False}
                logger.error(f"❌ {file_name}: NOT FOUND")
            except Exception as e:
                validation_results[file_name] = {'exists': True, 'loadable': False, 'error': str(e)}
                logger.error(f"❌ {file_name}: CORRUPTED - {e}")
        
        return validation_results


def main():
    """Main testing pipeline"""
    print("🧪 ML Workload Performance Analyzer - Testing Suite")
    print("=" * 60)
    
    tester = MLModelTester()
    
    # Step 1: Load models
    print("\n📥 Step 1: Loading Models")
    if not tester.load_models():
        print("❌ Cannot proceed without models. Run training script first.")
        return
    
    # Step 2: Validate model files
    print("\n🔍 Step 2: Validating Model Files")
    validation_results = tester.validate_model_files()
    
    # Step 3: Test with sample data
    print("\n🧪 Step 3: Testing with Sample Scenarios")
    sample_results = tester.test_with_sample_data()
    
    # Step 4: Performance benchmark
    print("\n⚡ Step 4: Performance Benchmark")
    perf_results = tester.benchmark_performance(n_tests=50)
    
    # Step 5: Test with custom data (example)
    print("\n🔬 Step 5: Testing with Custom Data Example")
    custom_nodes = [
        {'cpu_usage_pct': 75.5, 'memory_usage_pct': 45.2, 'ready': True},
        {'cpu_usage_pct': 78.1, 'memory_usage_pct': 43.8, 'ready': True},
        {'cpu_usage_pct': 72.3, 'memory_usage_pct': 46.7, 'ready': True}
    ]
    
    custom_hpa = {
        'current_hpa_pattern': 'cpu_based_dominant',
        'confidence': 'high',
        'total_hpas': 2
    }
    
    custom_result = tester.test_with_your_data(custom_nodes, custom_hpa)
    
    # Summary
    print("\n" + "="*60)
    print("📋 TESTING SUMMARY")
    print("="*60)
    
    if sample_results:
        correct = sum(1 for r in sample_results if r['correct'])
        total = len(sample_results)
        print(f"✅ Sample Tests: {correct}/{total} ({correct/total:.1%})")
    
    if perf_results:
        print(f"⚡ Average Response Time: {perf_results['avg_time_ms']:.2f}ms")
        print(f"⚡ Throughput: {perf_results['throughput_per_sec']:.1f} predictions/sec")
    
    if custom_result:
        print(f"🔬 Custom Test: {custom_result['workload_type']} (confidence: {custom_result['confidence']:.3f})")
    
    print("\n🎉 Testing completed successfully!")
    print("\n💡 To test with your own data, call:")
    print("   tester.test_with_your_data(your_nodes_data, your_hpa_data)")


if __name__ == "__main__":
    import os
    main()