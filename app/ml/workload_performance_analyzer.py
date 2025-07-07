"""
Complete Self-Learning Workload Analyzer with Rich Insights
==========================================================
Fully functional implementation combining comprehensive insight generation
with adaptive learning features and production-ready code.
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import logging
import json
import sqlite3
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from threading import Lock
import warnings
import math
from collections import defaultdict
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SelfLearningWorkloadClassifier:
    """Complete self-learning classifier with all original features intact"""
    
    def __init__(self, model_path: str = None, enable_self_learning: bool = True):
        # Initialize classifiers
        self.cpu_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.memory_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.pattern_classifier = RandomForestClassifier(n_estimators=150, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.enable_self_learning = enable_self_learning
        
        # Self-learning components
        self.learning_lock = Lock()
        self.learning_data = []
        self.feedback_data = []
        self.performance_history = []
        self.confidence_threshold = 0.7
        self.retrain_threshold = 50
        self.last_training_time = None
        self.retrain_interval_hours = 24
        
        # Model paths
        self.model_path = self._setup_model_path(model_path)
        if self.enable_self_learning:
            self.learning_db_path = os.path.join(self.model_path, "learning_data.db")
            self._initialize_learning_database()
        
        # Expected features (complete list)
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
            "memory_distribution_fairness", "cluster_size", "cluster_size_normalized",
            "cpu_extreme_detected", "memory_extreme_detected", "max_cpu_actual", "max_memory_actual"
        ]
        
        # Load existing models
        models_loaded = self.load_models()
        if not models_loaded:
            logger.info("📝 Models not available - using rule-based classification with learning")

    def _setup_model_path(self, model_path: str = None) -> str:
        """Setup model path"""
        if model_path is None:
            return os.getcwd()
        
        normalized_path = os.path.normpath(model_path)
        if not os.path.isabs(normalized_path):
            normalized_path = os.path.abspath(normalized_path)
        
        try:
            os.makedirs(normalized_path, exist_ok=True)
            logger.info(f"✅ Model directory: {normalized_path}")
        except Exception as e:
            logger.warning(f"⚠️ Model directory issue: {e}")
            normalized_path = os.getcwd()
        
        return normalized_path

    def _initialize_learning_database(self):
        """Initialize learning database"""
        try:
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    features TEXT NOT NULL,
                    true_label TEXT,
                    predicted_label TEXT,
                    confidence REAL,
                    feedback_score REAL,
                    cluster_context TEXT,
                    used_for_training BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    accuracy REAL,
                    avg_confidence REAL,
                    total_predictions INTEGER,
                    model_version TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Learning database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize learning database: {e}")

    def extract_advanced_features(self, metrics_data: Dict) -> pd.DataFrame:
        """Extract features with comprehensive data collection for insights"""
        try:
            logger.info("🔬 Extracting features for comprehensive insights...")
            
            # Get nodes data
            nodes = metrics_data.get('nodes', [])
            if not nodes:
                logger.warning("⚠️ No nodes data - using defaults")
                return self._get_default_feature_dataframe()
            
            # Extract CPU and memory utilization
            cpu_utils = []
            memory_utils = []
            
            for i, node in enumerate(nodes):
                if not isinstance(node, dict):
                    continue
                
                # Extract CPU with multiple field attempts
                cpu_val = None
                for field in ['cpu_usage_pct', 'cpu_actual', 'cpu_utilization']:
                    if field in node and node[field] is not None:
                        try:
                            cpu_val = float(node[field])
                            if 0 <= cpu_val <= 200:
                                break
                        except (ValueError, TypeError):
                            continue
                
                # Extract Memory
                memory_val = None
                for field in ['memory_usage_pct', 'memory_actual', 'memory_utilization']:
                    if field in node and node[field] is not None:
                        try:
                            memory_val = float(node[field])
                            if 0 <= memory_val <= 200:
                                break
                        except (ValueError, TypeError):
                            continue
                
                # Use intelligent defaults if needed
                if cpu_val is None:
                    cpu_val = 35.0 + (i * 5)
                if memory_val is None:
                    memory_val = 60.0 + (i * 3)
                
                cpu_utils.append(cpu_val)
                memory_utils.append(memory_val)
            
            if not cpu_utils:
                return self._get_default_feature_dataframe()
            
            # Extract comprehensive features for rich insights
            features = {}
            
            # Statistical features (for pattern recognition)
            features.update(self._calculate_statistical_features(cpu_utils, memory_utils))
            
            # HPA features (for HPA recommendations)
            hpa_data = metrics_data.get('hpa_implementation', {})
            if not hpa_data:
                hpa_data = {'current_hpa_pattern': 'no_hpa_detected', 'confidence': 'low', 'total_hpas': 0}
            features.update(self._calculate_hpa_features(hpa_data))
            
            # Behavior features (for optimization insights)
            features.update(self._calculate_behavior_features(cpu_utils, memory_utils))
            
            # Efficiency features (for cost optimization)
            features.update(self._calculate_efficiency_features(nodes, cpu_utils, memory_utils))
            
            # Temporal features (for time-aware recommendations)
            features.update(self._calculate_temporal_features())
            
            # Cluster health features (for infrastructure insights)
            features.update(self._calculate_cluster_health_features(nodes, cpu_utils, memory_utils))
            
            # Ensure all required features exist
            for feat in self.expected_features:
                if feat not in features:
                    features[feat] = self._get_safe_default(feat)
            
            # Build DataFrame with exact order
            feature_values = [float(features[feat]) for feat in self.expected_features]
            df = pd.DataFrame([feature_values], columns=self.expected_features)
            
            # Clean data
            df = df.fillna(0.0)
            df = df.replace([np.inf, -np.inf], 0.0)
            
            logger.info(f"✅ Extracted {len(df.columns)} features for comprehensive insights")
            return df
            
        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {e}")
            return self._get_default_feature_dataframe()

    def _calculate_statistical_features(self, cpu_utils: List[float], memory_utils: List[float]) -> Dict[str, float]:
        """ Calculate comprehensive statistical features with extreme value handling"""
        try:
            cpu_array = np.array(cpu_utils)
            memory_array = np.array(memory_utils)
            
            # CRITICAL FIX: Detect and handle extreme values properly
            cpu_extreme = np.any(cpu_array > 200)
            memory_extreme = np.any(memory_array > 200)
            
            if cpu_extreme:
                logger.warning(f"🔥 EXTREME CPU VALUES DETECTED: {cpu_array}")
                # Cap extreme values for statistical calculations but preserve in max
                cpu_stats_array = np.clip(cpu_array, 0, 200)
                cpu_max_actual = float(np.max(cpu_array))  # Preserve actual max
            else:
                cpu_stats_array = cpu_array
                cpu_max_actual = float(np.max(cpu_array))
                
            if memory_extreme:
                logger.warning(f"🔥 EXTREME MEMORY VALUES DETECTED: {memory_array}")
                memory_stats_array = np.clip(memory_array, 0, 200)
                memory_max_actual = float(np.max(memory_array))
            else:
                memory_stats_array = memory_array
                memory_max_actual = float(np.max(memory_array))
            
            # Basic statistics with capped values for stability
            features = {
                'cpu_mean': float(np.mean(cpu_stats_array)),
                'memory_mean': float(np.mean(memory_stats_array)),
                'cpu_std': float(np.std(cpu_stats_array)),
                'memory_std': float(np.std(memory_stats_array)),
                'cpu_var': float(np.var(cpu_stats_array)),
                'memory_var': float(np.var(memory_stats_array)),
                'cpu_min': float(np.min(cpu_array)),
                'cpu_max': cpu_max_actual,  # Use actual max values
                'memory_min': float(np.min(memory_array)),
                'memory_max': memory_max_actual  # Use actual max values
            }
            
            # Percentiles with capped values
            features.update({
                'cpu_p75': float(np.percentile(cpu_stats_array, 75)),
                'cpu_p95': float(np.percentile(cpu_stats_array, 95)),
                'cpu_p99': float(np.percentile(cpu_stats_array, 99)),
                'memory_p75': float(np.percentile(memory_stats_array, 75)),
                'memory_p95': float(np.percentile(memory_stats_array, 95)),
                'memory_p99': float(np.percentile(memory_stats_array, 99))
            })
            
            # Range and coefficient of variation
            features.update({
                'cpu_range': float(np.max(cpu_stats_array) - np.min(cpu_stats_array)),
                'memory_range': float(np.max(memory_stats_array) - np.min(memory_stats_array)),
                'cpu_cv': float(np.std(cpu_stats_array) / max(np.mean(cpu_stats_array), 1e-6)),
                'memory_cv': float(np.std(memory_stats_array) / max(np.mean(memory_stats_array), 1e-6))
            })
            
            # Cross-resource features
            features.update({
                'cpu_memory_ratio': float(np.mean(cpu_stats_array) / max(np.mean(memory_stats_array), 1e-6)),
                'cpu_memory_correlation': float(np.corrcoef(cpu_stats_array, memory_stats_array)[0, 1]) if len(cpu_stats_array) > 1 else 0.0,
                'resource_imbalance': float(abs(np.mean(cpu_stats_array) - np.mean(memory_stats_array)))
            })
            
            # Add extreme value flags
            features.update({
                'cpu_extreme_detected': float(cpu_extreme),
                'memory_extreme_detected': float(memory_extreme),
                'max_cpu_actual': cpu_max_actual,
                'max_memory_actual': memory_max_actual
            })
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Statistical features calculation failed: {e}")
            return self._get_default_statistical_features()

    def _calculate_hpa_features(self, hpa_data: Dict) -> Dict[str, float]:
        """Calculate HPA-related features"""
        try:
            pattern = hpa_data.get('current_hpa_pattern', 'no_hpa_detected')
            confidence = hpa_data.get('confidence', 'low')
            total_hpas = hpa_data.get('total_hpas', 0)
            
            # Encode HPA pattern
            pattern_encoding = {
                'cpu_based_hpa': 1.0,
                'memory_based_hpa': 2.0,
                'multi_metric_hpa': 3.0,
                'custom_metric_hpa': 4.0,
                'no_hpa_detected': 0.0
            }
            
            confidence_encoding = {
                'high': 0.9,
                'medium': 0.7,
                'low': 0.5,
                'unknown': 0.3
            }
            
            return {
                'hpa_implementation_score': float(min(total_hpas / 5.0, 1.0)),
                'hpa_pattern_encoded': float(pattern_encoding.get(pattern, 0.0)),
                'hpa_confidence_score': float(confidence_encoding.get(confidence, 0.3)),
                'hpa_density': float(total_hpas / max(1, len(hpa_data.get('workloads', [{'name': 'default'}]))))
            }
            
        except Exception as e:
            logger.error(f"❌ HPA features calculation failed: {e}")
            return {
                'hpa_implementation_score': 0.0,
                'hpa_pattern_encoded': 0.0,
                'hpa_confidence_score': 0.3,
                'hpa_density': 0.0
            }

    def _calculate_behavior_features(self, cpu_utils: List[float], memory_utils: List[float]) -> Dict[str, float]:
        """Calculate behavior-related features"""
        try:
            cpu_array = np.array(cpu_utils)
            memory_array = np.array(memory_utils)
            
            # Calculate burst frequency (significant deviations from mean)
            cpu_mean = np.mean(cpu_array)
            memory_mean = np.mean(memory_array)
            cpu_std = np.std(cpu_array)
            memory_std = np.std(memory_array)
            
            cpu_bursts = np.sum(np.abs(cpu_array - cpu_mean) > 2 * cpu_std) / len(cpu_array)
            memory_bursts = np.sum(np.abs(memory_array - memory_mean) > 2 * memory_std) / len(memory_array)
            
            # Stability scores (inverse of coefficient of variation)
            cpu_stability = 1.0 / (1.0 + cpu_std / max(cpu_mean, 1e-6))
            memory_stability = 1.0 / (1.0 + memory_std / max(memory_mean, 1e-6))
            
            # Peak to average ratios
            cpu_peak_avg = np.max(cpu_array) / max(cpu_mean, 1e-6)
            memory_peak_avg = np.max(memory_array) / max(memory_mean, 1e-6)
            
            return {
                'cpu_burst_frequency': float(cpu_bursts),
                'memory_burst_frequency': float(memory_bursts),
                'cpu_stability_score': float(min(cpu_stability, 1.0)),
                'memory_stability_score': float(min(memory_stability, 1.0)),
                'cpu_peak_avg_ratio': float(cpu_peak_avg),
                'memory_peak_avg_ratio': float(memory_peak_avg)
            }
            
        except Exception as e:
            logger.error(f"❌ Behavior features calculation failed: {e}")
            return {
                'cpu_burst_frequency': 0.1,
                'memory_burst_frequency': 0.1,
                'cpu_stability_score': 0.7,
                'memory_stability_score': 0.7,
                'cpu_peak_avg_ratio': 1.5,
                'memory_peak_avg_ratio': 1.5
            }

    def _calculate_efficiency_features(self, nodes: List[Dict], cpu_utils: List[float], memory_utils: List[float]) -> Dict[str, float]:
        """Calculate efficiency and optimization features"""
        try:
            # Calculate resource gaps (difference between requests and usage)
            cpu_gaps = []
            memory_gaps = []
            
            for i, node in enumerate(nodes):
                cpu_request = node.get('cpu_request_pct', cpu_utils[i] + 20)
                memory_request = node.get('memory_request_pct', memory_utils[i] + 15)
                
                cpu_gap = max(0, cpu_request - cpu_utils[i])
                memory_gap = max(0, memory_request - memory_utils[i])
                
                cpu_gaps.append(cpu_gap)
                memory_gaps.append(memory_gap)
            
            # Overall efficiency score
            cpu_efficiency = 1.0 - (np.mean(cpu_gaps) / 100.0)
            memory_efficiency = 1.0 - (np.mean(memory_gaps) / 100.0)
            overall_efficiency = (cpu_efficiency + memory_efficiency) / 2.0
            
            return {
                'avg_cpu_gap': float(np.mean(cpu_gaps)),
                'max_cpu_gap': float(np.max(cpu_gaps)),
                'cpu_gap_variance': float(np.var(cpu_gaps)),
                'avg_memory_gap': float(np.mean(memory_gaps)),
                'max_memory_gap': float(np.max(memory_gaps)),
                'memory_gap_variance': float(np.var(memory_gaps)),
                'overall_efficiency_score': float(max(0.0, min(1.0, overall_efficiency)))
            }
            
        except Exception as e:
            logger.error(f"❌ Efficiency features calculation failed: {e}")
            return {
                'avg_cpu_gap': 25.0,
                'max_cpu_gap': 40.0,
                'cpu_gap_variance': 100.0,
                'avg_memory_gap': 20.0,
                'max_memory_gap': 35.0,
                'memory_gap_variance': 80.0,
                'overall_efficiency_score': 0.6
            }

    def _calculate_temporal_features(self) -> Dict[str, float]:
        """Calculate time-based features"""
        try:
            now = datetime.now()
            hour = now.hour
            day_of_week = now.weekday()
            
            # Business hours (9 AM to 5 PM)
            is_business_hours = 1.0 if 9 <= hour <= 17 else 0.0
            
            # Weekend indicator
            is_weekend = 1.0 if day_of_week >= 5 else 0.0
            
            # Peak hours (morning and evening rushes)
            is_peak_hours = 1.0 if hour in [8, 9, 10, 17, 18, 19] else 0.0
            
            # Cyclical encoding
            hour_sin = math.sin(2 * math.pi * hour / 24)
            hour_cos = math.cos(2 * math.pi * hour / 24)
            day_sin = math.sin(2 * math.pi * day_of_week / 7)
            day_cos = math.cos(2 * math.pi * day_of_week / 7)
            
            return {
                'hour_of_day': float(hour),
                'is_business_hours': is_business_hours,
                'is_weekend': is_weekend,
                'is_peak_hours': is_peak_hours,
                'hour_sin': float(hour_sin),
                'hour_cos': float(hour_cos),
                'day_sin': float(day_sin),
                'day_cos': float(day_cos)
            }
            
        except Exception as e:
            logger.error(f"❌ Temporal features calculation failed: {e}")
            return {
                'hour_of_day': 12.0,
                'is_business_hours': 1.0,
                'is_weekend': 0.0,
                'is_peak_hours': 0.0,
                'hour_sin': 0.0,
                'hour_cos': 1.0,
                'day_sin': 0.0,
                'day_cos': 1.0
            }

    def _calculate_cluster_health_features(self, nodes: List[Dict], cpu_utils: List[float], memory_utils: List[float]) -> Dict[str, float]:
        """Calculate cluster health features"""
        try:
            # Node readiness
            ready_nodes = sum(1 for node in nodes if node.get('status', 'Ready') == 'Ready')
            node_readiness_ratio = ready_nodes / max(len(nodes), 1)
            
            # Resource distribution fairness (Gini coefficient approximation)
            cpu_gini = self._calculate_gini_coefficient(cpu_utils)
            memory_gini = self._calculate_gini_coefficient(memory_utils)
            
            cpu_fairness = 1.0 - cpu_gini
            memory_fairness = 1.0 - memory_gini
            
            # Cluster size metrics
            cluster_size = len(nodes)
            cluster_size_normalized = min(cluster_size / 10.0, 1.0)  # Normalize to 10 nodes
            
            return {
                'node_readiness_ratio': float(node_readiness_ratio),
                'cpu_distribution_fairness': float(max(0.0, min(1.0, cpu_fairness))),
                'memory_distribution_fairness': float(max(0.0, min(1.0, memory_fairness))),
                'cluster_size': float(cluster_size),
                'cluster_size_normalized': float(cluster_size_normalized)
            }
            
        except Exception as e:
            logger.error(f"❌ Cluster health features calculation failed: {e}")
            return {
                'node_readiness_ratio': 1.0,
                'cpu_distribution_fairness': 0.8,
                'memory_distribution_fairness': 0.8,
                'cluster_size': 3.0,
                'cluster_size_normalized': 0.3
            }

    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """Calculate Gini coefficient for distribution fairness"""
        try:
            if not values or len(values) < 2:
                return 0.0
            
            sorted_values = sorted(values)
            n = len(sorted_values)
            cumsum = np.cumsum(sorted_values)
            
            # Gini coefficient formula
            gini = (n + 1 - 2 * sum((n + 1 - i) * v for i, v in enumerate(sorted_values, 1))) / (n * sum(sorted_values))
            return max(0.0, min(1.0, gini))
            
        except Exception as e:
            logger.error(f"❌ Gini coefficient calculation failed: {e}")
            return 0.2  # Default to moderate inequality

    def _get_safe_default(self, feature_name: str) -> float:
        """ Get safe default values including new extreme detection features"""
        defaults = {
            'cpu_mean': 35.0, 'memory_mean': 60.0,
            'cpu_std': 10.0, 'memory_std': 15.0,
            'cpu_var': 100.0, 'memory_var': 225.0,
            'cpu_min': 20.0, 'cpu_max': 70.0,
            'memory_min': 40.0, 'memory_max': 80.0,
            'cpu_p75': 45.0, 'cpu_p95': 65.0, 'cpu_p99': 70.0,
            'memory_p75': 70.0, 'memory_p95': 80.0, 'memory_p99': 85.0,
            'cpu_range': 50.0, 'memory_range': 40.0,
            'cpu_cv': 0.3, 'memory_cv': 0.25,
            'cpu_memory_ratio': 0.6, 'cpu_memory_correlation': 0.3,
            'resource_imbalance': 25.0,
            'hpa_implementation_score': 0.0, 'hpa_pattern_encoded': 0.0,
            'hpa_confidence_score': 0.3, 'hpa_density': 0.0,
            'cpu_burst_frequency': 0.1, 'memory_burst_frequency': 0.1,
            'cpu_stability_score': 0.7, 'memory_stability_score': 0.7,
            'cpu_peak_avg_ratio': 1.5, 'memory_peak_avg_ratio': 1.3,
            'avg_cpu_gap': 25.0, 'max_cpu_gap': 40.0, 'cpu_gap_variance': 100.0,
            'avg_memory_gap': 20.0, 'max_memory_gap': 35.0, 'memory_gap_variance': 80.0,
            'overall_efficiency_score': 0.6,
            'hour_of_day': 12.0, 'is_business_hours': 1.0,
            'is_weekend': 0.0, 'is_peak_hours': 0.0,
            'hour_sin': 0.0, 'hour_cos': 1.0, 'day_sin': 0.0, 'day_cos': 1.0,
            'node_readiness_ratio': 1.0,
            'cpu_distribution_fairness': 0.8, 'memory_distribution_fairness': 0.8,
            'cluster_size': 3.0, 'cluster_size_normalized': 0.3,
            # NEW: Extreme detection defaults
            'cpu_extreme_detected': 0.0, 'memory_extreme_detected': 0.0,
            'max_cpu_actual': 70.0, 'max_memory_actual': 80.0
        }
        return defaults.get(feature_name, 0.0)

    def _get_default_feature_dataframe(self) -> pd.DataFrame:
        """Get default feature DataFrame"""
        feature_values = [self._get_safe_default(feat) for feat in self.expected_features]
        return pd.DataFrame([feature_values], columns=self.expected_features)

    def _get_default_statistical_features(self) -> Dict[str, float]:
        """Get default statistical features"""
        return {
            'cpu_mean': 35.0, 'memory_mean': 60.0,
            'cpu_std': 10.0, 'memory_std': 15.0,
            'cpu_var': 100.0, 'memory_var': 225.0,
            'cpu_min': 20.0, 'cpu_max': 70.0,
            'memory_min': 40.0, 'memory_max': 80.0,
            'cpu_p75': 45.0, 'cpu_p95': 65.0, 'cpu_p99': 70.0,
            'memory_p75': 70.0, 'memory_p95': 80.0, 'memory_p99': 85.0,
            'cpu_range': 50.0, 'memory_range': 40.0,
            'cpu_cv': 0.3, 'memory_cv': 0.25,
            'cpu_memory_ratio': 0.6, 'cpu_memory_correlation': 0.3,
            'resource_imbalance': 25.0
        }

    def classify_workload_type(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced classification with rich insights for recommendations"""
        try:
            if features_df is None or features_df.empty:
                return self._ml_enhanced_rule_classification(self._get_default_feature_dataframe())
            
            if not self.is_trained:
                return self._ml_enhanced_rule_classification(features_df)
            
            # Validate features
            if len(features_df.columns) != len(self.expected_features):
                logger.error(f"❌ Feature count mismatch: expected {len(self.expected_features)}, got {len(features_df.columns)}")
                return self._ml_enhanced_rule_classification(features_df)
            
            # Reorder features if needed
            if list(features_df.columns) != self.expected_features:
                try:
                    features_df = features_df[self.expected_features]
                except KeyError:
                    return self._ml_enhanced_rule_classification(features_df)
            
            # Scale features and predict
            try:
                features_scaled = self.scaler.transform(features_df)
                pattern_pred = self.pattern_classifier.predict(features_scaled)[0]
                pattern_proba = self.pattern_classifier.predict_proba(features_scaled)[0]
                confidence = float(max(pattern_proba))
                
                # Enhanced result with insights metadata
                result = {
                    'workload_type': pattern_pred,
                    'confidence': confidence,
                    'method': 'trained_ml_models',
                    'model_path': self.model_path,
                    'prediction_probabilities': dict(zip(self.pattern_classifier.classes_, pattern_proba)),
                    'ml_enhanced': True,
                    'feature_count': len(features_df.columns),
                    'self_learning_enabled': self.enable_self_learning,
                    
                    # Additional insights metadata for rich recommendations
                    'feature_insights': self._extract_feature_insights(features_df),
                    'pattern_strength': confidence,
                    'alternative_patterns': self._get_alternative_patterns(pattern_proba, self.pattern_classifier.classes_),
                    'confidence_level': self._categorize_confidence(confidence)
                }
                
                return result
                
            except Exception as e:
                logger.error(f"❌ ML prediction failed: {e}")
                return self._ml_enhanced_rule_classification(features_df)
            
        except Exception as e:
            logger.error(f"❌ Classification failed: {e}")
            return self._ml_enhanced_rule_classification(features_df)

    # ============================================================================
    # FIX 1: Enhanced Rule-Based Classification (workload_performance_analyzer.py)
    # ============================================================================

    def _ml_enhanced_rule_classification(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """ Enhanced rule-based classification with proper extreme case handling"""
        try:
            features = features_df.iloc[0] if not features_df.empty else {}
            
            cpu_mean = features.get('cpu_mean', 35)
            memory_mean = features.get('memory_mean', 60)
            cpu_cv = features.get('cpu_cv', 0.3)
            memory_cv = features.get('memory_cv', 0.25)
            burst_freq = features.get('cpu_burst_frequency', 0.1)
            efficiency = features.get('overall_efficiency_score', 0.6)
            cpu_max = features.get('cpu_max', cpu_mean)
            memory_max = features.get('memory_max', memory_mean)
            
            # CRITICAL FIX: Handle extreme over-allocation first
            if cpu_mean > 200 or cpu_max > 500:
                workload_type = 'CPU_INTENSIVE'
                confidence = 0.95
                logger.info(f"🔥 EXTREME CPU DETECTED: mean={cpu_mean:.1f}%, max={cpu_max:.1f}%")
            elif memory_mean > 200 or memory_max > 500:
                workload_type = 'MEMORY_INTENSIVE'
                confidence = 0.95
                logger.info(f"🔥 EXTREME MEMORY DETECTED: mean={memory_mean:.1f}%, max={memory_max:.1f}%")
            
            # High utilization cases (above normal ranges)
            elif cpu_mean > 90:
                if memory_mean > 80:
                    # Both high - determine dominant resource
                    if cpu_mean > memory_mean * 1.2:
                        workload_type = 'CPU_INTENSIVE'
                    elif memory_mean > cpu_mean * 1.2:
                        workload_type = 'MEMORY_INTENSIVE'
                    else:
                        workload_type = 'BURSTY'  # High load with both resources stressed
                    confidence = 0.9
                else:
                    workload_type = 'CPU_INTENSIVE'
                    confidence = 0.85
            elif memory_mean > 90:
                workload_type = 'MEMORY_INTENSIVE'
                confidence = 0.85
            
            # Medium-high utilization with resource dominance
            elif cpu_mean > 70 and memory_mean < 50:
                workload_type = 'CPU_INTENSIVE'
                confidence = 0.8
            elif memory_mean > 80 and cpu_mean < 40:
                workload_type = 'MEMORY_INTENSIVE'
                confidence = 0.8
            
            # Bursty patterns (high variability or burst frequency)
            elif burst_freq > 0.3 or cpu_cv > 0.5 or memory_cv > 0.5:
                workload_type = 'BURSTY'
                confidence = 0.75
            
            # Low utilization (both resources underused)
            elif cpu_mean < 25 and memory_mean < 35:
                workload_type = 'LOW_UTILIZATION'
                confidence = 0.85
            
            # Moderate utilization with efficiency check
            elif efficiency < 0.4:
                # Poor efficiency suggests optimization opportunity
                if cpu_mean > memory_mean:
                    workload_type = 'CPU_INTENSIVE'
                else:
                    workload_type = 'MEMORY_INTENSIVE'
                confidence = 0.7
            
            # Default balanced case
            else:
                workload_type = 'BALANCED'
                confidence = 0.6
            
            logger.info(f"🧠 CLASSIFICATION: {workload_type} (CPU:{cpu_mean:.1f}%, MEM:{memory_mean:.1f}%, confidence:{confidence:.2f})")
            
            return {
                'workload_type': workload_type,
                'confidence': confidence,
                'method': 'enhanced_rule_based_with_extreme_handling',
                'ml_enhanced': True,
                'feature_count': len(features_df.columns),
                'self_learning_enabled': self.enable_self_learning,
                'feature_insights': self._extract_feature_insights(features_df),
                'pattern_strength': confidence,
                'alternative_patterns': [],
                'confidence_level': self._categorize_confidence(confidence),
                'classification_reasoning': f'CPU:{cpu_mean:.1f}%, Memory:{memory_mean:.1f}%, Efficiency:{efficiency:.2f}'
            }
            
        except Exception as e:
            logger.error(f"❌ Rule-based classification failed: {e}")
            return self._fallback_classification()

    def _extract_feature_insights(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract detailed feature insights for comprehensive recommendations"""
        try:
            features = features_df.iloc[0]
            
            return {
                'resource_utilization': {
                    'cpu_mean': float(features.get('cpu_mean', 0)),
                    'memory_mean': float(features.get('memory_mean', 0)),
                    'cpu_peak': float(features.get('cpu_max', 0)),
                    'memory_peak': float(features.get('memory_max', 0)),
                    'resource_balance': abs(float(features.get('cpu_mean', 0)) - float(features.get('memory_mean', 0)))
                },
                'performance_patterns': {
                    'cpu_stability': float(features.get('cpu_stability_score', 0)),
                    'memory_stability': float(features.get('memory_stability_score', 0)),
                    'burst_frequency': float(features.get('cpu_burst_frequency', 0)),
                    'variability': float(features.get('cpu_cv', 0)) + float(features.get('memory_cv', 0))
                },
                'efficiency_metrics': {
                    'overall_efficiency': float(features.get('overall_efficiency_score', 0)),
                    'cpu_gap': float(features.get('avg_cpu_gap', 0)),
                    'memory_gap': float(features.get('avg_memory_gap', 0)),
                    'waste_indicator': float(features.get('avg_cpu_gap', 0)) + float(features.get('avg_memory_gap', 0))
                },
                'cluster_health': {
                    'node_readiness': float(features.get('node_readiness_ratio', 1.0)),
                    'distribution_fairness': (float(features.get('cpu_distribution_fairness', 0.8)) + 
                                            float(features.get('memory_distribution_fairness', 0.8))) / 2,
                    'cluster_size': int(features.get('cluster_size', 3))
                }
            }
        except Exception as e:
            logger.error(f"❌ Feature insights extraction failed: {e}")
            return {}

    def _get_alternative_patterns(self, probabilities, classes) -> List[Dict[str, Any]]:
        """Get alternative workload patterns with their probabilities"""
        try:
            pattern_probs = list(zip(classes, probabilities))
            pattern_probs.sort(key=lambda x: x[1], reverse=True)
            
            alternatives = []
            for pattern, prob in pattern_probs[:3]:
                alternatives.append({
                    'pattern': pattern,
                    'probability': float(prob),
                    'confidence_level': self._categorize_confidence(prob)
                })
            
            return alternatives
        except Exception as e:
            logger.error(f"❌ Alternative patterns extraction failed: {e}")
            return []

    def _categorize_confidence(self, confidence: float) -> str:
        """Categorize confidence level for better insights"""
        if confidence >= 0.9:
            return 'very_high'
        elif confidence >= 0.8:
            return 'high'
        elif confidence >= 0.7:
            return 'medium'
        elif confidence >= 0.6:
            return 'moderate'
        else:
            return 'low'

    def _fallback_classification(self) -> Dict[str, Any]:
        """Fallback classification when all else fails"""
        return {
            'workload_type': 'UNKNOWN',
            'confidence': 0.3,
            'method': 'fallback',
            'ml_enhanced': False,
            'feature_count': 0,
            'self_learning_enabled': self.enable_self_learning
        }

    # Self-learning methods
    def predict_with_learning(self, features_df: pd.DataFrame, cluster_context: Dict = None) -> Dict[str, Any]:
        """Predict with self-learning capabilities"""
        try:
            # Get prediction
            prediction = self.classify_workload_type(features_df)
            
            if self.enable_self_learning:
                # Store prediction for learning
                self._store_prediction_sample(features_df, prediction, cluster_context)
                
                # Check if retraining is needed
                if self._should_retrain():
                    self._retrain_models()
            
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Prediction with learning failed: {e}")
            return self._fallback_classification()

    def _store_prediction_sample(self, features_df: pd.DataFrame, prediction: Dict, cluster_context: Dict):
        """Store prediction sample for learning"""
        try:
            with self.learning_lock:
                sample = {
                    'timestamp': datetime.now().isoformat(),
                    'features': features_df.to_json(),
                    'predicted_label': prediction.get('workload_type'),
                    'confidence': prediction.get('confidence'),
                    'cluster_context': json.dumps(cluster_context) if cluster_context else None
                }
                
                conn = sqlite3.connect(self.learning_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO learning_samples 
                    (timestamp, features, predicted_label, confidence, cluster_context)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sample['timestamp'], sample['features'], sample['predicted_label'],
                     sample['confidence'], sample['cluster_context']))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"❌ Failed to store prediction sample: {e}")

    def provide_feedback(self, analysis_timestamp: str, correct_workload_type: str, 
                    feedback_score: float = 1.0, notes: str = ""):
        """Provide feedback for continuous learning"""
        try:
            if not self.enable_self_learning:
                return
            
            with self.learning_lock:
                conn = sqlite3.connect(self.learning_db_path)
                cursor = conn.cursor()
                
                # First check if the timestamp exists
                cursor.execute('SELECT COUNT(*) FROM learning_samples WHERE timestamp = ?', (analysis_timestamp,))
                count_before = cursor.fetchone()[0]
                
                if count_before == 0:
                    # Try to find the most recent sample if exact timestamp doesn't match
                    cursor.execute('''
                        SELECT timestamp FROM learning_samples 
                        ORDER BY timestamp DESC LIMIT 1
                    ''')
                    recent = cursor.fetchone()
                    if recent:
                        analysis_timestamp = recent[0]
                        logger.info(f"🔄 Using most recent timestamp: {analysis_timestamp}")
                
                # Update with feedback
                cursor.execute('''
                    UPDATE learning_samples 
                    SET true_label = ?, feedback_score = ?, used_for_training = TRUE
                    WHERE timestamp = ?
                ''', (correct_workload_type, feedback_score, analysis_timestamp))
                
                # Verify the update worked
                rows_updated = cursor.rowcount
                conn.commit()
                
                # Double-check supervised count
                cursor.execute('SELECT COUNT(*) FROM learning_samples WHERE true_label IS NOT NULL')
                supervised_count = cursor.fetchone()[0]
                
                conn.close()
                
                if rows_updated > 0:
                    logger.info(f"✅ Feedback recorded: {correct_workload_type} (score: {feedback_score}) - {supervised_count} supervised samples")
                else:
                    logger.warning(f"⚠️ No rows updated for timestamp: {analysis_timestamp}")
                
        except Exception as e:
            logger.error(f"❌ Failed to record feedback: {e}")

    def _should_retrain(self) -> bool:
        """Check if model retraining is needed"""
        try:
            # Check time-based retraining
            if self.last_training_time:
                time_since_training = datetime.now() - self.last_training_time
                if time_since_training.total_seconds() < self.retrain_interval_hours * 3600:
                    return False
            
            # Check sample-based retraining
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM learning_samples 
                WHERE true_label IS NOT NULL AND used_for_training = FALSE
            ''')
            
            new_samples = cursor.fetchone()[0]
            conn.close()
            
            return new_samples >= self.retrain_threshold
            
        except Exception as e:
            logger.error(f"❌ Failed to check retrain condition: {e}")
            return False

    def _retrain_models(self):
        """Retrain models with new data"""
        try:
            logger.info("🔄 Starting model retraining...")
            
            # Load training data
            training_data = self._load_training_data()
            if len(training_data) < 10:
                logger.warning("⚠️ Insufficient training data")
                return
            
            # Prepare training data
            X, y = self._prepare_training_data(training_data)
            
            if len(X) < 10:
                logger.warning("⚠️ Insufficient prepared training data")
                return
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            self.scaler.fit(X_train)
            X_train_scaled = self.scaler.transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train classifiers
            self.pattern_classifier.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.pattern_classifier.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Update training status
            self.is_trained = True
            self.last_training_time = datetime.now()
            
            # Save models
            self.save_models()
            
            # Record performance
            self._record_performance(accuracy, len(training_data))
            
            logger.info(f"✅ Model retrained - Accuracy: {accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Model retraining failed: {e}")

    def _load_training_data(self) -> List[Dict]:
        """Load training data from database"""
        try:
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT features, true_label, feedback_score 
                FROM learning_samples 
                WHERE true_label IS NOT NULL
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            training_data = []
            for features_json, true_label, feedback_score in rows:
                try:
                    features_df = pd.read_json(features_json)
                    training_data.append({
                        'features': features_df,
                        'label': true_label,
                        'weight': feedback_score
                    })
                except Exception:
                    continue
            
            return training_data
            
        except Exception as e:
            logger.error(f"❌ Failed to load training data: {e}")
            return []

    def _prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for model training"""
        try:
            X_list = []
            y_list = []
            
            for sample in training_data:
                features_df = sample['features']
                if len(features_df.columns) == len(self.expected_features):
                    # Reorder features if needed
                    if list(features_df.columns) != self.expected_features:
                        features_df = features_df[self.expected_features]
                    
                    X_list.append(features_df.iloc[0].values)
                    y_list.append(sample['label'])
            
            return np.array(X_list), np.array(y_list)
            
        except Exception as e:
            logger.error(f"❌ Failed to prepare training data: {e}")
            return np.array([]), np.array([])

    def _record_performance(self, accuracy: float, total_samples: int):
        """Record model performance"""
        try:
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_history 
                (timestamp, accuracy, total_predictions, model_version)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().isoformat(), accuracy, total_samples, "self_learning_v1"))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to record performance: {e}")

    def get_learning_status(self) -> Dict[str, Any]:
        """Get comprehensive learning status"""
        try:
            if not self.enable_self_learning:
                return {'learning_enabled': False}
            
            conn = sqlite3.connect(self.learning_db_path)
            cursor = conn.cursor()
            
            # Get sample counts
            cursor.execute('SELECT COUNT(*) FROM learning_samples')
            total_samples = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM learning_samples WHERE true_label IS NOT NULL')
            supervised_samples = cursor.fetchone()[0]
            
            # Get performance history
            cursor.execute('''
                SELECT accuracy, timestamp FROM performance_history 
                ORDER BY timestamp DESC LIMIT 5
            ''')
            recent_performance = cursor.fetchall()
            
            conn.close()
            
            return {
                'learning_enabled': True,
                'model_trained': self.is_trained,
                'samples': {
                    'total_collected': total_samples,
                    'supervised': supervised_samples,
                    'pending_retrain': max(0, supervised_samples - self.retrain_threshold)
                },
                'performance': {
                    'recent_accuracy': recent_performance[0][0] if recent_performance else 0.0,
                    'accuracy_history': [p[0] for p in recent_performance],
                    'last_training': self.last_training_time.isoformat() if self.last_training_time else None
                },
                'confidence_threshold': self.confidence_threshold,
                'retrain_threshold': self.retrain_threshold
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get learning status: {e}")
            return {'learning_enabled': False, 'error': str(e)}

    def save_models(self):
        """Save trained models"""
        try:
            if self.is_trained:
                joblib.dump(self.pattern_classifier, os.path.join(self.model_path, 'pattern_classifier.pkl'))
                joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
                logger.info("✅ Models saved successfully")
        except Exception as e:
            logger.error(f"❌ Failed to save models: {e}")

    def load_models(self) -> bool:
        """Load trained models"""
        try:
            pattern_path = os.path.join(self.model_path, 'pattern_classifier.pkl')
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            
            if os.path.exists(pattern_path) and os.path.exists(scaler_path):
                self.pattern_classifier = joblib.load(pattern_path)
                self.scaler = joblib.load(scaler_path)
                self.is_trained = True
                logger.info("✅ Models loaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            return False

    def force_retrain(self) -> bool:
        """Force model retraining"""
        try:
            self._retrain_models()
            return True
        except Exception as e:
            logger.error(f"❌ Force retrain failed: {e}")
            return False

    def export_learning_data(self, format: str = 'csv') -> str:
        """Export learning data"""
        try:
            conn = sqlite3.connect(self.learning_db_path)
            
            if format.lower() == 'csv':
                df = pd.read_sql_query("SELECT * FROM learning_samples", conn)
                filename = f"learning_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(self.model_path, filename)
                df.to_csv(filepath, index=False)
                conn.close()
                return filepath
            else:
                conn.close()
                raise ValueError("Only CSV format supported")
                
        except Exception as e:
            logger.error(f"❌ Failed to export learning data: {e}")
            return ""


class EnhancedPerformanceAnomalyDetector:
    """Enhanced anomaly detector with self-learning insights"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.normal_behavior_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def detect_optimization_scenarios(self, workload_features: pd.DataFrame, 
                                    current_metrics: Dict,
                                    learning_context: Dict = None) -> Dict[str, Any]:
        """Enhanced optimization detection with learning insights"""
        try:
            logger.info("🔍 Analyzing performance anomalies with learning context...")
            
            # Extract performance indicators
            performance_indicators = self._extract_performance_indicators(current_metrics)
            
            # Add learning context to analysis
            if learning_context:
                performance_indicators.update({
                    'historical_patterns': learning_context.get('historical_patterns', {}),
                    'feedback_trends': learning_context.get('feedback_trends', {}),
                    'confidence_history': learning_context.get('confidence_history', [])
                })
            
            # Enhanced CPU analysis
            cpu_analysis = self._analyze_cpu_efficiency_enhanced(performance_indicators)
            
            # Enhanced memory analysis
            memory_analysis = self._analyze_memory_patterns_enhanced(performance_indicators)
            
            # Cost optimization analysis
            cost_analysis = self._analyze_cost_optimization(performance_indicators)
            
            # Combined recommendation with rich insights
            recommendation = self._generate_comprehensive_recommendation(
                cpu_analysis, memory_analysis, cost_analysis, performance_indicators
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Enhanced anomaly detection failed: {e}")
            return self._fallback_optimization_decision(current_metrics)

    def _extract_performance_indicators(self, metrics: Dict) -> Dict[str, float]:
        """Extract performance indicators from metrics"""
        try:
            nodes = metrics.get('nodes', [])
            if not nodes:
                return self._get_default_indicators()
            
            # Extract utilization metrics
            cpu_utils = []
            memory_utils = []
            
            for node in nodes:
                cpu_val = self._safe_float_extract(node, ['cpu_usage_pct', 'cpu_actual'], 35.0)
                memory_val = self._safe_float_extract(node, ['memory_usage_pct', 'memory_actual'], 60.0)
                cpu_utils.append(cpu_val)
                memory_utils.append(memory_val)
            
            # Calculate indicators
            cpu_array = np.array(cpu_utils)
            memory_array = np.array(memory_utils)
            
            indicators = {
                'cpu_utilization': float(np.mean(cpu_array)),
                'memory_utilization': float(np.mean(memory_array)),
                'cpu_variance': float(np.var(cpu_array)),
                'memory_variance': float(np.var(memory_array)),
                'cpu_max': float(np.max(cpu_array)),
                'memory_max': float(np.max(memory_array)),
                'cpu_outlier_ratio': self._calculate_outlier_ratio(cpu_array),
                'memory_outlier_ratio': self._calculate_outlier_ratio(memory_array),
                'node_count': len(nodes),
                'cpu_efficiency_score': self._calculate_efficiency_score(cpu_array),
                'memory_efficiency_score': self._calculate_efficiency_score(memory_array)
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Performance indicators extraction failed: {e}")
            return self._get_default_indicators()

    def _safe_float_extract(self, node: Dict, fields: List[str], default: float) -> float:
        """Safely extract float value from node data"""
        for field in fields:
            if field in node and node[field] is not None:
                try:
                    val = float(node[field])
                    if 0 <= val <= 200:
                        return val
                except (ValueError, TypeError):
                    continue
        return default

    def _calculate_outlier_ratio(self, values: np.ndarray) -> float:
        """Calculate ratio of outliers using IQR method"""
        try:
            if len(values) < 3:
                return 0.0
            
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = np.sum((values < lower_bound) | (values > upper_bound))
            return float(outliers / len(values))
            
        except Exception:
            return 0.0

    def _calculate_efficiency_score(self, values: np.ndarray) -> float:
        """Calculate efficiency score based on utilization and variance"""
        try:
            mean_util = np.mean(values)
            variance = np.var(values)
            
            # Ideal utilization is around 70%
            util_score = 1.0 - abs(mean_util - 70) / 100.0
            
            # Lower variance is better
            var_score = 1.0 / (1.0 + variance / 1000.0)
            
            return float(max(0.0, min(1.0, (util_score + var_score) / 2.0)))
            
        except Exception:
            return 0.5

    def _get_default_indicators(self) -> Dict[str, float]:
        """Get default performance indicators"""
        return {
            'cpu_utilization': 35.0,
            'memory_utilization': 60.0,
            'cpu_variance': 100.0,
            'memory_variance': 200.0,
            'cpu_max': 70.0,
            'memory_max': 80.0,
            'cpu_outlier_ratio': 0.1,
            'memory_outlier_ratio': 0.1,
            'node_count': 3,
            'cpu_efficiency_score': 0.6,
            'memory_efficiency_score': 0.7
        }

    def _analyze_cpu_efficiency_enhanced(self, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Enhanced CPU analysis with detailed insights"""
        cpu_util = indicators.get('cpu_utilization', 35)
        cpu_variance = indicators.get('cpu_variance', 0)
        outlier_ratio = indicators.get('cpu_outlier_ratio', 0)
        
        analysis = {
            'utilization_level': 'low' if cpu_util < 30 else 'medium' if cpu_util < 70 else 'high',
            'variance_level': 'low' if cpu_variance < 100 else 'medium' if cpu_variance < 500 else 'high',
            'has_outliers': outlier_ratio > 0.2,
            'efficiency_score': indicators.get('cpu_efficiency_score', 0.5),
            
            # Enhanced insights
            'optimization_potential': self._calculate_optimization_potential(cpu_util, cpu_variance),
            'scaling_recommendation': self._get_scaling_recommendation(cpu_util, cpu_variance),
            'cost_impact': self._estimate_cost_impact(cpu_util, 'cpu'),
            'urgency_level': self._determine_urgency(cpu_util, cpu_variance)
        }
        
        # Enhanced decision logic with detailed reasoning
        if cpu_util > 100:  # Extreme case
            analysis.update({
                'recommendation': 'OPTIMIZE_APPLICATION_CRITICAL',
                'reasoning': f'Critical CPU over-allocation detected ({cpu_util:.1f}%). Immediate application optimization required.',
                'confidence': 0.95,
                'expected_improvement': '40-70% efficiency gain',
                'timeline': 'immediate',
                'complexity': 'high'
            })
        elif cpu_util > 85 and cpu_variance > 1000:
            analysis.update({
                'recommendation': 'OPTIMIZE_APPLICATION',
                'reasoning': f'High CPU usage ({cpu_util:.1f}%) with high variance suggests inefficient code patterns.',
                'confidence': 0.85,
                'expected_improvement': '20-40% efficiency gain',
                'timeline': '1-2 weeks',
                'complexity': 'medium'
            })
        elif cpu_util > 90 and cpu_variance < 200:
            analysis.update({
                'recommendation': 'SCALE_UP',
                'reasoning': f'Consistently high CPU ({cpu_util:.1f}%) indicates legitimate scaling need.',
                'confidence': 0.9,
                'expected_improvement': 'Linear scaling benefit',
                'timeline': 'immediate',
                'complexity': 'low'
            })
        elif outlier_ratio > 0.3:
            analysis.update({
                'recommendation': 'OPTIMIZE_WORKLOAD_DISTRIBUTION',
                'reasoning': f'Uneven CPU distribution ({outlier_ratio:.1%} outliers) suggests load balancing issues.',
                'confidence': 0.75,
                'expected_improvement': '15-25% efficiency gain',
                'timeline': '3-5 days',
                'complexity': 'medium'
            })
        else:
            analysis.update({
                'recommendation': 'MONITOR',
                'reasoning': f'CPU patterns within acceptable ranges ({cpu_util:.1f}% utilization).',
                'confidence': 0.6,
                'expected_improvement': 'N/A',
                'timeline': 'ongoing',
                'complexity': 'low'
            })
        
        return analysis

    def _analyze_memory_patterns_enhanced(self, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Enhanced memory analysis with detailed insights"""
        memory_util = indicators.get('memory_utilization', 60)
        memory_variance = indicators.get('memory_variance', 0)
        
        analysis = {
            'utilization_level': 'low' if memory_util < 40 else 'medium' if memory_util < 80 else 'high',
            'variance_level': 'low' if memory_variance < 50 else 'medium' if memory_variance < 200 else 'high',
            'efficiency_score': indicators.get('memory_efficiency_score', 0.5),
            
            # Enhanced insights
            'leak_probability': self._assess_memory_leak_probability(memory_util, memory_variance),
            'optimization_potential': self._calculate_optimization_potential(memory_util, memory_variance),
            'oom_risk': self._assess_oom_risk(memory_util, memory_variance),
            'cost_impact': self._estimate_cost_impact(memory_util, 'memory')
        }
        
        # Enhanced recommendations
        if memory_util > 90 and memory_variance < 50:
            analysis.update({
                'recommendation': 'SCALE_UP_URGENT',
                'reasoning': f'Critical memory pressure ({memory_util:.1f}%) with low variance indicates capacity constraint.',
                'confidence': 0.95,
                'expected_improvement': 'Prevent OOM crashes',
                'timeline': 'immediate',
                'priority': 'critical'
            })
        elif memory_util > 80 and memory_variance > 300:
            analysis.update({
                'recommendation': 'OPTIMIZE_MEMORY_USAGE',
                'reasoning': f'High variable memory ({memory_util:.1f}% ± {memory_variance:.0f}) suggests memory leaks or inefficient allocation.',
                'confidence': 0.8,
                'expected_improvement': '25-45% memory efficiency',
                'timeline': '1-3 weeks',
                'priority': 'high'
            })
        elif memory_util < 30:
            analysis.update({
                'recommendation': 'SCALE_DOWN',
                'reasoning': f'Low memory utilization ({memory_util:.1f}%) indicates over-provisioning.',
                'confidence': 0.75,
                'expected_improvement': '20-40% cost savings',
                'timeline': '1 week',
                'priority': 'medium'
            })
        else:
            analysis.update({
                'recommendation': 'MONITOR',
                'reasoning': f'Memory patterns within acceptable ranges ({memory_util:.1f}% utilization).',
                'confidence': 0.6,
                'expected_improvement': 'N/A',
                'timeline': 'ongoing',
                'priority': 'low'
            })
        
        return analysis

    def _analyze_cost_optimization(self, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Analyze cost optimization opportunities"""
        cpu_util = indicators.get('cpu_utilization', 35)
        memory_util = indicators.get('memory_utilization', 60)
        node_count = indicators.get('node_count', 3)
        
        # Calculate potential savings
        cpu_waste = max(0, 100 - cpu_util)
        memory_waste = max(0, 100 - memory_util)
        overall_waste = (cpu_waste + memory_waste) / 2
        
        # Estimate monthly cost impact (rough estimates)
        estimated_monthly_cost = node_count * 100  # $100 per node per month
        potential_savings = (overall_waste / 100) * estimated_monthly_cost
        
        return {
            'waste_percentage': overall_waste,
            'potential_monthly_savings': potential_savings,
            'right_sizing_opportunity': overall_waste > 30,
            'optimization_priority': 'high' if overall_waste > 50 else 'medium' if overall_waste > 30 else 'low',
            'payback_period': '1-2 months' if overall_waste > 40 else '3-6 months',
            'implementation_complexity': 'low' if overall_waste > 50 else 'medium'
        }

    def _generate_comprehensive_recommendation(self, cpu_analysis: Dict, memory_analysis: Dict, 
                                             cost_analysis: Dict, indicators: Dict) -> Dict[str, Any]:
        """Generate comprehensive recommendation with rich insights"""
        
        # Determine primary recommendation
        recommendations = []
        
        # Add CPU recommendation
        cpu_rec = cpu_analysis.get('recommendation', 'MONITOR')
        if cpu_rec != 'MONITOR':
            recommendations.append({
                'action': cpu_rec,
                'priority': cpu_analysis.get('confidence', 0.5),
                'reasoning': cpu_analysis.get('reasoning', ''),
                'type': 'cpu',
                'expected_improvement': cpu_analysis.get('expected_improvement', 'Unknown'),
                'timeline': cpu_analysis.get('timeline', 'Unknown'),
                'complexity': cpu_analysis.get('complexity', 'medium')
            })
        
        # Add memory recommendation
        memory_rec = memory_analysis.get('recommendation', 'MONITOR')
        if memory_rec != 'MONITOR':
            recommendations.append({
                'action': memory_rec,
                'priority': memory_analysis.get('confidence', 0.5),
                'reasoning': memory_analysis.get('reasoning', ''),
                'type': 'memory',
                'expected_improvement': memory_analysis.get('expected_improvement', 'Unknown'),
                'timeline': memory_analysis.get('timeline', 'Unknown'),
                'complexity': memory_analysis.get('complexity', 'medium')
            })
        
        # Select highest priority recommendation
        if recommendations:
            best_rec = max(recommendations, key=lambda x: x['priority'])
            
            return {
                'primary_action': best_rec['action'],
                'confidence': best_rec['priority'],
                'reasoning': best_rec['reasoning'],
                'resource_focus': best_rec['type'],
                'expected_improvement': best_rec['expected_improvement'],
                'implementation_timeline': best_rec['timeline'],
                'complexity': best_rec['complexity'],
                
                # Rich insights
                'all_recommendations': recommendations,
                'cpu_analysis': cpu_analysis,
                'memory_analysis': memory_analysis,
                'cost_analysis': cost_analysis,
                'decision_method': 'enhanced_ml_performance_analysis',
                
                # Actionable insights
                'immediate_actions': self._get_immediate_actions(recommendations),
                'long_term_strategy': self._get_long_term_strategy(cpu_analysis, memory_analysis),
                'monitoring_recommendations': self._get_monitoring_recommendations(indicators),
                'success_metrics': self._define_success_metrics(best_rec)
            }
        else:
            return {
                'primary_action': 'MONITOR',
                'confidence': 0.5,
                'reasoning': 'All metrics within normal ranges',
                'resource_focus': 'balanced',
                'cost_analysis': cost_analysis,
                'decision_method': 'enhanced_ml_performance_analysis'
            }

    # Helper methods for enhanced insights
    def _calculate_optimization_potential(self, utilization: float, variance: float) -> str:
        """Calculate optimization potential"""
        if utilization > 90 or variance > 500:
            return 'high'
        elif utilization > 70 or variance > 200:
            return 'medium'
        elif utilization < 30:
            return 'right_sizing'
        else:
            return 'low'

    def _get_scaling_recommendation(self, utilization: float, variance: float) -> str:
        """Get scaling recommendation"""
        if utilization > 85 and variance < 200:
            return 'scale_up'
        elif utilization < 30:
            return 'scale_down'
        elif variance > 500:
            return 'optimize_first'
        else:
            return 'maintain'

    def _estimate_cost_impact(self, utilization: float, resource_type: str) -> Dict[str, Any]:
        """Estimate cost impact"""
        if utilization > 90:
            return {'impact': 'high_cost_if_not_scaled', 'direction': 'increase', 'urgency': 'high'}
        elif utilization < 30:
            return {'impact': 'savings_opportunity', 'direction': 'decrease', 'urgency': 'medium'}
        else:
            return {'impact': 'neutral', 'direction': 'stable', 'urgency': 'low'}

    def _determine_urgency(self, utilization: float, variance: float) -> str:
        """Determine urgency level"""
        if utilization > 95 or variance > 1000:
            return 'critical'
        elif utilization > 85 or variance > 500:
            return 'high'
        elif utilization > 70 or variance > 200:
            return 'medium'
        else:
            return 'low'

    def _assess_memory_leak_probability(self, utilization: float, variance: float) -> str:
        """Assess memory leak probability"""
        if utilization > 80 and variance > 300:
            return 'high'
        elif utilization > 70 and variance > 200:
            return 'medium'
        else:
            return 'low'

    def _assess_oom_risk(self, utilization: float, variance: float) -> str:
        """Assess Out of Memory risk"""
        if utilization > 90:
            return 'high'
        elif utilization > 80:
            return 'medium'
        else:
            return 'low'

    def _get_immediate_actions(self, recommendations: List[Dict]) -> List[str]:
        """Get immediate actionable steps"""
        actions = []
        for rec in recommendations:
            if rec.get('timeline') == 'immediate':
                actions.append(f"Implement {rec['action']} for {rec['type']} optimization")
        return actions or ['Continue monitoring current patterns']

    def _get_long_term_strategy(self, cpu_analysis: Dict, memory_analysis: Dict) -> List[str]:
        """Get long-term strategic recommendations"""
        strategy = []
        
        if cpu_analysis.get('optimization_potential') == 'high':
            strategy.append('Develop CPU optimization roadmap with code profiling')
        
        if memory_analysis.get('optimization_potential') == 'high':
            strategy.append('Implement memory usage optimization and leak detection')
        
        if not strategy:
            strategy.append('Maintain current resource allocation with regular review')
        
        return strategy

    def _get_monitoring_recommendations(self, indicators: Dict) -> List[str]:
        """Get monitoring recommendations"""
        return [
            'Monitor resource utilization trends',
            'Set up alerts for resource threshold breaches', 
            'Track application performance metrics',
            'Review HPA scaling patterns weekly'
        ]

    def _define_success_metrics(self, recommendation: Dict) -> List[str]:
        """Define success metrics for recommendations"""
        action = recommendation.get('action', 'MONITOR')
        
        if 'OPTIMIZE' in action:
            return [
                'Reduce resource utilization variance by 30%',
                'Improve application response time by 20%',
                'Decrease resource waste by 25%'
            ]
        elif 'SCALE' in action:
            return [
                'Achieve target utilization levels',
                'Eliminate resource constraints',
                'Maintain stable performance under load'
            ]
        else:
            return [
                'Maintain current performance levels',
                'No degradation in service quality',
                'Stable resource consumption patterns'
            ]

    def _fallback_optimization_decision(self, metrics: Dict) -> Dict[str, Any]:
        """Fallback decision when analysis fails"""
        return {
            'primary_action': 'MONITOR',
            'confidence': 0.3,
            'reasoning': 'Analysis failed, manual review recommended',
            'resource_focus': 'unknown',
            'decision_method': 'fallback',
            'immediate_actions': ['Review metrics manually'],
            'cost_analysis': {'waste_percentage': 0, 'potential_monthly_savings': 0}
        }


class SelfLearningIntelligentHPAEngine:
    """Complete Self-learning HPA engine with comprehensive insights"""
    
    def __init__(self, model_path: str = None, enable_self_learning: bool = True):
        self.workload_classifier = SelfLearningWorkloadClassifier(
            model_path=model_path, 
            enable_self_learning=enable_self_learning
        )
        self.anomaly_detector = EnhancedPerformanceAnomalyDetector()
        self.enable_self_learning = enable_self_learning
        
        if self.workload_classifier.is_trained:
            logger.info("🧠 Enhanced self-learning HPA engine ready with comprehensive insights")
            self.ml_mode = True
        else:
            logger.info("📊 Enhanced self-learning HPA engine in rule-based mode with rich insights")
            self.ml_mode = False

    def analyze_and_recommend_with_comprehensive_insights(self, metrics_data: Dict, 
                                                         current_hpa_config: Dict,
                                                         cluster_id: str = None) -> Dict[str, Any]:
        """
        Enhanced analysis with comprehensive insights matching your original model plus self-learning
        """
        try:
            logger.info("🧠 Starting comprehensive self-learning HPA analysis with rich insights...")
            
            # Step 1: Extract features for classification
            features = self.workload_classifier.extract_advanced_features(metrics_data)
            
            # Step 2: Classify workload with learning
            cluster_context = {
                'cluster_id': cluster_id,
                'hpa_config': current_hpa_config,
                'node_count': len(metrics_data.get('nodes', [])),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            workload_classification = self.workload_classifier.predict_with_learning(
                features, cluster_context=cluster_context
            )
            
            # Step 3: Enhanced optimization analysis with learning context
            learning_context = self._build_learning_context()
            optimization_analysis = self.anomaly_detector.detect_optimization_scenarios(
                features, metrics_data, learning_context
            )
            
            # Step 4: Generate comprehensive HPA recommendations
            hpa_recommendation = self._generate_comprehensive_hpa_recommendation(
                workload_classification, optimization_analysis, current_hpa_config, metrics_data
            )
            
            # Step 5: Add learning insights and status
            learning_status = self.workload_classifier.get_learning_status()
            
            # Step 6: Generate workload characteristics (like your original model)
            workload_characteristics = self._generate_workload_characteristics(
                workload_classification, features, metrics_data
            )
            
            return {
                'workload_classification': workload_classification,
                'optimization_analysis': optimization_analysis,
                'hpa_recommendation': hpa_recommendation,
                'workload_characteristics': workload_characteristics,
                'self_learning_status': learning_status,
                'analysis_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'method': 'comprehensive_self_learning_analysis',
                    'learning_enabled': self.enable_self_learning,
                    'features_analyzed': len(features.columns) if features is not None else 0,
                    'cluster_context': cluster_context,
                    'insight_level': 'comprehensive'
                },
                
                # Additional insights like your original model
                'hpa_chart_data': self._generate_hpa_chart_data(workload_classification, optimization_analysis),
                'optimization_recommendation': self._format_optimization_recommendation(optimization_analysis),
                'current_implementation': self._analyze_current_implementation(metrics_data),
                'performance_insights': self._generate_performance_insights(features, metrics_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Comprehensive self-learning analysis failed: {e}")
            return self._fallback_comprehensive_analysis(metrics_data, current_hpa_config)

    def _generate_comprehensive_hpa_recommendation(self, workload_class: Dict, optimization: Dict, 
                                                  current_hpa: Dict, metrics_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive HPA recommendations with rich insights"""
        
        workload_type = workload_class.get('workload_type', 'BALANCED')
        primary_action = optimization.get('primary_action', 'MONITOR')
        confidence = min(workload_class.get('confidence', 0.5), optimization.get('confidence', 0.5))
        
        # Get current utilization
        nodes = metrics_data.get('nodes', [])
        if nodes:
            avg_cpu = np.mean([node.get('cpu_usage_pct', 0) for node in nodes])
            avg_memory = np.mean([node.get('memory_usage_pct', 0) for node in nodes])
        else:
            avg_cpu, avg_memory = 35, 60
        
        # Base recommendation structure (enhanced)
        recommendation = {
            'action': 'MONITOR',
            'title': 'Comprehensive Self-Learning HPA Analysis',
            'description': 'Advanced ML-based workload analysis with continuous learning',
            'confidence': confidence,
            'method': 'comprehensive_self_learning_ml',
            'workload_type': workload_type,
            'current_utilization': {'cpu': avg_cpu, 'memory': avg_memory},
            
            # Enhanced recommendation details
            'implementation_timeline': optimization.get('implementation_timeline', 'immediate'),
            'expected_improvement': optimization.get('expected_improvement', 'To be determined'),
            'complexity': optimization.get('complexity', 'medium'),
            'cost_impact': optimization.get('cost_analysis', {}),
            'success_metrics': optimization.get('success_metrics', [])
        }
        
        # Workload-specific enhanced recommendations
        if primary_action == 'OPTIMIZE_APPLICATION':
            recommendation.update({
                'action': 'OPTIMIZE_BEFORE_SCALING',
                'title': f'Optimize {workload_type} Workload Before Scaling',
                'description': f'ML analysis detected inefficient resource usage patterns. '
                             f'Current CPU: {avg_cpu:.1f}%, Memory: {avg_memory:.1f}%. '
                             f'{optimization.get("reasoning", "Application optimization recommended.")}',
                'priority': 'high',
                'optimization_focus': optimization.get('resource_focus', 'cpu'),
                'immediate_actions': optimization.get('immediate_actions', []),
                'long_term_strategy': optimization.get('long_term_strategy', [])
            })
            
        elif primary_action in ['SCALE_UP', 'SCALE_UP_URGENT']:
            if workload_type == 'CPU_INTENSIVE':
                recommendation.update({
                    'action': 'IMPLEMENT_CPU_BASED_HPA',
                    'title': 'CPU-Based HPA Recommended',
                    'description': f'ML classified workload as CPU-intensive with {confidence:.1%} confidence. '
                                 f'Current CPU utilization: {avg_cpu:.1f}%. '
                                 f'{optimization.get("reasoning", "CPU-based HPA will provide better responsiveness.")}',
                    'hpa_config': {
                        'metric': 'cpu',
                        'target': 70,
                        'min_replicas': max(2, int(avg_cpu / 50)),
                        'max_replicas': max(10, int(avg_cpu / 10))
                    },
                    'scaling_strategy': 'aggressive' if primary_action == 'SCALE_UP_URGENT' else 'moderate'
                })
            elif workload_type == 'MEMORY_INTENSIVE':
                recommendation.update({
                    'action': 'IMPLEMENT_MEMORY_BASED_HPA',
                    'title': 'Memory-Based HPA Recommended',
                    'description': f'ML classified workload as memory-intensive with {confidence:.1%} confidence. '
                                 f'Current memory utilization: {avg_memory:.1f}%. '
                                 f'{optimization.get("reasoning", "Memory-based HPA will prevent OOM issues.")}',
                    'hpa_config': {
                        'metric': 'memory',
                        'target': 75,
                        'min_replicas': max(3, int(avg_memory / 40)),
                        'max_replicas': max(15, int(avg_memory / 8))
                    },
                    'scaling_strategy': 'conservative' if avg_memory > 90 else 'moderate'
                })
            
        elif primary_action == 'SCALE_DOWN':
            recommendation.update({
                'action': 'REDUCE_RESOURCES',
                'title': 'Resource Right-Sizing Opportunity',
                'description': f'ML analysis indicates over-provisioning. '
                             f'{optimization.get("reasoning", "Consider reducing resource requests.")}',
                'cost_impact': 'potential_savings',
                'savings_estimate': optimization.get('cost_analysis', {}).get('potential_monthly_savings', 0)
            })
            
        elif workload_type == 'BURSTY':
            recommendation.update({
                'action': 'IMPLEMENT_PREDICTIVE_SCALING',
                'title': 'Predictive Scaling for Bursty Workload',
                'description': f'ML detected bursty traffic pattern with {confidence:.1%} confidence. '
                             f'Consider implementing predictive scaling or custom metrics-based HPA.',
                'advanced_config': True,
                'monitoring_requirements': ['Custom metrics', 'Predictive algorithms', 'Traffic pattern analysis']
            })
        
        # Add comprehensive ML insights
        recommendation['ml_insights'] = {
            'workload_pattern': workload_type,
            'pattern_confidence': workload_class.get('confidence', 0.5),
            'alternative_patterns': workload_class.get('alternative_patterns', []),
            'feature_insights': workload_class.get('feature_insights', {}),
            'optimization_opportunity': primary_action,
            'resource_efficiency': {
                'cpu_efficiency': optimization.get('cpu_analysis', {}).get('efficiency_score', 0.5),
                'memory_efficiency': optimization.get('memory_analysis', {}).get('efficiency_score', 0.5)
            },
            'learning_confidence': workload_class.get('confidence_level', 'medium'),
            'recommendation_reasoning': optimization.get('reasoning', 'ML-based analysis'),
            'model_source': workload_class.get('model_path', 'rule-based')
        }
        
        return recommendation

    def _generate_workload_characteristics(self, workload_class: Dict, features: pd.DataFrame, 
                                         metrics_data: Dict) -> Dict[str, Any]:
        """Generate detailed workload characteristics like your original model"""
        try:
            feature_insights = workload_class.get('feature_insights', {})
            
            return {
                'workload_type': workload_class.get('workload_type', 'BALANCED'),
                'confidence': workload_class.get('confidence', 0.5),
                'cpu_utilization': feature_insights.get('resource_utilization', {}).get('cpu_mean', 35),
                'memory_utilization': feature_insights.get('resource_utilization', {}).get('memory_mean', 60),
                'resource_balance': feature_insights.get('resource_utilization', {}).get('resource_balance', 25),
                'performance_stability': feature_insights.get('performance_patterns', {}).get('cpu_stability', 0.8),
                'burst_patterns': feature_insights.get('performance_patterns', {}).get('burst_frequency', 0.1),
                'efficiency_score': feature_insights.get('efficiency_metrics', {}).get('overall_efficiency', 0.6),
                'optimization_potential': 'high' if feature_insights.get('efficiency_metrics', {}).get('waste_indicator', 0) > 50 else 'medium',
                'cluster_health': feature_insights.get('cluster_health', {}),
                'ml_classification': {
                    'method': workload_class.get('method', 'rule-based'),
                    'feature_count': workload_class.get('feature_count', 53),
                    'confidence_level': workload_class.get('confidence_level', 'medium'),
                    'self_learning_enabled': workload_class.get('self_learning_enabled', False)
                }
            }
        except Exception as e:
            logger.error(f"❌ Workload characteristics generation failed: {e}")
            return {}

    def _generate_hpa_chart_data(self, workload_class: Dict, optimization: Dict) -> Dict[str, Any]:
        """Generate HPA chart data for visualization"""
        workload_type = workload_class.get('workload_type', 'BALANCED')
        
        # Generate dynamic chart data based on workload type
        if workload_type == 'CPU_INTENSIVE':
            base_replicas = [3, 2, 6, 1, 4]
            cpu_multiplier = 1.5
            memory_multiplier = 1.0
        elif workload_type == 'MEMORY_INTENSIVE':
            base_replicas = [4, 3, 8, 2, 5]
            cpu_multiplier = 1.0
            memory_multiplier = 1.4
        elif workload_type == 'BURSTY':
            base_replicas = [2, 1, 10, 1, 3]
            cpu_multiplier = 1.8
            memory_multiplier = 1.2
        elif workload_type == 'LOW_UTILIZATION':
            base_replicas = [2, 1, 3, 1, 2]
            cpu_multiplier = 0.8
            memory_multiplier = 0.8
        else:  # BALANCED
            base_replicas = [3, 2, 5, 1, 3]
            cpu_multiplier = 1.2
            memory_multiplier = 1.2
        
        return {
            'timePoints': ['Current', 'Optimized', 'Peak Load', 'Low Load', 'Average'],
            'cpuReplicas': [int(r * cpu_multiplier) for r in base_replicas],
            'memoryReplicas': [int(r * memory_multiplier) for r in base_replicas],
            'data_source': 'comprehensive_self_learning_analysis',
            'workload_type': workload_type,
            'confidence': workload_class.get('confidence', 0.5)
        }

    def _format_optimization_recommendation(self, optimization: Dict) -> Dict[str, Any]:
        """Format optimization recommendation for display"""
        return {
            'title': f"Optimization Recommendation: {optimization.get('primary_action', 'Monitor')}",
            'description': optimization.get('reasoning', 'Continue monitoring current patterns'),
            'action': optimization.get('primary_action', 'MONITOR'),
            'confidence': optimization.get('confidence', 0.5),
            'ml_enhanced': True,
            'resource_focus': optimization.get('resource_focus', 'balanced'),
            'expected_improvement': optimization.get('expected_improvement', 'To be determined'),
            'implementation_timeline': optimization.get('implementation_timeline', 'ongoing'),
            'cost_impact': optimization.get('cost_analysis', {}),
            'immediate_actions': optimization.get('immediate_actions', []),
            'success_metrics': optimization.get('success_metrics', [])
        }

    def _analyze_current_implementation(self, metrics_data: Dict) -> Dict[str, Any]:
        """Analyze current HPA implementation"""
        hpa_data = metrics_data.get('hpa_implementation', {})
        
        return {
            'pattern': hpa_data.get('current_hpa_pattern', 'not_detected'),
            'confidence': hpa_data.get('confidence', 'unknown'),
            'total_hpas': hpa_data.get('total_hpas', 0),
            'ml_analysis': True,
            'maturity_level': 'advanced' if hpa_data.get('total_hpas', 0) > 2 else 'basic',
            'optimization_opportunities': hpa_data.get('total_hpas', 0) == 0
        }

    def _generate_performance_insights(self, features: pd.DataFrame, metrics_data: Dict) -> Dict[str, Any]:
        """Generate additional performance insights"""
        try:
            if features is not None and not features.empty:
                feature_data = features.iloc[0]
                
                return {
                    'resource_utilization_trend': 'increasing' if feature_data.get('cpu_mean', 0) > 70 else 'stable',
                    'performance_stability': 'high' if feature_data.get('cpu_stability_score', 0) > 0.8 else 'medium',
                    'scalability_readiness': 'ready' if feature_data.get('overall_efficiency_score', 0) > 0.7 else 'needs_optimization',
                    'cost_efficiency': 'good' if feature_data.get('avg_cpu_gap', 0) < 30 else 'poor',
                    'monitoring_health': 'excellent' if feature_data.get('node_readiness_ratio', 1.0) == 1.0 else 'needs_attention'
                }
        except Exception as e:
            logger.error(f"❌ Performance insights generation failed: {e}")
        
        return {
            'resource_utilization_trend': 'unknown',
            'performance_stability': 'unknown',
            'scalability_readiness': 'unknown',
            'cost_efficiency': 'unknown',
            'monitoring_health': 'unknown'
        }

    def _build_learning_context(self) -> Dict[str, Any]:
        """Build learning context for enhanced analysis"""
        try:
            learning_status = self.workload_classifier.get_learning_status()
            
            return {
                'total_predictions': learning_status.get('samples', {}).get('total_collected', 0),
                'supervised_samples': learning_status.get('samples', {}).get('supervised', 0),
                'model_confidence': learning_status.get('confidence_threshold', 0.7),
                'learning_trend': 'improving' if learning_status.get('samples', {}).get('supervised', 0) > 10 else 'building'
            }
        except Exception as e:
            logger.error(f"❌ Learning context building failed: {e}")
            return {}

    def _fallback_comprehensive_analysis(self, metrics_data: Dict, current_hpa: Dict) -> Dict[str, Any]:
        """Comprehensive fallback analysis"""
        return {
            'workload_classification': {
                'workload_type': 'UNKNOWN',
                'confidence': 0.3,
                'method': 'fallback'
            },
            'optimization_analysis': {
                'primary_action': 'MONITOR',
                'confidence': 0.3,
                'reasoning': 'Analysis failed, using fallback'
            },
            'hpa_recommendation': {
                'action': 'MONITOR',
                'title': 'Manual Analysis Recommended',
                'description': 'Comprehensive analysis failed, please review manually',
                'confidence': 0.3
            },
            'workload_characteristics': {
                'workload_type': 'UNKNOWN',
                'optimization_potential': 'unknown'
            },
            'self_learning_status': {
                'error': 'Analysis failed',
                'learning_enabled': self.enable_self_learning
            },
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'method': 'fallback',
                'error': 'Comprehensive analysis failed'
            }
        }

    # Public methods for external use
    def provide_feedback(self, analysis_timestamp: str, correct_workload_type: str, 
                        feedback_score: float = 1.0, notes: str = ""):
        """Provide feedback for continuous learning"""
        if self.enable_self_learning:
            self.workload_classifier.provide_feedback(analysis_timestamp, correct_workload_type, feedback_score, notes)

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get comprehensive learning insights"""
        return self.workload_classifier.get_learning_status()

    def force_model_update(self) -> bool:
        """Force model retraining"""
        return self.workload_classifier.force_retrain()

    def export_learning_history(self, format: str = 'csv') -> str:
        """Export learning history"""
        return self.workload_classifier.export_learning_data(format)

def test_extreme_case_classification():
    """Test function to validate extreme case handling"""
    try:
        logger.info("🧪 Testing extreme case classification fixes...")
        
        # Test Case 1: Extreme CPU case (like your 1255% scenario)
        extreme_cpu_metrics = {
            'nodes': [
                {'cpu_usage_pct': 1255, 'memory_usage_pct': 65, 'status': 'Ready'},
                {'cpu_usage_pct': 800, 'memory_usage_pct': 70, 'status': 'Ready'},
                {'cpu_usage_pct': 1100, 'memory_usage_pct': 68, 'status': 'Ready'}
            ],
            'hpa_implementation': {
                'current_hpa_pattern': 'cpu_based_hpa',
                'confidence': 'high',
                'total_hpas': 5
            }
        }
        
        # Test Case 2: Normal utilization case
        normal_metrics = {
            'nodes': [
                {'cpu_usage_pct': 45, 'memory_usage_pct': 60, 'status': 'Ready'},
                {'cpu_usage_pct': 50, 'memory_usage_pct': 65, 'status': 'Ready'},
                {'cpu_usage_pct': 40, 'memory_usage_pct': 62, 'status': 'Ready'}
            ],
            'hpa_implementation': {
                'current_hpa_pattern': 'memory_based_hpa',
                'confidence': 'medium',
                'total_hpas': 2
            }
        }
        
        # Initialize engines
        from app.ml.workload_performance_analyzer import create_comprehensive_self_learning_hpa_engine
        
        engine = create_comprehensive_self_learning_hpa_engine(
            model_path="app/ml/data_feed",
            enable_self_learning=True
        )
        
        # Test extreme case
        print("\n=== TESTING EXTREME CPU CASE ===")
        extreme_result = engine.analyze_and_recommend_with_comprehensive_insights(
            metrics_data=extreme_cpu_metrics,
            current_hpa_config={},
            cluster_id="test-extreme-cpu"
        )
        
        extreme_workload_type = extreme_result['workload_classification']['workload_type']
        extreme_confidence = extreme_result['workload_classification']['confidence']
        extreme_chart = extreme_result.get('hpa_chart_data', {})
        
        print(f"Extreme CPU Classification: {extreme_workload_type} (confidence: {extreme_confidence:.2f})")
        print(f"CPU Replicas: {extreme_chart.get('cpuReplicas', [])}")
        print(f"Memory Replicas: {extreme_chart.get('memoryReplicas', [])}")
        print(f"Chart Differential: {extreme_chart.get('scaling_differential', 0):.2f}")
        
        # Test normal case
        print("\n=== TESTING NORMAL UTILIZATION CASE ===")
        normal_result = engine.analyze_and_recommend_with_comprehensive_insights(
            metrics_data=normal_metrics,
            current_hpa_config={},
            cluster_id="test-normal"
        )
        
        normal_workload_type = normal_result['workload_classification']['workload_type']
        normal_confidence = normal_result['workload_classification']['confidence']
        normal_chart = normal_result.get('hpa_chart_data', {})
        
        print(f"Normal Classification: {normal_workload_type} (confidence: {normal_confidence:.2f})")
        print(f"CPU Replicas: {normal_chart.get('cpuReplicas', [])}")
        print(f"Memory Replicas: {normal_chart.get('memoryReplicas', [])}")
        print(f"Chart Differential: {normal_chart.get('scaling_differential', 0):.2f}")
        
        # Validation checks
        validation_results = []
        
        # Check 1: Extreme CPU should be classified as CPU_INTENSIVE
        if extreme_workload_type == 'CPU_INTENSIVE':
            validation_results.append("✅ Extreme CPU correctly classified as CPU_INTENSIVE")
        else:
            validation_results.append(f"❌ Extreme CPU incorrectly classified as {extreme_workload_type}")
        
        # Check 2: Chart data should be different for CPU vs Memory
        extreme_cpu_replicas = extreme_chart.get('cpuReplicas', [])
        extreme_memory_replicas = extreme_chart.get('memoryReplicas', [])
        
        if extreme_cpu_replicas != extreme_memory_replicas:
            validation_results.append("✅ Extreme case shows different CPU vs Memory scaling")
        else:
            validation_results.append("❌ Extreme case shows identical CPU vs Memory scaling")
        
        # Check 3: Normal case should also show differentiation
        normal_cpu_replicas = normal_chart.get('cpuReplicas', [])
        normal_memory_replicas = normal_chart.get('memoryReplicas', [])
        
        if normal_cpu_replicas != normal_memory_replicas:
            validation_results.append("✅ Normal case shows different CPU vs Memory scaling")
        else:
            validation_results.append("❌ Normal case shows identical CPU vs Memory scaling")
        
        # Check 4: Confidence should be reasonable
        if extreme_confidence > 0.8:
            validation_results.append("✅ Extreme case has high confidence")
        else:
            validation_results.append(f"⚠️ Extreme case has lower confidence: {extreme_confidence:.2f}")
        
        print("\n=== VALIDATION RESULTS ===")
        for result in validation_results:
            print(result)
        
        # Overall assessment
        passed_checks = sum(1 for r in validation_results if r.startswith("✅"))
        total_checks = len(validation_results)
        
        if passed_checks == total_checks:
            print(f"\n🎉 ALL FIXES WORKING: {passed_checks}/{total_checks} checks passed")
            return True
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: {passed_checks}/{total_checks} checks passed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
def create_comprehensive_self_learning_hpa_engine(model_path: str = None, enable_self_learning: bool = True):
    """
    Create comprehensive self-learning HPA engine with rich insights
    
    This engine provides:
    - All insights from your original model
    - Self-learning capabilities
    - Enhanced optimization recommendations
    - Comprehensive cost analysis
    - Rich visualization data
    - Production-ready error handling
    - Complete feature extraction
    - Database-backed learning
    """
    return SelfLearningIntelligentHPAEngine(
        model_path=model_path, 
        enable_self_learning=enable_self_learning
    )


# Example usage
if __name__ == "__main__":
    # Initialize the engine
    engine = create_comprehensive_self_learning_hpa_engine(
        model_path="./hpa_models", 
        enable_self_learning=True
    )
    
    # Example metrics data
    sample_metrics = {
        'nodes': [
            {'cpu_usage_pct': 65, 'memory_usage_pct': 80, 'status': 'Ready'},
            {'cpu_usage_pct': 70, 'memory_usage_pct': 85, 'status': 'Ready'},
            {'cpu_usage_pct': 45, 'memory_usage_pct': 60, 'status': 'Ready'}
        ],
        'hpa_implementation': {
            'current_hpa_pattern': 'cpu_based_hpa',
            'confidence': 'medium',
            'total_hpas': 2
        }
    }
    
    # Analyze and get comprehensive insights
    result = engine.analyze_and_recommend_with_comprehensive_insights(
        metrics_data=sample_metrics,
        current_hpa_config={},
        cluster_id="production-cluster-1"
    )
    
    print("🚀 Complete Self-Learning HPA Engine Analysis:")
    print(f"Workload Type: {result['workload_classification']['workload_type']}")
    print(f"Confidence: {result['workload_classification']['confidence']:.2f}")
    print(f"Recommendation: {result['hpa_recommendation']['action']}")
    print(f"Learning Status: {result['self_learning_status']['learning_enabled']}")