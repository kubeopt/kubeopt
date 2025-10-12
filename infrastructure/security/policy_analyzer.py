#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Dynamic Policy Analyzer for AKS Security Posture - YAML Configuration Enabled
===============================================================================
ML-powered policy violation detection using YAML-configurable policies and standards.
Replaces hardcoded policy rules with flexible YAML configuration.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import yaml
from pathlib import Path

# Import the YAML configuration loader
from shared.utils.security_config_loader import SecurityConfigLoader, load_security_config

logger = logging.getLogger(__name__)

@dataclass
class PolicyViolation:
    """Policy violation data structure"""
    violation_id: str
    policy_name: str
    policy_category: str
    severity: str
    resource_type: str
    resource_name: str
    namespace: str
    violation_description: str
    current_value: Any
    expected_value: Any
    remediation_steps: List[str]
    auto_remediable: bool
    compliance_frameworks: List[str]
    detected_at: datetime
    risk_score: float
    additional_context: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __hash__(self):
        """Make PolicyViolation hashable for use in sets and as dict keys"""
        return hash(self.violation_id)
    
    def __eq__(self, other):
        """Equality comparison based on violation_id"""
        if not isinstance(other, PolicyViolation):
            return False
        return self.violation_id == other.violation_id

@dataclass
class PolicyRule:
    """Policy rule definition from YAML"""
    rule_id: str
    name: str
    description: str
    category: str
    severity: str
    resource_types: List[str]
    rule_logic: str
    remediation_template: str
    compliance_mappings: Dict[str, str]
    enabled: bool
    auto_remediable: bool = False
    risk_multiplier: float = 1.0

    def __hash__(self):
        """Make PolicyRule hashable"""
        return hash(self.rule_id)
    
    def __eq__(self, other):
        """Equality comparison based on rule_id"""
        if not isinstance(other, PolicyRule):
            return False
        return self.rule_id == other.rule_id

@dataclass 
class GovernanceReport:
    """Governance compliance report"""
    report_id: str
    framework: str
    overall_compliance: float
    policy_violations: List[PolicyViolation]
    compliance_by_category: Dict[str, float]
    recommendations: List[str]
    generated_at: datetime

    def __hash__(self):
        """Make GovernanceReport hashable"""
        return hash(self.report_id)

class DynamicPolicyAnalyzerYAML:
    """
    REFACTORED: Dynamic policy analyzer using YAML configuration
    Replaces all hardcoded policy rules with configurable YAML policies
    """
    
    def __init__(self, cluster_config: Dict, config_dir: str = None):
        """Initialize policy analyzer with YAML configuration"""
        self.cluster_config = cluster_config
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Initialize YAML configuration loader
        self.config_loader = SecurityConfigLoader(config_dir)
        self.security_config = self.config_loader.load_security_config()
        
        # Load policy rules from YAML
        self._load_policy_rules_from_yaml()
        
        # Load compliance frameworks from YAML
        self._load_compliance_frameworks_from_yaml()
        
        # Load rule context from YAML
        self._load_rule_context_from_yaml()
        
        # Initialize ML models with YAML configuration
        self._initialize_ml_models_from_yaml()
        
        logger.info("🛡️ YAML-Configured Dynamic Policy Analyzer initialized")
    
    def _load_policy_rules_from_yaml(self):
        """Load policy rules from YAML configuration"""
        
        yaml_policy_rules = self.security_config.policy_rules
        self.policy_rules = {}
        
        for rule_key, rule_data in yaml_policy_rules.items():
            try:
                policy_rule = PolicyRule(
                    rule_id=rule_data.get('rule_id'),
                    name=rule_data.get('name'),
                    description=rule_data.get('description'),
                    category=rule_data.get('category'),
                    severity=rule_data.get('severity'),
                    resource_types=rule_data.get('resource_types', []),
                    rule_logic=rule_data.get('rule_logic'),
                    remediation_template=rule_data.get('remediation_template'),
                    compliance_mappings=rule_data.get('compliance_mappings', {}),
                    enabled=rule_data.get('enabled', True),
                    auto_remediable=rule_data.get('auto_remediable', False),
                    risk_multiplier=rule_data.get('risk_multiplier', 1.0)
                )
                self.policy_rules[rule_key] = policy_rule
                
            except Exception as e:
                logger.error(f"❌ Failed to load policy rule {rule_key}: {e}")
                continue
        
        logger.info(f"📋 Loaded {len(self.policy_rules)} policy rules from YAML")
    
    def _load_compliance_frameworks_from_yaml(self):
        """Load compliance frameworks from YAML configuration"""
        
        self.compliance_frameworks = self.security_config.compliance_frameworks
        logger.info(f"🎯 Loaded {len(self.compliance_frameworks)} compliance frameworks from YAML")
    
    def _load_rule_context_from_yaml(self):
        """Load rule evaluation context from YAML configuration"""
        
        yaml_context = self.security_config.rule_context
        
        self.rule_context = {
            "required_labels": yaml_context.get('required_labels', []),
            "forbidden_capabilities": yaml_context.get('forbidden_capabilities', []),
            "trusted_registries": yaml_context.get('trusted_registries', []),
            "max_resource_limits": yaml_context.get('max_resource_limits', {}),
            "security_policies": yaml_context.get('security_policies', []),
            "system_namespaces": yaml_context.get('system_namespaces', [])
        }
        
        logger.info("⚖️ Rule evaluation context loaded from YAML")
    
    def _initialize_ml_models_from_yaml(self):
        """Initialize ML models using YAML configuration parameters"""
        
        ml_config = self.security_config.ml_parameters
        
        # Text analysis for policy descriptions
        text_config = ml_config.get('text_vectorizer', {})
        self.text_vectorizer = TfidfVectorizer(
            max_features=text_config.get('max_features', 1000),
            stop_words=text_config.get('stop_words', 'english'),
            ngram_range=tuple(text_config.get('ngram_range', [1, 2]))
        )
        
        # Policy clustering for pattern detection
        cluster_config = ml_config.get('policy_clusterer', {})
        self.policy_clusterer = KMeans(
            n_clusters=cluster_config.get('n_clusters', 8),
            random_state=cluster_config.get('random_state', 42)
        )
        
        # Severity classification model
        classifier_config = ml_config.get('severity_classifier', {})
        self.severity_classifier = RandomForestClassifier(
            n_estimators=classifier_config.get('n_estimators', 100),
            random_state=classifier_config.get('random_state', 42)
        )
        
        # Label encoder for categorical data
        self.label_encoder = LabelEncoder()
        
        # Load risk scoring configuration
        self.risk_scoring_config = ml_config.get('risk_scoring', {})
        
        # Pre-train models with policy data
        self._pretrain_policy_models_yaml()
        
        logger.info("🧠 Policy ML models initialized from YAML configuration")
    
    def _pretrain_policy_models_yaml(self):
        """Pre-train ML models with YAML-configured policy data"""
        
        # Generate training descriptions from YAML policy rules
        policy_descriptions = []
        severity_labels = []
        
        for rule_key, policy_rule in self.policy_rules.items():
            policy_descriptions.append(policy_rule.description)
            severity_labels.append(policy_rule.severity)
        
        # Expand dataset if needed
        if len(policy_descriptions) < 10:
            # Add some default descriptions if YAML has too few
            default_descriptions = [
                "Container running with privileged access violates security policy",
                "Pod missing required security context settings",
                "Service exposed without proper network policies",
                "Missing required labels for governance compliance",
                "Deployment lacks resource limits and requests"
            ]
            policy_descriptions.extend(default_descriptions)
            severity_labels.extend(["HIGH", "MEDIUM", "HIGH", "MEDIUM", "MEDIUM"])
        
        # Expand for training
        training_descriptions = policy_descriptions * max(1, 20 // len(policy_descriptions))
        training_severities = severity_labels * max(1, 20 // len(severity_labels))
        
        try:
            # Train text vectorizer
            description_vectors = self.text_vectorizer.fit_transform(training_descriptions)
            
            # Train clustering model
            self.policy_clusterer.fit(description_vectors.toarray())
            
            # Train severity classifier
            severity_encoded = self.label_encoder.fit_transform(training_severities)
            self.severity_classifier.fit(description_vectors.toarray(), severity_encoded)
            
            logger.info("✅ Policy ML models pre-trained with YAML data")
            
        except Exception as e:
            logger.warning(f"⚠️ ML model training failed, using defaults: {e}")
    
    def get_yaml_config_info(self) -> Dict[str, Any]:
        """Get information about loaded YAML configuration"""
        return self.config_loader.get_config_info()
    
    def reload_yaml_config(self):
        """Reload YAML configuration and reinitialize components"""
        logger.info("🔄 Reloading YAML configuration...")
        
        # Reload configuration
        self.security_config = self.config_loader.reload_config()
        
        # Reinitialize components with new config
        self._load_policy_rules_from_yaml()
        self._load_compliance_frameworks_from_yaml()
        self._load_rule_context_from_yaml()
        self._initialize_ml_models_from_yaml()
        
        logger.info("✅ YAML configuration reloaded successfully")
    
    def add_custom_policy_rule(self, rule_key: str, rule_data: Dict[str, Any]):
        """Add custom policy rule at runtime"""
        
        try:
            policy_rule = PolicyRule(
                rule_id=rule_data.get('rule_id'),
                name=rule_data.get('name'),
                description=rule_data.get('description'),
                category=rule_data.get('category'),
                severity=rule_data.get('severity'),
                resource_types=rule_data.get('resource_types', []),
                rule_logic=rule_data.get('rule_logic'),
                remediation_template=rule_data.get('remediation_template'),
                compliance_mappings=rule_data.get('compliance_mappings', {}),
                enabled=rule_data.get('enabled', True),
                auto_remediable=rule_data.get('auto_remediable', False),
                risk_multiplier=rule_data.get('risk_multiplier', 1.0)
            )
            
            self.policy_rules[rule_key] = policy_rule
            logger.info(f"✅ Added custom policy rule: {rule_key}")
            
        except Exception as e:
            logger.error(f"❌ Failed to add custom policy rule {rule_key}: {e}")
    
    def disable_policy_rule(self, rule_key: str):
        """Disable a specific policy rule"""
        if rule_key in self.policy_rules:
            self.policy_rules[rule_key].enabled = False
            logger.info(f"🔇 Disabled policy rule: {rule_key}")
    
    def enable_policy_rule(self, rule_key: str):
        """Enable a specific policy rule"""
        if rule_key in self.policy_rules:
            self.policy_rules[rule_key].enabled = True
            logger.info(f"🔊 Enabled policy rule: {rule_key}")
    
    def get_enabled_policy_rules(self) -> Dict[str, PolicyRule]:
        """Get only enabled policy rules"""
        return {k: v for k, v in self.policy_rules.items() if v.enabled}
    
    def get_policy_rules_by_category(self, category: str) -> Dict[str, PolicyRule]:
        """Get policy rules filtered by category"""
        return {k: v for k, v in self.policy_rules.items() if v.category == category and v.enabled}
    
    def get_policy_rules_by_severity(self, severity: str) -> Dict[str, PolicyRule]:
        """Get policy rules filtered by severity"""
        return {k: v for k, v in self.policy_rules.items() if v.severity == severity and v.enabled}
    
    async def analyze_policy_compliance(self) -> GovernanceReport:
        """
        YAML-CONFIGURED: Analyze policy compliance using YAML-defined rules
        """
        
        logger.info("🛡️ Starting YAML-configured policy compliance analysis...")
        
        if not self.cluster_config or self.cluster_config.get('status') != 'completed':
            raise ValueError("Valid cluster configuration required for policy analysis")
        
        violations = []
        
        # Analyze against all enabled YAML policy rules
        enabled_rules = self.get_enabled_policy_rules()
        
        analysis_tasks = [
            self._analyze_yaml_policy_category("Security"),
            self._analyze_yaml_policy_category("Network"),
            self._analyze_yaml_policy_category("Governance"),
            self._analyze_yaml_policy_category("Compliance")
        ]
        
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Collect violations from all categories
        for result in results:
            if isinstance(result, list):
                violations.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Policy analysis failed: {result}")
        
        # Calculate compliance using YAML configuration
        compliance_by_category = self._calculate_compliance_yaml(violations)
        overall_compliance = self._calculate_overall_compliance_yaml(violations, compliance_by_category)
        
        # Generate recommendations using YAML-enhanced ML
        recommendations = self._generate_recommendations_yaml(violations)
        
        report = GovernanceReport(
            report_id=f"yaml_policy_report_{int(datetime.now().timestamp())}",
            framework="YAML-Configured Policy Analysis",
            overall_compliance=overall_compliance,
            policy_violations=violations,
            compliance_by_category=compliance_by_category,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
        
        logger.info(f"✅ YAML policy analysis complete - Compliance: {overall_compliance:.1f}%")
        return report
    
    async def _analyze_yaml_policy_category(self, category: str) -> List[PolicyViolation]:
        """Analyze policy violations for a specific category using YAML rules"""
        
        violations = []
        category_rules = self.get_policy_rules_by_category(category)
        
        if not category_rules:
            logger.warning(f"No enabled {category} policies found in YAML configuration")
            return violations
        
        logger.info(f"🔍 Analyzing {len(category_rules)} {category} policies from YAML")
        
        # Analyze each YAML-configured policy rule
        for rule_key, policy_rule in category_rules.items():
            try:
                rule_violations = await self._analyze_policy_rule_yaml(rule_key, policy_rule)
                violations.extend(rule_violations)
                
            except Exception as e:
                logger.error(f"❌ Failed to analyze policy rule {rule_key}: {e}")
                continue
        
        # ML-based pattern enhancement
        if violations and len(violations) > 2:
            violations = await self._enhance_violations_with_ml_yaml(violations)
        
        logger.info(f"📊 Found {len(violations)} {category} policy violations")
        return violations
    
    async def _analyze_policy_rule_yaml(self, rule_key: str, policy_rule: PolicyRule) -> List[PolicyViolation]:
        """Analyze a specific YAML-configured policy rule"""
        
        violations = []
        
        # Get resources to check based on policy rule resource types
        for resource_type in policy_rule.resource_types:
            resources = self._get_resources_by_type_yaml(resource_type)
            
            for resource in resources:
                if not isinstance(resource, dict):
                    continue
                
                # Evaluate policy rule against resource
                violation_context = await self._evaluate_policy_rule_yaml(resource, policy_rule)
                
                if violation_context:
                    violation = await self._create_policy_violation_yaml(
                        policy_rule=policy_rule,
                        resource_name=violation_context['resource_name'],
                        namespace=violation_context['namespace'],
                        current_value=violation_context['current_value'],
                        expected_value=violation_context['expected_value'],
                        additional_context=violation_context.get('context', {})
                    )
                    violations.append(violation)
        
        return violations
    
    async def _evaluate_policy_rule_yaml(self, resource: Dict, policy_rule: PolicyRule) -> Optional[Dict]:
        """Evaluate YAML-configured policy rule against resource"""
        
        # Extract resource metadata
        metadata = resource.get('metadata', {})
        resource_name = metadata.get('name', 'unknown')
        namespace = metadata.get('namespace', 'default')
        
        # Dynamic rule evaluation based on YAML rule logic
        rule_logic = policy_rule.rule_logic
        violation_context = None
        
        # Dispatch to specific evaluation methods based on rule logic patterns
        if 'securityContext' in rule_logic:
            violation_context = await self._evaluate_security_context_rule_yaml(resource, rule_logic)
        elif 'resources.limits' in rule_logic:
            violation_context = await self._evaluate_resource_limits_rule_yaml(resource, rule_logic)
        elif 'labels' in rule_logic:
            violation_context = await self._evaluate_labels_rule_yaml(resource, rule_logic)
        elif 'NetworkPolicy' in rule_logic:
            violation_context = await self._evaluate_network_policy_rule_yaml(resource, rule_logic)
        elif 'tls' in rule_logic:
            violation_context = await self._evaluate_tls_rule_yaml(resource, rule_logic)
        elif 'imagePullPolicy' in rule_logic:
            violation_context = await self._evaluate_image_pull_policy_rule_yaml(resource, rule_logic)
        elif 'capabilities' in rule_logic:
            violation_context = await self._evaluate_capabilities_rule_yaml(resource, rule_logic)
        else:
            # Generic evaluation for custom rules
            violation_context = await self._evaluate_generic_rule_yaml(resource, rule_logic)
        
        if violation_context:
            violation_context['resource_name'] = resource_name
            violation_context['namespace'] = namespace
        
        return violation_context
    
    async def _evaluate_security_context_rule_yaml(self, resource: Dict, rule_logic: str) -> Optional[Dict]:
        """Evaluate security context rules using YAML configuration"""
        
        containers = self._extract_containers_from_resource(resource)
        
        for container in containers:
            container_name = container.get('name', 'unknown')
            security_context = container.get('securityContext', {})
            
            # Check for privileged containers (YAML configured)
            if 'privileged must be false' in rule_logic:
                if security_context.get('privileged', False) == True:
                    return {
                        'current_value': 'privileged: true',
                        'expected_value': 'privileged: false or undefined',
                        'context': {'container': container_name, 'security_field': 'privileged'}
                    }
            
            # Check for root user (YAML configured)
            if 'runAsUser must be > 0' in rule_logic:
                run_as_user = security_context.get('runAsUser', None)
                if run_as_user is not None and run_as_user == 0:
                    return {
                        'current_value': f'runAsUser: {run_as_user}',
                        'expected_value': 'runAsUser > 0',
                        'context': {'container': container_name, 'security_field': 'runAsUser'}
                    }
            
            # Check for security context existence (YAML configured)
            if 'securityContext must exist' in rule_logic:
                if not security_context:
                    return {
                        'current_value': 'no securityContext defined',
                        'expected_value': 'securityContext with proper settings',
                        'context': {'container': container_name, 'missing': 'securityContext'}
                    }
            
            # Check for forbidden capabilities (YAML configured)
            capabilities = security_context.get('capabilities', {})
            if capabilities:
                added_caps = capabilities.get('add', [])
                forbidden_caps = self.rule_context.get('forbidden_capabilities', [])
                
                for cap in added_caps:
                    if cap in forbidden_caps:
                        return {
                            'current_value': f'capability: {cap}',
                            'expected_value': f'capability {cap} not allowed',
                            'context': {'container': container_name, 'forbidden_capability': cap}
                        }
        
        return None
    
    async def _evaluate_resource_limits_rule_yaml(self, resource: Dict, rule_logic: str) -> Optional[Dict]:
        """Evaluate resource limits rules using YAML configuration"""
        
        containers = self._extract_containers_from_resource(resource)
        
        for container in containers:
            container_name = container.get('name', 'unknown')
            resources = container.get('resources', {})
            limits = resources.get('limits', {})
            
            if 'limits must exist' in rule_logic:
                if not limits:
                    return {
                        'current_value': 'no resource limits defined',
                        'expected_value': 'cpu and memory limits required',
                        'context': {'container': container_name, 'missing': ['cpu', 'memory']}
                    }
                
                missing_limits = []
                if 'cpu' not in limits:
                    missing_limits.append('cpu')
                if 'memory' not in limits:
                    missing_limits.append('memory')
                
                if missing_limits:
                    return {
                        'current_value': f'missing limits: {", ".join(missing_limits)}',
                        'expected_value': 'all resource limits defined',
                        'context': {'container': container_name, 'missing_limits': missing_limits}
                    }
            
            # Check against max limits from YAML configuration
            max_limits = self.rule_context.get('max_resource_limits', {})
            for resource_type, limit_value in limits.items():
                max_value = max_limits.get(resource_type)
                if max_value and self._compare_resource_values(limit_value, max_value) > 0:
                    return {
                        'current_value': f'{resource_type}: {limit_value}',
                        'expected_value': f'{resource_type} <= {max_value}',
                        'context': {'container': container_name, 'exceeded_resource': resource_type}
                    }
        
        return None
    
    async def _evaluate_labels_rule_yaml(self, resource: Dict, rule_logic: str) -> Optional[Dict]:
        """Evaluate label requirements using YAML configuration"""
        
        metadata = resource.get('metadata', {})
        labels = metadata.get('labels', {})
        
        if 'must contain' in rule_logic:
            # Get required labels from YAML configuration
            required_labels = self.rule_context.get('required_labels', [])
            
            missing_labels = [label for label in required_labels if label not in labels]
            
            if missing_labels:
                return {
                    'current_value': f'missing labels: {", ".join(missing_labels)}',
                    'expected_value': f'all required labels: {", ".join(required_labels)}',
                    'context': {'missing_labels': missing_labels, 'existing_labels': list(labels.keys())}
                }
        
        # Validate label values using YAML patterns
        invalid_labels = await self._validate_label_values_yaml(labels)
        if invalid_labels:
            return {
                'current_value': f'invalid label values: {invalid_labels}',
                'expected_value': 'valid label values according to YAML standards',
                'context': {'invalid_labels': invalid_labels}
            }
        
        return None
    
    async def _evaluate_network_policy_rule_yaml(self, resource: Dict, rule_logic: str) -> Optional[Dict]:
        """Evaluate network policy requirements using YAML configuration"""
        
        # For namespace resources, check if network policies exist
        if resource.get('kind') == 'Namespace' or 'namespace' in str(resource.get('metadata', {})):
            namespace_name = resource.get('metadata', {}).get('name', 'unknown')
            
            # Skip system namespaces defined in YAML
            system_namespaces = self.rule_context.get('system_namespaces', [])
            if namespace_name in system_namespaces:
                return None
            
            if 'NetworkPolicy must exist' in rule_logic:
                has_network_policy = await self._check_namespace_has_network_policy_yaml(namespace_name)
                
                if not has_network_policy:
                    return {
                        'current_value': 'no network policies defined',
                        'expected_value': 'at least one network policy for traffic control',
                        'context': {'namespace': namespace_name, 'policy_type': 'NetworkPolicy'}
                    }
        
        return None
    
    async def _evaluate_tls_rule_yaml(self, resource: Dict, rule_logic: str) -> Optional[Dict]:
        """Evaluate TLS configuration requirements using YAML configuration"""
        
        if resource.get('kind') == 'Ingress' or 'ingress' in str(resource.get('metadata', {})).lower():
            spec = resource.get('spec', {})
            tls_config = spec.get('tls', [])
            
            if 'tls must be defined' in rule_logic:
                if not tls_config:
                    return {
                        'current_value': 'no TLS configuration',
                        'expected_value': 'TLS certificates and hosts configured',
                        'context': {'missing': 'tls_configuration'}
                    }
                
                # Validate TLS configuration
                for tls_entry in tls_config:
                    if not tls_entry.get('secretName'):
                        return {
                            'current_value': 'TLS entry without certificate secret',
                            'expected_value': 'valid certificate secret reference',
                            'context': {'invalid_tls': 'missing_secret'}
                        }
        
        return None
    
    async def _evaluate_image_pull_policy_rule_yaml(self, resource: Dict, rule_logic: str) -> Optional[Dict]:
        """Evaluate image pull policy requirements using YAML configuration"""
        
        containers = self._extract_containers_from_resource(resource)
        
        for container in containers:
            container_name = container.get('name', 'unknown')
            image = container.get('image', '')
            image_pull_policy = container.get('imagePullPolicy', 'IfNotPresent')
            
            if 'imagePullPolicy must be Always' in rule_logic:
                if image_pull_policy != 'Always':
                    return {
                        'current_value': f'imagePullPolicy: {image_pull_policy}',
                        'expected_value': 'imagePullPolicy: Always',
                        'context': {'container': container_name, 'image': image}
                    }
            
            # Validate image registry using YAML trusted registries
            trusted_registries = self.rule_context.get('trusted_registries', [])
            if not self._is_image_from_trusted_registry_yaml(image, trusted_registries):
                return {
                    'current_value': f'image from untrusted registry: {image}',
                    'expected_value': f'image from trusted registries: {", ".join(trusted_registries)}',
                    'context': {'container': container_name, 'untrusted_image': image}
                }
        
        return None
    
    async def _evaluate_capabilities_rule_yaml(self, resource: Dict, rule_logic: str) -> Optional[Dict]:
        """Evaluate capabilities requirements using YAML configuration"""
        
        containers = self._extract_containers_from_resource(resource)
        
        for container in containers:
            container_name = container.get('name', 'unknown')
            security_context = container.get('securityContext', {})
            capabilities = security_context.get('capabilities', {})
            
            if 'capabilities.drop must include ALL' in rule_logic:
                dropped_caps = capabilities.get('drop', [])
                if 'ALL' not in dropped_caps:
                    return {
                        'current_value': f'dropped capabilities: {dropped_caps}',
                        'expected_value': 'capabilities.drop must include ALL',
                        'context': {'container': container_name, 'missing_drop': 'ALL'}
                    }
        
        return None
    
    async def _evaluate_generic_rule_yaml(self, resource: Dict, rule_logic: str) -> Optional[Dict]:
        """Generic evaluation for custom YAML-defined rules"""
        
        # This is a placeholder for custom rule evaluation
        # Can be extended to support complex YAML-defined rule logic
        
        # For now, return None (no violation) for unrecognized rule logic
        return None
    
    def _get_resources_by_type_yaml(self, resource_type: str) -> List[Dict]:
        """Get resources by type from cluster config using YAML configuration"""
        
        workload_resources = self.cluster_config.get('workload_resources', {}) or {}
        security_resources = self.cluster_config.get('security_resources', {}) or {}
        networking_resources = self.cluster_config.get('networking_resources', {}) or {}
        
        # Resource type mapping
        resource_mapping = {
            'Deployment': lambda: workload_resources.get('deployments', {}).get('items', []),
            'Pod': lambda: workload_resources.get('pods', {}).get('items', []),
            'StatefulSet': lambda: workload_resources.get('statefulsets', {}).get('items', []),
            'DaemonSet': lambda: workload_resources.get('daemonsets', {}).get('items', []),
            'Service': lambda: workload_resources.get('services', {}).get('items', []),
            'Namespace': lambda: workload_resources.get('namespaces', {}).get('items', []),
            'Ingress': lambda: networking_resources.get('ingresses', {}).get('items', []),
            'NetworkPolicy': lambda: networking_resources.get('networkpolicies', {}).get('items', []),
            'PodSecurityPolicy': lambda: security_resources.get('podsecuritypolicies', {}).get('items', [])
        }
        
        if resource_type in resource_mapping:
            resources = resource_mapping[resource_type]() or []
            return [r for r in resources if isinstance(r, dict)]
        
        return []
    
    async def _create_policy_violation_yaml(self, policy_rule: PolicyRule, resource_name: str, 
                                          namespace: str, current_value: Any, expected_value: Any,
                                          additional_context: Optional[Dict] = None) -> PolicyViolation:
        """Create policy violation using YAML-configured risk scoring"""
        
        if additional_context is None:
            additional_context = {}
        
        # Generate remediation steps
        remediation_steps = self._generate_remediation_steps_yaml(policy_rule, additional_context)
        
        # Calculate risk score using YAML configuration
        risk_score = self._calculate_risk_score_yaml(policy_rule, current_value, expected_value)
        
        violation = PolicyViolation(
            violation_id=f"{policy_rule.rule_id}_{int(datetime.now().timestamp())}_{hash(resource_name) % 1000}",
            policy_name=policy_rule.name,
            policy_category=policy_rule.category,
            severity=policy_rule.severity,
            resource_type=policy_rule.resource_types[0] if policy_rule.resource_types else "Unknown",
            resource_name=resource_name,
            namespace=namespace,
            violation_description=policy_rule.description,
            current_value=current_value,
            expected_value=expected_value,
            remediation_steps=remediation_steps,
            auto_remediable=policy_rule.auto_remediable,
            compliance_frameworks=list(policy_rule.compliance_mappings.keys()),
            detected_at=datetime.now(),
            risk_score=risk_score,
            additional_context=additional_context
        )
        
        return violation
    
    def _generate_remediation_steps_yaml(self, policy_rule: PolicyRule, context: Optional[Dict] = None) -> List[str]:
        """Generate remediation steps using YAML configuration"""
        
        steps = [policy_rule.remediation_template]
        
        # Add context-specific steps
        if context:
            if 'container' in context:
                steps.append(f"Apply changes to container: {context['container']}")
            
            if 'missing_labels' in context:
                for label in context['missing_labels']:
                    steps.append(f"Add label '{label}' with appropriate value")
            
            if 'missing' in context:
                steps.append(f"Address missing component: {context['missing']}")
        
        # Add compliance-specific steps
        for framework, control in policy_rule.compliance_mappings.items():
            steps.append(f"Verify compliance with {framework} control {control}")
        
        return steps
    
    def _calculate_risk_score_yaml(self, policy_rule: PolicyRule, current_value: Any, expected_value: Any) -> float:
        """Calculate risk score using YAML configuration"""
        
        # Get base severity score from YAML
        severity_scores = self.risk_scoring_config.get('severity_base_scores', {
            'CRITICAL': 10.0, 'HIGH': 7.5, 'MEDIUM': 5.0, 'LOW': 2.5, 'INFO': 1.0
        })
        base_score = severity_scores.get(policy_rule.severity, 5.0)
        
        # Apply category multiplier from YAML
        category_multipliers = self.risk_scoring_config.get('category_multipliers', {
            'Security': 1.2, 'Network': 1.1, 'Governance': 0.9, 'Compliance': 1.0
        })
        category_multiplier = category_multipliers.get(policy_rule.category, 1.0)
        
        # Apply rule-specific multiplier from YAML
        rule_multiplier = policy_rule.risk_multiplier
        
        # Compliance framework impact
        framework_weight = len(policy_rule.compliance_mappings) * self.risk_scoring_config.get('framework_impact_weight', 0.1)
        
        # Calculate final score
        final_score = base_score * category_multiplier * rule_multiplier * (1 + framework_weight)
        max_score = self.risk_scoring_config.get('max_risk_score', 10.0)
        
        return min(max_score, final_score)
    
    def _calculate_compliance_yaml(self, violations: List[PolicyViolation]) -> Dict[str, float]:
        """Calculate compliance by category using YAML configuration"""
        
        if not violations:
            # Get all categories from YAML policy rules
            categories = set(rule.category for rule in self.policy_rules.values())
            return {category: 100.0 for category in categories}
        
        # Get total resources estimate
        total_resources = self._estimate_total_resources()
        
        # Group violations by category
        category_violations = {}
        for violation in violations:
            category = violation.policy_category
            if category not in category_violations:
                category_violations[category] = []
            category_violations[category].append(violation)
        
        # Get severity weights from YAML
        severity_weights = self.risk_scoring_config.get('severity_weights', {
            'CRITICAL': 4.0, 'HIGH': 3.0, 'MEDIUM': 2.0, 'LOW': 1.0, 'INFO': 0.5
        })
        
        compliance_scores = {}
        all_categories = set(rule.category for rule in self.policy_rules.values())
        
        for category in all_categories:
            if category in category_violations:
                category_violations_list = category_violations[category]
                
                # Calculate weighted violations
                weighted_violations = sum(
                    severity_weights.get(v.severity, 2.0) * v.risk_score / 10.0
                    for v in category_violations_list
                )
                
                # Calculate compliance percentage
                max_theoretical_violations = total_resources * 4  # Assume max 4 violations per resource
                if max_theoretical_violations > 0:
                    compliance_percentage = max(0, 100 - (weighted_violations / max_theoretical_violations * 100))
                else:
                    compliance_percentage = 100.0
                
                compliance_scores[category] = round(compliance_percentage, 2)
            else:
                compliance_scores[category] = 100.0
        
        return compliance_scores
    
    def _calculate_overall_compliance_yaml(self, violations: List[PolicyViolation], 
                                         compliance_by_category: Dict[str, float]) -> float:
        """Calculate overall compliance using YAML-configured category weights"""
        
        if not violations:
            return 100.0
        
        # Get category weights from YAML
        compliance_config = self.security_config.policy_analysis.get('compliance_scoring', {})
        category_weights = compliance_config.get('category_weights', {
            'Security': 0.4, 'Network': 0.25, 'Governance': 0.2, 'Compliance': 0.15
        })
        
        # Calculate weighted score
        weighted_score = 0
        total_weight = 0
        
        for category, score in compliance_by_category.items():
            weight = category_weights.get(category, 0.1)
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            overall_compliance = weighted_score / total_weight
        else:
            overall_compliance = sum(compliance_by_category.values()) / len(compliance_by_category)
        
        return round(max(0, min(100, overall_compliance)), 1)
    
    def _generate_recommendations_yaml(self, violations: List[PolicyViolation]) -> List[str]:
        """Generate recommendations using YAML-enhanced ML analysis"""
        
        if not violations:
            return ["✅ No policy violations detected. Continue monitoring for drift."]
        
        recommendations = []
        
        # ML-based violation clustering using YAML configuration
        if len(violations) >= 3:
            try:
                violation_descriptions = [v.violation_description for v in violations]
                vectors = self.text_vectorizer.transform(violation_descriptions)
                clusters = self.policy_clusterer.predict(vectors.toarray())
                
                # Generate cluster-based recommendations
                cluster_groups = {}
                for i, violation in enumerate(violations):
                    cluster_id = clusters[i]
                    if cluster_id not in cluster_groups:
                        cluster_groups[cluster_id] = []
                    cluster_groups[cluster_id].append(violation)
                
                for cluster_id, cluster_violations in cluster_groups.items():
                    if len(cluster_violations) > 1:
                        avg_risk = np.mean([v.risk_score for v in cluster_violations])
                        common_category = max(set(v.policy_category for v in cluster_violations),
                                            key=lambda x: sum(1 for v in cluster_violations if v.policy_category == x))
                        
                        if avg_risk > 7:
                            recommendations.append(
                                f"🔴 Critical Pattern: {len(cluster_violations)} related {common_category.lower()} "
                                f"violations (avg risk: {avg_risk:.1f}) require coordinated remediation"
                            )
                        elif avg_risk > 5:
                            recommendations.append(
                                f"🟠 Important: Address {len(cluster_violations)} clustered {common_category.lower()} "
                                f"issues together for efficiency"
                            )
            except Exception as e:
                logger.warning(f"ML clustering failed, using basic recommendations: {e}")
        
        # Priority recommendations based on YAML configuration
        critical_violations = [v for v in violations if v.severity == 'CRITICAL']
        if critical_violations:
            recommendations.append(f"⚠️ URGENT: {len(critical_violations)} critical violations require immediate attention")
        
        # Auto-remediation opportunities
        auto_remediable = [v for v in violations if v.auto_remediable]
        if auto_remediable:
            recommendations.append(f"🤖 Quick Fix: {len(auto_remediable)} violations can be auto-remediated")
        
        # Compliance framework recommendations
        framework_violations = {}
        for violation in violations:
            for framework in violation.compliance_frameworks:
                framework_violations[framework] = framework_violations.get(framework, 0) + 1
        
        for framework, count in framework_violations.items():
            if count > 2:
                recommendations.append(f"📊 {framework} Compliance: {count} violations impact {framework} certification")
        
        return recommendations[:10]  # Limit to top 10
    
    async def _enhance_violations_with_ml_yaml(self, violations: List[PolicyViolation]) -> List[PolicyViolation]:
        """Enhance violations with ML analysis using YAML configuration"""
        
        if not violations:
            return violations
        
        try:
            # ML-based severity adjustment
            violation_texts = [v.violation_description for v in violations]
            vectors = self.text_vectorizer.transform(violation_texts)
            
            # Predict severity adjustments
            predicted_severities = self.severity_classifier.predict(vectors.toarray())
            
            # Apply ML-based enhancements
            for i, violation in enumerate(violations):
                try:
                    ml_severity = self.label_encoder.inverse_transform([predicted_severities[i]])[0]
                    
                    # Combine rule-based and ML-based severity (conservative approach)
                    if ml_severity == 'CRITICAL' and violation.severity != 'CRITICAL':
                        violation.severity = 'HIGH'  # Upgrade but be conservative
                    
                    # Enhance risk score with ML confidence
                    violation.risk_score = min(10.0, violation.risk_score * 1.1)
                    
                except Exception as e:
                    logger.debug(f"ML enhancement failed for violation {i}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"ML enhancement failed: {e}")
        
        return violations
    
    # Helper methods
    
    def _extract_containers_from_resource(self, resource: Dict) -> List[Dict]:
        """Extract containers from various resource types"""
        containers = []
        spec = resource.get('spec', {})
        
        # Deployment, StatefulSet, DaemonSet
        if 'template' in spec:
            pod_spec = spec.get('template', {}).get('spec', {})
            containers.extend(pod_spec.get('containers', []))
            containers.extend(pod_spec.get('initContainers', []))
        
        # Pod
        elif 'containers' in spec:
            containers.extend(spec.get('containers', []))
            containers.extend(spec.get('initContainers', []))
        
        return [c for c in containers if isinstance(c, dict)]
    
    def _compare_resource_values(self, actual: str, limit: str) -> int:
        """Compare Kubernetes resource values"""
        # Simplified implementation - can be enhanced
        try:
            actual_val = float(actual.rstrip('mGi'))
            limit_val = float(limit.rstrip('mGi'))
            return 1 if actual_val > limit_val else (-1 if actual_val < limit_val else 0)
        except:
            return 0
    
    async def _validate_label_values_yaml(self, labels: Dict[str, str]) -> Dict[str, str]:
        """Validate label values using YAML configuration"""
        # Placeholder implementation
        return {}
    
    async def _check_namespace_has_network_policy_yaml(self, namespace: str) -> bool:
        """Check if namespace has network policies using YAML configuration"""
        network_resources = self.cluster_config.get('networking_resources', {})
        network_policies = network_resources.get('networkpolicies', {}).get('items', [])
        
        for policy in network_policies:
            if isinstance(policy, dict):
                policy_namespace = policy.get('metadata', {}).get('namespace', '')
                if policy_namespace == namespace:
                    return True
        
        return False
    
    def _is_image_from_trusted_registry_yaml(self, image: str, trusted_registries: List[str]) -> bool:
        """Check if image is from trusted registry using YAML configuration"""
        if not image:
            return False
        
        for registry in trusted_registries:
            if image.startswith(registry) or (registry in image.split('/')[0]):
                return True
        
        return False
    
    def _estimate_total_resources(self) -> int:
        """Estimate total number of resources"""
        workload_resources = self.cluster_config.get('workload_resources', {}) or {}
        
        total_resources = 0
        for resource_type in ['deployments', 'services', 'pods', 'namespaces']:
            resources = workload_resources.get(resource_type, {})
            if isinstance(resources, dict) and 'items' in resources:
                items = resources.get('items')
                if items is not None and isinstance(items, list):
                    total_resources += len(items)
        
        return max(1, total_resources)

# Factory function for integration
def create_policy_analyzer(cluster_config: Dict, config_dir: str = None) -> DynamicPolicyAnalyzerYAML:
    """Create YAML-configured policy analyzer instance"""
    return DynamicPolicyAnalyzerYAML(cluster_config, config_dir)