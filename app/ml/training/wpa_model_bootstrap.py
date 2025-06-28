"""
ML Model Bootstrap Script
========================
Creates the missing workload_pattern_classifier.pkl and related model files
Generates synthetic training data and trains initial models
"""

import os
import sys
import logging
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import warnings
warnings.filterwarnings('ignore')

# Add the current directory to Python path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelBootstrap:
    """
    Bootstrap class to create initial ML models for workload analysis
    """
    
    def __init__(self):
        self.model_files = [
            'workload_pattern_classifier.pkl',
            'workload_feature_scaler.pkl'
        ]
        self.feature_names = [
            'cpu_mean', 'memory_mean', 'cpu_std', 'memory_std', 'cpu_var', 'memory_var',
            'cpu_min', 'cpu_max', 'memory_min', 'memory_max', 'cpu_p75', 'cpu_p95', 'cpu_p99',
            'memory_p75', 'memory_p95', 'memory_p99', 'cpu_range', 'memory_range', 'cpu_cv', 'memory_cv',
            'cpu_memory_ratio', 'cpu_memory_correlation', 'resource_imbalance',
            'hpa_implementation_score', 'hpa_pattern_encoded', 'hpa_confidence_score', 'hpa_density',
            'cpu_burst_frequency', 'memory_burst_frequency', 'cpu_stability_score', 'memory_stability_score',
            'cpu_peak_avg_ratio', 'memory_peak_avg_ratio', 'avg_cpu_gap', 'max_cpu_gap', 'cpu_gap_variance',
            'avg_memory_gap', 'max_memory_gap', 'memory_gap_variance', 'overall_efficiency_score',
            'hour_of_day', 'is_business_hours', 'is_weekend', 'is_peak_hours', 'hour_sin', 'hour_cos',
            'day_sin', 'day_cos', 'node_readiness_ratio', 'cpu_distribution_fairness',
            'memory_distribution_fairness', 'cluster_size', 'cluster_size_normalized'
        ]
        self.workload_types = ['CPU_INTENSIVE', 'MEMORY_INTENSIVE', 'BALANCED', 'BURSTY', 'LOW_UTILIZATION']

    def check_existing_models(self) -> Dict[str, bool]:
        """Check which model files already exist"""
        status = {}
        for model_file in self.model_files:
            status[model_file] = os.path.exists(model_file)
            if status[model_file]:
                logger.info(f"✅ Found existing model: {model_file}")
            else:
                logger.warning(f"❌ Missing model: {model_file}")
        return status

    def generate_synthetic_training_data(self, n_samples: int = 1000) -> Tuple[pd.DataFrame, List[str]]:
        """Generate synthetic training data for workload patterns"""
        logger.info(f"🔬 Generating {n_samples} synthetic training samples...")
        
        np.random.seed(42)  # For reproducibility
        
        data = []
        labels = []
        
        samples_per_type = n_samples // len(self.workload_types)
        
        for workload_type in self.workload_types:
            for _ in range(samples_per_type):
                sample = self._generate_workload_sample(workload_type)
                data.append(sample)
                labels.append(workload_type)
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=self.feature_names)
        
        logger.info(f"✅ Generated training data: {len(df)} samples, {len(df.columns)} features")
        return df, labels

    def _generate_workload_sample(self, workload_type: str) -> List[float]:
        """Generate a single workload sample based on type"""
        
        # Base temporal features
        hour = np.random.randint(0, 24)
        day = np.random.randint(0, 7)
        is_business = 1.0 if 9 <= hour <= 17 and day < 5 else 0.0
        is_weekend = 1.0 if day >= 5 else 0.0
        is_peak = 1.0 if hour in [10, 11, 14, 15] else 0.0
        
        # Cyclical encoding
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)
        day_sin = np.sin(2 * np.pi * day / 7)
        day_cos = np.cos(2 * np.pi * day / 7)
        
        # Cluster features
        node_readiness = np.random.uniform(0.9, 1.0)
        cluster_size = np.random.randint(3, 20)
        
        if workload_type == 'CPU_INTENSIVE':
            # High CPU, moderate memory
            cpu_mean = np.random.normal(75, 10)
            memory_mean = np.random.normal(50, 8)
            cpu_std = np.random.normal(15, 5)
            memory_std = np.random.normal(10, 3)
            cpu_burst_freq = np.random.uniform(0.3, 0.7)
            memory_burst_freq = np.random.uniform(0.1, 0.3)
            hpa_pattern = 1.0  # CPU-based
            efficiency_score = np.random.uniform(0.6, 0.8)
            
        elif workload_type == 'MEMORY_INTENSIVE':
            # High memory, moderate CPU
            cpu_mean = np.random.normal(40, 8)
            memory_mean = np.random.normal(80, 12)
            cpu_std = np.random.normal(8, 3)
            memory_std = np.random.normal(20, 7)
            cpu_burst_freq = np.random.uniform(0.1, 0.3)
            memory_burst_freq = np.random.uniform(0.4, 0.8)
            hpa_pattern = 2.0  # Memory-based
            efficiency_score = np.random.uniform(0.5, 0.7)
            
        elif workload_type == 'BALANCED':
            # Balanced CPU and memory
            cpu_mean = np.random.normal(55, 10)
            memory_mean = np.random.normal(58, 10)
            cpu_std = np.random.normal(10, 4)
            memory_std = np.random.normal(12, 4)
            cpu_burst_freq = np.random.uniform(0.2, 0.4)
            memory_burst_freq = np.random.uniform(0.2, 0.4)
            hpa_pattern = 3.0  # Hybrid
            efficiency_score = np.random.uniform(0.7, 0.9)
            
        elif workload_type == 'BURSTY':
            # High variance, irregular patterns
            cpu_mean = np.random.normal(60, 20)
            memory_mean = np.random.normal(65, 18)
            cpu_std = np.random.normal(25, 10)
            memory_std = np.random.normal(22, 8)
            cpu_burst_freq = np.random.uniform(0.6, 0.9)
            memory_burst_freq = np.random.uniform(0.5, 0.8)
            hpa_pattern = 3.0  # Hybrid
            efficiency_score = np.random.uniform(0.3, 0.6)
            
        else:  # LOW_UTILIZATION
            # Low resource usage
            cpu_mean = np.random.normal(20, 8)
            memory_mean = np.random.normal(30, 10)
            cpu_std = np.random.normal(5, 2)
            memory_std = np.random.normal(7, 3)
            cpu_burst_freq = np.random.uniform(0.05, 0.2)
            memory_burst_freq = np.random.uniform(0.05, 0.2)
            hpa_pattern = 0.0  # No HPA
            efficiency_score = np.random.uniform(0.2, 0.5)
        
        # Ensure values are within bounds
        cpu_mean = max(0, min(100, cpu_mean))
        memory_mean = max(0, min(100, memory_mean))
        cpu_std = max(0, cpu_std)
        memory_std = max(0, memory_std)
        
        # Calculate derived features
        cpu_var = cpu_std ** 2
        memory_var = memory_std ** 2
        cpu_min = max(0, cpu_mean - 2 * cpu_std)
        cpu_max = min(100, cpu_mean + 2 * cpu_std)
        memory_min = max(0, memory_mean - 2 * memory_std)
        memory_max = min(100, memory_mean + 2 * memory_std)
        
        # Percentiles
        cpu_p75 = cpu_mean + 0.5 * cpu_std
        cpu_p95 = cpu_mean + 1.5 * cpu_std
        cpu_p99 = cpu_mean + 2 * cpu_std
        memory_p75 = memory_mean + 0.5 * memory_std
        memory_p95 = memory_mean + 1.5 * memory_std
        memory_p99 = memory_mean + 2 * memory_std
        
        # Ranges and ratios
        cpu_range = cpu_max - cpu_min
        memory_range = memory_max - memory_min
        cpu_cv = cpu_std / max(cpu_mean, 1)
        memory_cv = memory_std / max(memory_mean, 1)
        cpu_memory_ratio = cpu_mean / max(memory_mean, 1)
        cpu_memory_correlation = np.random.uniform(-0.3, 0.7)
        resource_imbalance = abs(cpu_mean - memory_mean)
        
        # HPA features
        hpa_implementation_score = np.random.uniform(0.3, 0.9)
        hpa_confidence_score = np.random.uniform(0.5, 1.0)
        hpa_density = np.random.uniform(0.1, 0.8)
        
        # Stability and performance features
        cpu_stability_score = 1 / (1 + cpu_cv)
        memory_stability_score = 1 / (1 + memory_cv)
        cpu_peak_avg_ratio = cpu_max / max(cpu_mean, 1)
        memory_peak_avg_ratio = memory_max / max(memory_mean, 1)
        
        # Gap features (resource headroom)
        avg_cpu_gap = max(0, 100 - cpu_mean)
        max_cpu_gap = max(0, 100 - cpu_min)
        cpu_gap_variance = np.random.uniform(0, 100)
        avg_memory_gap = max(0, 100 - memory_mean)
        max_memory_gap = max(0, 100 - memory_min)
        memory_gap_variance = np.random.uniform(0, 100)
        
        # Distribution fairness
        cpu_distribution_fairness = np.random.uniform(0.6, 1.0)
        memory_distribution_fairness = np.random.uniform(0.6, 1.0)
        cluster_size_normalized = min(cluster_size / 10, 1.0)
        
        return [
            cpu_mean, memory_mean, cpu_std, memory_std, cpu_var, memory_var,
            cpu_min, cpu_max, memory_min, memory_max, cpu_p75, cpu_p95, cpu_p99,
            memory_p75, memory_p95, memory_p99, cpu_range, memory_range, cpu_cv, memory_cv,
            cpu_memory_ratio, cpu_memory_correlation, resource_imbalance,
            hpa_implementation_score, hpa_pattern, hpa_confidence_score, hpa_density,
            cpu_burst_freq, memory_burst_freq, cpu_stability_score, memory_stability_score,
            cpu_peak_avg_ratio, memory_peak_avg_ratio, avg_cpu_gap, max_cpu_gap, cpu_gap_variance,
            avg_memory_gap, max_memory_gap, memory_gap_variance, efficiency_score,
            hour, is_business, is_weekend, is_peak, hour_sin, hour_cos,
            day_sin, day_cos, node_readiness, cpu_distribution_fairness,
            memory_distribution_fairness, cluster_size, cluster_size_normalized
        ]

    def train_and_save_models(self, X: pd.DataFrame, y: List[str]) -> Dict[str, Any]:
        """Train and save ML models"""
        logger.info("🤖 Training workload classification models...")
        
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train classifier
            classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                random_state=42,
                class_weight='balanced'
            )
            classifier.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = classifier.predict(X_test_scaled)
            accuracy = classifier.score(X_test_scaled, y_test)
            
            logger.info(f"✅ Model training completed - Accuracy: {accuracy:.3f}")
            
            # Save models
            joblib.dump(classifier, 'workload_pattern_classifier.pkl')
            joblib.dump(scaler, 'workload_feature_scaler.pkl')
            
            logger.info("✅ Models saved successfully")
            
            # Generate classification report
            report = classification_report(y_test, y_pred, output_dict=True)
            
            return {
                'accuracy': accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features': len(X.columns),
                'classification_report': report,
                'feature_importance': dict(zip(X.columns, classifier.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"❌ Model training failed: {e}")
            raise

    def create_model_info_file(self, training_results: Dict):
        """Create an info file with model details"""
        info = {
            'created_at': datetime.now().isoformat(),
            'model_type': 'RandomForestClassifier',
            'feature_count': training_results['features'],
            'training_samples': training_results['training_samples'],
            'test_accuracy': training_results['accuracy'],
            'workload_types': self.workload_types,
            'feature_names': self.feature_names,
            'model_files': self.model_files,
            'version': '1.0',
            'description': 'Bootstrap ML models for workload pattern classification'
        }
        
        with open('model_info.json', 'w') as f:
            import json
            json.dump(info, f, indent=2)
        
        logger.info("✅ Model info file created: model_info.json")

    def run_bootstrap(self, n_samples: int = 1500) -> Dict[str, Any]:
        """Run the complete bootstrap process"""
        logger.info("🚀 Starting ML model bootstrap process...")
        
        try:
            # Check existing models
            existing = self.check_existing_models()
            
            if all(existing.values()):
                logger.info("✅ All models already exist. Bootstrap not needed.")
                return {'status': 'models_exist', 'action': 'none'}
            
            # Generate training data
            X, y = self.generate_synthetic_training_data(n_samples)
            
            # Train and save models
            results = self.train_and_save_models(X, y)
            
            # Create info file
            self.create_model_info_file(results)
            
            logger.info("🎉 Bootstrap process completed successfully!")
            
            return {
                'status': 'success',
                'action': 'created_models',
                'results': results,
                'models_created': self.model_files
            }
            
        except Exception as e:
            logger.error(f"❌ Bootstrap process failed: {e}")
            return {
                'status': 'error',
                'action': 'failed',
                'error': str(e)
            }

    def verify_models(self) -> Dict[str, Any]:
        """Verify that models can be loaded and used"""
        logger.info("🔍 Verifying created models...")
        
        try:
            # Load models
            classifier = joblib.load('workload_pattern_classifier.pkl')
            scaler = joblib.load('workload_feature_scaler.pkl')
            
            # Test with sample data
            sample_data = np.random.random((1, len(self.feature_names)))
            scaled_data = scaler.transform(sample_data)
            prediction = classifier.predict(scaled_data)[0]
            probabilities = classifier.predict_proba(scaled_data)[0]
            
            logger.info(f"✅ Model verification successful")
            logger.info(f"   Sample prediction: {prediction}")
            logger.info(f"   Prediction confidence: {max(probabilities):.3f}")
            
            return {
                'status': 'success',
                'sample_prediction': prediction,
                'confidence': float(max(probabilities)),
                'models_working': True
            }
            
        except Exception as e:
            logger.error(f"❌ Model verification failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'models_working': False
            }


def main():
    """Main function to run the bootstrap process"""
    print("=" * 60)
    print("ML Model Bootstrap for Workload Pattern Classification")
    print("=" * 60)
    
    bootstrap = ModelBootstrap()
    
    # Run bootstrap
    result = bootstrap.run_bootstrap(n_samples=1500)
    
    if result['status'] == 'success':
        # Verify models
        verification = bootstrap.verify_models()
        
        print(f"\n🎉 Bootstrap completed successfully!")
        print(f"   Models created: {result['models_created']}")
        print(f"   Training accuracy: {result['results']['accuracy']:.3f}")
        print(f"   Model verification: {'✅ PASSED' if verification['models_working'] else '❌ FAILED'}")
        
        if verification['models_working']:
            print(f"\n✅ Your ML models are ready to use!")
            print(f"   The warning about missing .pkl files should now be resolved.")
    
    elif result['status'] == 'models_exist':
        print(f"\n✅ Models already exist - no action needed.")
    
    else:
        print(f"\n❌ Bootstrap failed: {result.get('error', 'Unknown error')}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())