#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Security Analytics Database Manager
Handles all security and compliance data operations
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .database_config import DatabaseConfig

logger = logging.getLogger(__name__)

class SecurityAnalyticsDB:
    """Database manager for security and compliance operations"""
    
    def __init__(self):
        self.db_path = DatabaseConfig.get_database_path('security_analytics')
        self.logger = logging.getLogger(__name__)
    
    def store_security_assessment(self, cluster_id: str, assessment_id: str,
                                overall_score: float, grade: str, framework: str,
                                score_breakdown: Dict, confidence: float = 0.0,
                                based_on_real_data: bool = False,
                                trends_data: Dict = None) -> int:
        """Store security assessment results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO security_assessments 
                    (cluster_id, assessment_id, overall_score, grade, framework,
                     score_breakdown, confidence, based_on_real_data, trends_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    assessment_id,
                    overall_score,
                    grade,
                    framework,
                    json.dumps(score_breakdown),
                    confidence,
                    based_on_real_data,
                    json.dumps(trends_data) if trends_data else None
                ))
                
                assessment_db_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored security assessment: {assessment_id}")
                return assessment_db_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store security assessment: {e}")
            return 0
    
    def get_security_assessment(self, cluster_id: str, 
                              framework: str = None) -> Optional[Dict]:
        """Get latest security assessment for cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if framework is not None and framework:
                    cursor = conn.execute('''
                        SELECT * FROM security_assessments 
                        WHERE cluster_id = ? AND framework = ?
                        ORDER BY assessment_date DESC 
                        LIMIT 1
                    ''', (cluster_id, framework))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM security_assessments 
                        WHERE cluster_id = ?
                        ORDER BY assessment_date DESC 
                        LIMIT 1
                    ''', (cluster_id,))
                
                row = cursor.fetchone()
                if row is not None and row:
                    assessment = dict(row)
                    assessment['score_breakdown'] = json.loads(assessment['score_breakdown'])
                    if assessment['trends_data']:
                        assessment['trends_data'] = json.loads(assessment['trends_data'])
                    return assessment
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get security assessment: {e}")
            return None
    
    def store_vulnerability_scan(self, cluster_id: str, scan_id: str,
                               vulnerability_id: str, severity: str, category: str,
                               title: str, description: str = None,
                               resource_type: str = None, resource_name: str = None,
                               remediation: str = None) -> int:
        """Store vulnerability scan results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO vulnerability_scans 
                    (cluster_id, scan_id, vulnerability_id, severity, category,
                     title, description, resource_type, resource_name, remediation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    scan_id,
                    vulnerability_id,
                    severity,
                    category,
                    title,
                    description,
                    resource_type,
                    resource_name,
                    remediation
                ))
                
                vuln_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored vulnerability: {vulnerability_id}")
                return vuln_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store vulnerability: {e}")
            return 0
    
    def get_cluster_vulnerabilities(self, cluster_id: str, 
                                  severity: str = None,
                                  status: str = 'OPEN') -> List[Dict]:
        """Get vulnerabilities for a cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = ['cluster_id = ?']
                params = [cluster_id]
                
                if severity is not None and severity:
                    where_clauses.append('severity = ?')
                    params.append(severity)
                
                if status is not None and status:
                    where_clauses.append('status = ?')
                    params.append(status)
                
                where_sql = ' AND '.join(where_clauses)
                
                cursor = conn.execute(f'''
                    SELECT * FROM vulnerability_scans 
                    WHERE {where_sql}
                    ORDER BY scan_date DESC
                ''', params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get vulnerabilities: {e}")
            return []
    
    def store_policy_violation(self, cluster_id: str, violation_id: str,
                             policy_name: str, policy_category: str,
                             violation_type: str, severity: str,
                             resource_affected: str = None,
                             violation_details: str = None,
                             remediation_steps: str = None) -> int:
        """Store policy compliance violations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO policy_violations 
                    (cluster_id, violation_id, policy_name, policy_category,
                     violation_type, severity, resource_affected, 
                     violation_details, remediation_steps)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    violation_id,
                    policy_name,
                    policy_category,
                    violation_type,
                    severity,
                    resource_affected,
                    violation_details,
                    remediation_steps
                ))
                
                violation_db_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored policy violation: {violation_id}")
                return violation_db_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store policy violation: {e}")
            return 0
    
    def get_policy_violations(self, cluster_id: str, 
                            status: str = 'ACTIVE') -> List[Dict]:
        """Get policy violations for a cluster"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM policy_violations 
                    WHERE cluster_id = ? AND status = ?
                    ORDER BY detected_at DESC
                ''', (cluster_id, status))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get policy violations: {e}")
            return []
    
    def store_security_metric(self, cluster_id: str, metric_name: str,
                            metric_value: float, metric_category: str,
                            trend_direction: str = None,
                            baseline_value: float = None,
                            target_value: float = None) -> int:
        """Store security metrics and scoring"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO security_metrics 
                    (cluster_id, metric_name, metric_value, metric_category,
                     trend_direction, baseline_value, target_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cluster_id,
                    metric_name,
                    metric_value,
                    metric_category,
                    trend_direction,
                    baseline_value,
                    target_value
                ))
                
                metric_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"✅ Stored security metric: {metric_name}")
                return metric_id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to store security metric: {e}")
            return 0
    
    def get_security_metrics(self, cluster_id: str, 
                           metric_category: str = None,
                           days_back: int = 30) -> List[Dict]:
        """Get security metrics for a cluster"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_back * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if metric_category is not None and metric_category:
                    cursor = conn.execute('''
                        SELECT * FROM security_metrics 
                        WHERE cluster_id = ? AND metric_category = ?
                        AND measurement_date > datetime(?, 'unixepoch')
                        ORDER BY measurement_date DESC
                    ''', (cluster_id, metric_category, cutoff_date))
                else:
                    cursor = conn.execute('''
                        SELECT * FROM security_metrics 
                        WHERE cluster_id = ?
                        AND measurement_date > datetime(?, 'unixepoch')
                        ORDER BY measurement_date DESC
                    ''', (cluster_id, cutoff_date))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get security metrics: {e}")
            return []
    
    def get_security_summary(self, cluster_id: str) -> Dict[str, Any]:
        """Get comprehensive security summary for a cluster"""
        try:
            summary = {
                'latest_assessment': None,
                'vulnerability_counts': {},
                'policy_violation_counts': {},
                'security_trends': {}
            }
            
            # Get latest assessment
            summary['latest_assessment'] = self.get_security_assessment(cluster_id)
            
            # Get vulnerability counts by severity
            vulnerabilities = self.get_cluster_vulnerabilities(cluster_id)
            for vuln in vulnerabilities:
                severity = vuln['severity']
                summary['vulnerability_counts'][severity] = summary['vulnerability_counts'].get(severity, 0) + 1
            
            # Get policy violation counts by category
            violations = self.get_policy_violations(cluster_id)
            for violation in violations:
                category = violation['policy_category']
                summary['policy_violation_counts'][category] = summary['policy_violation_counts'].get(category, 0) + 1
            
            # Get recent security metrics trends
            metrics = self.get_security_metrics(cluster_id, days_back=7)
            for metric in metrics:
                metric_name = metric['metric_name']
                if metric_name not in summary['security_trends']:
                    summary['security_trends'][metric_name] = []
                summary['security_trends'][metric_name].append({
                    'value': metric['metric_value'],
                    'date': metric['measurement_date'],
                    'trend': metric['trend_direction']
                })
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get security summary: {e}")
            return {}

# Global instance
security_analytics_db = SecurityAnalyticsDB()