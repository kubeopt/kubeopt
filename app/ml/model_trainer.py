#!/usr/bin/env python3
"""
Comprehensive ML Model Trainer for >80% Accuracy
===============================================
Advanced training system for the self-learning HPA engine with extensive data generation,
feature optimization, and accuracy improvement techniques.
"""

import numpy as np
import pandas as pd
import logging
import json
import os
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.utils.class_weight import compute_class_weight
import joblib
from typing import Dict, List, Tuple, Any
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import random

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveMLTrainer:
    """
    Comprehensive ML Trainer for achieving >80% accuracy
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
        
        # Target classes
        self.target_classes = ['CPU_INTENSIVE', 'MEMORY_INTENSIVE', 'BALANCED', 'BURSTY', 'LOW_UTILIZATION']
        
        # Create directories
        os.makedirs(self.model_path, exist_ok=True)
        os.makedirs(os.path.join(self.model_path, "training_data"), exist_ok=True)
        os.makedirs(os.path.join(self.model_path, "evaluation"), exist_ok=True)
        
        logger.info(f"🎯 Comprehensive ML Trainer initialized for >80% accuracy target")
        logger.info(f"📂 Model path: {self.model_path}")
        logger.info(f"🎲 Features: {len(self.expected_features)}")
        logger.info(f"🏷️ Classes: {len(self.target_classes)}")

    def generate_extensive_training_data(self, num_samples: int = 5000) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate extensive, realistic training data for all workload types
        """
        logger.info(f"🏭 Generating {num_samples} comprehensive training samples...")
        
        all_features = []
        all_labels = []
        
        # Calculate samples per class (with some imbalance to reflect reality)
        class_distributions = {
            'BALANCED': 0.30,      # Most common
            'CPU_INTENSIVE': 0.25,  # Common
            'MEMORY_INTENSIVE': 0.20, # Common
            'LOW_UTILIZATION': 0.15,  # Moderate
            'BURSTY': 0.10         # Less common but important
        }
        
        for workload_type, proportion in class_distributions.items():
            class_samples = int(num_samples * proportion)
            logger.info(f"🎲 Generating {class_samples} samples for {workload_type}")
            
            for i in range(class_samples):
                features = self._generate_workload_specific_sample(workload_type, i)
                all_features.append(features)
                all_labels.append(workload_type)
        
        # Create DataFrames
        features_df = pd.DataFrame(all_features, columns=self.expected_features)
        labels_df = pd.DataFrame(all_labels, columns=['workload_type'])
        
        # Add noise and edge cases for robustness
        features_df = self._add_realistic_noise(features_df, labels_df)
        
        # Validate data quality
        self._validate_training_data(features_df, labels_df)
        
        logger.info(f"✅ Generated {len(features_df)} high-quality training samples")
        self._log_class_distribution(labels_df)
        
        return features_df, labels_df

    def _generate_workload_specific_sample(self, workload_type: str, sample_index: int) -> List[float]:
        """
        Generate realistic features for specific workload type
        """
        
        # Base random variations
        np.random.seed(sample_index + hash(workload_type) % 10000)
        
        if workload_type == 'CPU_INTENSIVE':
            return self._generate_cpu_intensive_sample()
        elif workload_type == 'MEMORY_INTENSIVE':
            return self._generate_memory_intensive_sample()
        elif workload_type == 'BURSTY':
            return self._generate_bursty_sample()
        elif workload_type == 'LOW_UTILIZATION':
            return self._generate_low_utilization_sample()
        else:  # BALANCED
            return self._generate_balanced_sample()

    def _generate_cpu_intensive_sample(self) -> List[float]:
        """Generate CPU-intensive workload features"""
        
        # CPU-dominant characteristics
        cpu_base = np.random.uniform(70, 95)  # High CPU
        memory_base = np.random.uniform(40, 70)  # Moderate memory
        
        # Add realistic variability
        cpu_std = np.random.uniform(5, 15)
        memory_std = np.random.uniform(3, 10)
        
        # Generate correlated values
        cpu_values = np.clip(np.random.normal(cpu_base, cpu_std, 10), 0, 100)
        memory_values = np.clip(np.random.normal(memory_base, memory_std, 10), 0, 100)
        
        features = []
        
        # Basic statistical features
        features.extend([
            np.mean(cpu_values), np.mean(memory_values),
            np.std(cpu_values), np.std(memory_values),
            np.var(cpu_values), np.var(memory_values),
            np.min(cpu_values), np.max(cpu_values),
            np.min(memory_values), np.max(memory_values)
        ])
        
        # Percentiles
        features.extend([
            np.percentile(cpu_values, 75), np.percentile(cpu_values, 95), np.percentile(cpu_values, 99),
            np.percentile(memory_values, 75), np.percentile(memory_values, 95), np.percentile(memory_values, 99)
        ])
        
        # Range and variability
        features.extend([
            np.max(cpu_values) - np.min(cpu_values),
            np.max(memory_values) - np.min(memory_values),
            np.std(cpu_values) / max(np.mean(cpu_values), 1),
            np.std(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Cross-resource features
        features.extend([
            np.mean(cpu_values) / max(np.mean(memory_values), 1),  # CPU/Memory ratio (should be >1)
            np.corrcoef(cpu_values, memory_values)[0, 1],
            abs(np.mean(cpu_values) - np.mean(memory_values))  # Resource imbalance
        ])
        
        # HPA features (CPU workloads often have some HPA)
        features.extend([
            np.random.uniform(0.3, 0.8),  # HPA implementation score
            1.0,  # CPU-based HPA pattern
            np.random.uniform(0.6, 0.9),  # HPA confidence
            np.random.uniform(0.2, 0.6)   # HPA density
        ])
        
        # Behavior features
        features.extend([
            np.random.uniform(0.05, 0.2),  # CPU burst frequency
            np.random.uniform(0.02, 0.1),  # Memory burst frequency
            np.random.uniform(0.6, 0.8),   # CPU stability (lower due to high usage)
            np.random.uniform(0.7, 0.9),   # Memory stability (higher)
            np.max(cpu_values) / max(np.mean(cpu_values), 1),
            np.max(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Resource gaps (CPU-intensive often has higher gaps)
        features.extend([
            np.random.uniform(15, 35),  # avg_cpu_gap
            np.random.uniform(25, 50),  # max_cpu_gap
            np.random.uniform(50, 200), # cpu_gap_variance
            np.random.uniform(10, 25),  # avg_memory_gap
            np.random.uniform(15, 35),  # max_memory_gap
            np.random.uniform(30, 100), # memory_gap_variance
            np.random.uniform(0.4, 0.7) # overall_efficiency_score
        ])
        
        # Temporal features
        features.extend(self._generate_temporal_features())
        
        # Cluster health features
        features.extend([
            np.random.uniform(0.9, 1.0),   # node_readiness_ratio
            np.random.uniform(0.6, 0.8),   # cpu_distribution_fairness (lower due to uneven CPU)
            np.random.uniform(0.8, 0.95),  # memory_distribution_fairness
            np.random.randint(2, 8),       # cluster_size
            min(np.random.randint(2, 8) / 10, 1.0)  # cluster_size_normalized
        ])
        
        return features

    def _generate_memory_intensive_sample(self) -> List[float]:
        """Generate Memory-intensive workload features"""
        
        # Memory-dominant characteristics
        cpu_base = np.random.uniform(30, 60)  # Moderate CPU
        memory_base = np.random.uniform(75, 95)  # High memory
        
        cpu_std = np.random.uniform(3, 10)
        memory_std = np.random.uniform(5, 15)
        
        cpu_values = np.clip(np.random.normal(cpu_base, cpu_std, 10), 0, 100)
        memory_values = np.clip(np.random.normal(memory_base, memory_std, 10), 0, 100)
        
        features = []
        
        # Basic statistical features
        features.extend([
            np.mean(cpu_values), np.mean(memory_values),
            np.std(cpu_values), np.std(memory_values),
            np.var(cpu_values), np.var(memory_values),
            np.min(cpu_values), np.max(cpu_values),
            np.min(memory_values), np.max(memory_values)
        ])
        
        # Percentiles
        features.extend([
            np.percentile(cpu_values, 75), np.percentile(cpu_values, 95), np.percentile(cpu_values, 99),
            np.percentile(memory_values, 75), np.percentile(memory_values, 95), np.percentile(memory_values, 99)
        ])
        
        # Range and variability
        features.extend([
            np.max(cpu_values) - np.min(cpu_values),
            np.max(memory_values) - np.min(memory_values),
            np.std(cpu_values) / max(np.mean(cpu_values), 1),
            np.std(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Cross-resource features (Memory/CPU ratio should be >1)
        features.extend([
            np.mean(cpu_values) / max(np.mean(memory_values), 1),  # Should be <1
            np.corrcoef(cpu_values, memory_values)[0, 1],
            abs(np.mean(cpu_values) - np.mean(memory_values))
        ])
        
        # HPA features (Memory workloads often have memory-based HPA)
        features.extend([
            np.random.uniform(0.4, 0.9),  # HPA implementation score
            2.0,  # Memory-based HPA pattern
            np.random.uniform(0.7, 0.95), # HPA confidence
            np.random.uniform(0.3, 0.7)   # HPA density
        ])
        
        # Behavior features
        features.extend([
            np.random.uniform(0.02, 0.1),  # CPU burst frequency (lower)
            np.random.uniform(0.1, 0.3),   # Memory burst frequency (higher)
            np.random.uniform(0.7, 0.9),   # CPU stability (higher)
            np.random.uniform(0.5, 0.7),   # Memory stability (lower due to high usage)
            np.max(cpu_values) / max(np.mean(cpu_values), 1),
            np.max(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Resource gaps
        features.extend([
            np.random.uniform(10, 25),  # avg_cpu_gap
            np.random.uniform(15, 35),  # max_cpu_gap
            np.random.uniform(30, 100), # cpu_gap_variance
            np.random.uniform(20, 40),  # avg_memory_gap (higher)
            np.random.uniform(30, 60),  # max_memory_gap (higher)
            np.random.uniform(80, 250), # memory_gap_variance (higher)
            np.random.uniform(0.3, 0.6) # overall_efficiency_score
        ])
        
        # Temporal features
        features.extend(self._generate_temporal_features())
        
        # Cluster health features
        features.extend([
            np.random.uniform(0.85, 1.0),  # node_readiness_ratio
            np.random.uniform(0.8, 0.95),  # cpu_distribution_fairness
            np.random.uniform(0.6, 0.8),   # memory_distribution_fairness (lower)
            np.random.randint(3, 10),      # cluster_size
            min(np.random.randint(3, 10) / 10, 1.0)
        ])
        
        return features

    def _generate_bursty_sample(self) -> List[float]:
        """Generate Bursty workload features - KEY FOR IMPROVING ACCURACY"""
        
        # Bursty characteristics: High variability, peaks and valleys
        cpu_base = np.random.uniform(40, 80)
        memory_base = np.random.uniform(45, 75)
        
        # HIGH variability is key for bursty detection
        cpu_std = np.random.uniform(20, 40)  # Much higher std
        memory_std = np.random.uniform(15, 30)
        
        # Generate more variable data with clear peaks
        cpu_values = []
        memory_values = []
        
        for i in range(10):
            if i % 3 == 0:  # Peak periods
                cpu_val = np.clip(np.random.normal(cpu_base + 30, 10), 0, 100)
                memory_val = np.clip(np.random.normal(memory_base + 20, 8), 0, 100)
            else:  # Normal/low periods
                cpu_val = np.clip(np.random.normal(cpu_base - 15, 5), 0, 100)
                memory_val = np.clip(np.random.normal(memory_base - 10, 5), 0, 100)
            
            cpu_values.append(cpu_val)
            memory_values.append(memory_val)
        
        cpu_values = np.array(cpu_values)
        memory_values = np.array(memory_values)
        
        features = []
        
        # Basic statistical features
        features.extend([
            np.mean(cpu_values), np.mean(memory_values),
            np.std(cpu_values), np.std(memory_values),  # These will be high
            np.var(cpu_values), np.var(memory_values),  # These will be high
            np.min(cpu_values), np.max(cpu_values),     # Large range
            np.min(memory_values), np.max(memory_values)
        ])
        
        # Percentiles (wide spread)
        features.extend([
            np.percentile(cpu_values, 75), np.percentile(cpu_values, 95), np.percentile(cpu_values, 99),
            np.percentile(memory_values, 75), np.percentile(memory_values, 95), np.percentile(memory_values, 99)
        ])
        
        # Range and variability (HIGH for bursty)
        features.extend([
            np.max(cpu_values) - np.min(cpu_values),    # Large range
            np.max(memory_values) - np.min(memory_values),
            np.std(cpu_values) / max(np.mean(cpu_values), 1),  # High CV
            np.std(memory_values) / max(np.mean(memory_values), 1)  # High CV
        ])
        
        # Cross-resource features
        features.extend([
            np.mean(cpu_values) / max(np.mean(memory_values), 1),
            np.corrcoef(cpu_values, memory_values)[0, 1],
            abs(np.mean(cpu_values) - np.mean(memory_values))
        ])
        
        # HPA features (Bursty workloads often have multi-metric HPA)
        features.extend([
            np.random.uniform(0.6, 0.95), # HPA implementation score (often high)
            3.0,  # Multi-metric HPA pattern
            np.random.uniform(0.8, 0.95), # HPA confidence (high)
            np.random.uniform(0.5, 0.9)   # HPA density (high)
        ])
        
        # Behavior features (KEY for bursty detection)
        features.extend([
            np.random.uniform(0.3, 0.6),   # HIGH CPU burst frequency
            np.random.uniform(0.25, 0.5),  # HIGH Memory burst frequency
            np.random.uniform(0.3, 0.6),   # LOW CPU stability (key indicator)
            np.random.uniform(0.4, 0.7),   # LOW Memory stability
            np.max(cpu_values) / max(np.mean(cpu_values), 1),  # High peak ratio
            np.max(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Resource gaps (highly variable)
        features.extend([
            np.random.uniform(20, 45),  # avg_cpu_gap (high)
            np.random.uniform(40, 80),  # max_cpu_gap (very high)
            np.random.uniform(200, 500), # cpu_gap_variance (very high)
            np.random.uniform(18, 40),  # avg_memory_gap
            np.random.uniform(35, 70),  # max_memory_gap
            np.random.uniform(150, 400), # memory_gap_variance (high)
            np.random.uniform(0.2, 0.5) # overall_efficiency_score (low due to variability)
        ])
        
        # Temporal features
        features.extend(self._generate_temporal_features())
        
        # Cluster health features
        features.extend([
            np.random.uniform(0.8, 0.95),  # node_readiness_ratio
            np.random.uniform(0.4, 0.7),   # cpu_distribution_fairness (low due to bursts)
            np.random.uniform(0.5, 0.8),   # memory_distribution_fairness
            np.random.randint(3, 12),      # cluster_size (often larger for burst handling)
            min(np.random.randint(3, 12) / 10, 1.0)
        ])
        
        return features

    def _generate_low_utilization_sample(self) -> List[float]:
        """Generate Low utilization workload features"""
        
        # Low utilization characteristics
        cpu_base = np.random.uniform(10, 35)  # Low CPU
        memory_base = np.random.uniform(15, 45)  # Low memory
        
        cpu_std = np.random.uniform(2, 8)
        memory_std = np.random.uniform(3, 10)
        
        cpu_values = np.clip(np.random.normal(cpu_base, cpu_std, 10), 0, 100)
        memory_values = np.clip(np.random.normal(memory_base, memory_std, 10), 0, 100)
        
        features = []
        
        # Basic statistical features (all low)
        features.extend([
            np.mean(cpu_values), np.mean(memory_values),
            np.std(cpu_values), np.std(memory_values),
            np.var(cpu_values), np.var(memory_values),
            np.min(cpu_values), np.max(cpu_values),
            np.min(memory_values), np.max(memory_values)
        ])
        
        # Percentiles (all low)
        features.extend([
            np.percentile(cpu_values, 75), np.percentile(cpu_values, 95), np.percentile(cpu_values, 99),
            np.percentile(memory_values, 75), np.percentile(memory_values, 95), np.percentile(memory_values, 99)
        ])
        
        # Range and variability
        features.extend([
            np.max(cpu_values) - np.min(cpu_values),
            np.max(memory_values) - np.min(memory_values),
            np.std(cpu_values) / max(np.mean(cpu_values), 1),
            np.std(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Cross-resource features
        features.extend([
            np.mean(cpu_values) / max(np.mean(memory_values), 1),
            np.corrcoef(cpu_values, memory_values)[0, 1],
            abs(np.mean(cpu_values) - np.mean(memory_values))
        ])
        
        # HPA features (Low utilization often has no HPA)
        features.extend([
            np.random.uniform(0.0, 0.3),   # HPA implementation score (low)
            0.0,  # No HPA pattern
            np.random.uniform(0.1, 0.4),   # HPA confidence (low)
            np.random.uniform(0.0, 0.2)    # HPA density (very low)
        ])
        
        # Behavior features
        features.extend([
            np.random.uniform(0.0, 0.05),  # CPU burst frequency (very low)
            np.random.uniform(0.0, 0.05),  # Memory burst frequency (very low)
            np.random.uniform(0.85, 0.98), # CPU stability (very high)
            np.random.uniform(0.85, 0.98), # Memory stability (very high)
            np.max(cpu_values) / max(np.mean(cpu_values), 1),
            np.max(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Resource gaps (high due to over-provisioning)
        features.extend([
            np.random.uniform(30, 60),  # avg_cpu_gap (high)
            np.random.uniform(45, 80),  # max_cpu_gap (high)
            np.random.uniform(100, 300), # cpu_gap_variance
            np.random.uniform(25, 50),  # avg_memory_gap (high)
            np.random.uniform(40, 70),  # max_memory_gap (high)
            np.random.uniform(80, 250), # memory_gap_variance
            np.random.uniform(0.1, 0.4) # overall_efficiency_score (low)
        ])
        
        # Temporal features
        features.extend(self._generate_temporal_features())
        
        # Cluster health features
        features.extend([
            np.random.uniform(0.95, 1.0),  # node_readiness_ratio (high)
            np.random.uniform(0.85, 0.98), # cpu_distribution_fairness (high)
            np.random.uniform(0.85, 0.98), # memory_distribution_fairness (high)
            np.random.randint(1, 5),       # cluster_size (often smaller)
            min(np.random.randint(1, 5) / 10, 1.0)
        ])
        
        return features

    def _generate_balanced_sample(self) -> List[float]:
        """Generate Balanced workload features"""
        
        # Balanced characteristics
        cpu_base = np.random.uniform(50, 75)
        memory_base = np.random.uniform(55, 80)
        
        cpu_std = np.random.uniform(8, 15)
        memory_std = np.random.uniform(8, 15)
        
        cpu_values = np.clip(np.random.normal(cpu_base, cpu_std, 10), 0, 100)
        memory_values = np.clip(np.random.normal(memory_base, memory_std, 10), 0, 100)
        
        features = []
        
        # Basic statistical features
        features.extend([
            np.mean(cpu_values), np.mean(memory_values),
            np.std(cpu_values), np.std(memory_values),
            np.var(cpu_values), np.var(memory_values),
            np.min(cpu_values), np.max(cpu_values),
            np.min(memory_values), np.max(memory_values)
        ])
        
        # Percentiles
        features.extend([
            np.percentile(cpu_values, 75), np.percentile(cpu_values, 95), np.percentile(cpu_values, 99),
            np.percentile(memory_values, 75), np.percentile(memory_values, 95), np.percentile(memory_values, 99)
        ])
        
        # Range and variability
        features.extend([
            np.max(cpu_values) - np.min(cpu_values),
            np.max(memory_values) - np.min(memory_values),
            np.std(cpu_values) / max(np.mean(cpu_values), 1),
            np.std(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Cross-resource features (balanced ratio ~1)
        features.extend([
            np.mean(cpu_values) / max(np.mean(memory_values), 1),  # Should be ~1
            np.corrcoef(cpu_values, memory_values)[0, 1],
            abs(np.mean(cpu_values) - np.mean(memory_values))  # Should be small
        ])
        
        # HPA features (Balanced workloads often have hybrid HPA)
        features.extend([
            np.random.uniform(0.5, 0.8),   # HPA implementation score
            np.random.choice([1.0, 2.0, 3.0]),  # Mixed HPA patterns
            np.random.uniform(0.6, 0.8),   # HPA confidence
            np.random.uniform(0.3, 0.6)    # HPA density
        ])
        
        # Behavior features
        features.extend([
            np.random.uniform(0.05, 0.15), # CPU burst frequency (moderate)
            np.random.uniform(0.05, 0.15), # Memory burst frequency (moderate)
            np.random.uniform(0.7, 0.85),  # CPU stability (moderate-high)
            np.random.uniform(0.7, 0.85),  # Memory stability (moderate-high)
            np.max(cpu_values) / max(np.mean(cpu_values), 1),
            np.max(memory_values) / max(np.mean(memory_values), 1)
        ])
        
        # Resource gaps (moderate)
        features.extend([
            np.random.uniform(15, 30),  # avg_cpu_gap
            np.random.uniform(25, 45),  # max_cpu_gap
            np.random.uniform(60, 150), # cpu_gap_variance
            np.random.uniform(15, 30),  # avg_memory_gap
            np.random.uniform(25, 45),  # max_memory_gap
            np.random.uniform(60, 150), # memory_gap_variance
            np.random.uniform(0.5, 0.8) # overall_efficiency_score
        ])
        
        # Temporal features
        features.extend(self._generate_temporal_features())
        
        # Cluster health features
        features.extend([
            np.random.uniform(0.9, 1.0),   # node_readiness_ratio
            np.random.uniform(0.75, 0.9),  # cpu_distribution_fairness
            np.random.uniform(0.75, 0.9),  # memory_distribution_fairness
            np.random.randint(2, 8),       # cluster_size
            min(np.random.randint(2, 8) / 10, 1.0)
        ])
        
        return features

    def _generate_temporal_features(self) -> List[float]:
        """Generate realistic temporal features"""
        hour = np.random.randint(0, 24)
        day = np.random.randint(0, 7)
        
        return [
            hour,  # hour_of_day
            1.0 if 9 <= hour <= 17 else 0.0,  # is_business_hours
            1.0 if day >= 5 else 0.0,  # is_weekend
            1.0 if hour in [9, 10, 14, 15] else 0.0,  # is_peak_hours
            np.sin(2 * np.pi * hour / 24),  # hour_sin
            np.cos(2 * np.pi * hour / 24),  # hour_cos
            np.sin(2 * np.pi * day / 7),    # day_sin
            np.cos(2 * np.pi * day / 7)     # day_cos
        ]

    def _add_realistic_noise(self, features_df: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic noise and edge cases for robustness"""
        
        # Add 5% noise to numerical features
        noise_factor = 0.05
        numerical_cols = features_df.select_dtypes(include=[np.number]).columns
        
        for col in numerical_cols:
            if col not in ['hour_of_day', 'is_business_hours', 'is_weekend', 'is_peak_hours']:
                noise = np.random.normal(0, features_df[col].std() * noise_factor, len(features_df))
                features_df[col] += noise
        
        # Clip values to reasonable ranges
        features_df = features_df.clip(lower=0)
        
        # Add some extreme edge cases (2% of data)
        num_edge_cases = int(len(features_df) * 0.02)
        edge_indices = np.random.choice(len(features_df), num_edge_cases, replace=False)
        
        for idx in edge_indices:
            # Create extreme scenarios
            if np.random.random() > 0.5:
                # Extreme high utilization
                features_df.loc[idx, 'cpu_mean'] = np.random.uniform(95, 100)
                features_df.loc[idx, 'memory_mean'] = np.random.uniform(95, 100)
            else:
                # Extreme low utilization
                features_df.loc[idx, 'cpu_mean'] = np.random.uniform(0, 5)
                features_df.loc[idx, 'memory_mean'] = np.random.uniform(0, 5)
        
        return features_df

    def _validate_training_data(self, features_df: pd.DataFrame, labels_df: pd.DataFrame):
        """Validate training data quality"""
        
        # Check for missing values
        if features_df.isnull().sum().sum() > 0:
            logger.warning("⚠️ Found missing values in training data")
        
        # Check for infinite values
        if np.isinf(features_df.values).sum() > 0:
            logger.warning("⚠️ Found infinite values in training data")
            features_df.replace([np.inf, -np.inf], 0, inplace=True)
        
        # Check feature ranges
        for feature in self.expected_features:
            if feature in features_df.columns:
                col_data = features_df[feature]
                logger.info(f"📊 {feature}: min={col_data.min():.2f}, max={col_data.max():.2f}, mean={col_data.mean():.2f}")

    def _log_class_distribution(self, labels_df: pd.DataFrame):
        """Log class distribution"""
        class_counts = labels_df['workload_type'].value_counts()
        logger.info("📊 Class Distribution:")
        for class_name, count in class_counts.items():
            percentage = (count / len(labels_df)) * 100
            logger.info(f"   {class_name}: {count} ({percentage:.1f}%)")

    def train_high_accuracy_model(self, features_df: pd.DataFrame, labels_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train models with optimizations for >80% accuracy
        """
        logger.info("🚀 Training high-accuracy models with advanced optimization...")
        
        # Prepare data
        X = features_df.values
        y = labels_df['workload_type'].values
        
        # Split data with stratification
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Calculate class weights to handle imbalance
        class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
        class_weight_dict = dict(zip(np.unique(y_train), class_weights))
        
        logger.info(f"⚖️ Class weights: {class_weight_dict}")
        
        # Hyperparameter optimization
        logger.info("🔧 Optimizing hyperparameters...")
        
        param_grid = {
            'n_estimators': [150, 200, 300],
            'max_depth': [10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None]
        }
        
        rf = RandomForestClassifier(
            random_state=42,
            class_weight=class_weight_dict,
            n_jobs=-1
        )
        
        # Grid search with cross-validation
        grid_search = GridSearchCV(
            rf, param_grid, 
            cv=5, 
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train_scaled, y_train)
        
        # Best model
        best_model = grid_search.best_estimator_
        
        # Evaluate on test set
        y_pred = best_model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation score
        cv_scores = cross_val_score(best_model, X_train_scaled, y_train, cv=5)
        
        logger.info(f"✅ Test Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
        logger.info(f"✅ CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        logger.info(f"🎯 Best Parameters: {grid_search.best_params_}")
        
        # Detailed classification report
        class_report = classification_report(y_test, y_pred, output_dict=True)
        logger.info("📊 Classification Report:")
        for class_name in self.target_classes:
            if class_name in class_report:
                metrics = class_report[class_name]
                logger.info(f"   {class_name}: P={metrics['precision']:.3f}, R={metrics['recall']:.3f}, F1={metrics['f1-score']:.3f}")
        
        # Feature importance analysis
        feature_importance = best_model.feature_importances_
        feature_importance_df = pd.DataFrame({
            'feature': self.expected_features,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        logger.info("🔍 Top 10 Most Important Features:")
        for i, row in feature_importance_df.head(10).iterrows():
            logger.info(f"   {row['feature']}: {row['importance']:.4f}")
        
        # Save models and metadata
        model_data = {
            'model': best_model,
            'scaler': scaler,
            'accuracy': accuracy,
            'cv_scores': cv_scores.tolist(),
            'best_params': grid_search.best_params_,
            'class_report': class_report,
            'feature_importance': feature_importance_df.to_dict('records'),
            'training_timestamp': datetime.now().isoformat(),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        # Save models
        self._save_trained_models(model_data)
        
        # Generate evaluation plots
        self._generate_evaluation_plots(y_test, y_pred, feature_importance_df, accuracy)
        
        return model_data

    def _save_trained_models(self, model_data: Dict):
        """Save trained models and metadata"""
        
        # Save main model
        joblib.dump(model_data['model'], os.path.join(self.model_path, 'pattern_classifier.pkl'))
        joblib.dump(model_data['scaler'], os.path.join(self.model_path, 'scaler.pkl'))
        
        # Save metadata
        metadata = {
            'accuracy': model_data['accuracy'],
            'cv_scores': model_data['cv_scores'],
            'best_params': model_data['best_params'],
            'class_report': model_data['class_report'],
            'feature_importance': model_data['feature_importance'],
            'training_timestamp': model_data['training_timestamp'],
            'training_samples': model_data['training_samples'],
            'test_samples': model_data['test_samples'],
            'target_classes': self.target_classes,
            'features': self.expected_features
        }
        
        with open(os.path.join(self.model_path, 'model_info.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"💾 Models saved to {self.model_path}")

    def _generate_evaluation_plots(self, y_test, y_pred, feature_importance_df, accuracy):
        """Generate evaluation plots"""
        
        try:
            # Confusion Matrix
            plt.figure(figsize=(10, 8))
            cm = confusion_matrix(y_test, y_pred, labels=self.target_classes)
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                       xticklabels=self.target_classes, yticklabels=self.target_classes)
            plt.title(f'Confusion Matrix (Accuracy: {accuracy:.1%})')
            plt.ylabel('True Label')
            plt.xlabel('Predicted Label')
            plt.tight_layout()
            plt.savefig(os.path.join(self.model_path, 'evaluation', 'confusion_matrix.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
            # Feature Importance
            plt.figure(figsize=(12, 8))
            top_features = feature_importance_df.head(15)
            plt.barh(range(len(top_features)), top_features['importance'])
            plt.yticks(range(len(top_features)), top_features['feature'])
            plt.xlabel('Feature Importance')
            plt.title('Top 15 Feature Importances')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.savefig(os.path.join(self.model_path, 'evaluation', 'feature_importance.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("📊 Evaluation plots saved")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not generate plots: {e}")

    def run_comprehensive_training(self, num_samples: int = 5000) -> Dict[str, Any]:
        """
        Run complete training pipeline for >80% accuracy
        """
        logger.info("🎯 Starting comprehensive training for >80% accuracy...")
        
        # Step 1: Generate extensive training data
        features_df, labels_df = self.generate_extensive_training_data(num_samples)
        
        # Step 2: Save training data
        training_data_path = os.path.join(self.model_path, "training_data")
        features_df.to_csv(os.path.join(training_data_path, "features.csv"), index=False)
        labels_df.to_csv(os.path.join(training_data_path, "labels.csv"), index=False)
        logger.info(f"💾 Training data saved to {training_data_path}")
        
        # Step 3: Train high-accuracy model
        model_data = self.train_high_accuracy_model(features_df, labels_df)
        
        # Step 4: Final validation
        if model_data['accuracy'] >= 0.80:
            logger.info(f"🎉 SUCCESS! Achieved {model_data['accuracy']:.1%} accuracy (>80% target)")
        else:
            logger.warning(f"⚠️ Accuracy {model_data['accuracy']:.1%} below 80% target")
            logger.info("💡 Suggestions for improvement:")
            logger.info("   - Increase training data size")
            logger.info("   - Add more edge cases")
            logger.info("   - Tune hyperparameters further")
            logger.info("   - Add more feature engineering")
        
        return model_data

def main():
    """
    Main training function
    """
    print("🚀 Comprehensive ML Training for >80% Accuracy")
    print("=" * 60)
    
    # Initialize trainer
    trainer = ComprehensiveMLTrainer()
    
    # Run comprehensive training
    model_data = trainer.run_comprehensive_training(num_samples=8000)  # Large dataset
    
    print(f"\n{'=' * 60}")
    print("🎉 TRAINING COMPLETED")
    print("=" * 60)
    
    print(f"📊 Final Results:")
    print(f"   - Test Accuracy: {model_data['accuracy']:.1%}")
    print(f"   - CV Accuracy: {np.mean(model_data['cv_scores']):.1%} ± {np.std(model_data['cv_scores']):.1%}")
    print(f"   - Training Samples: {model_data['training_samples']:,}")
    print(f"   - Test Samples: {model_data['test_samples']:,}")
    
    print(f"\n🎯 Target Achievement:")
    if model_data['accuracy'] >= 0.80:
        print("   ✅ SUCCESS: >80% accuracy achieved!")
    else:
        print("   ❌ Target not reached - consider additional training")
    
    print(f"\n📁 Files Generated:")
    print(f"   - Models: app/ml/data_feed/pattern_classifier.pkl")
    print(f"   - Scaler: app/ml/data_feed/scaler.pkl")
    print(f"   - Metadata: app/ml/data_feed/model_info.json")
    print(f"   - Training Data: app/ml/data_feed/training_data/")
    print(f"   - Evaluation: app/ml/data_feed/evaluation/")

if __name__ == "__main__":
    main()