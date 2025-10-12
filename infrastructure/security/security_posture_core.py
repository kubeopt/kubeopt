#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
AKS Security Posture Core Engine - YAML Configuration Enabled
============================================================
Dynamic ML-based security analysis with YAML-driven configuration.
Replaces hardcoded security standards with configurable YAML policies.
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import the new YAML configuration loader
from shared.utils.security_config_loader import SecurityConfigLoader, load_security_config

logger = logging.getLogger(__name__)

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # POLICY, VULNERABILITY, DRIFT, EXPOSURE
    title: str
    description: str
    resource_type: str
    resource_name: str
    namespace: str
    remediation: str
    risk_score: float
    detected_at: datetime
    metadata: Dict

@dataclass
class SecurityScore:
    """Security score breakdown"""
    overall_score: float  # 0-100
    grade: str  # A, B, C, D, F
    rbac_score: float
    network_score: float
    encryption_score: float
    vulnerability_score: float
    compliance_score: float
    drift_score: float
    trends: Dict
    last_updated: datetime

@dataclass
class ComplianceResult:
    """Compliance assessment result"""
    framework: str  # CIS, NIST, ISO27001, SOC2
    overall_compliance: float
    passed_controls: int
    failed_controls: int
    control_results: List[Dict]
    recommendations: List[str]
    assessed_at: datetime

class SecurityPostureEngineYAML:
    """
    REFACTORED: Security posture analysis engine using YAML configuration
    Replaces all hardcoded security standards with configurable YAML policies
    """
    
    def __init__(self, cluster_config: Dict, database_path: str = None, config_dir: str = None):
        """Initialize security engine with YAML configuration"""
        self.cluster_config = cluster_config
        
        # Initialize YAML configuration loader
        self.config_loader = SecurityConfigLoader(config_dir)
        self.security_config = self.config_loader.load_security_config()
        
        # Use unified database structure
        if database_path is None:
            from infrastructure.persistence.database_config import DatabaseConfig
            self.database_path = str(DatabaseConfig.DATABASES['security_analytics'])
        else:
            self.database_path = database_path
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize ML models with YAML configuration
        self._initialize_ml_models_from_yaml()
        
        # Load security standards from YAML
        self._load_security_standards_from_yaml()
        
        # Load vulnerability database from YAML
        self._load_vulnerability_patterns_from_yaml()
        
        # Initialize database and components
        self._initialize_database()
        
        logger.info("🔐 YAML-Configured Security Posture Engine initialized")
    
    def _initialize_ml_models_from_yaml(self):
        """Initialize ML models using YAML configuration parameters"""
        
        # Get ML parameters from YAML config
        ml_config = self.security_config.ml_parameters
        
        # Anomaly detection model configuration
        anomaly_config = ml_config.get('anomaly_detection', {})
        isolation_forest_config = anomaly_config.get('isolation_forest', {})
        
        self.anomaly_detector = IsolationForest(
            contamination=isolation_forest_config.get('contamination', 0.1),
            random_state=isolation_forest_config.get('random_state', 42),
            n_estimators=isolation_forest_config.get('n_estimators', 100),
            max_samples=isolation_forest_config.get('max_samples', 100)
        )
        
        # Risk classification model configuration
        risk_config = ml_config.get('risk_classification', {})
        self.risk_classifier = RandomForestClassifier(
            n_estimators=risk_config.get('n_estimators', 200),
            max_depth=risk_config.get('max_depth', 10),
            random_state=risk_config.get('random_state', 42)
        )
        
        # Text analysis configuration
        text_config = ml_config.get('text_vectorizer', {})
        self.text_analysis_config = {
            'max_features': text_config.get('max_features', 1000),
            'stop_words': text_config.get('stop_words', 'english'),
            'ngram_range': tuple(text_config.get('ngram_range', [1, 2]))
        }
        
        # Clustering configuration
        cluster_config = ml_config.get('policy_clusterer', {})
        self.cluster_config = {
            'n_clusters': cluster_config.get('n_clusters', 8),
            'random_state': cluster_config.get('random_state', 42)
        }
        
        # Feature scaler for normalization
        self.scaler = StandardScaler()
        
        # Network analysis for attack surface mapping
        self.attack_graph = nx.DiGraph()
        
        # Load risk scoring parameters from YAML
        self.risk_scoring_config = ml_config.get('risk_scoring', {})
        
        logger.info("🧠 ML models initialized from YAML configuration")
    
    def _load_security_standards_from_yaml(self):
        """Load security standards and compliance frameworks from YAML"""
        
        # Load compliance frameworks
        self.compliance_frameworks = self.security_config.compliance_frameworks
        
        # Load CIS controls from YAML (if available) or use dynamic loading
        self.cis_controls = self._load_cis_controls_from_yaml()
        
        # Load NIST framework controls
        self.nist_controls = self._load_nist_controls_from_yaml()
        
        # Load security standards
        self.security_standards = self.security_config.security_standards
        
        # Load rule context
        self.rule_context = self.security_config.rule_context
        
        logger.info("📋 Security standards loaded from YAML configuration")
    
    def _load_cis_controls_from_yaml(self) -> Dict[str, Any]:
        """Load CIS Kubernetes Benchmark controls from YAML or generate dynamically"""
        
        # Try to load from YAML first
        cis_framework = self.compliance_frameworks.get('CIS', {})
        
        # If no detailed controls in YAML, generate standard CIS controls
        # This can be extended to load from external CIS benchmark files
        cis_controls = {
            "1.1.1": {
                "title": "Ensure API server audit log path is set",
                "category": "Master Node Configuration Files",
                "severity": "HIGH",
                "check": self._check_audit_log_path
            },
            "1.1.2": {
                "title": "Ensure API server admission control plugin AlwaysAdmit is not set",
                "category": "Master Node Configuration Files", 
                "severity": "HIGH",
                "check": self._check_admission_control
            },
            "4.2.1": {
                "title": "Minimize the admission of privileged containers",
                "category": "Pod Security Policies",
                "severity": "HIGH",
                "check": self._check_privileged_containers
            },
            "4.2.6": {
                "title": "Minimize the admission of containers with runAsUser of 0",
                "category": "Pod Security Policies", 
                "severity": "MEDIUM",
                "check": self._check_root_containers
            },
            "3.2.1": {
                "title": "Ensure that the --audit-log-path argument is set",
                "category": "Etcd Node Configuration",
                "severity": "HIGH", 
                "check": self._check_etcd_audit_log
            }
        }
        
        # Override with any custom controls from YAML
        yaml_controls = cis_framework.get('controls', {})
        if isinstance(yaml_controls, dict):
            cis_controls.update(yaml_controls)
        
        return cis_controls
    
    def _load_nist_controls_from_yaml(self) -> Dict[str, Any]:
        """Load NIST Cybersecurity Framework controls from YAML"""
        
        nist_framework = self.compliance_frameworks.get('NIST', {})
        
        # Standard NIST functions and categories
        nist_controls = {
            "PR.AC-1": {
                "function": "Protect",
                "category": "Access Control",
                "title": "Identities and credentials are managed for authorized devices and users",
                "check": self._check_identity_management
            },
            "PR.AC-4": {
                "function": "Protect", 
                "category": "Access Control",
                "title": "Access permissions are managed, incorporating the principles of least privilege",
                "check": self._check_least_privilege
            },
            "PR.DS-2": {
                "function": "Protect",
                "category": "Data Security", 
                "title": "Data-in-transit is protected",
                "check": self._check_data_in_transit
            },
            "DE.CM-1": {
                "function": "Detect",
                "category": "Security Continuous Monitoring",
                "title": "The network is monitored to detect potential cybersecurity events",
                "check": self._check_network_monitoring
            }
        }
        
        # Override with any custom controls from YAML
        yaml_controls = nist_framework.get('controls', {})
        if isinstance(yaml_controls, dict):
            nist_controls.update(yaml_controls)
        
        return nist_controls
    
    def _load_vulnerability_patterns_from_yaml(self):
        """Load vulnerability patterns from YAML configuration"""
        
        # Try to load from YAML, with fallback to built-in patterns
        yaml_patterns = self.security_config.rule_context.get('vulnerability_patterns', {})
        
        # Base vulnerability patterns (can be overridden by YAML)
        base_patterns = {
            "exposed_dashboard": {
                "severity": "CRITICAL",
                "cve": "CVE-2018-18264",
                "description": "Kubernetes Dashboard exposed without authentication"
            },
            "privileged_container": {
                "severity": "HIGH", 
                "description": "Container running with privileged access"
            },
            "host_network": {
                "severity": "HIGH",
                "description": "Pod using host network namespace"
            },
            "root_user": {
                "severity": "MEDIUM",
                "description": "Container running as root user"
            },
            "host_pid": {
                "severity": "HIGH",
                "description": "Pod using host PID namespace" 
            },
            "host_ipc": {
                "severity": "MEDIUM",
                "description": "Pod using host IPC namespace"
            },
            "capability_sys_admin": {
                "severity": "HIGH",
                "description": "Container granted SYS_ADMIN capability"
            },
            "insecure_registry": {
                "severity": "MEDIUM", 
                "description": "Using insecure container registry"
            }
        }
        
        # Merge YAML patterns with base patterns
        base_patterns.update(yaml_patterns)
        self.vulnerability_patterns = base_patterns
        
        logger.info(f"🔍 Loaded {len(self.vulnerability_patterns)} vulnerability patterns")
    
    def _initialize_database(self):
        """Initialize SQLite database for security data"""
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Security alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE,
                    severity TEXT,
                    category TEXT,
                    title TEXT,
                    description TEXT,
                    resource_type TEXT,
                    resource_name TEXT,
                    namespace TEXT,
                    remediation TEXT,
                    risk_score REAL,
                    detected_at TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Security scores table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cluster_id TEXT,
                    overall_score REAL,
                    grade TEXT,
                    rbac_score REAL,
                    network_score REAL,
                    encryption_score REAL,
                    vulnerability_score REAL,
                    compliance_score REAL,
                    drift_score REAL,
                    trends TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Compliance results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    framework TEXT,
                    overall_compliance REAL,
                    passed_controls INTEGER,
                    failed_controls INTEGER,
                    control_results TEXT,
                    recommendations TEXT,
                    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
        
        logger.info("💾 Security database initialized")
    
    def get_yaml_config_info(self) -> Dict[str, Any]:
        """Get information about loaded YAML configuration"""
        return self.config_loader.get_config_info()
    
    def reload_yaml_config(self):
        """Reload YAML configuration and reinitialize components"""
        logger.info("🔄 Reloading YAML configuration...")
        
        # Reload configuration
        self.security_config = self.config_loader.reload_config()
        
        # Reinitialize components with new config
        self._initialize_ml_models_from_yaml()
        self._load_security_standards_from_yaml()
        self._load_vulnerability_patterns_from_yaml()
        
        logger.info("✅ YAML configuration reloaded successfully")
    
    def get_risk_score_from_yaml(self, severity: str, category: str = "Security") -> float:
        """Calculate risk score using YAML configuration"""
        
        risk_config = self.risk_scoring_config
        
        # Get base score for severity
        base_scores = risk_config.get('severity_base_scores', {})
        base_score = base_scores.get(severity, 5.0)
        
        # Apply category multiplier
        category_multipliers = risk_config.get('category_multipliers', {})
        category_multiplier = category_multipliers.get(category, 1.0)
        
        # Calculate final score
        final_score = base_score * category_multiplier
        max_score = risk_config.get('max_risk_score', 10.0)
        
        return min(final_score, max_score)
    
    def validate_yaml_config(self) -> List[str]:
        """Validate YAML configuration and return any issues"""
        return self.config_loader.validate_config_files()
    
    async def analyze_security_posture(self) -> SecurityScore:
        """
        YAML-CONFIGURED: Analyze security posture using YAML-driven configuration
        """
        
        logger.info("🔍 Starting YAML-configured security posture analysis...")
        
        if not self.cluster_config or not isinstance(self.cluster_config, dict):
            raise ValueError("Valid cluster configuration required for security analysis")
        
        try:
            # Run parallel security analysis using YAML configuration
            analysis_tasks = [
                self._analyze_rbac_security_yaml(),
                self._analyze_network_security_yaml(),
                self._analyze_encryption_security_yaml(),
                self._analyze_vulnerability_security_yaml(),
                self._analyze_compliance_yaml(),
                self._analyze_drift_detection_yaml()
            ]
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Extract scores with error handling
            scores = {}
            score_names = ['rbac', 'network', 'encryption', 'vulnerability', 'compliance', 'drift']
            
            for i, (name, result) in enumerate(zip(score_names, results)):
                if isinstance(result, Exception):
                    logger.error(f"❌ {name.title()} analysis failed: {result}")
                    scores[name] = 50.0  # Default score for failed analysis
                else:
                    scores[name] = result
            
            # Calculate overall score using YAML weights
            overall_score = self._calculate_overall_score_yaml(scores)
            grade = self._calculate_security_grade(overall_score)
            
            # Create security score object
            security_score = SecurityScore(
                overall_score=overall_score,
                grade=grade,
                rbac_score=scores['rbac'],
                network_score=scores['network'],
                encryption_score=scores['encryption'],
                vulnerability_score=scores['vulnerability'],
                compliance_score=scores['compliance'],
                drift_score=scores['drift'],
                trends=await self._calculate_security_trends(),
                last_updated=datetime.now()
            )
            
            # Store in database
            await self._store_security_score(security_score)
            
            logger.info(f"✅ Security analysis complete - Overall Score: {overall_score:.1f} ({grade})")
            return security_score
            
        except Exception as e:
            logger.error(f"❌ Security posture analysis failed: {e}")
            raise
    
    def _calculate_overall_score_yaml(self, scores: Dict[str, float]) -> float:
        """Calculate overall security score using YAML-configured weights"""
        
        # Get weights from YAML configuration
        analysis_config = self.security_config.policy_analysis
        weights = analysis_config.get('score_weights', {
            'rbac': 0.25,
            'network': 0.20,
            'encryption': 0.20,
            'vulnerability': 0.20,
            'compliance': 0.10,
            'drift': 0.05
        })
        
        # Calculate weighted score
        weighted_score = 0
        total_weight = 0
        
        for component, score in scores.items():
            weight = weights.get(component, 0.1)
            weighted_score += score * weight
            total_weight += weight
        
        # Normalize if weights don't sum to 1
        if total_weight > 0:
            overall_score = weighted_score / total_weight
        else:
            overall_score = sum(scores.values()) / len(scores)
        
        return round(min(100, max(0, overall_score)), 1)
    
    async def _analyze_rbac_security_yaml(self) -> float:
        """YAML-CONFIGURED: Analyze RBAC security using YAML standards"""
        
        # Get RBAC standards from YAML
        auth_standards = self.security_standards.get('authorization', {})
        rbac_enabled = auth_standards.get('enable_rbac', True)
        least_privilege = auth_standards.get('principle_of_least_privilege', True)
        
        # Base score
        score = 100.0
        
        # Check RBAC configuration against YAML standards
        security_resources = self.cluster_config.get('security_resources', {})
        
        # Check if RBAC is enabled (required by YAML config)
        if rbac_enabled:
            rbac_resources = security_resources.get('rbac', {})
            if not rbac_resources or rbac_resources.get('item_count', 0) == 0:
                score -= 30.0
                await self._create_security_alert_yaml(
                    category="POLICY",
                    severity="HIGH", 
                    title="RBAC Not Configured",
                    description="RBAC is required by security standards but not configured"
                )
        
        # Additional RBAC checks based on YAML configuration
        cluster_admin_roles = security_resources.get('clusterroles', {}).get('items', [])
        admin_role_count = sum(1 for role in cluster_admin_roles 
                              if 'cluster-admin' in role.get('metadata', {}).get('name', ''))
        
        if admin_role_count > auth_standards.get('max_cluster_admin_roles', 2):
            score -= 15.0
        
        return max(0, score)
    
    async def _analyze_network_security_yaml(self) -> float:
        """YAML-CONFIGURED: Analyze network security using YAML standards"""
        
        # Get network security standards from YAML
        network_standards = self.security_standards.get('network_security', {})
        require_network_policies = network_standards.get('enable_network_policies', True)
        min_tls_version = network_standards.get('minimum_tls_version', '1.2')
        
        score = 100.0
        
        # Check network policies
        if require_network_policies:
            network_resources = self.cluster_config.get('networking_resources', {})
            network_policies = network_resources.get('networkpolicies', {}).get('item_count', 0)
            
            if network_policies == 0:
                score -= 40.0
                await self._create_security_alert_yaml(
                    category="POLICY",
                    severity="HIGH",
                    title="No Network Policies",
                    description="Network policies are required by security standards"
                )
        
        # Check TLS configuration
        ingresses = self.cluster_config.get('networking_resources', {}).get('ingresses', {}).get('items', [])
        non_tls_ingresses = 0
        
        for ingress in ingresses:
            tls_config = ingress.get('spec', {}).get('tls', [])
            if not tls_config:
                non_tls_ingresses += 1
        
        if non_tls_ingresses > 0:
            score -= min(30.0, non_tls_ingresses * 10)
        
        return max(0, score)
    
    async def _analyze_encryption_security_yaml(self) -> float:
        """YAML-CONFIGURED: Analyze encryption security using YAML standards"""
        
        # Get encryption standards from YAML
        encryption_standards = self.security_standards.get('data_protection', {})
        require_encryption_at_rest = encryption_standards.get('enable_encryption_at_rest', True)
        require_encryption_in_transit = encryption_standards.get('enable_encryption_in_transit', True)
        
        score = 100.0
        
        # Check secrets management
        secrets = self.cluster_config.get('workload_resources', {}).get('secrets', {})
        secrets_count = secrets.get('item_count', 0)
        
        deployments = self.cluster_config.get('workload_resources', {}).get('deployments', {})
        deployment_items = deployments.get('items', [])
        
        if deployment_items:
            deployments_using_secrets = 0
            deployments_with_hardcoded = 0
            
            for deployment in deployment_items:
                template = deployment.get('spec', {}).get('template', {})
                pod_spec = template.get('spec', {})
                
                uses_secrets = False
                has_hardcoded = False
                
                # Check for secret usage and hardcoded credentials
                containers = pod_spec.get('containers', [])
                for container in containers:
                    env_vars = container.get('env', [])
                    for env_var in env_vars:
                        if 'valueFrom' in env_var and 'secretKeyRef' in env_var.get('valueFrom', {}):
                            uses_secrets = True
                        elif env_var.get('value'):
                            name = env_var.get('name', '').lower()
                            if any(pattern in name for pattern in ['password', 'secret', 'key', 'token', 'api']):
                                value = str(env_var.get('value', ''))
                                if value and len(value) > 5 and value not in ['true', 'false', 'none', 'null']:
                                    has_hardcoded = True
                
                if uses_secrets:
                    deployments_using_secrets += 1
                if has_hardcoded:
                    deployments_with_hardcoded += 1
            
            # Calculate secret usage ratio
            secret_usage_ratio = deployments_using_secrets / len(deployment_items)
            
            if secret_usage_ratio < 0.3:
                score -= 20.0
            
            # Penalize hardcoded credentials heavily
            if deployments_with_hardcoded > 0:
                score -= (deployments_with_hardcoded * 15)
                await self._create_security_alert_yaml(
                    category="VULNERABILITY",
                    severity="CRITICAL",
                    title="Hardcoded Credentials Detected",
                    description=f"{deployments_with_hardcoded} deployments may have hardcoded credentials"
                )
        
        return max(0, score)
    
    async def _analyze_vulnerability_security_yaml(self) -> float:
        """YAML-CONFIGURED: Analyze vulnerabilities using YAML patterns"""
        
        score = 100.0
        vulnerabilities_found = 0
        
        # Check against YAML-configured vulnerability patterns
        for pattern_name, pattern_config in self.vulnerability_patterns.items():
            vulnerability_count = await self._check_vulnerability_pattern_yaml(pattern_name, pattern_config)
            
            if vulnerability_count > 0:
                vulnerabilities_found += vulnerability_count
                severity = pattern_config.get('severity', 'MEDIUM')
                penalty = self._get_vulnerability_penalty_yaml(severity)
                score -= (vulnerability_count * penalty)
        
        if vulnerabilities_found > 0:
            logger.warning(f"🚨 Found {vulnerabilities_found} security vulnerabilities")
        
        return max(0, score)
    
    def _get_vulnerability_penalty_yaml(self, severity: str) -> float:
        """Get vulnerability penalty based on YAML configuration"""
        
        penalties = self.risk_scoring_config.get('vulnerability_penalties', {
            'CRITICAL': 25.0,
            'HIGH': 15.0,
            'MEDIUM': 10.0,
            'LOW': 5.0
        })
        
        return penalties.get(severity, 10.0)
    
    async def _check_vulnerability_pattern_yaml(self, pattern_name: str, pattern_config: Dict) -> int:
        """Check for specific vulnerability pattern using YAML configuration"""
        
        count = 0
        
        if pattern_name == "privileged_container":
            deployments = self.cluster_config.get('workload_resources', {}).get('deployments', {}).get('items', [])
            for deployment in deployments:
                containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
                for container in containers:
                    if container.get('securityContext', {}).get('privileged', False):
                        count += 1
        
        elif pattern_name == "root_user":
            deployments = self.cluster_config.get('workload_resources', {}).get('deployments', {}).get('items', [])
            for deployment in deployments:
                containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
                for container in containers:
                    run_as_user = container.get('securityContext', {}).get('runAsUser', 0)
                    if run_as_user == 0:
                        count += 1
        
        # Add more pattern checks as needed based on YAML configuration
        
        return count
    
    async def _analyze_compliance_yaml(self) -> float:
        """YAML-CONFIGURED: Analyze compliance using YAML frameworks"""
        
        compliance_scores = []
        
        # Check compliance against each YAML-configured framework
        for framework_id, framework_config in self.compliance_frameworks.items():
            framework_score = await self._check_compliance_framework_yaml(framework_id, framework_config)
            
            # Weight by framework priority
            priority_weight = framework_config.get('priority_weight', 1.0)
            weighted_score = framework_score * priority_weight
            compliance_scores.append(weighted_score)
        
        if compliance_scores:
            return sum(compliance_scores) / len(compliance_scores)
        else:
            return 85.0  # Default if no frameworks configured
    
    async def _check_compliance_framework_yaml(self, framework_id: str, framework_config: Dict) -> float:
        """Check compliance against specific framework using YAML configuration"""
        
        # This is a simplified implementation - in practice, this would check
        # specific controls defined in the YAML configuration
        
        if framework_id == "CIS":
            return await self._check_cis_compliance_yaml()
        elif framework_id == "NIST":
            return await self._check_nist_compliance_yaml()
        else:
            # Generic compliance check
            return 80.0
    
    async def _check_cis_compliance_yaml(self) -> float:
        """Check CIS compliance using YAML-configured controls"""
        
        total_controls = len(self.cis_controls)
        passed_controls = 0
        
        for control_id, control_config in self.cis_controls.items():
            check_function = control_config.get('check')
            if check_function and await check_function():
                passed_controls += 1
        
        if total_controls > 0:
            return (passed_controls / total_controls) * 100
        else:
            return 90.0
    
    async def _check_nist_compliance_yaml(self) -> float:
        """Check NIST compliance using YAML-configured controls"""
        
        total_controls = len(self.nist_controls)
        passed_controls = 0
        
        for control_id, control_config in self.nist_controls.items():
            check_function = control_config.get('check')
            if check_function and await check_function():
                passed_controls += 1
        
        if total_controls > 0:
            return (passed_controls / total_controls) * 100
        else:
            return 85.0
    
    async def _analyze_drift_detection_yaml(self) -> float:
        """YAML-CONFIGURED: Analyze configuration drift using YAML standards"""
        
        score = 100.0
        
        # Use YAML configuration for drift detection parameters
        drift_config = self.security_config.policy_analysis.get('drift_detection', {})
        drift_threshold = drift_config.get('drift_threshold', 0.1)
        
        # Implement drift detection logic here based on YAML configuration
        # This is a placeholder implementation
        
        return score
    
    async def _create_security_alert_yaml(self, category: str, severity: str, 
                                         title: str, description: str, 
                                         resource_type: str = "Cluster",
                                         resource_name: str = "default",
                                         namespace: str = "default",
                                         remediation: str = "Review security configuration"):
        """Create security alert using YAML-configured risk scoring"""
        
        risk_score = self.get_risk_score_from_yaml(severity, category)
        
        alert = SecurityAlert(
            alert_id=f"alert_{int(datetime.now().timestamp())}_{hash(title) % 1000}",
            severity=severity,
            category=category,
            title=title,
            description=description,
            resource_type=resource_type,
            resource_name=resource_name,
            namespace=namespace,
            remediation=remediation,
            risk_score=risk_score,
            detected_at=datetime.now(),
            metadata={"source": "yaml_config", "config_version": self.security_config.integration.get('version', '1.0')}
        )
        
        # Store alert in database
        await self._store_security_alert(alert)
    
    async def _store_security_alert(self, alert: SecurityAlert):
        """Store security alert in database"""
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cluster_id = self.cluster_config.get('cluster_name', 'default')
            cursor.execute("""
                INSERT OR REPLACE INTO security_alerts 
                (cluster_id, alert_id, severity, category, title, description, resource_type, 
                 resource_name, namespace, remediation, risk_score, detected_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cluster_id, alert.alert_id, alert.severity, alert.category, alert.title,
                alert.description, alert.resource_type, alert.resource_name,
                alert.namespace, alert.remediation, alert.risk_score,
                alert.detected_at, json.dumps(alert.metadata)
            ))
            conn.commit()
    
    async def _store_security_score(self, score: SecurityScore):
        """Store security score in database"""
        
        cluster_id = self.cluster_config.get('cluster_name', 'default')
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO security_scores 
                (cluster_id, overall_score, grade, rbac_score, network_score, 
                 encryption_score, vulnerability_score, compliance_score, drift_score, trends)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cluster_id, score.overall_score, score.grade, score.rbac_score,
                score.network_score, score.encryption_score, score.vulnerability_score,
                score.compliance_score, score.drift_score, json.dumps(score.trends)
            ))
            conn.commit()
    
    def _calculate_security_grade(self, overall_score: float) -> str:
        """Calculate security grade from overall score"""
        
        # Get grading thresholds from YAML or use defaults
        grading_config = self.security_config.policy_analysis.get('grading_thresholds', {
            'A': 90,
            'B': 80,
            'C': 70,
            'D': 60
        })
        
        if overall_score >= grading_config.get('A', 90):
            return 'A'
        elif overall_score >= grading_config.get('B', 80):
            return 'B'
        elif overall_score >= grading_config.get('C', 70):
            return 'C'
        elif overall_score >= grading_config.get('D', 60):
            return 'D'
        else:
            return 'F'
    
    async def _calculate_security_trends(self) -> Dict[str, Any]:
        """Calculate security trends from historical data"""
        
        # Placeholder implementation
        return {
            "trend_direction": "improving",
            "score_change": 2.5,
            "last_7_days": [],
            "alerts_trend": "decreasing"
        }
    
    # Placeholder check functions for CIS and NIST controls
    async def _check_audit_log_path(self) -> bool:
        return True  # Placeholder
    
    async def _check_admission_control(self) -> bool:
        return True  # Placeholder
    
    async def _check_privileged_containers(self) -> bool:
        return True  # Placeholder
    
    async def _check_root_containers(self) -> bool:
        return True  # Placeholder
    
    async def _check_etcd_audit_log(self) -> bool:
        return True  # Placeholder
    
    async def _check_identity_management(self) -> bool:
        return True  # Placeholder
    
    async def _check_least_privilege(self) -> bool:
        return True  # Placeholder
    
    async def _check_data_in_transit(self) -> bool:
        return True  # Placeholder
    
    async def _check_network_monitoring(self) -> bool:
        return True  # Placeholder

# Factory function for integration
def create_security_posture_engine(cluster_config: Dict, database_path: str = None, config_dir: str = None) -> SecurityPostureEngineYAML:
    """Create YAML-configured security posture engine instance"""
    return SecurityPostureEngineYAML(cluster_config, database_path, config_dir)