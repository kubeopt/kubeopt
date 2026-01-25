#!/usr/bin/env python3
"""
Workload Performance Analyzer - Consistent and Simplified
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer

Complete self-learning workload analyzer with consistent variable naming.
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

# Import unified node processor
try:
    from shared.node_data_processor import NodeDataProcessor
except ImportError:
    NodeDataProcessor = None

# Import performance standards
try:
    from shared.standards.performance_standards import SystemPerformanceStandards
    # Create SysPerf alias for compatibility
    SysPerf = SystemPerformanceStandards
except ImportError:
    SystemPerformanceStandards = None
    SysPerf = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WorkloadPerformanceAnalyzer:
    """Main workload analyzer with comprehensive insights"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.classifier = SelfLearningWorkloadClassifier()
        self.anomaly_detector = AnomalyDetector()
        self.insight_generator = InsightGenerator()
        logger.info("WorkloadPerformanceAnalyzer initialized")
    
    def analyze(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis method with consistent variable naming
        
        Args:
            metrics_data: Dictionary with nodes, workloads, etc.
            
        Returns:
            Comprehensive analysis results
        """
        try:
            logger.info("Starting workload performance analysis")
            
            # Extract features with consistent naming
            features_df = self.classifier.extract_features(metrics_data)
            
            # Classify workload type
            classification = self.classifier.classify_workload_type(features_df)
            
            # Detect anomalies
            anomalies = self.anomaly_detector.detect_anomalies(features_df)
            
            # Generate insights
            insights = self.insight_generator.generate_insights(
                metrics_data, classification, anomalies
            )
            
            # Build comprehensive result
            result = {
                'workload_classification': classification,
                'anomalies': anomalies,
                'insights': insights,
                'feature_summary': self._extract_feature_summary(features_df),
                'recommendations': self._generate_recommendations(
                    classification, anomalies, insights
                ),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Analysis complete: {classification.get('workload_type', 'UNKNOWN')} "
                       f"with {classification.get('confidence') or 0:.2f} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"Workload analysis failed: {e}")
            raise ValueError(f"Failed to analyze workload performance: {e}")
    
    def _extract_feature_summary(self, features_df: pd.DataFrame) -> Dict[str, float]:
        """Extract summary statistics from features"""
        if features_df.empty:
            return {}
        
        features = features_df.iloc[0]
        return {
            'cpu_usage_pct': float(features.get('cpu_mean') or 0),
            'memory_usage_pct': float(features.get('memory_mean') or 0),
            'cpu_peak_pct': float(features.get('cpu_max') or 0),
            'memory_peak_pct': float(features.get('memory_max') or 0),
            'efficiency_score': float(features.get('overall_efficiency_score') or 0),
            'stability_score': float(
                ((features.get('cpu_stability_score') or 0) + 
                 (features.get('memory_stability_score') or 0)) / 2
            )
        }
    
    def _generate_recommendations(
        self, 
        classification: Dict[str, Any],
        anomalies: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        workload_type = classification.get('workload_type', 'UNKNOWN')
        confidence = classification.get('confidence') or 0
        
        # Workload-specific recommendations
        if workload_type == 'CPU_INTENSIVE':
            recommendations.append({
                'type': 'scaling',
                'priority': 'high',
                'action': 'Consider CPU-based HPA',
                'details': 'High CPU utilization detected. Implement HPA with CPU metric.',
                'confidence': confidence
            })
        elif workload_type == 'MEMORY_INTENSIVE':
            recommendations.append({
                'type': 'scaling',
                'priority': 'high',
                'action': 'Consider memory-based HPA',
                'details': 'High memory utilization detected. Implement HPA with memory metric.',
                'confidence': confidence
            })
        elif workload_type == 'BURSTY':
            recommendations.append({
                'type': 'scaling',
                'priority': 'medium',
                'action': 'Implement adaptive scaling',
                'details': 'Bursty workload pattern detected. Consider HPA with multiple metrics.',
                'confidence': confidence
            })
        elif workload_type == 'LOW_UTILIZATION':
            recommendations.append({
                'type': 'optimization',
                'priority': 'medium',
                'action': 'Reduce resource allocation',
                'details': 'Resources are underutilized. Consider reducing requests/limits.',
                'confidence': confidence
            })
        
        # Anomaly-based recommendations
        if anomalies.get('has_anomalies'):
            for anomaly in anomalies.get('anomaly_details', []):
                recommendations.append({
                    'type': 'investigation',
                    'priority': 'high',
                    'action': f"Investigate {anomaly['type']} anomaly",
                    'details': anomaly.get('description', 'Unusual pattern detected'),
                    'confidence': anomaly.get('severity', 0.5)
                })
        
        return recommendations

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get learning insights from actual ML classifier state - strict .clauderc compliance"""
        if not hasattr(self, 'classifier'):
            raise ValueError("Classifier not initialized")
        
        # Get real learning status from classifier
        if not hasattr(self.classifier, 'enable_self_learning'):
            raise ValueError("Classifier missing enable_self_learning attribute")
        
        learning_enabled = self.classifier.enable_self_learning
        
        # Validate model state - check actual classifier attributes
        if not hasattr(self.classifier, 'cpu_classifier'):
            raise ValueError("Classifier missing cpu_classifier attribute")
        if not hasattr(self.classifier, 'memory_classifier'):
            raise ValueError("Classifier missing memory_classifier attribute")
        if not hasattr(self.classifier, 'pattern_classifier'):
            raise ValueError("Classifier missing pattern_classifier attribute")
        
        models_loaded = (self.classifier.cpu_classifier is not None and 
                        self.classifier.memory_classifier is not None and 
                        self.classifier.pattern_classifier is not None)
        
        # Get real training samples count
        training_samples = 0
        if hasattr(self.classifier, 'learning_db_path') and self.classifier.learning_db_path:
            try:
                import sqlite3
                conn = sqlite3.connect(self.classifier.learning_db_path)
                cursor = conn.cursor()
                # Check if table exists first
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workload_features'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM workload_features")
                    training_samples = cursor.fetchone()[0]
                conn.close()
            except Exception as db_error:
                logger.warning(f"Could not read training samples from {self.classifier.learning_db_path}: {db_error}")
                training_samples = 0
        else:
            logger.info("No learning database path available")
        
        # Calculate real confidence based on training data
        if training_samples < 10:
            confidence_level = 0.3
        elif training_samples < 50:
            confidence_level = 0.6
        elif training_samples < 100:
            confidence_level = 0.8
        else:
            confidence_level = 0.9
        
        # Get real accuracy if model is trained
        if models_loaded and hasattr(self.classifier, 'last_accuracy'):
            model_accuracy = self.classifier.last_accuracy
        else:
            model_accuracy = 0.0
        
        return {
            'learning_enabled': learning_enabled,
            'model_loaded': models_loaded,
            'training_samples': training_samples,
            'confidence_level': confidence_level,
            'model_accuracy': model_accuracy,
            'last_updated': datetime.now().isoformat(),
            'features_available': training_samples > 0,
            'anomaly_detection_enabled': hasattr(self, 'anomaly_detector') and self.anomaly_detector is not None
        }

    def analyze_and_recommend_with_comprehensive_insights(self, metrics_data: Dict, current_hpa_config: Dict = None, cluster_id: str = None) -> Dict[str, Any]:
        """
        Comprehensive analysis method required by ML HPA recommendation engine.
        Strict .clauderc compliance - no fallback values, explicit validation.
        """
        # Strict validation - no fallbacks
        if not metrics_data:
            raise ValueError("metrics_data is required and cannot be None")
        
        if not isinstance(metrics_data, dict):
            raise ValueError("metrics_data must be a dictionary")
            
        if 'nodes' not in metrics_data:
            raise ValueError("metrics_data missing required 'nodes' key")
            
        nodes = metrics_data['nodes']
        if not nodes:
            raise ValueError("No nodes data provided in metrics_data")
        
        logger.info(f"Starting comprehensive ML analysis for {len(nodes)} nodes")
        
        # Try to use existing analyze method, but provide fallback for feature extraction issues
        try:
            analysis_result = self.analyze(metrics_data)
            
            # Extract required components - strict validation
            if 'workload_classification' not in analysis_result:
                raise ValueError("Base analysis failed to produce workload_classification")
            
            workload_classification = analysis_result['workload_classification']
            if 'workload_type' not in workload_classification:
                raise ValueError("workload_classification missing required workload_type")
            if 'confidence' not in workload_classification:
                raise ValueError("workload_classification missing required confidence")
                
        except ValueError as analysis_error:
            logger.error(f"ML analysis failed: {analysis_error}")
            raise ValueError(f"ML analysis failed: {analysis_error}") from analysis_error
        
        # Calculate workload characteristics from actual node data
        workload_characteristics = self._extract_workload_characteristics_from_nodes(nodes)
        
        # Generate required components
        optimization_analysis = self._create_optimization_analysis(workload_classification, workload_characteristics)
        hpa_recommendation = self._create_hpa_recommendation(workload_classification, workload_characteristics)
        
        result = {
            'workload_classification': workload_classification,
            'optimization_analysis': optimization_analysis,
            'hpa_recommendation': hpa_recommendation,
            'workload_characteristics': workload_characteristics
        }
        
        logger.info(f"Comprehensive analysis completed successfully")
        return result
    
    def _extract_workload_characteristics_from_nodes(self, nodes: List[Dict]) -> Dict[str, Any]:
        """Extract workload characteristics from nodes - strict .clauderc compliance"""
        if not isinstance(nodes, list):
            raise ValueError("nodes must be a list")
        if len(nodes) == 0:
            raise ValueError("nodes list cannot be empty")
        
        cpu_values = []
        memory_values = []
        
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValueError(f"Node {i} must be a dictionary")
            if 'cpu_usage_pct' not in node:
                raise ValueError(f"Node {i} missing required cpu_usage_pct field")
            if 'memory_usage_pct' not in node:
                raise ValueError(f"Node {i} missing required memory_usage_pct field")
                
            cpu_usage = node['cpu_usage_pct']
            memory_usage = node['memory_usage_pct']
            
            if not isinstance(cpu_usage, (int, float)):
                raise ValueError(f"Node {i} cpu_usage_pct must be numeric, got {type(cpu_usage)}")
            if not isinstance(memory_usage, (int, float)):
                raise ValueError(f"Node {i} memory_usage_pct must be numeric, got {type(memory_usage)}")
                
            cpu_values.append(float(cpu_usage))
            memory_values.append(float(memory_usage))
        
        # Calculate characteristics using actual data
        import statistics
        
        return {
            'cpu_usage_pct': statistics.mean(cpu_values),
            'memory_usage_pct': statistics.mean(memory_values),
            'cpu_std': statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0.0,
            'memory_std': statistics.stdev(memory_values) if len(memory_values) > 1 else 0.0,
            'total_nodes': len(nodes),
            'cpu_min': min(cpu_values),
            'cpu_max': max(cpu_values),
            'memory_min': min(memory_values),
            'memory_max': max(memory_values)
        }
    
    def _create_optimization_analysis(self, workload_classification: Dict, workload_characteristics: Dict) -> Dict[str, Any]:
        """Create optimization analysis - strict .clauderc compliance"""
        workload_type = workload_classification['workload_type']
        confidence = workload_classification['confidence']
        cpu_usage = workload_characteristics['cpu_usage_pct']
        memory_usage = workload_characteristics['memory_usage_pct']
        
        # Determine primary action based on actual usage patterns
        if cpu_usage > 85 or memory_usage > 85:
            primary_action = 'SCALE_UP'
        elif cpu_usage < 15 and memory_usage < 15:
            primary_action = 'SCALE_DOWN'
        elif workload_type in ['CPU_INTENSIVE', 'MEMORY_INTENSIVE'] and confidence > 0.7:
            primary_action = 'OPTIMIZE'
        else:
            primary_action = 'MONITOR'
        
        return {
            'primary_action': primary_action,
            'confidence_score': confidence,
            'optimization_potential_pct': self._calculate_optimization_potential(cpu_usage, memory_usage),
            'resource_efficiency': self._calculate_resource_efficiency(cpu_usage, memory_usage)
        }
    
    def _create_hpa_recommendation(self, workload_classification: Dict, workload_characteristics: Dict) -> Dict[str, Any]:
        """Create HPA recommendation - strict .clauderc compliance"""
        workload_type = workload_classification['workload_type']
        cpu_usage = workload_characteristics['cpu_usage_pct']
        memory_usage = workload_characteristics['memory_usage_pct']
        
        # HPA recommendations based on actual workload patterns
        hpa_enabled = cpu_usage > 25 or memory_usage > 25  # Only for active workloads
        
        if hpa_enabled:
            cpu_target = min(80, max(50, cpu_usage + 15))
            memory_target = min(80, max(50, memory_usage + 15))
            min_replicas = 2 if workload_type == 'CRITICAL' else 1
            max_replicas = 8 if workload_type == 'VARIABLE' else 4
        else:
            cpu_target = 70
            memory_target = 70
            min_replicas = 1
            max_replicas = 2
        
        return {
            'enabled': hpa_enabled,
            'cpu_target_utilization': int(cpu_target),
            'memory_target_utilization': int(memory_target),
            'min_replicas': min_replicas,
            'max_replicas': max_replicas,
            'scale_up_cooldown_seconds': 300,
            'scale_down_cooldown_seconds': 600
        }
    
    def _calculate_optimization_potential(self, cpu_usage: float, memory_usage: float) -> float:
        """Calculate optimization potential percentage"""
        avg_utilization = (cpu_usage + memory_usage) / 2
        if avg_utilization > 80:
            return 15.0
        elif avg_utilization < 20:
            return 60.0
        else:
            return max(0, 50 - avg_utilization)
    
    def _calculate_resource_efficiency(self, cpu_usage: float, memory_usage: float) -> float:
        """Calculate current resource efficiency percentage"""
        return min(100.0, (cpu_usage + memory_usage) / 2 * 1.25)
    
    def _create_simple_workload_classification(self, workload_characteristics: Dict) -> Dict[str, Any]:
        """Create simplified workload classification when full ML analysis fails - strict .clauderc compliance"""
        cpu_usage = workload_characteristics['cpu_usage_pct']
        memory_usage = workload_characteristics['memory_usage_pct']
        cpu_std = workload_characteristics['cpu_std']
        memory_std = workload_characteristics['memory_std']
        
        # Classify workload type based on usage patterns
        if cpu_usage > memory_usage * 1.5:
            workload_type = 'CPU_INTENSIVE'
            confidence = 0.8 if cpu_usage > 60 else 0.6
        elif memory_usage > cpu_usage * 1.5:
            workload_type = 'MEMORY_INTENSIVE'
            confidence = 0.8 if memory_usage > 60 else 0.6
        elif cpu_std > 20 or memory_std > 20:
            workload_type = 'VARIABLE'
            confidence = 0.7
        elif cpu_usage > 70 or memory_usage > 70:
            workload_type = 'HIGH_UTILIZATION'
            confidence = 0.8
        elif cpu_usage < 20 and memory_usage < 20:
            workload_type = 'LOW_UTILIZATION'
            confidence = 0.9
        else:
            workload_type = 'BALANCED'
            confidence = 0.7
        
        return {
            'workload_type': workload_type,
            'confidence': confidence,
            'classification_method': 'simplified_rule_based'
        }


class SelfLearningWorkloadClassifier:
    """Self-learning classifier with simplified logic"""
    
    def __init__(self, model_path: str = None, enable_self_learning: bool = True):
        """Initialize the classifier"""
        # ML models
        self.cpu_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.memory_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.pattern_classifier = RandomForestClassifier(n_estimators=150, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.enable_self_learning = enable_self_learning
        
        # Self-learning components
        self.learning_lock = Lock()
        self.confidence_threshold = 0.7
        
        # Model paths
        self.model_path = self._setup_model_path(model_path)
        if self.enable_self_learning:
            self.learning_db_path = os.path.join(self.model_path, "learning_data.db")
            self._initialize_learning_database()
        
        # Expected features with consistent naming
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
        self.load_models()
    
    def _setup_model_path(self, model_path: str = None) -> str:
        """Setup model path"""
        if model_path is None:
            model_path = os.path.join(os.getcwd(), "machine_learning", "data")
        
        normalized_path = os.path.normpath(model_path)
        if not os.path.isabs(normalized_path):
            normalized_path = os.path.abspath(normalized_path)
        
        try:
            os.makedirs(normalized_path, exist_ok=True)
            logger.info(f"Model directory: {normalized_path}")
        except Exception as e:
            logger.warning(f"Model directory issue: {e}")
            normalized_path = os.getcwd()
        
        return normalized_path
    
    def _initialize_learning_database(self):
        """Initialize SQLite database for learning data"""
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
            logger.info("Learning database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize learning database: {e}")
    
    def extract_features(self, metrics_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract features with consistent variable naming
        
        Args:
            metrics_data: Dictionary containing nodes and other metrics
            
        Returns:
            DataFrame with extracted features
        """
        try:
            logger.info("Extracting ML features")
            
            # Get original nodes for feature extraction (needs status.allocatable)
            original_nodes = metrics_data.get('original_nodes')
            if original_nodes:
                logger.info("Using original Kubernetes nodes for feature extraction")
                nodes_for_extraction = original_nodes
            else:
                # No original nodes available - cannot do proper feature extraction
                raise ValueError("original_nodes required for ML feature extraction (needs status.allocatable)")
            
            # Use NodeDataProcessor if available
            if NodeDataProcessor:
                processed_nodes = NodeDataProcessor.parse_node_data(nodes_for_extraction)
                is_valid, errors = NodeDataProcessor.validate_node_data(processed_nodes)
                if not is_valid:
                    raise ValueError(f"Invalid node data: {errors[0]}")
                nodes_for_extraction = processed_nodes
            
            if not nodes_for_extraction:
                raise ValueError("No nodes data available")
            
            # Extract utilization values using consistent field names
            cpu_utils = []
            memory_utils = []
            
            for node in nodes_for_extraction:
                if not isinstance(node, dict):
                    continue
                
                # Use consistent field names: cpu_usage_pct, memory_usage_pct
                cpu_val = node.get('cpu_usage_pct')
                memory_val = node.get('memory_usage_pct')
                
                if cpu_val is None or not isinstance(cpu_val, (int, float)):
                    raise ValueError(f"Node missing valid cpu_usage_pct")
                if memory_val is None or not isinstance(memory_val, (int, float)):
                    raise ValueError(f"Node missing valid memory_usage_pct")
                
                cpu_utils.append(float(cpu_val))
                memory_utils.append(float(memory_val))
            
            if not cpu_utils:
                raise ValueError("No utilization data extracted")
            
            # Calculate features
            features = {}
            
            # Statistical features
            features.update(self._calculate_statistical_features(cpu_utils, memory_utils))
            
            # HPA features
            hpa_data = metrics_data.get('hpa_implementation', {})
            features.update(self._calculate_hpa_features(hpa_data))
            
            # Behavior features
            features.update(self._calculate_behavior_features(cpu_utils, memory_utils))
            
            # Efficiency features
            features.update(self._calculate_efficiency_features(nodes_for_extraction, cpu_utils, memory_utils))
            
            # Temporal features
            features.update(self._calculate_temporal_features())
            
            # Cluster health features
            features.update(self._calculate_cluster_health_features(nodes_for_extraction, cpu_utils, memory_utils))
            
            # Validate all required features exist
            missing_features = [feat for feat in self.expected_features if feat not in features]
            if missing_features:
                raise ValueError(f"Missing required features: {missing_features}")
            
            # Build DataFrame
            feature_values = [float(features[feat]) for feat in self.expected_features]
            df = pd.DataFrame([feature_values], columns=self.expected_features)
            
            # Clean data
            df = df.fillna(0.0)
            df = df.replace([np.inf, -np.inf], 0.0)
            
            logger.info(f"Extracted {len(df.columns)} features")
            
            return df
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            raise ValueError(f"Failed to extract features: {e}")
    
    def _calculate_statistical_features(
        self, cpu_utils: List[float], memory_utils: List[float]
    ) -> Dict[str, float]:
        """Calculate statistical features"""
        try:
            cpu_array = np.array(cpu_utils)
            memory_array = np.array(memory_utils)
            
            # Detect extreme values using standards
            extreme_threshold = SysPerf.CPU_UTILIZATION_CRITICAL * 2.1 if SystemPerformanceStandards else 200
            cpu_extreme = np.any(cpu_array > extreme_threshold)
            memory_extreme = np.any(memory_array > extreme_threshold)
            
            # Cap for statistics but preserve actual max
            if cpu_extreme:
                cpu_stats_array = np.clip(cpu_array, 0, extreme_threshold)
                cpu_max_actual = float(np.max(cpu_array))
            else:
                cpu_stats_array = cpu_array
                cpu_max_actual = float(np.max(cpu_array))
            
            if memory_extreme:
                memory_stats_array = np.clip(memory_array, 0, extreme_threshold)
                memory_max_actual = float(np.max(memory_array))
            else:
                memory_stats_array = memory_array
                memory_max_actual = float(np.max(memory_array))
            
            # Calculate features
            features = {
                'cpu_mean': float(np.mean(cpu_stats_array)),
                'memory_mean': float(np.mean(memory_stats_array)),
                'cpu_std': float(np.std(cpu_stats_array)),
                'memory_std': float(np.std(memory_stats_array)),
                'cpu_var': float(np.var(cpu_stats_array)),
                'memory_var': float(np.var(memory_stats_array)),
                'cpu_min': float(np.min(cpu_array)),
                'cpu_max': cpu_max_actual,
                'memory_min': float(np.min(memory_array)),
                'memory_max': memory_max_actual,
                'cpu_p75': float(np.percentile(cpu_stats_array, 75)),
                'cpu_p95': float(np.percentile(cpu_stats_array, 95)),
                'cpu_p99': float(np.percentile(cpu_stats_array, 99)),
                'memory_p75': float(np.percentile(memory_stats_array, 75)),
                'memory_p95': float(np.percentile(memory_stats_array, 95)),
                'memory_p99': float(np.percentile(memory_stats_array, 99)),
                'cpu_range': float(np.max(cpu_stats_array) - np.min(cpu_stats_array)),
                'memory_range': float(np.max(memory_stats_array) - np.min(memory_stats_array)),
                'cpu_cv': float(np.std(cpu_stats_array) / max(np.mean(cpu_stats_array), 1e-6)),
                'memory_cv': float(np.std(memory_stats_array) / max(np.mean(memory_stats_array), 1e-6)),
                'cpu_memory_ratio': float(np.mean(cpu_stats_array) / max(np.mean(memory_stats_array), 1e-6)),
                'cpu_memory_correlation': float(
                    np.corrcoef(cpu_stats_array, memory_stats_array)[0, 1]
                ) if len(cpu_stats_array) > 1 else 0.0,
                'resource_imbalance': float(abs(np.mean(cpu_stats_array) - np.mean(memory_stats_array))),
                'cpu_extreme_detected': float(cpu_extreme),
                'memory_extreme_detected': float(memory_extreme),
                'max_cpu_actual': cpu_max_actual,
                'max_memory_actual': memory_max_actual
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Statistical features failed: {e}")
            raise
    
    def _calculate_hpa_features(self, hpa_data: Dict) -> Dict[str, float]:
        """Calculate HPA-related features"""
        try:
            pattern = hpa_data.get('current_hpa_pattern', 'no_hpa_detected')
            confidence = hpa_data.get('confidence', 'low')
            total_hpas = hpa_data.get('total_hpas')
            if total_hpas is None:
                total_hpas = 0
            
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
                'hpa_density': float(total_hpas / max(1, 10))  # Normalized to 10 workloads
            }
            
        except Exception as e:
            logger.error(f"HPA features failed: {e}")
            raise
    
    def _calculate_behavior_features(
        self, cpu_utils: List[float], memory_utils: List[float]
    ) -> Dict[str, float]:
        """Calculate behavior-related features"""
        try:
            cpu_array = np.array(cpu_utils)
            memory_array = np.array(memory_utils)
            
            # Calculate burst frequency
            cpu_mean = np.mean(cpu_array)
            memory_mean = np.mean(memory_array)
            cpu_std = np.std(cpu_array)
            memory_std = np.std(memory_array)
            
            cpu_bursts = np.sum(np.abs(cpu_array - cpu_mean) > 2 * cpu_std) / len(cpu_array)
            memory_bursts = np.sum(np.abs(memory_array - memory_mean) > 2 * memory_std) / len(memory_array)
            
            # Stability scores
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
            logger.error(f"Behavior features failed: {e}")
            raise
    
    def _calculate_efficiency_features(
        self, nodes: List[Dict], cpu_utils: List[float], memory_utils: List[float]
    ) -> Dict[str, float]:
        """Calculate efficiency features"""
        try:
            cpu_gaps = []
            memory_gaps = []
            
            for i, node in enumerate(nodes):
                # Use consistent field names
                cpu_request = node.get('cpu_request_pct', cpu_utils[i] + 20)
                memory_request = node.get('memory_request_pct', memory_utils[i] + 15)
                
                cpu_gap = max(0, cpu_request - cpu_utils[i])
                memory_gap = max(0, memory_request - memory_utils[i])
                
                cpu_gaps.append(cpu_gap)
                memory_gaps.append(memory_gap)
            
            # Overall efficiency
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
            logger.error(f"Efficiency features failed: {e}")
            raise
    
    def _calculate_temporal_features(self) -> Dict[str, float]:
        """Calculate time-based features"""
        try:
            now = datetime.now()
            hour = now.hour
            day_of_week = now.weekday()
            
            # Time indicators
            is_business_hours = 1.0 if 9 <= hour <= 17 else 0.0
            is_weekend = 1.0 if day_of_week >= 5 else 0.0
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
            logger.error(f"Temporal features failed: {e}")
            raise
    
    def _calculate_cluster_health_features(
        self, nodes: List[Dict], cpu_utils: List[float], memory_utils: List[float]
    ) -> Dict[str, float]:
        """Calculate cluster health features"""
        try:
            # Node readiness
            ready_nodes = sum(1 for node in nodes if node.get('status', 'Ready') == 'Ready')
            node_readiness_ratio = ready_nodes / max(len(nodes), 1)
            
            # Resource distribution fairness
            cpu_gini = self._calculate_gini_coefficient(cpu_utils)
            memory_gini = self._calculate_gini_coefficient(memory_utils)
            
            cpu_fairness = 1.0 - cpu_gini
            memory_fairness = 1.0 - memory_gini
            
            # Cluster size
            cluster_size = len(nodes)
            cluster_size_normalized = min(cluster_size / 10.0, 1.0)
            
            return {
                'node_readiness_ratio': float(node_readiness_ratio),
                'cpu_distribution_fairness': float(max(0.0, min(1.0, cpu_fairness))),
                'memory_distribution_fairness': float(max(0.0, min(1.0, memory_fairness))),
                'cluster_size': float(cluster_size),
                'cluster_size_normalized': float(cluster_size_normalized)
            }
            
        except Exception as e:
            logger.error(f"Cluster health features failed: {e}")
            raise
    
    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """Calculate Gini coefficient"""
        try:
            if not values or len(values) < 2:
                return 0.0
            
            sorted_values = sorted(values)
            n = len(sorted_values)
            cumsum = np.cumsum(sorted_values)
            
            gini = (n + 1 - 2 * sum((n + 1 - i) * v for i, v in enumerate(sorted_values, 1))) / (n * sum(sorted_values))
            return max(0.0, min(1.0, gini))
            
        except Exception:
            return 0.2
    
    def classify_workload_type(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Classify workload type"""
        try:
            if features_df is None or features_df.empty:
                raise ValueError("Cannot classify without features")
            
            if not self.is_trained:
                return self._rule_based_classification(features_df)
            
            # ML-based classification
            try:
                features_scaled = self.scaler.transform(features_df)
                pattern_pred = self.pattern_classifier.predict(features_scaled)[0]
                pattern_proba = self.pattern_classifier.predict_proba(features_scaled)[0]
                confidence = float(max(pattern_proba))
                
                result = {
                    'workload_type': pattern_pred,
                    'confidence': confidence,
                    'method': 'trained_ml_model',
                    'ml_enhanced': True,
                    'feature_count': len(features_df.columns),
                    'feature_insights': self._extract_feature_insights(features_df),
                    'confidence_level': self._categorize_confidence(confidence)
                }
                
                return result
                
            except Exception as e:
                logger.error(f"ML prediction failed: {e}")
                return self._rule_based_classification(features_df)
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise
    
    def _rule_based_classification(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Rule-based classification"""
        try:
            features = features_df.iloc[0] if not features_df.empty else {}
            
            # Validate required features
            if 'cpu_mean' not in features or 'memory_mean' not in features:
                raise ValueError("Missing required features for classification")
            
            cpu_mean = features['cpu_mean']
            memory_mean = features['memory_mean']
            cpu_max = features.get('cpu_max', cpu_mean)
            memory_max = features.get('memory_max', memory_mean)
            cpu_cv = features.get('cpu_cv') or 0
            memory_cv = features.get('memory_cv') or 0
            burst_freq = features.get('cpu_burst_frequency') or 0
            efficiency = features.get('overall_efficiency_score', 0.5)
            
            # Classification logic with thresholds from standards
            if not SystemPerformanceStandards:
                raise ValueError("Performance standards are required for classification")
            
            cpu_high = SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE
            memory_high = SystemPerformanceStandards.MEMORY_UTILIZATION_HIGH
            cpu_optimal = SystemPerformanceStandards.CPU_UTILIZATION_OPTIMAL
            cpu_stress = SystemPerformanceStandards.CPU_UTILIZATION_STRESS
            cpu_critical = SystemPerformanceStandards.CPU_UTILIZATION_CRITICAL
            memory_stress = SystemPerformanceStandards.MEMORY_UTILIZATION_STRESS
            
            # Extreme cases using standards
            extreme_mean_threshold = cpu_critical * 2.1
            extreme_max_threshold = cpu_critical * 5.3
            
            if cpu_mean > extreme_mean_threshold or cpu_max > extreme_max_threshold:
                workload_type = 'CPU_INTENSIVE'
                confidence = 0.95
            elif memory_mean > extreme_mean_threshold or memory_max > extreme_max_threshold:
                workload_type = 'MEMORY_INTENSIVE'
                confidence = 0.95
            
            # High utilization using standards
            elif cpu_mean > cpu_stress:
                if memory_mean > cpu_high:
                    workload_type = 'BURSTY' if cpu_mean > memory_mean else 'MEMORY_INTENSIVE'
                    confidence = 0.9
                else:
                    workload_type = 'CPU_INTENSIVE'
                    confidence = 0.85
            elif memory_mean > memory_stress:
                workload_type = 'MEMORY_INTENSIVE'
                confidence = 0.85
            
            # Medium-high utilization using standards
            elif cpu_mean > cpu_optimal and memory_mean < (cpu_optimal * 0.71):
                workload_type = 'CPU_INTENSIVE'
                confidence = 0.8
            elif memory_mean > cpu_high and cpu_mean < (cpu_optimal * 0.57):
                workload_type = 'MEMORY_INTENSIVE'
                confidence = 0.8
            
            # Bursty patterns
            elif burst_freq > 0.3 or cpu_cv > 0.5 or memory_cv > 0.5:
                workload_type = 'BURSTY'
                confidence = 0.75
            
            # Low utilization using standards
            elif cpu_mean < (cpu_optimal * 0.36) and memory_mean < (cpu_optimal * 0.5):
                workload_type = 'LOW_UTILIZATION'
                confidence = 0.85
            
            # Default balanced
            else:
                workload_type = 'BALANCED'
                confidence = 0.6
            
            logger.info(f"Classification: {workload_type} "
                       f"(CPU:{cpu_mean:.1f}%, MEM:{memory_mean:.1f}%, conf:{confidence:.2f})")
            
            return {
                'workload_type': workload_type,
                'confidence': confidence,
                'method': 'rule_based',
                'ml_enhanced': False,
                'feature_count': len(features_df.columns),
                'feature_insights': self._extract_feature_insights(features_df),
                'confidence_level': self._categorize_confidence(confidence)
            }
            
        except Exception as e:
            logger.error(f"Rule-based classification failed: {e}")
            raise
    
    def _extract_feature_insights(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract feature insights"""
        try:
            if features_df.empty:
                return {}
            
            features = features_df.iloc[0]
            
            return {
                'resource_utilization': {
                    'cpu_mean': float(features.get('cpu_mean') or 0),
                    'memory_mean': float(features.get('memory_mean') or 0),
                    'cpu_peak': float(features.get('cpu_max') or 0),
                    'memory_peak': float(features.get('memory_max') or 0)
                },
                'performance_patterns': {
                    'cpu_stability': float(features.get('cpu_stability_score') or 0),
                    'memory_stability': float(features.get('memory_stability_score') or 0),
                    'burst_frequency': float(features.get('cpu_burst_frequency') or 0)
                },
                'efficiency_metrics': {
                    'overall_efficiency': float(features.get('overall_efficiency_score', 0)),
                    'cpu_gap': float(features.get('avg_cpu_gap', 0)),
                    'memory_gap': float(features.get('avg_memory_gap', 0))
                }
            }
            
        except Exception as e:
            logger.error(f"Feature insights extraction failed: {e}")
            return {}
    
    def _categorize_confidence(self, confidence: float) -> str:
        """Categorize confidence level"""
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
    
    def load_models(self) -> bool:
        """Load trained models"""
        try:
            cpu_model_path = os.path.join(self.model_path, 'cpu_classifier.pkl')
            memory_model_path = os.path.join(self.model_path, 'memory_classifier.pkl')
            pattern_model_path = os.path.join(self.model_path, 'pattern_classifier.pkl')
            scaler_path = os.path.join(self.model_path, 'scaler.pkl')
            
            if all(os.path.exists(p) for p in [cpu_model_path, memory_model_path, pattern_model_path, scaler_path]):
                self.cpu_classifier = joblib.load(cpu_model_path)
                self.memory_classifier = joblib.load(memory_model_path)
                self.pattern_classifier = joblib.load(pattern_model_path)
                self.scaler = joblib.load(scaler_path)
                self.is_trained = True
                logger.info("Models loaded successfully")
                return True
            
        except Exception as e:
            logger.warning(f"Failed to load models: {e}")
        
        self.is_trained = False
        return False
    
    def save_models(self) -> bool:
        """Save trained models"""
        try:
            joblib.dump(self.cpu_classifier, os.path.join(self.model_path, 'cpu_classifier.pkl'))
            joblib.dump(self.memory_classifier, os.path.join(self.model_path, 'memory_classifier.pkl'))
            joblib.dump(self.pattern_classifier, os.path.join(self.model_path, 'pattern_classifier.pkl'))
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            logger.info("Models saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
            return False


class AnomalyDetector:
    """Anomaly detection using Isolation Forest"""
    
    def __init__(self):
        """Initialize the anomaly detector"""
        self.detector = IsolationForest(contamination=0.1, random_state=42)
        self.is_fitted = False
    
    def detect_anomalies(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in features"""
        try:
            if features_df.empty:
                return {'has_anomalies': False, 'anomaly_details': []}
            
            # Simple threshold-based detection
            features = features_df.iloc[0]
            anomalies = []
            
            # Check for extreme CPU using standards
            extreme_threshold = SystemPerformanceStandards.CPU_UTILIZATION_CRITICAL * 1.58 if SystemPerformanceStandards else 150
            
            if features.get('cpu_max', 0) > extreme_threshold:
                anomalies.append({
                    'type': 'cpu_extreme',
                    'severity': min(features['cpu_max'] / (extreme_threshold * 1.33), 1.0),
                    'value': features['cpu_max'],
                    'description': f"Extreme CPU usage: {features['cpu_max']:.1f}%"
                })
            
            # Check for extreme memory using standards
            if features.get('memory_max', 0) > extreme_threshold:
                anomalies.append({
                    'type': 'memory_extreme',
                    'severity': min(features['memory_max'] / (extreme_threshold * 1.33), 1.0),
                    'value': features['memory_max'],
                    'description': f"Extreme memory usage: {features['memory_max']:.1f}%"
                })
            
            # Check for high variability
            if features.get('cpu_cv', 0) > 1.0:
                anomalies.append({
                    'type': 'cpu_instability',
                    'severity': min(features['cpu_cv'], 1.0),
                    'value': features['cpu_cv'],
                    'description': f"High CPU variability: CV={features['cpu_cv']:.2f}"
                })
            
            return {
                'has_anomalies': len(anomalies) > 0,
                'anomaly_count': len(anomalies),
                'anomaly_details': anomalies
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {'has_anomalies': False, 'anomaly_details': []}


class InsightGenerator:
    """Generate actionable insights from analysis"""
    
    def generate_insights(
        self,
        metrics_data: Dict[str, Any],
        classification: Dict[str, Any],
        anomalies: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive insights"""
        insights = []
        
        try:
            # Workload type insights
            workload_type = classification.get('workload_type', 'UNKNOWN')
            confidence = classification.get('confidence') or 0
            
            if workload_type == 'CPU_INTENSIVE':
                insights.append({
                    'category': 'resource_optimization',
                    'severity': 'high',
                    'insight': 'Workload is CPU-intensive',
                    'recommendation': f'Consider implementing CPU-based HPA with target {SystemPerformanceStandards.CPU_UTILIZATION_OPTIMAL if SystemPerformanceStandards else 70}-{SystemPerformanceStandards.CPU_UTILIZATION_HIGH_PERFORMANCE if SystemPerformanceStandards else 80}%',
                    'confidence': confidence
                })
            elif workload_type == 'MEMORY_INTENSIVE':
                insights.append({
                    'category': 'resource_optimization',
                    'severity': 'high',
                    'insight': 'Workload is memory-intensive',
                    'recommendation': 'Consider implementing memory-based HPA with target 75-85%',
                    'confidence': confidence
                })
            elif workload_type == 'BURSTY':
                insights.append({
                    'category': 'scaling_strategy',
                    'severity': 'medium',
                    'insight': 'Workload shows bursty behavior',
                    'recommendation': 'Implement multi-metric HPA with behavior configuration',
                    'confidence': confidence
                })
            elif workload_type == 'LOW_UTILIZATION':
                insights.append({
                    'category': 'cost_optimization',
                    'severity': 'medium',
                    'insight': 'Resources are significantly underutilized',
                    'recommendation': 'Reduce resource requests and limits to save costs',
                    'confidence': confidence
                })
            
            # Anomaly insights
            if anomalies.get('has_anomalies'):
                for anomaly in anomalies.get('anomaly_details', []):
                    insights.append({
                        'category': 'anomaly',
                        'severity': 'high' if anomaly['severity'] > 0.7 else 'medium',
                        'insight': anomaly['description'],
                        'recommendation': f"Investigate and address {anomaly['type']}",
                        'confidence': anomaly['severity']
                    })
            
            # Efficiency insights
            feature_insights = classification.get('feature_insights', {})
            efficiency = feature_insights.get('efficiency_metrics', {}).get('overall_efficiency', 0)
            
            if efficiency < 0.5:
                insights.append({
                    'category': 'efficiency',
                    'severity': 'high',
                    'insight': f"Poor resource efficiency: {efficiency:.1%}",
                    'recommendation': 'Review and optimize resource allocations',
                    'confidence': 0.8
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return []


# Export main class
__all__ = ['WorkloadPerformanceAnalyzer']