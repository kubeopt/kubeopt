#!/usr/bin/env python3
"""
Operational Data Database Manager
Handles operational metrics, performance data, and audit logs
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .database_config import DatabaseConfig

logger = logging.getLogger(__name__)

class OperationalDataDB:
    """Database manager for operational data and metrics"""
    
    def __init__(self):
        self.db_path = DatabaseConfig.get_database_path('operational_data')
        self.logger = logging.getLogger(__name__)
    
    def store_security_scan_result(self, result_id: str, cluster_id: str,
                                 resource_group: str, cluster_name: str,
                                 scan_timestamp: str, analysis_data: Dict,
                                 confidence: float = 0.0,
                                 frameworks_analyzed: List[str] = None,
                                 based_on_real_data: bool = False) -> int:
        """Store security scan results from JSON files"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO security_scan_results 
                    (result_id, cluster_id, resource_group, cluster_name,
                     scan_timestamp, analysis_data, confidence, 
                     frameworks_analyzed, based_on_real_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result_id,
                    cluster_id,
                    resource_group,
                    cluster_name,
                    scan_timestamp,
                    json.dumps(analysis_data),
                    confidence,
                    json.dumps(frameworks_analyzed or []),
                    based_on_real_data
                ))
                
                scan_db_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored security scan result: {result_id}")
                return scan_db_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store security scan result: {e}")
            return 0
    
    def get_security_scan_results(self, cluster_id: str = None, 
                                limit: int = 50) -> List[Dict]:
        """Get security scan results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if cluster_id:
                    cursor = conn.execute('''
                        SELECT * FROM security_scan_results 
                        WHERE cluster_id = ?
                        ORDER BY scan_timestamp DESC 
                        LIMIT ?
                    ''', (cluster_id, limit))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM security_scan_results 
                        ORDER BY scan_timestamp DESC 
                        LIMIT ?
                    ''', (limit,))
                
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    result['analysis_data'] = json.loads(result['analysis_data'])
                    result['frameworks_analyzed'] = json.loads(result['frameworks_analyzed'])
                    results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get security scan results: {e}")
            return []
    
    def store_performance_metric(self, cluster_id: str, metric_name: str,
                               metric_value: float, metric_unit: str = None,
                               collection_source: str = None,
                               aggregation_period: str = 'instant') -> int:
        """Store performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO performance_metrics 
                    (cluster_id, metric_name, metric_value, metric_unit,
                     collection_source, aggregation_period)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    metric_name,
                    metric_value,
                    metric_unit,
                    collection_source,
                    aggregation_period
                ))
                
                metric_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored performance metric: {metric_name}")
                return metric_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store performance metric: {e}")
            return 0
    
    def get_performance_metrics(self, cluster_id: str, metric_name: str = None,
                              hours_back: int = 24) -> List[Dict]:
        """Get performance metrics for analysis"""
        try:
            cutoff_time = datetime.now().timestamp() - (hours_back * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if metric_name:
                    cursor = conn.execute('''
                        SELECT * FROM performance_metrics 
                        WHERE cluster_id = ? AND metric_name = ?
                        AND measurement_timestamp > datetime(?, 'unixepoch')
                        ORDER BY measurement_timestamp DESC
                    ''', (cluster_id, metric_name, cutoff_time))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM performance_metrics 
                        WHERE cluster_id = ?
                        AND measurement_timestamp > datetime(?, 'unixepoch')
                        ORDER BY measurement_timestamp DESC
                    ''', (cluster_id, cutoff_time))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get performance metrics: {e}")
            return []
    
    def store_cost_analysis(self, cluster_id: str, analysis_date: str,
                          total_cost: float, compute_cost: float = 0.0,
                          storage_cost: float = 0.0, network_cost: float = 0.0,
                          potential_savings: float = 0.0,
                          optimization_opportunities: Dict = None,
                          cost_breakdown: Dict = None,
                          currency: str = 'USD') -> int:
        """Store cost analysis history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO cost_analysis_history 
                    (cluster_id, analysis_date, total_cost, compute_cost,
                     storage_cost, network_cost, potential_savings,
                     optimization_opportunities, cost_breakdown, currency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    analysis_date,
                    total_cost,
                    compute_cost,
                    storage_cost,
                    network_cost,
                    potential_savings,
                    json.dumps(optimization_opportunities or {}),
                    json.dumps(cost_breakdown or {}),
                    currency
                ))
                
                cost_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored cost analysis: {cost_id}")
                return cost_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store cost analysis: {e}")
            return 0
    
    def get_cost_analysis_history(self, cluster_id: str, 
                                days_back: int = 90) -> List[Dict]:
        """Get cost analysis history for trending"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_back * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM cost_analysis_history 
                    WHERE cluster_id = ?
                    AND analysis_date > datetime(?, 'unixepoch')
                    ORDER BY analysis_date DESC
                ''', (cluster_id, cutoff_time))
                
                history = []
                for row in cursor.fetchall():
                    record = dict(row)
                    record['optimization_opportunities'] = json.loads(record['optimization_opportunities'])
                    record['cost_breakdown'] = json.loads(record['cost_breakdown'])
                    history.append(record)
                
                return history
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get cost analysis history: {e}")
            return []
    
    def store_resource_utilization(self, cluster_id: str, resource_type: str,
                                 resource_name: str, utilization_percentage: float,
                                 allocated_amount: float = None,
                                 used_amount: float = None,
                                 namespace: str = None,
                                 workload_name: str = None) -> int:
        """Store resource utilization data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO resource_utilization 
                    (cluster_id, resource_type, resource_name, utilization_percentage,
                     allocated_amount, used_amount, namespace, workload_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    resource_type,
                    resource_name,
                    utilization_percentage,
                    allocated_amount,
                    used_amount,
                    namespace,
                    workload_name
                ))
                
                util_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored resource utilization: {resource_type}")
                return util_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store resource utilization: {e}")
            return 0
    
    def get_resource_utilization(self, cluster_id: str, resource_type: str = None,
                               hours_back: int = 24) -> List[Dict]:
        """Get resource utilization patterns"""
        try:
            cutoff_time = datetime.now().timestamp() - (hours_back * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if resource_type:
                    cursor = conn.execute('''
                        SELECT * FROM resource_utilization 
                        WHERE cluster_id = ? AND resource_type = ?
                        AND measurement_time > datetime(?, 'unixepoch')
                        ORDER BY measurement_time DESC
                    ''', (cluster_id, resource_type, cutoff_time))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM resource_utilization 
                        WHERE cluster_id = ?
                        AND measurement_time > datetime(?, 'unixepoch')
                        ORDER BY measurement_time DESC
                    ''', (cluster_id, cutoff_time))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get resource utilization: {e}")
            return []
    
    def store_audit_log(self, event_id: str, event_type: str, event_category: str,
                       action_performed: str, user_id: str = None,
                       cluster_id: str = None, resource_affected: str = None,
                       success: bool = True, error_message: str = None,
                       ip_address: str = None, user_agent: str = None) -> int:
        """Store audit log entry"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO audit_logs 
                    (event_id, event_type, event_category, action_performed,
                     user_id, cluster_id, resource_affected, success,
                     error_message, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id,
                    event_type,
                    event_category,
                    action_performed,
                    user_id,
                    cluster_id,
                    resource_affected,
                    success,
                    error_message,
                    ip_address,
                    user_agent
                ))
                
                audit_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored audit log: {event_type}")
                return audit_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store audit log: {e}")
            return 0
    
    def get_audit_logs(self, cluster_id: str = None, event_type: str = None,
                      days_back: int = 30, limit: int = 100) -> List[Dict]:
        """Get audit logs for security and compliance"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_back * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = ['event_timestamp > datetime(?, "unixepoch")']
                params = [cutoff_time]
                
                if cluster_id:
                    where_clauses.append('cluster_id = ?')
                    params.append(cluster_id)
                
                if event_type:
                    where_clauses.append('event_type = ?')
                    params.append(event_type)
                
                where_sql = ' AND '.join(where_clauses)
                params.append(limit)
                
                cursor = conn.execute(f'''
                    SELECT * FROM audit_logs 
                    WHERE {where_sql}
                    ORDER BY event_timestamp DESC 
                    LIMIT ?
                ''', params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get audit logs: {e}")
            return []
    
    def get_operational_summary(self, cluster_id: str) -> Dict[str, Any]:
        """Get comprehensive operational summary for a cluster"""
        try:
            summary = {
                'recent_scans': 0,
                'performance_metrics_count': 0,
                'cost_analysis_count': 0,
                'resource_utilization_count': 0,
                'recent_audit_events': 0,
                'latest_cost_analysis': None
            }
            
            # Count recent security scans
            recent_scans = self.get_security_scan_results(cluster_id, limit=10)
            summary['recent_scans'] = len(recent_scans)
            
            # Count performance metrics (last 24 hours)
            performance_metrics = self.get_performance_metrics(cluster_id, hours_back=24)
            summary['performance_metrics_count'] = len(performance_metrics)
            
            # Count cost analyses (last 30 days)
            cost_history = self.get_cost_analysis_history(cluster_id, days_back=30)
            summary['cost_analysis_count'] = len(cost_history)
            if cost_history:
                summary['latest_cost_analysis'] = cost_history[0]
            
            # Count resource utilization entries (last 24 hours)
            utilization = self.get_resource_utilization(cluster_id, hours_back=24)
            summary['resource_utilization_count'] = len(utilization)
            
            # Count recent audit events (last 7 days)
            audit_logs = self.get_audit_logs(cluster_id, days_back=7)
            summary['recent_audit_events'] = len(audit_logs)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get operational summary: {e}")
            return {}

# Global instance
operational_data_db = OperationalDataDB()