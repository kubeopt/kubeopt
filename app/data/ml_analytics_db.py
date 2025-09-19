#!/usr/bin/env python3
"""
ML Analytics Database Manager
Handles all machine learning and analytics data operations
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .database_config import DatabaseConfig

logger = logging.getLogger(__name__)

class MLAnalyticsDB:
    """Database manager for ML and analytics operations"""
    
    def __init__(self):
        self.db_path = DatabaseConfig.get_database_path('ml_analytics')
        self.logger = logging.getLogger(__name__)
    
    def store_learning_data(self, cluster_id: str, workload_name: str, 
                           feature_vector: Dict, target_values: Dict, 
                           namespace: str = None, confidence_score: float = 0.0) -> int:
        """Store learning data for ML training"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO learning_data 
                    (cluster_id, workload_name, namespace, feature_vector, target_values, 
                     confidence_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    workload_name,
                    namespace,
                    json.dumps(feature_vector),
                    json.dumps(target_values),
                    confidence_score,
                    json.dumps({'source': 'analysis', 'created_at': datetime.now().isoformat()})
                ))
                
                learning_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored learning data: {learning_id}")
                return learning_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store learning data: {e}")
            return 0
    
    def get_learning_data(self, cluster_id: str = None, limit: int = 1000) -> List[Dict]:
        """Retrieve learning data for ML training"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if cluster_id:
                    cursor = conn.execute('''
                        SELECT * FROM learning_data 
                        WHERE cluster_id = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (cluster_id, limit))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM learning_data 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (limit,))
                
                data = []
                for row in cursor.fetchall():
                    record = dict(row)
                    record['feature_vector'] = json.loads(record['feature_vector'])
                    record['target_values'] = json.loads(record['target_values'])
                    record['metadata'] = json.loads(record.get('metadata', '{}'))
                    data.append(record)
                
                return data
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get learning data: {e}")
            return []
    
    def store_model_metadata(self, model_name: str, model_type: str, version: str,
                           algorithm: str, parameters: Dict, accuracy_score: float = 0.0,
                           training_data_count: int = 0) -> int:
        """Store ML model metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO model_metadata 
                    (model_name, model_type, version, algorithm, parameters, 
                     accuracy_score, training_data_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    model_name,
                    model_type,
                    version,
                    algorithm,
                    json.dumps(parameters),
                    accuracy_score,
                    training_data_count
                ))
                
                model_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored model metadata: {model_id}")
                return model_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store model metadata: {e}")
            return 0
    
    def store_optimization_result(self, cluster_id: str, optimization_type: str,
                                original_value: float, optimized_value: float,
                                confidence_level: str = 'medium',
                                estimated_savings: float = 0.0) -> int:
        """Store optimization results"""
        try:
            improvement_pct = ((original_value - optimized_value) / original_value) * 100
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO optimization_results 
                    (cluster_id, optimization_type, original_value, optimized_value,
                     improvement_percentage, confidence_level, estimated_savings)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    optimization_type,
                    original_value,
                    optimized_value,
                    improvement_pct,
                    confidence_level,
                    estimated_savings
                ))
                
                result_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored optimization result: {result_id}")
                return result_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store optimization result: {e}")
            return 0
    
    def get_optimization_history(self, cluster_id: str, 
                               optimization_type: str = None) -> List[Dict]:
        """Get optimization history for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if optimization_type:
                    cursor = conn.execute('''
                        SELECT * FROM optimization_results 
                        WHERE cluster_id = ? AND optimization_type = ?
                        ORDER BY created_at DESC
                    ''', (cluster_id, optimization_type))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM optimization_results 
                        WHERE cluster_id = ?
                        ORDER BY created_at DESC
                    ''', (cluster_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get optimization history: {e}")
            return []
    
    def store_pattern_analysis(self, cluster_id: str, pattern_type: str,
                             pattern_data: Dict, similarity_score: float = 0.0) -> int:
        """Store workload pattern analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO pattern_analysis 
                    (cluster_id, pattern_type, pattern_data, similarity_score)
                    VALUES (?, ?, ?, ?)
                ''', (
                    cluster_id,
                    pattern_type,
                    json.dumps(pattern_data),
                    similarity_score
                ))
                
                pattern_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored pattern analysis: {pattern_id}")
                return pattern_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store pattern analysis: {e}")
            return 0
    
    def get_cluster_patterns(self, cluster_id: str) -> List[Dict]:
        """Get all patterns for a cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM pattern_analysis 
                    WHERE cluster_id = ? AND is_active = 1
                    ORDER BY detected_at DESC
                ''', (cluster_id,))
                
                patterns = []
                for row in cursor.fetchall():
                    pattern = dict(row)
                    pattern['pattern_data'] = json.loads(pattern['pattern_data'])
                    patterns.append(pattern)
                
                return patterns
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get cluster patterns: {e}")
            return []

# Global instance
ml_analytics_db = MLAnalyticsDB()