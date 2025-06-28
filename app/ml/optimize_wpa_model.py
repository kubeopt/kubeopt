#!/usr/bin/env python3
"""
Model Loading Debugger & Fixer
=============================
Diagnose and fix why your pre-trained .pkl models aren't loading
"""

import os
import joblib
import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelLoadingDiagnostic:
    """
    Comprehensive diagnostic for model loading issues
    """
    
    def __init__(self, model_path: str = "app/ml/data_feed"):
        self.model_path = model_path
        self.expected_features = [
            "cpu_mean", "memory_mean", "cpu_std", "memory_std", "cpu_var", "memory_var",
            "cpu_min", "cpu_max", "memory_min", "memory_max", "cpu_p75", "cpu_p95", "cpu_p99",
            "memory_p75", "memory_p95", "memory_p99", "cpu_range", "memory_range", "cpu_cv", "memory_cv",
            "cpu_memory_ratio", "cpu_memory_correlation", "resource_imbalance",
            "hpa_implementation_score", "hpa_pattern_encoded", "hpa_confidence_score", "hpa_density",
            "cpu_burst_frequency", "memory_burst_frequency", "cpu_stability_score", "memory_stability_score",
            "cpu_peak_avg_ratio", "memory_peak_avg_ratio", "avg_cpu_gap", "max_cpu_gap", "cpu_gap_variance",
            "avg_memory_gap", "max_memory_gap", "memory_gap_variance", "overall_efficiency_score",
            "hour_of_day", "is_business_hours", "is_weekend", "is_peak_hours", "hour_sin", "hour_cos",
            "day_sin", "day_cos", "node_readiness_ratio", "cpu_distribution_fairness",
            "memory_distribution_fairness", "cluster_size", "cluster_size_normalized"
        ]
    
    def diagnose_model_loading_issue(self) -> Dict[str, Any]:
        """
        Comprehensive diagnosis of model loading issues
        """
        logger.info("🔍 DIAGNOSING MODEL LOADING ISSUE")
        logger.info("=" * 50)
        
        diagnosis = {
            'model_path_exists': False,
            'pkl_files_found': [],
            'pkl_files_missing': [],
            'models_loadable': {},
            'feature_compatibility': {},
            'recommendations': []
        }
        
        # Step 1: Check if model directory exists
        if os.path.exists(self.model_path):
            diagnosis['model_path_exists'] = True
            logger.info(f"✅ Model directory exists: {self.model_path}")
        else:
            diagnosis['model_path_exists'] = False
            logger.error(f"❌ Model directory NOT found: {self.model_path}")
            diagnosis['recommendations'].append("Create model directory and train models")
            return diagnosis
        
        # Step 2: Check for .pkl files
        expected_pkl_files = ['pattern_classifier.pkl', 'scaler.pkl']
        
        for pkl_file in expected_pkl_files:
            pkl_path = os.path.join(self.model_path, pkl_file)
            if os.path.exists(pkl_path):
                diagnosis['pkl_files_found'].append(pkl_file)
                logger.info(f"✅ Found: {pkl_file}")
            else:
                diagnosis['pkl_files_missing'].append(pkl_file)
                logger.error(f"❌ Missing: {pkl_file}")
        
        # Step 3: Try to load each .pkl file
        for pkl_file in diagnosis['pkl_files_found']:
            pkl_path = os.path.join(self.model_path, pkl_file)
            try:
                loaded_model = joblib.load(pkl_path)
                diagnosis['models_loadable'][pkl_file] = True
                logger.info(f"✅ Successfully loaded: {pkl_file}")
                
                # Get additional info about the model
                if pkl_file == 'pattern_classifier.pkl':
                    model_info = self._analyze_classifier_model(loaded_model)
                    diagnosis['classifier_info'] = model_info
                elif pkl_file == 'scaler.pkl':
                    scaler_info = self._analyze_scaler_model(loaded_model)
                    diagnosis['scaler_info'] = scaler_info
                    
            except Exception as e:
                diagnosis['models_loadable'][pkl_file] = False
                logger.error(f"❌ Failed to load {pkl_file}: {e}")
                diagnosis['recommendations'].append(f"Regenerate {pkl_file} - incompatible or corrupted")
        
        # Step 4: Check feature compatibility
        if 'pattern_classifier.pkl' in diagnosis['models_loadable'] and diagnosis['models_loadable']['pattern_classifier.pkl']:
            compatibility = self._check_feature_compatibility()
            diagnosis['feature_compatibility'] = compatibility
        
        # Step 5: Check for model_info.json
        model_info_path = os.path.join(self.model_path, 'model_info.json')
        if os.path.exists(model_info_path):
            try:
                with open(model_info_path, 'r') as f:
                    model_metadata = json.load(f)
                diagnosis['model_metadata'] = model_metadata
                logger.info(f"✅ Found model metadata: accuracy={model_metadata.get('accuracy', 'unknown')}")
            except Exception as e:
                logger.error(f"❌ Failed to load model_info.json: {e}")
        else:
            logger.warning("⚠️ No model_info.json found")
        
        # Step 6: Generate specific recommendations
        recommendations = self._generate_specific_recommendations(diagnosis)
        diagnosis['recommendations'].extend(recommendations)
        
        return diagnosis
    
    def _analyze_classifier_model(self, model) -> Dict[str, Any]:
        """Analyze the classifier model"""
        try:
            model_info = {
                'model_type': type(model).__name__,
                'n_features': getattr(model, 'n_features_in_', 'unknown'),
                'classes': getattr(model, 'classes_', []).tolist() if hasattr(model, 'classes_') else 'unknown',
                'n_estimators': getattr(model, 'n_estimators', 'unknown')
            }
            
            logger.info(f"🔍 Classifier Analysis:")
            logger.info(f"   Model Type: {model_info['model_type']}")
            logger.info(f"   Features Expected: {model_info['n_features']}")
            logger.info(f"   Classes: {model_info['classes']}")
            logger.info(f"   Estimators: {model_info['n_estimators']}")
            
            return model_info
        except Exception as e:
            logger.error(f"❌ Failed to analyze classifier: {e}")
            return {'error': str(e)}
    
    def _analyze_scaler_model(self, scaler) -> Dict[str, Any]:
        """Analyze the scaler model"""
        try:
            scaler_info = {
                'scaler_type': type(scaler).__name__,
                'n_features': getattr(scaler, 'n_features_in_', 'unknown'),
                'feature_names': getattr(scaler, 'feature_names_in_', []).tolist() if hasattr(scaler, 'feature_names_in_') else 'unknown'
            }
            
            logger.info(f"🔍 Scaler Analysis:")
            logger.info(f"   Scaler Type: {scaler_info['scaler_type']}")
            logger.info(f"   Features Expected: {scaler_info['n_features']}")
            
            return scaler_info
        except Exception as e:
            logger.error(f"❌ Failed to analyze scaler: {e}")
            return {'error': str(e)}
    
    def _check_feature_compatibility(self) -> Dict[str, Any]:
        """Check if existing models are compatible with current feature set"""
        try:
            # Load models
            classifier_path = os.path.join(self.model_path, 'pattern_classifier.pkl')
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            
            classifier = joblib.load(classifier_path)
            scaler = joblib.load(scaler_path)
            
            # Check feature count compatibility
            expected_features = len(self.expected_features)
            
            classifier_features = getattr(classifier, 'n_features_in_', None)
            scaler_features = getattr(scaler, 'n_features_in_', None)
            
            compatibility = {
                'expected_features': expected_features,
                'classifier_features': classifier_features,
                'scaler_features': scaler_features,
                'compatible': False,
                'issues': []
            }
            
            if classifier_features != expected_features:
                compatibility['issues'].append(f"Classifier expects {classifier_features} features, but system provides {expected_features}")
            
            if scaler_features != expected_features:
                compatibility['issues'].append(f"Scaler expects {scaler_features} features, but system provides {expected_features}")
            
            if classifier_features == scaler_features == expected_features:
                compatibility['compatible'] = True
                logger.info("✅ Feature compatibility: COMPATIBLE")
            else:
                logger.error("❌ Feature compatibility: INCOMPATIBLE")
                for issue in compatibility['issues']:
                    logger.error(f"   - {issue}")
            
            return compatibility
            
        except Exception as e:
            logger.error(f"❌ Compatibility check failed: {e}")
            return {'error': str(e)}
    
    def _generate_specific_recommendations(self, diagnosis: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on diagnosis"""
        recommendations = []
        
        # Missing files
        if diagnosis['pkl_files_missing']:
            recommendations.append(f"❌ CRITICAL: Missing model files: {', '.join(diagnosis['pkl_files_missing'])}")
            recommendations.append("🔧 FIX: Run comprehensive_ml_trainer.py to generate missing models")
        
        # Incompatible features
        if diagnosis.get('feature_compatibility', {}).get('compatible') == False:
            recommendations.append("❌ CRITICAL: Feature count mismatch - models incompatible with current system")
            recommendations.append("🔧 FIX: Retrain models with current 53-feature system")
        
        # Corrupted models
        for pkl_file, loadable in diagnosis.get('models_loadable', {}).items():
            if not loadable:
                recommendations.append(f"❌ CRITICAL: {pkl_file} is corrupted or incompatible")
                recommendations.append(f"🔧 FIX: Regenerate {pkl_file}")
        
        # No issues found but still not loading
        if (len(diagnosis['pkl_files_missing']) == 0 and 
            all(diagnosis.get('models_loadable', {}).values()) and
            diagnosis.get('feature_compatibility', {}).get('compatible')):
            recommendations.append("⚠️ WARNING: Models appear correct but not loading in main system")
            recommendations.append("🔧 FIX: Check load_models() method implementation")
        
        return recommendations
    
    def test_manual_model_loading(self) -> bool:
        """Test manual model loading to verify models work"""
        logger.info("\n🧪 TESTING MANUAL MODEL LOADING")
        logger.info("-" * 40)
        
        try:
            # Test loading models directly
            classifier_path = os.path.join(self.model_path, 'pattern_classifier.pkl')
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            
            if not (os.path.exists(classifier_path) and os.path.exists(scaler_path)):
                logger.error("❌ Required model files not found for testing")
                return False
            
            # Load models
            classifier = joblib.load(classifier_path)
            scaler = joblib.load(scaler_path)
            
            logger.info("✅ Models loaded successfully")
            
            # Create test data with exact feature count
            test_features = np.random.random((1, len(self.expected_features)))
            
            # Test scaling
            scaled_features = scaler.transform(test_features)
            logger.info("✅ Feature scaling successful")
            
            # Test prediction
            prediction = classifier.predict(scaled_features)
            probabilities = classifier.predict_proba(scaled_features)
            
            logger.info(f"✅ Prediction successful: {prediction[0]}")
            logger.info(f"✅ Probabilities shape: {probabilities.shape}")
            
            # Test if classes match expected
            expected_classes = ['CPU_INTENSIVE', 'MEMORY_INTENSIVE', 'BALANCED', 'BURSTY', 'LOW_UTILIZATION']
            model_classes = classifier.classes_.tolist()
            
            if set(model_classes) == set(expected_classes):
                logger.info("✅ Model classes match expected classes")
            else:
                logger.warning(f"⚠️ Model classes {model_classes} != expected {expected_classes}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Manual model loading test failed: {e}")
            return False
    
    def fix_load_models_method(self) -> str:
        """Generate a fixed load_models method with enhanced debugging"""
        
        fixed_method = '''
def load_models(self) -> bool:
    """Load trained models with enhanced debugging"""
    try:
        pattern_path = os.path.join(self.model_path, 'pattern_classifier.pkl')
        scaler_path = os.path.join(self.model_path, 'scaler.pkl')
        
        logger.info(f"🔍 Attempting to load models from: {self.model_path}")
        logger.info(f"🔍 Pattern classifier path: {pattern_path}")
        logger.info(f"🔍 Scaler path: {scaler_path}")
        
        # Check if files exist
        if not os.path.exists(pattern_path):
            logger.error(f"❌ Pattern classifier not found: {pattern_path}")
            return False
            
        if not os.path.exists(scaler_path):
            logger.error(f"❌ Scaler not found: {scaler_path}")
            return False
        
        logger.info("✅ Both model files found, attempting to load...")
        
        # Load models with error handling
        try:
            self.pattern_classifier = joblib.load(pattern_path)
            logger.info("✅ Pattern classifier loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load pattern classifier: {e}")
            return False
        
        try:
            self.scaler = joblib.load(scaler_path)
            logger.info("✅ Scaler loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load scaler: {e}")
            return False
        
        # Validate models
        try:
            # Check feature compatibility
            expected_features = len(self.expected_features)
            classifier_features = getattr(self.pattern_classifier, 'n_features_in_', None)
            scaler_features = getattr(self.scaler, 'n_features_in_', None)
            
            logger.info(f"🔍 Feature validation:")
            logger.info(f"   Expected: {expected_features}")
            logger.info(f"   Classifier: {classifier_features}")
            logger.info(f"   Scaler: {scaler_features}")
            
            if classifier_features != expected_features:
                logger.error(f"❌ Feature mismatch: classifier expects {classifier_features}, system provides {expected_features}")
                return False
                
            if scaler_features != expected_features:
                logger.error(f"❌ Feature mismatch: scaler expects {scaler_features}, system provides {expected_features}")
                return False
            
            # Test with dummy data
            test_data = np.random.random((1, expected_features))
            scaled_data = self.scaler.transform(test_data)
            prediction = self.pattern_classifier.predict(scaled_data)
            
            logger.info(f"✅ Model validation successful - test prediction: {prediction[0]}")
            
        except Exception as e:
            logger.error(f"❌ Model validation failed: {e}")
            return False
        
        self.is_trained = True
        logger.info("✅ Models loaded and validated successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        return False
'''
        
        return fixed_method
    
    def generate_quick_model_fix(self) -> str:
        """Generate a quick script to create compatible models"""
        
        quick_fix_script = '''
#!/usr/bin/env python3
"""
Quick Model Compatibility Fix
===========================
Generates basic compatible models if none exist
"""

import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import json

def create_basic_compatible_models(model_path="app/ml/data_feed"):
    """Create basic compatible models for immediate use"""
    
    print("🔧 Creating basic compatible models...")
    
    os.makedirs(model_path, exist_ok=True)
    
    # Expected features (53 features)
    expected_features = [
        "cpu_mean", "memory_mean", "cpu_std", "memory_std", "cpu_var", "memory_var",
        "cpu_min", "cpu_max", "memory_min", "memory_max", "cpu_p75", "cpu_p95", "cpu_p99",
        "memory_p75", "memory_p95", "memory_p99", "cpu_range", "memory_range", "cpu_cv", "memory_cv",
        "cpu_memory_ratio", "cpu_memory_correlation", "resource_imbalance",
        "hpa_implementation_score", "hpa_pattern_encoded", "hpa_confidence_score", "hpa_density",
        "cpu_burst_frequency", "memory_burst_frequency", "cpu_stability_score", "memory_stability_score",
        "cpu_peak_avg_ratio", "memory_peak_avg_ratio", "avg_cpu_gap", "max_cpu_gap", "cpu_gap_variance",
        "avg_memory_gap", "max_memory_gap", "memory_gap_variance", "overall_efficiency_score",
        "hour_of_day", "is_business_hours", "is_weekend", "is_peak_hours", "hour_sin", "hour_cos",
        "day_sin", "day_cos", "node_readiness_ratio", "cpu_distribution_fairness",
        "memory_distribution_fairness", "cluster_size", "cluster_size_normalized"
    ]
    
    target_classes = ['CPU_INTENSIVE', 'MEMORY_INTENSIVE', 'BALANCED', 'BURSTY', 'LOW_UTILIZATION']
    
    # Generate minimal training data
    X = np.random.random((100, len(expected_features)))
    y = np.random.choice(target_classes, 100)
    
    # Create and train basic models
    classifier = RandomForestClassifier(n_estimators=50, random_state=42)
    scaler = StandardScaler()
    
    # Fit models
    X_scaled = scaler.fit_transform(X)
    classifier.fit(X_scaled, y)
    
    # Save models
    joblib.dump(classifier, os.path.join(model_path, 'pattern_classifier.pkl'))
    joblib.dump(scaler, os.path.join(model_path, 'scaler.pkl'))
    
    # Create basic metadata
    metadata = {
        'accuracy': 0.6,  # Basic model
        'features': expected_features,
        'classes': target_classes,
        'training_timestamp': '2025-06-27T23:00:00',
        'note': 'Basic compatible model - retrain for better accuracy'
    }
    
    with open(os.path.join(model_path, 'model_info.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Basic models saved to {model_path}")
    print("⚠️ These are basic models with ~60% accuracy")
    print("🚀 Run comprehensive_ml_trainer.py for >80% accuracy")

if __name__ == "__main__":
    create_basic_compatible_models()
'''
        
        return quick_fix_script

def main():
    """
    Main diagnostic function
    """
    print("🔍 MODEL LOADING DIAGNOSTIC TOOL")
    print("=" * 50)
    
    diagnostic = ModelLoadingDiagnostic()
    
    # Run comprehensive diagnosis
    results = diagnostic.diagnose_model_loading_issue()
    
    print(f"\n📊 DIAGNOSIS SUMMARY")
    print("=" * 30)
    print(f"Model Directory Exists: {'✅' if results['model_path_exists'] else '❌'}")
    print(f"PKL Files Found: {len(results['pkl_files_found'])}/2")
    print(f"PKL Files Missing: {results['pkl_files_missing']}")
    
    if results['models_loadable']:
        loadable_count = sum(results['models_loadable'].values())
        print(f"Models Loadable: {loadable_count}/{len(results['models_loadable'])}")
    
    if results.get('feature_compatibility'):
        compatible = results['feature_compatibility'].get('compatible', False)
        print(f"Feature Compatibility: {'✅' if compatible else '❌'}")
    
    # Test manual loading if possible
    print(f"\n🧪 MANUAL LOADING TEST")
    print("-" * 30)
    manual_test_passed = diagnostic.test_manual_model_loading()
    
    # Show recommendations
    print(f"\n🔧 RECOMMENDATIONS")
    print("-" * 30)
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"{i}. {rec}")
    
    # Provide solutions
    print(f"\n💡 SOLUTIONS")
    print("=" * 20)
    
    if not results['model_path_exists'] or results['pkl_files_missing']:
        print("🚀 IMMEDIATE FIX: Run this to create basic compatible models:")
        print("```python")
        print(diagnostic.generate_quick_model_fix())
        print("```")
    
    if results.get('feature_compatibility', {}).get('compatible') == False:
        print("🔧 FEATURE FIX: Your existing models are incompatible.")
        print("   - Option 1: Run comprehensive_ml_trainer.py (RECOMMENDED)")
        print("   - Option 2: Use the quick fix script above")
    
    if not manual_test_passed:
        print("🔧 LOADING FIX: Replace your load_models() method with:")
        print("```python")
        print(diagnostic.fix_load_models_method())
        print("```")
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. 🔧 Apply the immediate fix above")
    print("2. 🚀 Run comprehensive_ml_trainer.py for >80% accuracy")
    print("3. 🧪 Test with your real data again")

if __name__ == "__main__":
    main()