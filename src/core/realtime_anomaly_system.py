#!/usr/bin/env python3
"""
Real-Time Anomaly Detection & Enterprise Integration System
Advanced real-time anomaly detection with ML models and enterprise integrations
for ITSM, monitoring, and business intelligence platforms.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import numpy as np
import pandas as pd

# Real-time Processing
import asyncio
from asyncio import Queue
import websockets
from kafka import KafkaProducer, KafkaConsumer
import redis
import aioredis

# ML for Anomaly Detection
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM
import torch
import torch.nn as nn
from pyod.models.knn import KNN
from pyod.models.lof import LOF
from pyod.models.auto_encoder import AutoEncoder

# Time Series Analysis
from prophet import Prophet
import statsmodels.api as sm
from scipy import stats
import ruptures as rpt

# Enterprise Integrations
import requests
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from azure.servicebus.aio import ServiceBusClient
from azure.storage.queue.aio import QueueClient
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Monitoring & Observability
import structlog
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace

# Utilities
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

logger = structlog.get_logger()

# Metrics
ANOMALIES_DETECTED = Counter('anomalies_detected_total', 'Total anomalies detected', ['type', 'severity'])
ANOMALY_DETECTION_DURATION = Histogram('anomaly_detection_duration_seconds', 'Anomaly detection duration')
INTEGRATION_REQUESTS = Counter('integration_requests_total', 'Integration requests', ['service', 'status'])
REAL_TIME_EVENTS = Counter('realtime_events_total', 'Real-time events processed', ['event_type'])

class AnomalyType(str, Enum):
    COST_SPIKE = "cost_spike"
    RESOURCE_WASTE = "resource_waste"
    UNUSUAL_PATTERN = "unusual_pattern"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_ANOMALY = "security_anomaly"
    CAPACITY_ANOMALY = "capacity_anomaly"
    NETWORK_ANOMALY = "network_anomaly"

class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IntegrationType(str, Enum):
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SERVICENOW = "servicenow"
    JIRA = "jira"
    PAGERDUTY = "pagerduty"
    DATADOG = "datadog"
    SPLUNK = "splunk"

@dataclass
class Anomaly:
    """Anomaly detection result."""
    anomaly_id: str
    type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    cluster_id: str
    resource: Optional[str]
    metric_name: str
    metric_value: float
    baseline_value: float
    deviation_score: float
    confidence: float
    timestamp: datetime
    context: Dict[str, Any]
    suggested_actions: List[str]
    estimated_impact: Dict[str, Any]

@dataclass
class IntegrationConfig:
    """Configuration for enterprise integrations."""
    type: IntegrationType
    name: str
    enabled: bool
    config: Dict[str, Any]
    filters: Dict[str, Any]
    retry_config: Dict[str, Any]

class AdvancedAnomalyDetector:
    """Advanced multi-model anomaly detection system."""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.baselines = {}
        self.model_weights = {}
        self.detection_history = []
        
    async def initialize_models(self):
        """Initialize multiple anomaly detection models."""
        try:
            logger.info("Initializing anomaly detection models")
            
            # Statistical models
            self.models['isolation_forest'] = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_jobs=-1
            )
            
            self.models['one_class_svm'] = OneClassSVM(
                kernel='rbf',
                gamma='scale',
                nu=0.1
            )
            
            # Proximity-based models
            self.models['knn'] = KNN(contamination=0.1)
            self.models['lof'] = LOF(contamination=0.1)
            
            # Neural network models
            self.models['autoencoder'] = self._create_autoencoder()
            self.models['lstm_ae'] = self._create_lstm_autoencoder()
            
            # Ensemble weights
            self.model_weights = {
                'isolation_forest': 0.2,
                'one_class_svm': 0.15,
                'knn': 0.15,
                'lof': 0.15,
                'autoencoder': 0.25,
                'lstm_ae': 0.1
            }
            
            logger.info("Anomaly detection models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize anomaly detection models: {e}")
            raise
    
    def _create_autoencoder(self) -> tf.keras.Model:
        """Create autoencoder for anomaly detection."""
        input_dim = 20  # Adjust based on feature count
        
        # Encoder
        input_layer = Input(shape=(input_dim,))
        encoded = Dense(16, activation='relu')(input_layer)
        encoded = Dense(8, activation='relu')(encoded)
        encoded = Dense(4, activation='relu')(encoded)
        
        # Decoder
        decoded = Dense(8, activation='relu')(encoded)
        decoded = Dense(16, activation='relu')(decoded)
        decoded = Dense(input_dim, activation='sigmoid')(decoded)
        
        autoencoder = Model(input_layer, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')
        
        return autoencoder
    
    def _create_lstm_autoencoder(self) -> tf.keras.Model:
        """Create LSTM autoencoder for time series anomaly detection."""
        timesteps = 10
        features = 5
        
        # Encoder
        inputs = Input(shape=(timesteps, features))
        encoded = LSTM(50, activation='relu', return_sequences=True)(inputs)
        encoded = LSTM(25, activation='relu', return_sequences=False)(encoded)
        
        # Decoder
        decoded = Dense(25, activation='relu')(encoded)
        decoded = tf.keras.layers.RepeatVector(timesteps)(decoded)
        decoded = LSTM(25, activation='relu', return_sequences=True)(decoded)
        decoded = LSTM(50, activation='relu', return_sequences=True)(decoded)
        decoded = tf.keras.layers.TimeDistributed(Dense(features))(decoded)
        
        model = Model(inputs, decoded)
        model.compile(optimizer='adam', loss='mse')
        
        return model
    
    async def detect_anomalies(self, data: pd.DataFrame, 
                             context: Dict[str, Any]) -> List[Anomaly]:
        """Detect anomalies using ensemble of models."""
        try:
            anomalies = []
            
            with ANOMALY_DETECTION_DURATION.time():
                # Prepare data
                processed_data = await self._preprocess_data(data)
                
                # Statistical anomaly detection
                stat_anomalies = await self._detect_statistical_anomalies(processed_data, context)
                anomalies.extend(stat_anomalies)
                
                # ML-based anomaly detection
                ml_anomalies = await self._detect_ml_anomalies(processed_data, context)
                anomalies.extend(ml_anomalies)
                
                # Time series anomaly detection
                ts_anomalies = await self._detect_time_series_anomalies(data, context)
                anomalies.extend(ts_anomalies)
                
                # Business rule-based anomalies
                rule_anomalies = await self._detect_rule_based_anomalies(data, context)
                anomalies.extend(rule_anomalies)
                
                # Ensemble scoring and filtering
                filtered_anomalies = await self._filter_and_score_anomalies(anomalies)
                
                # Update detection history
                self.detection_history.extend(filtered_anomalies)
                
                # Keep only recent history
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                self.detection_history = [
                    a for a in self.detection_history 
                    if a.timestamp > cutoff_time
                ]
                
                # Update metrics
                for anomaly in filtered_anomalies:
                    ANOMALIES_DETECTED.labels(
                        type=anomaly.type.value,
                        severity=anomaly.severity.value
                    ).inc()
                
                logger.info(f"Detected {len(filtered_anomalies)} anomalies")
                return filtered_anomalies
                
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []
    
    async def _preprocess_data(self, data: pd.DataFrame) -> np.ndarray:
        """Preprocess data for anomaly detection."""
        try:
            # Handle missing values
            data_filled = data.fillna(data.mean())
            
            # Select numeric columns
            numeric_data = data_filled.select_dtypes(include=[np.number])
            
            # Scale features
            scaler = RobustScaler()
            scaled_data = scaler.fit_transform(numeric_data)
            
            return scaled_data
            
        except Exception as e:
            logger.error(f"Data preprocessing failed: {e}")
            return np.array([])
    
    async def _detect_statistical_anomalies(self, data: np.ndarray, 
                                           context: Dict[str, Any]) -> List[Anomaly]:
        """Detect anomalies using statistical methods."""
        anomalies = []
        
        try:
            if len(data) == 0:
                return anomalies
            
            # Z-score based detection
            z_scores = np.abs(stats.zscore(data, axis=0))
            threshold = 3.0
            
            outlier_indices = np.where(np.any(z_scores > threshold, axis=1))[0]
            
            for idx in outlier_indices:
                anomaly = Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    type=AnomalyType.UNUSUAL_PATTERN,
                    severity=self._calculate_severity(z_scores[idx].max()),
                    title="Statistical Anomaly Detected",
                    description=f"Data point deviates significantly from normal distribution (Z-score: {z_scores[idx].max():.2f})",
                    cluster_id=context.get('cluster_id', 'unknown'),
                    resource=context.get('resource'),
                    metric_name="statistical_deviation",
                    metric_value=float(data[idx].mean()),
                    baseline_value=float(data.mean()),
                    deviation_score=float(z_scores[idx].max()),
                    confidence=min(0.99, z_scores[idx].max() / 5.0),
                    timestamp=datetime.utcnow(),
                    context=context,
                    suggested_actions=[
                        "Investigate the cause of statistical deviation",
                        "Check for data quality issues",
                        "Review recent changes to the system"
                    ],
                    estimated_impact={
                        "cost_impact": "unknown",
                        "performance_impact": "medium"
                    }
                )
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Statistical anomaly detection failed: {e}")
            return []
    
    async def _detect_ml_anomalies(self, data: np.ndarray, 
                                 context: Dict[str, Any]) -> List[Anomaly]:
        """Detect anomalies using ML models."""
        anomalies = []
        
        try:
            if len(data) == 0:
                return anomalies
            
            ensemble_scores = np.zeros(len(data))
            
            # Isolation Forest
            if 'isolation_forest' in self.models:
                try:
                    self.models['isolation_forest'].fit(data)
                    if_scores = self.models['isolation_forest'].decision_function(data)
                    if_outliers = self.models['isolation_forest'].predict(data)
                    
                    # Normalize scores to 0-1
                    if_scores_norm = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min() + 1e-8)
                    ensemble_scores += self.model_weights['isolation_forest'] * (1 - if_scores_norm)
                    
                except Exception as e:
                    logger.warning(f"Isolation Forest failed: {e}")
            
            # One-Class SVM
            if 'one_class_svm' in self.models:
                try:
                    self.models['one_class_svm'].fit(data)
                    svm_scores = self.models['one_class_svm'].decision_function(data)
                    
                    # Normalize scores
                    svm_scores_norm = (svm_scores - svm_scores.min()) / (svm_scores.max() - svm_scores.min() + 1e-8)
                    ensemble_scores += self.model_weights['one_class_svm'] * (1 - svm_scores_norm)
                    
                except Exception as e:
                    logger.warning(f"One-Class SVM failed: {e}")
            
            # KNN
            if 'knn' in self.models:
                try:
                    self.models['knn'].fit(data)
                    knn_scores = self.models['knn'].decision_scores_
                    
                    # Normalize scores
                    knn_scores_norm = (knn_scores - knn_scores.min()) / (knn_scores.max() - knn_scores.min() + 1e-8)
                    ensemble_scores += self.model_weights['knn'] * knn_scores_norm
                    
                except Exception as e:
                    logger.warning(f"KNN failed: {e}")
            
            # Find anomalies based on ensemble scores
            threshold = np.percentile(ensemble_scores, 95)  # Top 5% as anomalies
            anomaly_indices = np.where(ensemble_scores > threshold)[0]
            
            for idx in anomaly_indices:
                anomaly = Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    type=AnomalyType.UNUSUAL_PATTERN,
                    severity=self._calculate_severity(ensemble_scores[idx]),
                    title="ML-Detected Anomaly",
                    description=f"Machine learning models detected unusual behavior (Ensemble score: {ensemble_scores[idx]:.3f})",
                    cluster_id=context.get('cluster_id', 'unknown'),
                    resource=context.get('resource'),
                    metric_name="ml_anomaly_score",
                    metric_value=float(ensemble_scores[idx]),
                    baseline_value=float(np.median(ensemble_scores)),
                    deviation_score=float(ensemble_scores[idx]),
                    confidence=min(0.99, ensemble_scores[idx]),
                    timestamp=datetime.utcnow(),
                    context=context,
                    suggested_actions=[
                        "Analyze the anomalous data point",
                        "Check for system changes or events",
                        "Review resource utilization patterns"
                    ],
                    estimated_impact={
                        "cost_impact": "medium",
                        "performance_impact": "medium"
                    }
                )
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"ML anomaly detection failed: {e}")
            return []
    
    async def _detect_time_series_anomalies(self, data: pd.DataFrame, 
                                          context: Dict[str, Any]) -> List[Anomaly]:
        """Detect time series anomalies."""
        anomalies = []
        
        try:
            if 'timestamp' not in data.columns or len(data) < 10:
                return anomalies
            
            # Prepare time series data
            ts_data = data.set_index('timestamp').select_dtypes(include=[np.number])
            
            for column in ts_data.columns:
                try:
                    # Change point detection
                    values = ts_data[column].fillna(ts_data[column].mean()).values
                    
                    if len(values) < 5:
                        continue
                    
                    # Use ruptures for change point detection
                    algo = rpt.Pelt(model="rbf").fit(values)
                    change_points = algo.predict(pen=10)
                    
                    # Check for significant changes
                    for i, cp in enumerate(change_points[:-1]):
                        if i == 0:
                            segment_before = values[:cp]
                        else:
                            segment_before = values[change_points[i-1]:cp]
                        
                        if i+1 < len(change_points):
                            segment_after = values[cp:change_points[i+1]]
                        else:
                            segment_after = values[cp:]
                        
                        if len(segment_before) > 0 and len(segment_after) > 0:
                            # Check for significant change
                            before_mean = np.mean(segment_before)
                            after_mean = np.mean(segment_after)
                            
                            if before_mean > 0:
                                change_ratio = abs(after_mean - before_mean) / before_mean
                                
                                if change_ratio > 0.3:  # 30% change threshold
                                    severity = AnomalySeverity.HIGH if change_ratio > 0.8 else AnomalySeverity.MEDIUM
                                    
                                    anomaly = Anomaly(
                                        anomaly_id=str(uuid.uuid4()),
                                        type=AnomalyType.COST_SPIKE if after_mean > before_mean else AnomalyType.UNUSUAL_PATTERN,
                                        severity=severity,
                                        title=f"Significant Change Point in {column}",
                                        description=f"Detected {change_ratio*100:.1f}% change in {column} at time series position {cp}",
                                        cluster_id=context.get('cluster_id', 'unknown'),
                                        resource=context.get('resource'),
                                        metric_name=column,
                                        metric_value=float(after_mean),
                                        baseline_value=float(before_mean),
                                        deviation_score=float(change_ratio),
                                        confidence=min(0.99, change_ratio * 2),
                                        timestamp=datetime.utcnow(),
                                        context=context,
                                        suggested_actions=[
                                            f"Investigate the cause of the {change_ratio*100:.1f}% change in {column}",
                                            "Check for configuration changes or deployments",
                                            "Review system events around the change point"
                                        ],
                                        estimated_impact={
                                            "cost_impact": "high" if change_ratio > 0.5 else "medium",
                                            "performance_impact": "medium"
                                        }
                                    )
                                    anomalies.append(anomaly)
                
                except Exception as e:
                    logger.warning(f"Time series analysis failed for column {column}: {e}")
                    continue
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Time series anomaly detection failed: {e}")
            return []
    
    async def _detect_rule_based_anomalies(self, data: pd.DataFrame, 
                                         context: Dict[str, Any]) -> List[Anomaly]:
        """Detect anomalies based on business rules."""
        anomalies = []
        
        try:
            # Cost spike detection
            if 'daily_cost' in data.columns:
                costs = data['daily_cost'].dropna()
                if len(costs) > 1:
                    cost_increase = costs.pct_change().fillna(0)
                    spike_threshold = 0.5  # 50% increase
                    
                    spikes = cost_increase[cost_increase > spike_threshold]
                    for idx, spike_value in spikes.items():
                        anomaly = Anomaly(
                            anomaly_id=str(uuid.uuid4()),
                            type=AnomalyType.COST_SPIKE,
                            severity=AnomalySeverity.HIGH if spike_value > 1.0 else AnomalySeverity.MEDIUM,
                            title="Cost Spike Detected",
                            description=f"Daily cost increased by {spike_value*100:.1f}%",
                            cluster_id=context.get('cluster_id', 'unknown'),
                            resource=context.get('resource'),
                            metric_name="daily_cost",
                            metric_value=float(costs.loc[idx]),
                            baseline_value=float(costs.mean()),
                            deviation_score=float(spike_value),
                            confidence=0.95,
                            timestamp=datetime.utcnow(),
                            context=context,
                            suggested_actions=[
                                "Review recent resource provisioning",
                                "Check for auto-scaling events",
                                "Analyze workload changes"
                            ],
                            estimated_impact={
                                "cost_impact": f"${costs.loc[idx] - costs.mean():.2f} per day",
                                "performance_impact": "unknown"
                            }
                        )
                        anomalies.append(anomaly)
            
            # Resource waste detection
            cpu_util = data.get('cpu_utilization', pd.Series())
            memory_util = data.get('memory_utilization', pd.Series())
            
            if not cpu_util.empty and not memory_util.empty:
                low_utilization = (cpu_util < 10) & (memory_util < 10)
                
                if low_utilization.any():
                    anomaly = Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        type=AnomalyType.RESOURCE_WASTE,
                        severity=AnomalySeverity.MEDIUM,
                        title="Resource Waste Detected",
                        description=f"Low resource utilization detected: CPU {cpu_util.mean():.1f}%, Memory {memory_util.mean():.1f}%",
                        cluster_id=context.get('cluster_id', 'unknown'),
                        resource=context.get('resource'),
                        metric_name="resource_utilization",
                        metric_value=float((cpu_util.mean() + memory_util.mean()) / 2),
                        baseline_value=50.0,  # Expected baseline
                        deviation_score=float(50.0 - (cpu_util.mean() + memory_util.mean()) / 2),
                        confidence=0.90,
                        timestamp=datetime.utcnow(),
                        context=context,
                        suggested_actions=[
                            "Consider right-sizing resources",
                            "Implement auto-scaling",
                            "Review resource requests and limits"
                        ],
                        estimated_impact={
                            "cost_impact": "high",
                            "performance_impact": "low"
                        }
                    )
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Rule-based anomaly detection failed: {e}")
            return []
    
    async def _filter_and_score_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """Filter and score anomalies to reduce false positives."""
        try:
            if not anomalies:
                return []
            
            # Remove duplicates based on similarity
            filtered_anomalies = []
            
            for anomaly in anomalies:
                is_duplicate = False
                
                for existing in filtered_anomalies:
                    # Check for similarity
                    if (anomaly.type == existing.type and
                        anomaly.cluster_id == existing.cluster_id and
                        anomaly.resource == existing.resource and
                        abs(anomaly.metric_value - existing.metric_value) < 0.1 * existing.metric_value):
                        
                        # Keep the one with higher confidence
                        if anomaly.confidence > existing.confidence:
                            filtered_anomalies.remove(existing)
                            filtered_anomalies.append(anomaly)
                        
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    filtered_anomalies.append(anomaly)
            
            # Score anomalies based on business impact
            for anomaly in filtered_anomalies:
                business_score = self._calculate_business_impact_score(anomaly)
                anomaly.confidence = min(0.99, anomaly.confidence * business_score)
            
            # Filter by minimum confidence threshold
            high_confidence_anomalies = [
                a for a in filtered_anomalies 
                if a.confidence >= 0.7
            ]
            
            # Sort by severity and confidence
            sorted_anomalies = sorted(
                high_confidence_anomalies,
                key=lambda x: (
                    ['low', 'medium', 'high', 'critical'].index(x.severity.value),
                    x.confidence
                ),
                reverse=True
            )
            
            return sorted_anomalies
            
        except Exception as e:
            logger.error(f"Anomaly filtering failed: {e}")
            return anomalies
    
    def _calculate_severity(self, score: float) -> AnomalySeverity:
        """Calculate severity based on anomaly score."""
        if score > 0.9:
            return AnomalySeverity.CRITICAL
        elif score > 0.7:
            return AnomalySeverity.HIGH
        elif score > 0.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_business_impact_score(self, anomaly: Anomaly) -> float:
        """Calculate business impact score for anomaly."""
        try:
            base_score = 1.0
            
            # Adjust based on anomaly type
            type_weights = {
                AnomalyType.COST_SPIKE: 1.2,
                AnomalyType.RESOURCE_WASTE: 1.1,
                AnomalyType.PERFORMANCE_DEGRADATION: 1.3,
                AnomalyType.SECURITY_ANOMALY: 1.5,
                AnomalyType.CAPACITY_ANOMALY: 1.2,
                AnomalyType.UNUSUAL_PATTERN: 0.8,
                AnomalyType.NETWORK_ANOMALY: 1.0
            }
            
            base_score *= type_weights.get(anomaly.type, 1.0)
            
            # Adjust based on deviation magnitude
            if anomaly.deviation_score > 2.0:
                base_score *= 1.2
            elif anomaly.deviation_score < 0.5:
                base_score *= 0.8
            
            return min(1.5, base_score)
            
        except Exception:
            return 1.0

class RealTimeEventProcessor:
    """Real-time event processing system."""
    
    def __init__(self):
        self.event_queue = Queue()
        self.anomaly_detector = AdvancedAnomalyDetector()
        self.integration_manager = EnterpriseIntegrationManager()
        self.processing_active = False
        
    async def start_processing(self):
        """Start real-time event processing."""
        try:
            logger.info("Starting real-time event processor")
            
            # Initialize anomaly detector
            await self.anomaly_detector.initialize_models()
            
            self.processing_active = True
            
            # Start processing tasks
            tasks = [
                asyncio.create_task(self._process_events()),
                asyncio.create_task(self._monitor_health()),
            ]
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Real-time processor failed to start: {e}")
            raise
    
    async def stop_processing(self):
        """Stop real-time event processing."""
        self.processing_active = False
        logger.info("Real-time event processor stopped")
    
    async def ingest_event(self, event: Dict[str, Any]):
        """Ingest event for real-time processing."""
        try:
            await self.event_queue.put(event)
            REAL_TIME_EVENTS.labels(event_type=event.get('type', 'unknown')).inc()
            
        except Exception as e:
            logger.error(f"Failed to ingest event: {e}")
    
    async def _process_events(self):
        """Process events from the queue."""
        while self.processing_active:
            try:
                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process event
                await self._process_single_event(event)
                
            except Exception as e:
                logger.error(f"Event processing error: {e}")
                await asyncio.sleep(1)
    
    async def _process_single_event(self, event: Dict[str, Any]):
        """Process a single event."""
        try:
            event_type = event.get('type', 'unknown')
            
            if event_type == 'metrics_update':
                await self._process_metrics_event(event)
            elif event_type == 'cost_update':
                await self._process_cost_event(event)
            elif event_type == 'alert':
                await self._process_alert_event(event)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Failed to process event: {e}")
    
    async def _process_metrics_event(self, event: Dict[str, Any]):
        """Process metrics update event."""
        try:
            metrics_data = event.get('data', {})
            context = event.get('context', {})
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame([metrics_data])
            
            # Detect anomalies
            anomalies = await self.anomaly_detector.detect_anomalies(df, context)
            
            # Send notifications for anomalies
            for anomaly in anomalies:
                await self.integration_manager.send_anomaly_notification(anomaly)
                
        except Exception as e:
            logger.error(f"Failed to process metrics event: {e}")
    
    async def _process_cost_event(self, event: Dict[str, Any]):
        """Process cost update event."""
        try:
            cost_data = event.get('data', {})
            context = event.get('context', {})
            
            # Check for cost spikes
            current_cost = cost_data.get('current_cost', 0)
            previous_cost = cost_data.get('previous_cost', 0)
            
            if previous_cost > 0:
                cost_change = (current_cost - previous_cost) / previous_cost
                
                if cost_change > 0.3:  # 30% increase
                    anomaly = Anomaly(
                        anomaly_id=str(uuid.uuid4()),
                        type=AnomalyType.COST_SPIKE,
                        severity=AnomalySeverity.HIGH if cost_change > 0.8 else AnomalySeverity.MEDIUM,
                        title="Real-time Cost Spike",
                        description=f"Cost increased by {cost_change*100:.1f}%",
                        cluster_id=context.get('cluster_id', 'unknown'),
                        resource=context.get('resource'),
                        metric_name="cost",
                        metric_value=current_cost,
                        baseline_value=previous_cost,
                        deviation_score=cost_change,
                        confidence=0.95,
                        timestamp=datetime.utcnow(),
                        context=context,
                        suggested_actions=[
                            "Investigate recent changes",
                            "Check auto-scaling events",
                            "Review resource provisioning"
                        ],
                        estimated_impact={
                            "cost_impact": f"${current_cost - previous_cost:.2f}",
                            "performance_impact": "unknown"
                        }
                    )
                    
                    await self.integration_manager.send_anomaly_notification(anomaly)
                    
        except Exception as e:
            logger.error(f"Failed to process cost event: {e}")
    
    async def _process_alert_event(self, event: Dict[str, Any]):
        """Process alert event."""
        try:
            alert_data = event.get('data', {})
            
            # Forward alert to integrations
            await self.integration_manager.forward_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Failed to process alert event: {e}")
    
    async def _monitor_health(self):
        """Monitor processor health."""
        while self.processing_active:
            try:
                queue_size = self.event_queue.qsize()
                
                if queue_size > 1000:
                    logger.warning(f"Event queue size is high: {queue_size}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)

class EnterpriseIntegrationManager:
    """Manager for enterprise integrations."""
    
    def __init__(self):
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.client_session = None
        
    async def initialize(self):
        """Initialize integration manager."""
        self.client_session = aiohttp.ClientSession()
        await self._load_integration_configs()
        
    async def shutdown(self):
        """Shutdown integration manager."""
        if self.client_session:
            await self.client_session.close()
    
    async def _load_integration_configs(self):
        """Load integration configurations."""
        try:
            # Load from environment or configuration file
            configs = [
                IntegrationConfig(
                    type=IntegrationType.SLACK,
                    name="slack_alerts",
                    enabled=bool(os.getenv('SLACK_WEBHOOK_URL')),
                    config={
                        'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                        'channel': os.getenv('SLACK_CHANNEL', '#alerts'),
                        'username': 'AKS Intelligence Bot'
                    },
                    filters={'severity': ['high', 'critical']},
                    retry_config={'max_retries': 3, 'backoff_factor': 2}
                ),
                IntegrationConfig(
                    type=IntegrationType.EMAIL,
                    name="email_alerts",
                    enabled=bool(os.getenv('SMTP_SERVER')),
                    config={
                        'smtp_server': os.getenv('SMTP_SERVER'),
                        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                        'username': os.getenv('SMTP_USERNAME'),
                        'password': os.getenv('SMTP_PASSWORD'),
                        'recipients': os.getenv('ALERT_RECIPIENTS', '').split(',')
                    },
                    filters={'severity': ['critical']},
                    retry_config={'max_retries': 2, 'backoff_factor': 1}
                ),
                IntegrationConfig(
                    type=IntegrationType.WEBHOOK,
                    name="custom_webhook",
                    enabled=bool(os.getenv('CUSTOM_WEBHOOK_URL')),
                    config={
                        'url': os.getenv('CUSTOM_WEBHOOK_URL'),
                        'headers': {'Content-Type': 'application/json'},
                        'auth_token': os.getenv('WEBHOOK_AUTH_TOKEN')
                    },
                    filters={},
                    retry_config={'max_retries': 3, 'backoff_factor': 2}
                )
            ]
            
            for config in configs:
                if config.enabled:
                    self.integrations[config.name] = config
                    
            logger.info(f"Loaded {len(self.integrations)} integration configurations")
            
        except Exception as e:
            logger.error(f"Failed to load integration configs: {e}")
    
    async def send_anomaly_notification(self, anomaly: Anomaly):
        """Send anomaly notification to all configured integrations."""
        try:
            tasks = []
            
            for integration_name, integration in self.integrations.items():
                # Check filters
                if self._should_send_notification(anomaly, integration):
                    task = asyncio.create_task(
                        self._send_to_integration(anomaly, integration)
                    )
                    tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Failed to send anomaly notification: {e}")
    
    def _should_send_notification(self, anomaly: Anomaly, integration: IntegrationConfig) -> bool:
        """Check if notification should be sent based on filters."""
        try:
            filters = integration.filters
            
            # Check severity filter
            if 'severity' in filters:
                if anomaly.severity.value not in filters['severity']:
                    return False
            
            # Check type filter
            if 'type' in filters:
                if anomaly.type.value not in filters['type']:
                    return False
            
            # Check cluster filter
            if 'cluster_id' in filters:
                if anomaly.cluster_id not in filters['cluster_id']:
                    return False
            
            return True
            
        except Exception:
            return True  # Send by default if filter check fails
    
    async def _send_to_integration(self, anomaly: Anomaly, integration: IntegrationConfig):
        """Send notification to specific integration."""
        try:
            if integration.type == IntegrationType.SLACK:
                await self._send_slack_notification(anomaly, integration)
            elif integration.type == IntegrationType.EMAIL:
                await self._send_email_notification(anomaly, integration)
            elif integration.type == IntegrationType.WEBHOOK:
                await self._send_webhook_notification(anomaly, integration)
            elif integration.type == IntegrationType.TEAMS:
                await self._send_teams_notification(anomaly, integration)
            else:
                logger.warning(f"Unsupported integration type: {integration.type}")
                
            INTEGRATION_REQUESTS.labels(service=integration.type.value, status="success").inc()
            
        except Exception as e:
            logger.error(f"Failed to send to {integration.name}: {e}")
            INTEGRATION_REQUESTS.labels(service=integration.type.value, status="error").inc()
    
    async def _send_slack_notification(self, anomaly: Anomaly, integration: IntegrationConfig):
        """Send notification to Slack."""
        webhook_url = integration.config.get('webhook_url')
        if not webhook_url:
            return
        
        # Build Slack message
        color = {
            AnomalySeverity.LOW: "#36a64f",      # Green
            AnomalySeverity.MEDIUM: "#ffaa00",   # Orange
            AnomalySeverity.HIGH: "#ff0000",     # Red
            AnomalySeverity.CRITICAL: "#800080"  # Purple
        }.get(anomaly.severity, "#cccccc")
        
        payload = {
            "username": integration.config.get('username', 'AKS Intelligence'),
            "channel": integration.config.get('channel', '#alerts'),
            "attachments": [{
                "color": color,
                "title": f"🚨 {anomaly.title}",
                "text": anomaly.description,
                "fields": [
                    {
                        "title": "Cluster",
                        "value": anomaly.cluster_id,
                        "short": True
                    },
                    {
                        "title": "Severity",
                        "value": anomaly.severity.value.upper(),
                        "short": True
                    },
                    {
                        "title": "Metric",
                        "value": f"{anomaly.metric_name}: {anomaly.metric_value:.2f}",
                        "short": True
                    },
                    {
                        "title": "Confidence",
                        "value": f"{anomaly.confidence*100:.1f}%",
                        "short": True
                    }
                ],
                "actions": [
                    {
                        "type": "button",
                        "text": "View Details",
                        "url": f"https://your-dashboard.com/anomalies/{anomaly.anomaly_id}"
                    }
                ],
                "footer": "AKS Cost Intelligence",
                "ts": int(anomaly.timestamp.timestamp())
            }]
        }
        
        async with self.client_session.post(webhook_url, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Slack webhook failed: {response.status}")
    
    async def _send_email_notification(self, anomaly: Anomaly, integration: IntegrationConfig):
        """Send email notification."""
        config = integration.config
        recipients = config.get('recipients', [])
        
        if not recipients:
            return
        
        # Build email
        subject = f"AKS Alert: {anomaly.title} - {anomaly.severity.value.upper()}"
        
        html_body = f"""
        <html>
        <body>
        <h2 style="color: {'red' if anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL] else 'orange'}">
            {anomaly.title}
        </h2>
        
        <p><strong>Description:</strong> {anomaly.description}</p>
        
        <table border="1" style="border-collapse: collapse;">
        <tr><td><strong>Cluster ID</strong></td><td>{anomaly.cluster_id}</td></tr>
        <tr><td><strong>Severity</strong></td><td>{anomaly.severity.value.upper()}</td></tr>
        <tr><td><strong>Type</strong></td><td>{anomaly.type.value}</td></tr>
        <tr><td><strong>Metric</strong></td><td>{anomaly.metric_name}</td></tr>
        <tr><td><strong>Value</strong></td><td>{anomaly.metric_value:.2f}</td></tr>
        <tr><td><strong>Baseline</strong></td><td>{anomaly.baseline_value:.2f}</td></tr>
        <tr><td><strong>Confidence</strong></td><td>{anomaly.confidence*100:.1f}%</td></tr>
        <tr><td><strong>Timestamp</strong></td><td>{anomaly.timestamp}</td></tr>
        </table>
        
        <h3>Suggested Actions:</h3>
        <ul>
        {"".join(f"<li>{action}</li>" for action in anomaly.suggested_actions)}
        </ul>
        
        <p><a href="https://your-dashboard.com/anomalies/{anomaly.anomaly_id}">View Details in Dashboard</a></p>
        </body>
        </html>
        """
        
        # Send email (implementation depends on your email service)
        # This is a basic SMTP implementation
        try:
            import smtplib
            from email.mime.multipart import MimeMultipart
            from email.mime.text import MimeText
            
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config.get('username')
            msg['To'] = ', '.join(recipients)
            
            html_part = MimeText(html_body, 'html')
            msg.attach(html_part)
            
            server = smtplib.SMTP(config.get('smtp_server'), config.get('smtp_port'))
            server.starttls()
            server.login(config.get('username'), config.get('password'))
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    async def _send_webhook_notification(self, anomaly: Anomaly, integration: IntegrationConfig):
        """Send webhook notification."""
        url = integration.config.get('url')
        if not url:
            return
        
        headers = integration.config.get('headers', {})
        auth_token = integration.config.get('auth_token')
        
        if auth_token:
            headers['Authorization'] = f"Bearer {auth_token}"
        
        payload = {
            "anomaly_id": anomaly.anomaly_id,
            "type": anomaly.type.value,
            "severity": anomaly.severity.value,
            "title": anomaly.title,
            "description": anomaly.description,
            "cluster_id": anomaly.cluster_id,
            "resource": anomaly.resource,
            "metric_name": anomaly.metric_name,
            "metric_value": anomaly.metric_value,
            "baseline_value": anomaly.baseline_value,
            "deviation_score": anomaly.deviation_score,
            "confidence": anomaly.confidence,
            "timestamp": anomaly.timestamp.isoformat(),
            "context": anomaly.context,
            "suggested_actions": anomaly.suggested_actions,
            "estimated_impact": anomaly.estimated_impact
        }
        
        async with self.client_session.post(url, json=payload, headers=headers) as response:
            if response.status >= 400:
                raise Exception(f"Webhook failed: {response.status}")
    
    async def _send_teams_notification(self, anomaly: Anomaly, integration: IntegrationConfig):
        """Send Microsoft Teams notification."""
        webhook_url = integration.config.get('webhook_url')
        if not webhook_url:
            return
        
        # Build Teams adaptive card
        color = {
            AnomalySeverity.LOW: "Good",
            AnomalySeverity.MEDIUM: "Warning", 
            AnomalySeverity.HIGH: "Attention",
            AnomalySeverity.CRITICAL: "Attention"
        }.get(anomaly.severity, "Default")
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000" if anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL] else "FFA500",
            "summary": anomaly.title,
            "sections": [{
                "activityTitle": f"🚨 {anomaly.title}",
                "activitySubtitle": f"Cluster: {anomaly.cluster_id}",
                "text": anomaly.description,
                "facts": [
                    {"name": "Severity", "value": anomaly.severity.value.upper()},
                    {"name": "Type", "value": anomaly.type.value},
                    {"name": "Metric", "value": f"{anomaly.metric_name}: {anomaly.metric_value:.2f}"},
                    {"name": "Confidence", "value": f"{anomaly.confidence*100:.1f}%"},
                    {"name": "Timestamp", "value": anomaly.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
                ]
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name": "View Details",
                "targets": [{
                    "os": "default",
                    "uri": f"https://your-dashboard.com/anomalies/{anomaly.anomaly_id}"
                }]
            }]
        }
        
        async with self.client_session.post(webhook_url, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Teams webhook failed: {response.status}")
    
    async def forward_alert(self, alert_data: Dict[str, Any]):
        """Forward alert to integrations."""
        try:
            # Convert alert to anomaly format if needed
            # Implementation depends on alert format
            pass
            
        except Exception as e:
            logger.error(f"Failed to forward alert: {e}")

# Example usage and testing
if __name__ == "__main__":
    async def demo():
        # Initialize components
        processor = RealTimeEventProcessor()
        
        # Start processing
        processing_task = asyncio.create_task(processor.start_processing())
        
        # Simulate events
        await asyncio.sleep(2)
        
        # Test metrics event
        metrics_event = {
            'type': 'metrics_update',
            'data': {
                'cpu_utilization': 95.0,
                'memory_utilization': 85.0,
                'daily_cost': 150.0,
                'pod_count': 50
            },
            'context': {
                'cluster_id': 'test-cluster-001',
                'resource': 'nodepool-1'
            }
        }
        
        await processor.ingest_event(metrics_event)
        
        # Test cost event
        cost_event = {
            'type': 'cost_update',
            'data': {
                'current_cost': 200.0,
                'previous_cost': 100.0
            },
            'context': {
                'cluster_id': 'test-cluster-001'
            }
        }
        
        await processor.ingest_event(cost_event)
        
        # Let it process for a bit
        await asyncio.sleep(5)
        
        # Stop processing
        await processor.stop_processing()
        
        print("Demo completed!")
    
    asyncio.run(demo())