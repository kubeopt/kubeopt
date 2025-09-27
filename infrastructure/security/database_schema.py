#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & KubeVista
Project: AKS Cost Optimizer
"""

"""
Database Schema and Setup for AKS Security Posture
=================================================
Comprehensive database schema creation and migration utilities.
Supports SQLite for development and PostgreSQL for production.
"""

import sqlite3
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class SecurityDatabaseManager:
    """
    Database manager for security posture system
    """
    
    def __init__(self, database_path: str = None):
        """Initialize database manager"""
        # Use unified database structure
        if database_path is None:
            from infrastructure.persistence.database_config import DatabaseConfig
            self.database_path = str(DatabaseConfig.DATABASES['security_analytics'])
        else:
            self.database_path = database_path
        self.database_dir = Path(self.database_path).parent
        
        # Ensure directory exists
        self.database_dir.mkdir(parents=True, exist_ok=True)
        
        # Schema version for migrations
        self.schema_version = "1.0.0"
        
        logger.info(f"🗃️ Database manager initialized: {database_path}")
    
    def initialize_database(self) -> bool:
        """Initialize complete database schema"""
        
        try:
            logger.info("🔄 Initializing security posture database...")
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Enable foreign keys
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Create schema version table
                self._create_schema_version_table(cursor)
                
                # Create core security tables - order matters for foreign keys!
                self._create_reporting_tables(cursor)  # Must be first - creates clusters table
                self._create_security_posture_tables(cursor)
                self._create_policy_tables(cursor)
                self._create_compliance_tables(cursor)
                self._create_vulnerability_tables(cursor)
                self._create_audit_tables(cursor)
                
                # Create indexes for performance
                self._create_indexes(cursor)
                
                # Insert initial data
                self._insert_initial_data(cursor)
                
                # Record schema version
                self._update_schema_version(cursor)
                
                conn.commit()
                
            logger.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    def _create_schema_version_table(self, cursor: sqlite3.Cursor):
        """Create schema version tracking table"""
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY,
                version TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
    
    def _create_security_posture_tables(self, cursor: sqlite3.Cursor):
        """Create security posture related tables"""
        
        # Security scores history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_name TEXT NOT NULL,
                overall_score REAL NOT NULL,
                grade TEXT NOT NULL,
                rbac_score REAL NOT NULL,
                network_score REAL NOT NULL,
                encryption_score REAL NOT NULL, 
                vulnerability_score REAL NOT NULL,
                compliance_score REAL NOT NULL,
                drift_score REAL NOT NULL,
                trends TEXT, -- JSON
                ml_confidence REAL DEFAULT 0.8,
                assessment_metadata TEXT, -- JSON
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cluster_name) REFERENCES clusters(name)
            )
        """)
        
        # Security alerts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
                category TEXT NOT NULL CHECK (category IN ('POLICY', 'VULNERABILITY', 'DRIFT', 'EXPOSURE', 'COMPLIANCE')),
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                namespace TEXT DEFAULT 'default',
                remediation TEXT NOT NULL,
                risk_score REAL NOT NULL,
                detection_method TEXT DEFAULT 'automated',
                false_positive BOOLEAN DEFAULT FALSE,
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by TEXT,
                acknowledged_at TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_by TEXT,
                resolved_at TIMESTAMP,
                metadata TEXT, -- JSON
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Security configurations baseline
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_name TEXT NOT NULL,
                baseline_name TEXT NOT NULL,
                configuration_hash TEXT NOT NULL,
                configuration_data TEXT NOT NULL, -- JSON
                is_active BOOLEAN DEFAULT TRUE,
                created_by TEXT DEFAULT 'system',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cluster_name, baseline_name)
            )
        """)
        
        # Security scan results (for operational data integration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                scan_status TEXT NOT NULL,
                total_findings INTEGER DEFAULT 0,
                critical_findings INTEGER DEFAULT 0,
                high_findings INTEGER DEFAULT 0,
                medium_findings INTEGER DEFAULT 0,
                low_findings INTEGER DEFAULT 0,
                scan_duration REAL,
                scan_metadata TEXT,
                scan_results TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (cluster_name) REFERENCES clusters(name)
            )
        """)
        
        # Security assessments (for security analytics integration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_id TEXT NOT NULL,
                assessment_id TEXT UNIQUE NOT NULL,
                overall_score REAL NOT NULL,
                grade TEXT NOT NULL,
                framework TEXT,
                score_breakdown TEXT,
                confidence REAL DEFAULT 0.8,
                based_on_real_data BOOLEAN DEFAULT FALSE,
                trends_data TEXT,
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Security drift detection
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_drift (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_name TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                namespace TEXT DEFAULT 'default',
                drift_type TEXT NOT NULL,
                baseline_config TEXT NOT NULL, -- JSON
                current_config TEXT NOT NULL, -- JSON
                drift_score REAL NOT NULL,
                confidence_score REAL DEFAULT 0.8,
                auto_remediation_available BOOLEAN DEFAULT FALSE,
                remediation_plan TEXT,
                status TEXT DEFAULT 'detected' CHECK (status IN ('detected', 'investigating', 'remediated', 'accepted')),
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_policy_tables(self, cursor: sqlite3.Cursor):
        """Create policy analysis tables"""
        
        # Policy rules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policy_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
                resource_types TEXT NOT NULL, -- JSON array
                rule_logic TEXT NOT NULL,
                remediation_template TEXT NOT NULL,
                compliance_mappings TEXT, -- JSON
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Policy violations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policy_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                violation_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                policy_rule_id TEXT NOT NULL,
                policy_name TEXT NOT NULL,
                policy_category TEXT NOT NULL,
                severity TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                namespace TEXT DEFAULT 'default',
                violation_description TEXT NOT NULL,
                current_value TEXT,
                expected_value TEXT,
                remediation_steps TEXT, -- JSON array
                auto_remediable BOOLEAN DEFAULT FALSE,
                remediation_status TEXT DEFAULT 'open' CHECK (remediation_status IN ('open', 'in_progress', 'resolved', 'accepted')),
                compliance_frameworks TEXT, -- JSON array
                risk_score REAL NOT NULL,
                confidence_score REAL DEFAULT 0.9,
                detection_method TEXT DEFAULT 'policy_engine',
                remediated_by TEXT,
                remediated_at TIMESTAMP,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (policy_rule_id) REFERENCES policy_rules(rule_id)
            )
        """)
        
        # Governance reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS governance_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                report_type TEXT DEFAULT 'policy_compliance',
                overall_compliance REAL NOT NULL,
                total_violations INTEGER NOT NULL,
                violations_by_severity TEXT NOT NULL, -- JSON
                compliance_by_category TEXT NOT NULL, -- JSON
                recommendations TEXT, -- JSON array
                ml_analysis_applied BOOLEAN DEFAULT TRUE,
                confidence_score REAL DEFAULT 0.8,
                report_data TEXT, -- JSON - full report
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_compliance_tables(self, cursor: sqlite3.Cursor):
        """Create compliance framework tables"""
        
        # Compliance frameworks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_frameworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                framework_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                categories TEXT, -- JSON array
                total_controls INTEGER NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Compliance controls
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_controls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                control_id TEXT UNIQUE NOT NULL,
                framework_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL CHECK (priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
                implementation_guidance TEXT,
                testing_procedure TEXT,
                evidence_requirements TEXT, -- JSON array
                automated_check BOOLEAN DEFAULT FALSE,
                manual_review_required BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(framework_id)
            )
        """)
        
        # Compliance assessments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                framework_id TEXT NOT NULL,
                control_id TEXT NOT NULL,
                compliance_status TEXT NOT NULL CHECK (compliance_status IN ('COMPLIANT', 'NON_COMPLIANT', 'PARTIAL', 'NOT_TESTED')),
                assessment_method TEXT DEFAULT 'automated',
                evidence_collected TEXT, -- JSON
                assessor TEXT DEFAULT 'system',
                assessment_notes TEXT,
                remediation_plan TEXT,
                confidence_score REAL DEFAULT 0.8,
                next_assessment_due DATE,
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(framework_id),
                FOREIGN KEY (control_id) REFERENCES compliance_controls(control_id)
            )
        """)
        
        # Compliance reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                framework_id TEXT NOT NULL,
                report_type TEXT DEFAULT 'assessment',
                overall_compliance REAL NOT NULL,
                compliance_grade TEXT NOT NULL,
                passed_controls INTEGER NOT NULL,
                failed_controls INTEGER NOT NULL,
                partial_controls INTEGER DEFAULT 0,
                not_tested_controls INTEGER DEFAULT 0,
                executive_summary TEXT,
                detailed_findings TEXT, -- JSON
                risk_summary TEXT, -- JSON
                recommendations TEXT, -- JSON array
                evidence_attachments TEXT, -- JSON array
                certified_by TEXT DEFAULT 'AKS Security Engine',
                valid_until DATE,
                report_data TEXT, -- JSON - full report
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(framework_id)
            )
        """)
    
    def _create_vulnerability_tables(self, cursor: sqlite3.Cursor):
        """Create vulnerability management tables"""
        
        # Vulnerabilities
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vuln_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                cve_id TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
                cvss_score REAL NOT NULL,
                cvss_vector TEXT,
                affected_component TEXT NOT NULL,
                component_type TEXT NOT NULL CHECK (component_type IN ('CONTAINER', 'KUBERNETES', 'OS', 'LIBRARY')),
                current_version TEXT,
                fixed_version TEXT,
                detection_method TEXT NOT NULL CHECK (detection_method IN ('STATIC_ANALYSIS', 'CVE_DATABASE', 'ML_PREDICTION', 'RUNTIME_DETECTION')),
                confidence_score REAL DEFAULT 0.8,
                exploit_available BOOLEAN DEFAULT FALSE,
                exploit_maturity TEXT CHECK (exploit_maturity IN ('PROOF_OF_CONCEPT', 'FUNCTIONAL', 'HIGH')),
                attack_vector TEXT CHECK (attack_vector IN ('NETWORK', 'ADJACENT', 'LOCAL', 'PHYSICAL')),
                attack_complexity TEXT CHECK (attack_complexity IN ('LOW', 'HIGH')),
                remediation_guidance TEXT,
                remediation_status TEXT DEFAULT 'open' CHECK (remediation_status IN ('open', 'in_progress', 'resolved', 'accepted', 'false_positive')),
                priority_score REAL DEFAULT 0.0,
                business_impact TEXT,
                remediated_by TEXT,
                remediated_at TIMESTAMP,
                vulnerability_references TEXT, -- JSON array
                metadata TEXT, -- JSON
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vulnerability scan results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerability_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                scan_type TEXT NOT NULL CHECK (scan_type IN ('FULL', 'INCREMENTAL', 'TARGETED', 'SCHEDULED')),
                target_resource TEXT DEFAULT 'cluster-wide',
                scan_status TEXT NOT NULL CHECK (scan_status IN ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')),
                scanner_version TEXT NOT NULL,
                scan_configuration TEXT, -- JSON
                total_vulnerabilities INTEGER DEFAULT 0,
                critical_vulnerabilities INTEGER DEFAULT 0,
                high_vulnerabilities INTEGER DEFAULT 0,
                medium_vulnerabilities INTEGER DEFAULT 0,
                low_vulnerabilities INTEGER DEFAULT 0,
                exploitable_vulnerabilities INTEGER DEFAULT 0,
                vulnerabilities_with_cve INTEGER DEFAULT 0,
                coverage_percentage REAL DEFAULT 0.0,
                scan_duration REAL, -- seconds
                error_message TEXT,
                scan_metadata TEXT, -- JSON
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                created_by TEXT DEFAULT 'system'
            )
        """)
        
        # CVE database cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cve_database (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cve_id TEXT UNIQUE NOT NULL,
                published_date DATE,
                last_modified DATE,
                description TEXT,
                cvss_v3_score REAL,
                cvss_v3_vector TEXT,
                cvss_v2_score REAL,
                cvss_v2_vector TEXT,
                severity TEXT,
                affected_products TEXT, -- JSON array
                cve_references TEXT, -- JSON array
                exploit_available BOOLEAN DEFAULT FALSE,
                patch_available BOOLEAN DEFAULT FALSE,
                threat_intelligence TEXT, -- JSON
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        # Threat intelligence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_intelligence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                threat_id TEXT UNIQUE NOT NULL,
                threat_type TEXT NOT NULL CHECK (threat_type IN ('APT', 'MALWARE', 'EXPLOIT_KIT', 'RANSOMWARE', 'VULNERABILITY', 'IOC')),
                threat_name TEXT NOT NULL,
                description TEXT,
                indicators TEXT, -- JSON array of IOCs
                ttps TEXT, -- JSON array of tactics, techniques, procedures
                affected_platforms TEXT, -- JSON array
                severity TEXT CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
                confidence TEXT CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
                source TEXT NOT NULL,
                source_reliability TEXT DEFAULT 'unknown',
                related_cves TEXT, -- JSON array
                mitigation_strategies TEXT, -- JSON array
                published_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_audit_tables(self, cursor: sqlite3.Cursor):
        """Create audit and logging tables"""
        
        # Audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL CHECK (event_type IN ('ASSESSMENT', 'REMEDIATION', 'CONFIG_CHANGE', 'ACCESS', 'SCAN', 'ALERT')),
                event_category TEXT DEFAULT 'security',
                user_id TEXT,
                user_name TEXT,
                user_role TEXT,
                source_ip TEXT,
                user_agent TEXT,
                resource_type TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                namespace TEXT DEFAULT 'default',
                action TEXT NOT NULL,
                action_result TEXT DEFAULT 'success',
                before_state TEXT, -- JSON
                after_state TEXT, -- JSON
                compliance_impact TEXT,
                risk_level TEXT DEFAULT 'low',
                source_system TEXT DEFAULT 'aks_security_engine',
                correlation_id TEXT,
                session_id TEXT,
                metadata TEXT -- JSON
            )
        """)
        
        # System logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT,
                log_level TEXT NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                exception_info TEXT,
                context TEXT, -- JSON
                correlation_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Evidence repository
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_repository (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                evidence_type TEXT NOT NULL CHECK (evidence_type IN ('CONFIGURATION', 'LOG', 'SCREENSHOT', 'REPORT', 'CERTIFICATE')),
                control_id TEXT,
                assessment_id TEXT,
                violation_id TEXT,
                vulnerability_id TEXT,
                evidence_name TEXT NOT NULL,
                evidence_description TEXT,
                file_path TEXT,
                file_size INTEGER,
                file_hash TEXT,
                evidence_data TEXT, -- JSON or base64 encoded data
                retention_period INTEGER DEFAULT 2555, -- days (7 years)
                encryption_applied BOOLEAN DEFAULT FALSE,
                access_level TEXT DEFAULT 'internal',
                collected_by TEXT NOT NULL,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
    
    def _create_reporting_tables(self, cursor: sqlite3.Cursor):
        """Create reporting and dashboard tables"""
        
        # Clusters registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT,
                description TEXT,
                environment TEXT CHECK (environment IN ('development', 'staging', 'production')),
                region TEXT,
                resource_group TEXT,
                subscription_id TEXT,
                kubernetes_version TEXT,
                node_count INTEGER,
                cluster_status TEXT DEFAULT 'active',
                monitoring_enabled BOOLEAN DEFAULT TRUE,
                security_enabled BOOLEAN DEFAULT TRUE,
                compliance_frameworks TEXT, -- JSON array
                tags TEXT, -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Dashboard configurations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                user_id TEXT,
                dashboard_type TEXT NOT NULL,
                configuration TEXT NOT NULL, -- JSON
                is_default BOOLEAN DEFAULT FALSE,
                is_shared BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cluster_name) REFERENCES clusters(name)
            )
        """)
        
        # Scheduled reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                cluster_name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                report_name TEXT NOT NULL,
                schedule_cron TEXT NOT NULL,
                recipients TEXT, -- JSON array
                report_format TEXT DEFAULT 'pdf',
                include_attachments BOOLEAN DEFAULT TRUE,
                filters TEXT, -- JSON
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cluster_name) REFERENCES clusters(name)
            )
        """)
        
        # Report executions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE NOT NULL,
                scheduled_report_id TEXT NOT NULL,
                cluster_name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                execution_status TEXT NOT NULL CHECK (execution_status IN ('running', 'completed', 'failed')),
                report_file_path TEXT,
                file_size INTEGER,
                execution_duration REAL, -- seconds
                error_message TEXT,
                recipients_notified INTEGER DEFAULT 0,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scheduled_report_id) REFERENCES scheduled_reports(report_id)
            )
        """)
    
    def _create_indexes(self, cursor: sqlite3.Cursor):
        """Create database indexes for performance"""
        
        # Security scores indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_scores_cluster_time ON security_scores(cluster_name, assessed_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_scores_overall ON security_scores(overall_score, assessed_at)")
        
        # Security alerts indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_alerts_cluster_severity ON security_alerts(cluster_name, severity, detected_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_alerts_status ON security_alerts(resolved, acknowledged)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_security_alerts_category ON security_alerts(category, severity)")
        
        # Policy violations indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_violations_cluster_status ON policy_violations(cluster_name, remediation_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_policy_violations_severity ON policy_violations(severity, detected_at)")
        
        # Vulnerability indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vulnerabilities_cluster_severity ON vulnerabilities(cluster_name, severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vulnerabilities_cve ON vulnerabilities(cve_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vulnerabilities_status ON vulnerabilities(remediation_status, detected_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vulnerabilities_component ON vulnerabilities(component_type, affected_component)")
        
        # Compliance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compliance_assessments_cluster_framework ON compliance_assessments(cluster_name, framework_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compliance_assessments_status ON compliance_assessments(compliance_status, assessed_at)")
        
        # Audit trail indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_trail_cluster_time ON audit_trail(cluster_name, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_trail_event_type ON audit_trail(event_type, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_trail_user ON audit_trail(user_name, timestamp)")
        
        # CVE database indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cve_database_severity ON cve_database(severity, published_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cve_database_score ON cve_database(cvss_v3_score)")
        
        logger.info("✅ Database indexes created")
    
    def _insert_initial_data(self, cursor: sqlite3.Cursor):
        """Insert initial reference data"""
        
        # Insert compliance frameworks
        frameworks = [
            ('CIS', 'CIS Kubernetes Benchmark', '1.6.0', 'Center for Internet Security Kubernetes Benchmark', 
             '["Master Node Configuration", "Worker Node Configuration", "Pod Security", "Network Policies", "Storage"]', 100),
            ('NIST', 'NIST Cybersecurity Framework', '1.1', 'National Institute of Standards and Technology Cybersecurity Framework',
             '["Identify", "Protect", "Detect", "Respond", "Recover"]', 108),
            ('SOC2', 'SOC 2 Type II', '2017', 'Service Organization Control 2 Trust Services Criteria',
             '["Security", "Availability", "Processing Integrity", "Confidentiality", "Privacy"]', 64),
            ('ISO27001', 'ISO/IEC 27001', '2013', 'International Information Security Management Standard',
             '["Information Security Policies", "Access Control", "Cryptography", "Physical Security"]', 114),
            ('PCI-DSS', 'PCI Data Security Standard', '3.2.1', 'Payment Card Industry Data Security Standard',
             '["Network Security", "Data Protection", "Vulnerability Management", "Access Control"]', 78),
            ('HIPAA', 'HIPAA Security Rule', '2013', 'Healthcare Information Security and Privacy Regulations',
             '["Administrative Safeguards", "Physical Safeguards", "Technical Safeguards"]', 45)
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO compliance_frameworks 
            (framework_id, name, version, description, categories, total_controls)
            VALUES (?, ?, ?, ?, ?, ?)
        """, frameworks)
        
        # Insert sample policy rules
        policy_rules = [
            ('SEC001', 'No Privileged Containers', 'Containers must not run in privileged mode', 'Security', 'CRITICAL',
             '["Deployment", "Pod", "StatefulSet", "DaemonSet"]',
             'spec.template.spec.containers[*].securityContext.privileged must be false or undefined',
             'Remove privileged: true from container securityContext',
             '{"CIS": "4.2.1", "PCI-DSS": "2.2"}'),
            ('SEC002', 'Non-Root User Required', 'Containers must not run as root user', 'Security', 'HIGH',
             '["Deployment", "Pod", "StatefulSet", "DaemonSet"]',
             'spec.template.spec.containers[*].securityContext.runAsUser must be > 0',
             'Set runAsUser to non-zero value in securityContext',
             '{"CIS": "4.2.6", "NIST": "PR.AC-1"}'),
            ('GOV001', 'Resource Limits Required', 'All containers must have CPU and memory limits', 'Governance', 'MEDIUM',
             '["Deployment", "Pod", "StatefulSet", "DaemonSet"]',
             'spec.template.spec.containers[*].resources.limits must exist',
             'Add CPU and memory limits to container resources',
             '{"FinOps": "Cost Control"}')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO policy_rules 
            (rule_id, name, description, category, severity, resource_types, rule_logic, remediation_template, compliance_mappings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, policy_rules)
        
        logger.info("✅ Initial data inserted")
    
    def _update_schema_version(self, cursor: sqlite3.Cursor):
        """Update schema version"""
        
        cursor.execute("""
            INSERT INTO schema_version (version, description)
            VALUES (?, ?)
        """, (self.schema_version, "Initial security posture database schema"))
    
    def get_schema_version(self) -> Optional[str]:
        """Get current schema version"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get schema version: {e}")
            return None
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create database backup"""
        
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.database_path}.backup_{timestamp}"
        
        try:
            import shutil
            shutil.copy2(self.database_path, backup_path)
            logger.info(f"✅ Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Database backup failed: {e}")
            raise
    
    def vacuum_database(self):
        """Vacuum database to reclaim space and optimize performance"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            logger.info("✅ Database vacuumed and analyzed")
        except Exception as e:
            logger.error(f"❌ Database vacuum failed: {e}")
            raise
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Get table counts
                tables = [
                    'security_scores', 'security_alerts', 'policy_violations',
                    'vulnerabilities', 'compliance_assessments', 'audit_trail'
                ]
                
                stats = {'tables': {}}
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats['tables'][table] = count
                
                # Get database size
                db_size = os.path.getsize(self.database_path)
                stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
                
                # Get schema version
                stats['schema_version'] = self.get_schema_version()
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def cleanup_old_data(self, retention_days: int = 365):
        """Clean up old data based on retention policy"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old security scores (keep latest 100 per cluster)
                cursor.execute("""
                    DELETE FROM security_scores 
                    WHERE id NOT IN (
                        SELECT id FROM security_scores 
                        ORDER BY assessed_at DESC 
                        LIMIT 100
                    ) AND assessed_at < ?
                """, (cutoff_date,))
                
                # Clean up resolved alerts older than retention period
                cursor.execute("""
                    DELETE FROM security_alerts 
                    WHERE resolved = TRUE AND resolved_at < ?
                """, (cutoff_date,))
                
                # Clean up old audit trail entries
                cursor.execute("""
                    DELETE FROM audit_trail 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                # Clean up old system logs
                cursor.execute("""
                    DELETE FROM system_logs 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                conn.commit()
                
            logger.info(f"✅ Cleaned up data older than {retention_days} days")
            
        except Exception as e:
            logger.error(f"❌ Data cleanup failed: {e}")
            raise


# Factory function and utilities
def create_security_database_manager(database_path: str = None) -> SecurityDatabaseManager:
    """Create security database manager instance"""
    return SecurityDatabaseManager(database_path)

def initialize_security_database(database_path: str = None) -> bool:
    """Initialize security database with complete schema"""
    db_manager = create_security_database_manager(database_path)
    return db_manager.initialize_database()

if __name__ == "__main__":
    # Command line usage
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        db_path = sys.argv[2] if len(sys.argv) > 2 else "app/security/data/security_posture.db"
        
        db_manager = create_security_database_manager(db_path)
        
        if command == "init":
            success = db_manager.initialize_database()
            print(f"Database initialization: {'SUCCESS' if success else 'FAILED'}")
        
        elif command == "backup":
            backup_path = db_manager.backup_database()
            print(f"Database backed up to: {backup_path}")
        
        elif command == "vacuum":
            db_manager.vacuum_database()
            print("Database vacuumed successfully")
        
        elif command == "stats":
            stats = db_manager.get_database_stats()
            print(json.dumps(stats, indent=2))
        
        elif command == "cleanup":
            retention_days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
            db_manager.cleanup_old_data(retention_days)
            print(f"Database cleaned up (retention: {retention_days} days)")
        
        else:
            print("Usage: python database_schema.py [init|backup|vacuum|stats|cleanup] [db_path] [retention_days]")
    
    else:
        # Default: initialize database
        success = initialize_security_database()
        print(f"Database initialization: {'SUCCESS' if success else 'FAILED'}")