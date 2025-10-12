#!/usr/bin/env python3
"""
Security Configuration Loader
=============================
Utility to load and validate security policies and standards from YAML files.
Replaces hardcoded security constants throughout the security framework.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Security configuration container"""
    policy_rules: Dict[str, Any]
    compliance_frameworks: Dict[str, Any]
    rule_context: Dict[str, Any]
    ml_parameters: Dict[str, Any]
    security_standards: Dict[str, Any]
    policy_analysis: Dict[str, Any]
    integration: Dict[str, Any]

class SecurityConfigLoader:
    """
    Load and validate security configurations from YAML files
    """
    
    def __init__(self, config_dir: str = None):
        """Initialize config loader"""
        if config_dir is None:
            # Default to config directory relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self.security_config_path = self.config_dir / "security_policies.yaml"
        self.implementation_standards_path = self.config_dir / "aks_implementation_standards.yaml"
        self.scoring_standards_path = self.config_dir / "aks_scoring.yaml"
        
        # Cache for loaded configurations
        self._config_cache = {}
        
        logger.info(f"🔧 SecurityConfigLoader initialized with config dir: {self.config_dir}")
    
    def load_security_config(self) -> SecurityConfig:
        """Load complete security configuration"""
        
        if 'security_config' in self._config_cache:
            return self._config_cache['security_config']
        
        try:
            # Load main security policies
            security_data = self._load_yaml_file(self.security_config_path)
            
            # Load related configuration files for integration
            implementation_data = self._load_yaml_file(self.implementation_standards_path, required=False)
            scoring_data = self._load_yaml_file(self.scoring_standards_path, required=False)
            
            # Validate and merge configurations
            config = self._validate_and_merge_config(security_data, implementation_data, scoring_data)
            
            # Cache the configuration
            self._config_cache['security_config'] = config
            
            logger.info("✅ Security configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load security configuration: {e}")
            # Return default configuration to prevent system failure
            return self._get_default_security_config()
    
    def reload_config(self) -> SecurityConfig:
        """Reload configuration from files (clear cache)"""
        self._config_cache.clear()
        return self.load_security_config()
    
    def get_policy_rules(self) -> Dict[str, Any]:
        """Get policy rules configuration"""
        config = self.load_security_config()
        return config.policy_rules
    
    def get_compliance_frameworks(self) -> Dict[str, Any]:
        """Get compliance frameworks configuration"""
        config = self.load_security_config()
        return config.compliance_frameworks
    
    def get_ml_parameters(self) -> Dict[str, Any]:
        """Get ML model parameters"""
        config = self.load_security_config()
        return config.ml_parameters
    
    def get_security_standards(self) -> Dict[str, Any]:
        """Get security standards configuration"""
        config = self.load_security_config()
        return config.security_standards
    
    def get_rule_context(self) -> Dict[str, Any]:
        """Get rule context and constants"""
        config = self.load_security_config()
        return config.rule_context
    
    def get_policy_analysis_config(self) -> Dict[str, Any]:
        """Get policy analysis configuration"""
        config = self.load_security_config()
        return config.policy_analysis
    
    def _load_yaml_file(self, file_path: Path, required: bool = True) -> Dict[str, Any]:
        """Load and parse YAML file"""
        
        if not file_path.exists():
            if required:
                raise FileNotFoundError(f"Required configuration file not found: {file_path}")
            else:
                logger.warning(f"Optional configuration file not found: {file_path}")
                return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            if not isinstance(data, dict):
                raise ValueError(f"Configuration file must contain a dictionary: {file_path}")
            
            logger.debug(f"Loaded configuration from: {file_path}")
            return data
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load {file_path}: {e}")
    
    def _validate_and_merge_config(self, security_data: Dict, 
                                   implementation_data: Dict, 
                                   scoring_data: Dict) -> SecurityConfig:
        """Validate and merge configuration data"""
        
        # Validate required sections in security_data
        required_sections = [
            'policy_rules', 'compliance_frameworks', 'rule_context', 
            'ml_parameters', 'security_standards', 'policy_analysis'
        ]
        
        for section in required_sections:
            if section not in security_data:
                raise ValueError(f"Missing required section in security_policies.yaml: {section}")
        
        # Merge integration data if available
        integration_config = security_data.get('integration', {})
        
        # Enhance ML parameters with data from other configs
        ml_params = security_data['ml_parameters'].copy()
        if implementation_data and 'ml_analytics' in implementation_data:
            ml_params.update(implementation_data['ml_analytics'])
        
        # Enhance security standards with scoring data
        security_standards = security_data['security_standards'].copy()
        if scoring_data and 'official_standards' in scoring_data:
            security_standards.update(scoring_data['official_standards'])
        
        return SecurityConfig(
            policy_rules=security_data['policy_rules'],
            compliance_frameworks=security_data['compliance_frameworks'],
            rule_context=security_data['rule_context'],
            ml_parameters=ml_params,
            security_standards=security_standards,
            policy_analysis=security_data['policy_analysis'],
            integration=integration_config
        )
    
    def _get_default_security_config(self) -> SecurityConfig:
        """Return default security configuration as fallback"""
        
        logger.warning("Using default security configuration - some features may be limited")
        
        return SecurityConfig(
            policy_rules={
                "security_context_required": {
                    "rule_id": "SEC001",
                    "name": "Security Context Required",
                    "severity": "HIGH",
                    "enabled": True
                }
            },
            compliance_frameworks={
                "CIS": {
                    "name": "CIS Kubernetes Benchmark",
                    "version": "1.6.0",
                    "priority_weight": 1.0
                }
            },
            rule_context={
                "required_labels": ["app", "version"],
                "forbidden_capabilities": ["SYS_ADMIN"],
                "trusted_registries": ["mcr.microsoft.com"]
            },
            ml_parameters={
                "risk_scoring": {
                    "severity_base_scores": {
                        "CRITICAL": 10.0,
                        "HIGH": 7.5,
                        "MEDIUM": 5.0,
                        "LOW": 2.5
                    }
                }
            },
            security_standards={
                "authentication": {"enable_rbac": True},
                "network_security": {"minimum_tls_version": "1.2"}
            },
            policy_analysis={
                "enabled_categories": ["Security", "Network", "Governance"],
                "block_on_critical": True
            },
            integration={}
        )
    
    def validate_config_files(self) -> List[str]:
        """Validate all configuration files and return any issues"""
        
        issues = []
        
        # Check security_policies.yaml
        if not self.security_config_path.exists():
            issues.append(f"Missing security_policies.yaml at {self.security_config_path}")
        else:
            try:
                self._load_yaml_file(self.security_config_path)
            except Exception as e:
                issues.append(f"Invalid security_policies.yaml: {e}")
        
        # Check optional files
        for file_path, name in [
            (self.implementation_standards_path, "aks_implementation_standards.yaml"),
            (self.scoring_standards_path, "aks_scoring.yaml")
        ]:
            if file_path.exists():
                try:
                    self._load_yaml_file(file_path)
                except Exception as e:
                    issues.append(f"Invalid {name}: {e}")
        
        return issues
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about loaded configuration"""
        
        config = self.load_security_config()
        
        return {
            "config_dir": str(self.config_dir),
            "files_loaded": {
                "security_policies": self.security_config_path.exists(),
                "implementation_standards": self.implementation_standards_path.exists(),
                "scoring_standards": self.scoring_standards_path.exists()
            },
            "policy_rules_count": len(config.policy_rules),
            "compliance_frameworks_count": len(config.compliance_frameworks),
            "ml_parameters_configured": bool(config.ml_parameters),
            "security_standards_configured": bool(config.security_standards)
        }

# Global instance for easy access
_config_loader = None

def get_security_config_loader(config_dir: str = None) -> SecurityConfigLoader:
    """Get global security config loader instance"""
    global _config_loader
    if _config_loader is None or config_dir is not None:
        _config_loader = SecurityConfigLoader(config_dir)
    return _config_loader

def load_security_config(config_dir: str = None) -> SecurityConfig:
    """Load security configuration (convenience function)"""
    loader = get_security_config_loader(config_dir)
    return loader.load_security_config()

# Example usage functions
def get_policy_rule(rule_id: str) -> Optional[Dict[str, Any]]:
    """Get specific policy rule by ID"""
    config = load_security_config()
    for rule_key, rule_data in config.policy_rules.items():
        if rule_data.get('rule_id') == rule_id:
            return rule_data
    return None

def get_compliance_framework(framework_id: str) -> Optional[Dict[str, Any]]:
    """Get specific compliance framework by ID"""
    config = load_security_config()
    return config.compliance_frameworks.get(framework_id)

def get_ml_parameter(parameter_path: str, default: Any = None) -> Any:
    """Get ML parameter by dot notation path (e.g., 'risk_scoring.severity_base_scores.CRITICAL')"""
    config = load_security_config()
    
    try:
        value = config.ml_parameters
        for key in parameter_path.split('.'):
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

def get_security_standard(standard_path: str, default: Any = None) -> Any:
    """Get security standard by dot notation path"""
    config = load_security_config()
    
    try:
        value = config.security_standards
        for key in standard_path.split('.'):
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default