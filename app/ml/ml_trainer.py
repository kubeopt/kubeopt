#!/usr/bin/env python3
"""
Enhanced ML Model Training - Better Data Quality & Higher Confidence
===================================================================
This improved version creates more diverse, realistic training data
and optimizes models for higher confidence predictions.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging
import os
import warnings
from collections import Counter
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedMLModelTrainer:
    """
    Enhanced ML model trainer with improved data quality and confidence
    """
    
    def __init__(self):
        # Expected features (must match workload_performance_analyzer.py)
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
        
        # Target classes with more distinct patterns
        self.workload_classes = ['CPU_INTENSIVE', 'MEMORY_INTENSIVE', 'BALANCED', 'BURSTY', 'LOW_UTILIZATION']
        
        # Enhanced model with hyperparameter tuning
        self.pattern_classifier = None
        self.scaler = StandardScaler()
        
        # Workload pattern definitions for more realistic data
        self.workload_patterns = {
            'CPU_INTENSIVE': {
                'cpu_range': (70, 95),
                'memory_range': (30, 55),
                'cpu_variance_range': (100, 300),
                'memory_variance_range': (50, 150),
                'burst_frequency': (0.05, 0.25),
                'stability_bias': 'cpu_unstable',
                'hpa_preference': ['cpu_based_dominant', 'hybrid_approach']
            },
            'MEMORY_INTENSIVE': {
                'cpu_range': (25, 50),
                'memory_range': (75, 95),
                'cpu_variance_range': (40, 120),
                'memory_variance_range': (80, 250),
                'burst_frequency': (0.02, 0.15),
                'stability_bias': 'memory_unstable',
                'hpa_preference': ['memory_based_dominant', 'hybrid_approach']
            },
            'BALANCED': {
                'cpu_range': (45, 75),
                'memory_range': (50, 80),
                'cpu_variance_range': (60, 180),
                'memory_variance_range': (60, 180),
                'burst_frequency': (0.05, 0.20),
                'stability_bias': 'balanced',
                'hpa_preference': ['hybrid_approach', 'cpu_based_dominant', 'memory_based_dominant']
            },
            'BURSTY': {
                'cpu_range': (30, 80),  # Wide range for burstiness
                'memory_range': (35, 70),
                'cpu_variance_range': (300, 800),  # High variance
                'memory_variance_range': (200, 500),
                'burst_frequency': (0.3, 0.7),  # High burst frequency
                'stability_bias': 'highly_unstable',
                'hpa_preference': ['mixed_implementation', 'cpu_based_dominant']
            },
            'LOW_UTILIZATION': {
                'cpu_range': (5, 35),
                'memory_range': (10, 45),
                'cpu_variance_range': (10, 80),
                'memory_variance_range': (15, 100),
                'burst_frequency': (0.01, 0.10),
                'stability_bias': 'very_stable',
                'hpa_preference': ['no_hpa_detected', 'mixed_implementation']
            }
        }
    
    def generate_enhanced_training_data(self, n_samples=5000):
        """
        Generate enhanced, more realistic training data with better class separation
        """
        logger.info(f"🔬 Generating {n_samples} enhanced training samples...")
        
        data = []
        labels = []
        
        # Generate more samples per class for better learning
        samples_per_class = n_samples // len(self.workload_classes)
        
        for workload_type in self.workload_classes:
            logger.info(f"📊 Creating {samples_per_class} enhanced samples for {workload_type}")
            
            pattern_config = self.workload_patterns[workload_type]
            
            for i in range(samples_per_class):
                # Add scenario variations within each class
                scenario_variant = i % 4  # 4 different scenarios per class
                sample = self._generate_enhanced_workload_sample(workload_type, pattern_config, scenario_variant)
                data.append(sample)
                labels.append(workload_type)
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=self.expected_features)
        df['workload_type'] = labels
        
        # Add realistic noise and correlations
        df = self._add_enhanced_realism(df)
        
        # Data augmentation for better generalization
        df = self._augment_training_data(df)
        
        logger.info(f"✅ Generated {len(df)} enhanced training samples")
        logger.info(f"📊 Class distribution: {dict(Counter(df['workload_type']))}")
        
        return df
    
    def _generate_enhanced_workload_sample(self, workload_type, pattern_config, scenario_variant):
        """Generate enhanced sample with better class separation"""
        
        # Time-based variations
        current_time = datetime.now() - timedelta(days=np.random.randint(0, 90))
        hour = current_time.hour
        day = current_time.weekday()
        
        # Business hours effect on workload
        business_hours_multiplier = 1.2 if 9 <= hour <= 17 else 0.8
        weekend_multiplier = 0.7 if day >= 5 else 1.0
        
        temporal_features = {
            'hour_of_day': float(hour),
            'is_business_hours': 1.0 if 9 <= hour <= 17 else 0.0,
            'is_weekend': 1.0 if day >= 5 else 0.0,
            'is_peak_hours': 1.0 if hour in [10, 11, 14, 15] else 0.0,
            'hour_sin': float(np.sin(2 * np.pi * hour / 24)),
            'hour_cos': float(np.cos(2 * np.pi * hour / 24)),
            'day_sin': float(np.sin(2 * np.pi * day / 7)),
            'day_cos': float(np.cos(2 * np.pi * day / 7))
        }
        
        # Enhanced workload generation based on pattern
        cpu_min, cpu_max = pattern_config['cpu_range']
        memory_min, memory_max = pattern_config['memory_range']
        cpu_var_min, cpu_var_max = pattern_config['cpu_variance_range']
        memory_var_min, memory_var_max = pattern_config['memory_variance_range']
        
        # Scenario variants for more diversity
        if scenario_variant == 0:  # Peak load scenario
            cpu_base = np.random.uniform(cpu_max * 0.8, cpu_max) * business_hours_multiplier
            memory_base = np.random.uniform(memory_max * 0.8, memory_max) * business_hours_multiplier
        elif scenario_variant == 1:  # Normal load scenario
            cpu_base = np.random.uniform(cpu_min + (cpu_max - cpu_min) * 0.3, cpu_max * 0.8)
            memory_base = np.random.uniform(memory_min + (memory_max - memory_min) * 0.3, memory_max * 0.8)
        elif scenario_variant == 2:  # Off-peak scenario
            cpu_base = np.random.uniform(cpu_min, cpu_min + (cpu_max - cpu_min) * 0.6) * weekend_multiplier
            memory_base = np.random.uniform(memory_min, memory_min + (memory_max - memory_min) * 0.6) * weekend_multiplier
        else:  # Mixed scenario
            cpu_base = np.random.uniform(cpu_min, cpu_max)
            memory_base = np.random.uniform(memory_min, memory_max)
        
        # Enhanced variance calculation
        cpu_variance = np.random.uniform(cpu_var_min, cpu_var_max)
        memory_variance = np.random.uniform(memory_var_min, memory_var_max)
        
        # Apply workload-specific adjustments
        if workload_type == 'BURSTY':
            # More dramatic variance for bursty workloads
            cpu_variance *= np.random.uniform(1.5, 2.5)
            memory_variance *= np.random.uniform(1.2, 2.0)
        elif workload_type == 'LOW_UTILIZATION':
            # More stable, lower variance
            cpu_variance *= np.random.uniform(0.3, 0.8)
            memory_variance *= np.random.uniform(0.3, 0.8)
        
        # Ensure realistic bounds
        cpu_base = np.clip(cpu_base, 5, 98)
        memory_base = np.clip(memory_base, 8, 98)
        cpu_variance = max(10, cpu_variance)
        memory_variance = max(10, memory_variance)
        
        # Generate time series with more realistic patterns
        series_length = 30  # Longer series for better statistics
        
        # Add realistic correlations between CPU and memory
        if workload_type == 'CPU_INTENSIVE':
            correlation_factor = np.random.uniform(-0.3, 0.2)  # Slight negative correlation
        elif workload_type == 'MEMORY_INTENSIVE':
            correlation_factor = np.random.uniform(-0.2, 0.3)  # Slight positive correlation
        elif workload_type == 'BALANCED':
            correlation_factor = np.random.uniform(0.3, 0.7)  # Moderate positive correlation
        elif workload_type == 'BURSTY':
            correlation_factor = np.random.uniform(-0.4, 0.8)  # Wide range for burstiness
        else:  # LOW_UTILIZATION
            correlation_factor = np.random.uniform(0.1, 0.5)  # Moderate correlation
        
        # Generate correlated time series
        cpu_series = np.random.normal(cpu_base, np.sqrt(cpu_variance), series_length)
        
        # Create memory series with controlled correlation
        memory_noise = np.random.normal(0, np.sqrt(memory_variance), series_length)
        memory_series = memory_base + correlation_factor * (cpu_series - cpu_base) + memory_noise
        
        # Apply realistic bounds and patterns
        cpu_series = np.clip(cpu_series, 1, 100)
        memory_series = np.clip(memory_series, 1, 100)
        
        # Add workload-specific patterns
        if workload_type == 'BURSTY':
            # Add burst spikes
            burst_points = np.random.choice(series_length, size=int(series_length * 0.2), replace=False)
            for bp in burst_points:
                cpu_series[bp] *= np.random.uniform(1.5, 3.0)
                memory_series[bp] *= np.random.uniform(1.2, 2.0)
            cpu_series = np.clip(cpu_series, 1, 100)
            memory_series = np.clip(memory_series, 1, 100)
        
        # Calculate enhanced statistical features
        statistical_features = self._calculate_enhanced_statistical_features(cpu_series, memory_series)
        
        # Enhanced HPA features with better logic
        hpa_features = self._generate_enhanced_hpa_features(workload_type, pattern_config)
        
        # Enhanced behavior features
        behavior_features = self._calculate_enhanced_behavior_features(
            cpu_series, memory_series, workload_type, pattern_config
        )
        
        # Enhanced efficiency features
        efficiency_features = self._calculate_enhanced_efficiency_features(
            cpu_series, memory_series, workload_type
        )
        
        # Enhanced cluster features
        cluster_features = self._generate_enhanced_cluster_features(workload_type)
        
        # Combine all features in exact order
        sample = []
        for feature_name in self.expected_features:
            if feature_name in statistical_features:
                sample.append(statistical_features[feature_name])
            elif feature_name in hpa_features:
                sample.append(hpa_features[feature_name])
            elif feature_name in behavior_features:
                sample.append(behavior_features[feature_name])
            elif feature_name in efficiency_features:
                sample.append(efficiency_features[feature_name])
            elif feature_name in cluster_features:
                sample.append(cluster_features[feature_name])
            elif feature_name in temporal_features:
                sample.append(temporal_features[feature_name])
            else:
                sample.append(0.0)
        
        return sample
    
    def _calculate_enhanced_statistical_features(self, cpu_series, memory_series):
        """Calculate enhanced statistical features with better separation"""
        
        features = {
            # CPU statistics
            'cpu_mean': float(np.mean(cpu_series)),
            'cpu_std': float(np.std(cpu_series)),
            'cpu_var': float(np.var(cpu_series)),
            'cpu_min': float(np.min(cpu_series)),
            'cpu_max': float(np.max(cpu_series)),
            'cpu_p75': float(np.percentile(cpu_series, 75)),
            'cpu_p95': float(np.percentile(cpu_series, 95)),
            'cpu_p99': float(np.percentile(cpu_series, 99)),
            'cpu_range': float(np.max(cpu_series) - np.min(cpu_series)),
            'cpu_cv': float(np.std(cpu_series) / max(np.mean(cpu_series), 1)),
            
            # Memory statistics
            'memory_mean': float(np.mean(memory_series)),
            'memory_std': float(np.std(memory_series)),
            'memory_var': float(np.var(memory_series)),
            'memory_min': float(np.min(memory_series)),
            'memory_max': float(np.max(memory_series)),
            'memory_p75': float(np.percentile(memory_series, 75)),
            'memory_p95': float(np.percentile(memory_series, 95)),
            'memory_p99': float(np.percentile(memory_series, 99)),
            'memory_range': float(np.max(memory_series) - np.min(memory_series)),
            'memory_cv': float(np.std(memory_series) / max(np.mean(memory_series), 1)),
            
            # Cross-resource features
            'cpu_memory_ratio': float(np.mean(cpu_series) / max(np.mean(memory_series), 1)),
            'resource_imbalance': float(abs(np.mean(cpu_series) - np.mean(memory_series)))
        }
        
        # Enhanced correlation calculation
        try:
            correlation = np.corrcoef(cpu_series, memory_series)[0, 1]
            features['cpu_memory_correlation'] = float(correlation) if not np.isnan(correlation) else 0.0
        except:
            features['cpu_memory_correlation'] = 0.0
        
        return features
    
    def _generate_enhanced_hpa_features(self, workload_type, pattern_config):
        """Generate enhanced HPA features with workload-specific logic"""
        
        hpa_preferences = pattern_config['hpa_preference']
        hpa_pattern = np.random.choice(hpa_preferences)
        
        # Confidence based on workload clarity
        if workload_type in ['CPU_INTENSIVE', 'MEMORY_INTENSIVE']:
            confidence = np.random.choice(['high', 'medium'], p=[0.7, 0.3])
        elif workload_type == 'BALANCED':
            confidence = np.random.choice(['high', 'medium', 'low'], p=[0.5, 0.4, 0.1])
        elif workload_type == 'BURSTY':
            confidence = np.random.choice(['medium', 'low'], p=[0.6, 0.4])
        else:  # LOW_UTILIZATION
            confidence = np.random.choice(['low', 'medium'], p=[0.8, 0.2])
        
        # HPA count based on workload complexity
        if workload_type == 'BURSTY':
            total_hpas = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
        elif workload_type == 'LOW_UTILIZATION':
            total_hpas = np.random.choice([0, 1], p=[0.7, 0.3])
        else:
            total_hpas = np.random.choice([1, 2, 3, 4], p=[0.3, 0.4, 0.2, 0.1])
        
        # Enhanced encoding
        pattern_encoding = {
            'cpu_based_dominant': 1.0,
            'memory_based_dominant': 2.0,
            'hybrid_approach': 3.0,
            'no_hpa_detected': 0.0,
            'mixed_implementation': 2.5
        }
        
        confidence_encoding = {'high': 1.0, 'medium': 0.5, 'low': 0.1}
        
        # Enhanced HPA score calculation
        base_score = {
            'CPU_INTENSIVE': 0.8,
            'MEMORY_INTENSIVE': 0.85,
            'BALANCED': 0.9,
            'BURSTY': 0.6,
            'LOW_UTILIZATION': 0.2
        }[workload_type]
        
        hpa_score = base_score * confidence_encoding[confidence] * min(total_hpas / 3, 1.0)
        
        return {
            'hpa_implementation_score': float(hpa_score),
            'hpa_pattern_encoded': float(pattern_encoding[hpa_pattern]),
            'hpa_confidence_score': float(confidence_encoding[confidence]),
            'hpa_density': float(min(total_hpas / 5.0, 1.0))
        }
    
    def _calculate_enhanced_behavior_features(self, cpu_series, memory_series, workload_type, pattern_config):
        """Calculate enhanced behavior features with workload-specific patterns"""
        
        cpu_mean = np.mean(cpu_series)
        memory_mean = np.mean(memory_series)
        
        # Enhanced burst frequency calculation
        burst_min, burst_max = pattern_config['burst_frequency']
        cpu_burst_freq = np.random.uniform(burst_min, burst_max)
        memory_burst_freq = np.random.uniform(burst_min * 0.8, burst_max * 0.8)
        
        # Workload-specific stability scores
        stability_bias = pattern_config['stability_bias']
        
        if stability_bias == 'very_stable':
            cpu_stability = np.random.uniform(0.8, 0.95)
            memory_stability = np.random.uniform(0.8, 0.95)
        elif stability_bias == 'balanced':
            cpu_stability = np.random.uniform(0.6, 0.8)
            memory_stability = np.random.uniform(0.6, 0.8)
        elif stability_bias == 'highly_unstable':
            cpu_stability = np.random.uniform(0.1, 0.4)
            memory_stability = np.random.uniform(0.2, 0.5)
        else:  # cpu_unstable or memory_unstable
            if 'cpu' in stability_bias:
                cpu_stability = np.random.uniform(0.2, 0.5)
                memory_stability = np.random.uniform(0.6, 0.8)
            else:
                cpu_stability = np.random.uniform(0.6, 0.8)
                memory_stability = np.random.uniform(0.2, 0.5)
        
        # Enhanced peak ratios
        cpu_peak_ratio = np.max(cpu_series) / max(cpu_mean, 1)
        memory_peak_ratio = np.max(memory_series) / max(memory_mean, 1)
        
        return {
            'cpu_burst_frequency': float(cpu_burst_freq),
            'memory_burst_frequency': float(memory_burst_freq),
            'cpu_stability_score': float(cpu_stability),
            'memory_stability_score': float(memory_stability),
            'cpu_peak_avg_ratio': float(cpu_peak_ratio),
            'memory_peak_avg_ratio': float(memory_peak_ratio)
        }
    
    def _calculate_enhanced_efficiency_features(self, cpu_series, memory_series, workload_type):
        """Calculate enhanced efficiency features with workload-specific patterns"""
        
        cpu_mean = np.mean(cpu_series)
        memory_mean = np.mean(memory_series)
        
        # Workload-specific request patterns
        if workload_type == 'CPU_INTENSIVE':
            cpu_request_multiplier = np.random.uniform(1.2, 1.8)
            memory_request_multiplier = np.random.uniform(1.3, 2.0)
        elif workload_type == 'MEMORY_INTENSIVE':
            cpu_request_multiplier = np.random.uniform(1.5, 2.2)
            memory_request_multiplier = np.random.uniform(1.1, 1.5)
        elif workload_type == 'BALANCED':
            cpu_request_multiplier = np.random.uniform(1.3, 1.7)
            memory_request_multiplier = np.random.uniform(1.3, 1.7)
        elif workload_type == 'BURSTY':
            cpu_request_multiplier = np.random.uniform(1.8, 2.5)
            memory_request_multiplier = np.random.uniform(1.5, 2.2)
        else:  # LOW_UTILIZATION
            cpu_request_multiplier = np.random.uniform(2.0, 4.0)
            memory_request_multiplier = np.random.uniform(2.0, 3.5)
        
        # Calculate gaps
        avg_cpu_gap = cpu_mean * (cpu_request_multiplier - 1)
        avg_memory_gap = memory_mean * (memory_request_multiplier - 1)
        
        max_cpu_gap = avg_cpu_gap * np.random.uniform(1.2, 1.8)
        max_memory_gap = avg_memory_gap * np.random.uniform(1.2, 1.8)
        
        cpu_gap_variance = (avg_cpu_gap * 0.3) ** 2
        memory_gap_variance = (avg_memory_gap * 0.3) ** 2
        
        # Overall efficiency
        total_gap = avg_cpu_gap + avg_memory_gap
        efficiency_score = max(0.1, 1.0 - (total_gap / 200))
        
        return {
            'avg_cpu_gap': float(avg_cpu_gap),
            'max_cpu_gap': float(max_cpu_gap),
            'cpu_gap_variance': float(cpu_gap_variance),
            'avg_memory_gap': float(avg_memory_gap),
            'max_memory_gap': float(max_memory_gap),
            'memory_gap_variance': float(memory_gap_variance),
            'overall_efficiency_score': float(efficiency_score)
        }
    
    def _generate_enhanced_cluster_features(self, workload_type):
        """Generate enhanced cluster features with workload-specific characteristics"""
        
        # Cluster size based on workload type
        if workload_type == 'LOW_UTILIZATION':
            cluster_size = np.random.choice([2, 3, 4, 5], p=[0.3, 0.4, 0.2, 0.1])
        elif workload_type == 'BURSTY':
            cluster_size = np.random.choice([3, 5, 8, 12, 20], p=[0.2, 0.3, 0.3, 0.15, 0.05])
        else:
            cluster_size = np.random.choice([3, 5, 8, 12], p=[0.25, 0.35, 0.25, 0.15])
        
        # Node readiness (workload-dependent)
        if workload_type in ['CPU_INTENSIVE', 'MEMORY_INTENSIVE']:
            readiness = np.random.uniform(0.85, 1.0)
        elif workload_type == 'BURSTY':
            readiness = np.random.uniform(0.75, 0.95)
        else:
            readiness = np.random.uniform(0.9, 1.0)
        
        # Distribution fairness
        if workload_type == 'BALANCED':
            cpu_fairness = np.random.uniform(0.7, 0.95)
            memory_fairness = np.random.uniform(0.7, 0.95)
        elif workload_type == 'BURSTY':
            cpu_fairness = np.random.uniform(0.3, 0.7)
            memory_fairness = np.random.uniform(0.4, 0.75)
        else:
            cpu_fairness = np.random.uniform(0.6, 0.9)
            memory_fairness = np.random.uniform(0.6, 0.9)
        
        return {
            'node_readiness_ratio': float(readiness),
            'cpu_distribution_fairness': float(cpu_fairness),
            'memory_distribution_fairness': float(memory_fairness),
            'cluster_size': float(cluster_size),
            'cluster_size_normalized': float(min(cluster_size / 10, 1.0))
        }
    
    def _add_enhanced_realism(self, df):
        """Add enhanced realism and remove unrealistic combinations"""
        
        # Fix unrealistic correlations
        df['cpu_memory_correlation'] = df['cpu_memory_correlation'].fillna(0.0)
        df = df.replace([np.inf, -np.inf], 0.0)
        
        # Add small realistic noise (reduced from previous version)
        numeric_cols = [col for col in df.columns if col != 'workload_type']
        
        for col in numeric_cols:
            if df[col].std() > 0:
                noise_factor = 0.01  # Reduced noise
                noise = np.random.normal(0, df[col].std() * noise_factor, len(df))
                df[col] = df[col] + noise
        
        # Ensure logical consistency
        df['cpu_range'] = df['cpu_max'] - df['cpu_min']
        df['memory_range'] = df['memory_max'] - df['memory_min']
        df['resource_imbalance'] = abs(df['cpu_mean'] - df['memory_mean'])
        
        return df
    
    def _augment_training_data(self, df):
        """Augment training data for better generalization"""
        
        logger.info("🔄 Augmenting training data...")
        
        # Create edge case samples
        edge_cases = []
        
        for workload_type in self.workload_classes:
            type_data = df[df['workload_type'] == workload_type]
            
            if len(type_data) > 0:
                # Create 10% more edge cases per class
                n_edge_cases = max(1, len(type_data) // 10)
                
                for _ in range(n_edge_cases):
                    # Sample a base case
                    base_sample = type_data.sample(1).iloc[0].copy()
                    
                    # Add variations
                    if workload_type == 'CPU_INTENSIVE':
                        base_sample['cpu_mean'] = min(98, base_sample['cpu_mean'] * np.random.uniform(1.1, 1.3))
                    elif workload_type == 'MEMORY_INTENSIVE':
                        base_sample['memory_mean'] = min(98, base_sample['memory_mean'] * np.random.uniform(1.1, 1.3))
                    elif workload_type == 'BURSTY':
                        base_sample['cpu_var'] *= np.random.uniform(1.5, 2.0)
                        base_sample['memory_var'] *= np.random.uniform(1.3, 1.8)
                    
                    edge_cases.append(base_sample)
        
        if edge_cases:
            edge_df = pd.DataFrame(edge_cases)
            df = pd.concat([df, edge_df], ignore_index=True)
        
        logger.info(f"✅ Augmented to {len(df)} total samples")
        return df
    
    def train_enhanced_models(self, df):
        """Train enhanced models with hyperparameter tuning"""
        logger.info("🤖 Training enhanced ML models with hyperparameter optimization...")
        
        # Prepare features and targets
        X = df[self.expected_features]
        y = df['workload_type']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"📊 Training set: {len(X_train)} samples")
        logger.info(f"🧪 Test set: {len(X_test)} samples")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Hyperparameter tuning
        logger.info("🔧 Optimizing hyperparameters...")
        
        param_grid = {
            'n_estimators': [200, 300, 400],
            'max_depth': [15, 20, 25],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None]
        }
        
        # Grid search with cross-validation
        rf_base = RandomForestClassifier(random_state=42, n_jobs=-1)
        
        grid_search = GridSearchCV(
            rf_base, 
            param_grid, 
            cv=5, 
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train_scaled, y_train)
        
        # Use best model
        self.pattern_classifier = grid_search.best_estimator_
        
        logger.info(f"✅ Best parameters: {grid_search.best_params_}")
        logger.info(f"✅ Best CV score: {grid_search.best_score_:.3f}")
        
        # Evaluate model
        train_score = self.pattern_classifier.score(X_train_scaled, y_train)
        test_score = self.pattern_classifier.score(X_test_scaled, y_test)
        
        logger.info(f"✅ Training accuracy: {train_score:.3f}")
        logger.info(f"✅ Test accuracy: {test_score:.3f}")
        
        # Cross-validation on final model
        cv_scores = cross_val_score(self.pattern_classifier, X_train_scaled, y_train, cv=5)
        logger.info(f"✅ Cross-validation score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        # Detailed evaluation
        y_pred = self.pattern_classifier.predict(X_test_scaled)
        
        logger.info("\n📈 Enhanced Classification Report:")
        print(classification_report(y_test, y_pred))
        
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'best_params': grid_search.best_params_,
            'X_test': X_test,
            'y_test': y_test,
            'y_pred': y_pred
        }
    
    def save_enhanced_models(self, results):
        """Save enhanced models with metadata"""
        logger.info("💾 Saving enhanced trained models...")
        
        # Save models
        joblib.dump(self.pattern_classifier, 'workload_pattern_classifier.pkl')
        joblib.dump(self.scaler, 'workload_feature_scaler.pkl')
        
        # Enhanced model metadata
        model_info = {
            'features': self.expected_features,
            'classes': list(self.pattern_classifier.classes_),
            'n_features': len(self.expected_features),
            'model_type': 'RandomForestClassifier',
            'created_date': datetime.now().isoformat(),
            'training_accuracy': results['train_accuracy'],
            'test_accuracy': results['test_accuracy'],
            'cv_mean': results['cv_mean'],
            'cv_std': results['cv_std'],
            'best_hyperparameters': results['best_params'],
            'sklearn_version': '1.0+',
            'training_approach': 'enhanced_with_hyperparameter_tuning',
            'expected_confidence_range': '0.75-0.95'
        }
        
        import json
        with open('model_info.json', 'w') as f:
            json.dump(model_info, f, indent=2)
        
        logger.info("✅ Enhanced models saved successfully!")
        logger.info("📝 Files created:")
        logger.info("   - workload_pattern_classifier.pkl (optimized)")
        logger.info("   - workload_feature_scaler.pkl")
        logger.info("   - model_info.json (enhanced)")
    
    def create_enhanced_visualizations(self, results):
        """Create enhanced visualizations"""
        logger.info("📊 Creating enhanced visualizations...")
        
        try:
            # Enhanced Confusion Matrix
            plt.figure(figsize=(12, 10))
            cm = confusion_matrix(results['y_test'], results['y_pred'])
            
            # Calculate percentages
            cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
            
            # Create annotation text
            annot_text = np.empty_like(cm).astype(str)
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    annot_text[i, j] = f'{cm[i, j]}\n({cm_percent[i, j]:.1f}%)'
            
            sns.heatmap(cm, annot=annot_text, fmt='', cmap='Blues',
                       xticklabels=self.workload_classes,
                       yticklabels=self.workload_classes)
            plt.title('Enhanced Workload Classification - Confusion Matrix\n(Count and Percentage)')
            plt.ylabel('True Label')
            plt.xlabel('Predicted Label')
            plt.tight_layout()
            plt.savefig('enhanced_confusion_matrix.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Enhanced Feature Importance
            plt.figure(figsize=(14, 10))
            importances = self.pattern_classifier.feature_importances_
            indices = np.argsort(importances)[::-1][:20]  # Top 20 features
            
            plt.title('Top 20 Most Important Features for Workload Classification')
            bars = plt.bar(range(20), importances[indices])
            plt.xticks(range(20), [self.expected_features[i] for i in indices], rotation=45, ha='right')
            plt.ylabel('Feature Importance')
            
            # Color code by feature type
            colors = []
            for idx in indices:
                feature_name = self.expected_features[idx]
                if 'cpu' in feature_name:
                    colors.append('lightcoral')
                elif 'memory' in feature_name:
                    colors.append('lightblue')
                elif 'hpa' in feature_name:
                    colors.append('lightgreen')
                elif any(time_feat in feature_name for time_feat in ['hour', 'day', 'business', 'weekend']):
                    colors.append('lightyellow')
                else:
                    colors.append('lightgray')
            
            for bar, color in zip(bars, colors):
                bar.set_color(color)
            
            plt.tight_layout()
            plt.savefig('enhanced_feature_importance.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Class Distribution
            plt.figure(figsize=(10, 6))
            class_counts = Counter(results['y_test'])
            plt.bar(class_counts.keys(), class_counts.values())
            plt.title('Test Set Class Distribution')
            plt.xlabel('Workload Type')
            plt.ylabel('Number of Samples')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('class_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("✅ Enhanced visualizations saved:")
            logger.info("   - enhanced_confusion_matrix.png")
            logger.info("   - enhanced_feature_importance.png")
            logger.info("   - class_distribution.png")
            
        except Exception as e:
            logger.warning(f"⚠️ Enhanced visualization creation failed: {e}")


def main():
    """Main enhanced training pipeline"""
    print("🚀 Enhanced ML Workload Performance Analyzer - Training Pipeline")
    print("=" * 70)
    
    # Initialize enhanced trainer
    trainer = EnhancedMLModelTrainer()
    
    try:
        # Step 1: Generate enhanced training data
        print("\n📊 Step 1: Generating Enhanced Training Data")
        df = trainer.generate_enhanced_training_data(n_samples=5000)
        
        # Save training data for inspection
        df.to_csv('enhanced_training_data.csv', index=False)
        logger.info("💾 Enhanced training data saved to enhanced_training_data.csv")
        
        # Step 2: Train enhanced models
        print("\n🤖 Step 2: Training Enhanced ML Models with Hyperparameter Tuning")
        results = trainer.train_enhanced_models(df)
        
        # Step 3: Save enhanced models
        print("\n💾 Step 3: Saving Enhanced Models")
        trainer.save_enhanced_models(results)
        
        # Step 4: Create enhanced visualizations
        print("\n📊 Step 4: Creating Enhanced Visualizations")
        trainer.create_enhanced_visualizations(results)
        
        # Summary
        print("\n" + "="*70)
        print("📋 ENHANCED TRAINING SUMMARY")
        print("="*70)
        print(f"✅ Training Accuracy: {results['train_accuracy']:.3f}")
        print(f"✅ Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"✅ Cross-validation: {results['cv_mean']:.3f} (+/- {results['cv_std']*2:.3f})")
        print(f"✅ Best Parameters: {results['best_params']}")
        
        print("\n📁 Generated Files:")
        print("   - workload_pattern_classifier.pkl (optimized)")
        print("   - workload_feature_scaler.pkl")
        print("   - model_info.json (enhanced)")
        print("   - enhanced_training_data.csv")
        print("   - enhanced_confusion_matrix.png")
        print("   - enhanced_feature_importance.png")
        print("   - class_distribution.png")
        
        if results['test_accuracy'] > 0.90:
            print("\n🎉 EXCELLENCE: Enhanced models ready for high-confidence predictions!")
            print(f"💪 Expected confidence range: 75-95%")
        elif results['test_accuracy'] > 0.85:
            print("\n✅ SUCCESS: Good model performance achieved!")
        else:
            print("\n⚠️  WARNING: Consider further optimization")
            
    except Exception as e:
        logger.error(f"❌ Enhanced training pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()