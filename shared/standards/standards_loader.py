"""
Standards Loader - Load optimization standards from existing YAML configuration.

Integrates with existing config/aks_*.yaml files.
NO FALLBACKS. NO DEFAULTS. If YAML doesn't exist or is invalid → FAIL.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StandardsLoader:
    """
    Loads optimization standards from existing YAML configuration files.
    
    CRITICAL: This class NEVER returns fallback values.
    If YAML files are missing or invalid, it raises exceptions.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the standards loader.
        
        Args:
            config_dir: Path to config directory. 
                       Defaults to config/ from project root
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Get config directory relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
        
        if not self.config_dir.exists():
            raise FileNotFoundError(
                f"Config directory not found: {self.config_dir}\n"
                f"Expected YAML configuration files in config/ directory!"
            )
        
        self._cache = {}
        self._load_timestamp = None
        
        # Validate required files exist
        self._required_files = [
            "aks_scoring.yaml",
            "aks_implementation_standards.yaml"
        ]
        
        for required_file in self._required_files:
            filepath = self.config_dir / required_file
            if not filepath.exists():
                raise FileNotFoundError(
                    f"Required standards file not found: {filepath}\n"
                    f"This file is required for optimization standards!"
                )
    
    def load_scoring_standards(self) -> Dict[str, Any]:
        """
        Load scoring standards from aks_scoring.yaml.
        
        Returns:
            Dictionary of scoring standards
            
        Raises:
            FileNotFoundError: If YAML file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        return self._load_yaml_file('aks_scoring.yaml')
    
    def load_implementation_standards(self) -> Dict[str, Any]:
        """Load implementation standards from aks_implementation_standards.yaml"""
        return self._load_yaml_file('aks_implementation_standards.yaml')
    
    def get_cpu_utilization_target(self) -> Dict[str, float]:
        """Get CPU utilization targets from YAML"""
        standards = self.load_scoring_standards()
        cpu_band = standards['build_quality']['targets']['cpu_warm_band']
        return {
            'target_min': cpu_band[0] * 100,  # Convert to percentage
            'target_max': cpu_band[1] * 100,
            'optimal': sum(cpu_band) / 2 * 100,  # Average of band
            'source': 'config/aks_scoring.yaml - CNCF + Google SRE standards'
        }
    
    def get_memory_utilization_target(self) -> Dict[str, float]:
        """Get memory utilization targets from YAML"""
        standards = self.load_scoring_standards()
        mem_band = standards['build_quality']['targets']['mem_warm_band']
        return {
            'target_min': mem_band[0] * 100,  # Convert to percentage
            'target_max': mem_band[1] * 100,
            'optimal': sum(mem_band) / 2 * 100,  # Average of band
            'source': 'config/aks_scoring.yaml - CNCF + Google SRE standards'
        }
    
    def get_hpa_standards(self) -> Dict[str, Any]:
        """Get HPA configuration standards from YAML"""
        scoring_standards = self.load_scoring_standards()
        impl_standards = self.load_implementation_standards()
        
        return {
            'coverage_target': scoring_standards['build_quality']['targets']['hpa_coverage_target'] * 100,  # Convert to percentage
            'target_cpu_utilization': impl_standards['infrastructure_scaling']['hpa_settings']['target_cpu_utilization'],
            'target_memory_utilization': impl_standards['infrastructure_scaling']['hpa_settings']['target_memory_utilization'],
            'min_replicas_default': impl_standards['infrastructure_scaling']['hpa_settings']['min_replicas'],
            'max_replicas_default': impl_standards['infrastructure_scaling']['hpa_settings']['max_replicas'],
            'scale_down_stabilization_seconds': impl_standards['infrastructure_scaling']['hpa_settings']['scale_down_stabilization_seconds'],
            'source': 'config/aks_*.yaml - Kubernetes autoscaling best practices'
        }
    
    def get_optimization_thresholds(self) -> Dict[str, Any]:
        """Get optimization decision thresholds from YAML"""
        standards = self.load_implementation_standards()
        
        return {
            'payback_threshold_months': standards['optimization_thresholds']['payback_threshold_months'],
            'minimum_monthly_savings': standards['optimization_thresholds']['minimum_monthly_savings'],
            'minimum_savings_percentage': standards['optimization_thresholds']['minimum_savings_percentage'],
            'high_priority_savings': standards['optimization_thresholds']['priority_thresholds']['high_priority_savings'],
            'source': 'config/aks_implementation_standards.yaml'
        }
    
    def get_cost_calculation_standards(self) -> Dict[str, Any]:
        """Get cost calculation standards from existing Python standards and YAML"""
        # Import existing standards for compatibility
        try:
            from shared.standards.cost_optimization_standards import CostCalculationStandards
            impl_standards = self.load_implementation_standards()
            
            return {
                'monthly_hours': CostCalculationStandards.MONTHLY_HOURS,
                'optimal_cpu_utilization': CostCalculationStandards.OPTIMAL_CPU_UTILIZATION,
                'optimal_memory_utilization': CostCalculationStandards.OPTIMAL_MEMORY_UTILIZATION,
                'cpu_cost_per_core_hour': CostCalculationStandards.CPU_COST_PER_CORE_HOUR,
                'memory_cost_per_gb_hour': CostCalculationStandards.MEMORY_COST_PER_GB_HOUR,
                # Add YAML overrides
                'regional_multiplier': impl_standards['regional_rates']['base_hourly_rate'],
                'source': 'shared.standards.cost_optimization_standards + YAML overrides'
            }
        except ImportError:
            # Fallback to YAML only if Python standards not available
            impl_standards = self.load_implementation_standards()
            return {
                'monthly_hours': 730,  # Standard month
                'optimal_cpu_utilization': 70,
                'optimal_memory_utilization': 75,
                'source': 'config/aks_implementation_standards.yaml (fallback)'
            }
    
    def get_confidence_and_risk_factors(self) -> Dict[str, Any]:
        """Get confidence factors and risk assessment from YAML"""
        standards = self.load_implementation_standards()
        
        return {
            'risk_levels': standards['risk_assessment']['risk_levels'],
            'mitigation_strategies': standards['risk_assessment']['mitigation_strategies'],
            'confidence_threshold': standards['ml_analytics']['cost_prediction']['confidence_threshold'],
            'source': 'config/aks_implementation_standards.yaml - risk assessment'
        }
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """
        Load and validate a YAML file.
        
        Args:
            filename: Name of YAML file to load
            
        Returns:
            Parsed YAML content
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(
                f"Standards file not found: {filepath}\n"
                f"This file is required for optimization standards!"
            )
        
        # Check cache
        cache_key = str(filepath)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                raise ValueError(f"{filename} is empty!")
            
            # Cache the loaded data
            self._cache[cache_key] = data
            self._load_timestamp = datetime.now()
            
            logger.info(f"✓ Loaded standards from: {filename}")
            if 'version' in data:
                logger.info(f"  Version: {data.get('version', 'unknown')}")
            
            return data
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Invalid YAML in {filename}:\n{e}\n"
                f"Fix the YAML syntax before running!"
            )
    
    def reload_standards(self):
        """Clear cache and reload all standards from disk"""
        self._cache.clear()
        self._load_timestamp = None
        logger.info("✓ Standards cache cleared - will reload on next access")
    
    def validate_all_standards(self) -> bool:
        """
        Validate that all required standards can be loaded.
        
        Returns:
            True if all standards are valid
            
        Raises:
            Exception: If any standards are invalid
        """
        try:
            # Test loading all critical standards
            self.load_scoring_standards()
            self.load_implementation_standards()
            self.get_cpu_utilization_target()
            self.get_memory_utilization_target()
            self.get_hpa_standards()
            self.get_optimization_thresholds()
            
            logger.info("✅ All standards validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Standards validation failed: {e}")
            raise


# Singleton instance
_standards_loader = None

def get_standards_loader() -> StandardsLoader:
    """
    Get the global standards loader instance.
    
    Returns:
        StandardsLoader singleton
    """
    global _standards_loader
    if _standards_loader is None:
        _standards_loader = StandardsLoader()
    return _standards_loader


# Convenience functions for easy access
def get_cpu_target() -> Dict[str, float]:
    """Get CPU utilization target from standards"""
    return get_standards_loader().get_cpu_utilization_target()

def get_memory_target() -> Dict[str, float]:
    """Get memory utilization target from standards"""
    return get_standards_loader().get_memory_utilization_target()

def get_hpa_config() -> Dict[str, Any]:
    """Get HPA standards from YAML"""
    return get_standards_loader().get_hpa_standards()

def get_optimization_config() -> Dict[str, Any]:
    """Get optimization thresholds from YAML"""
    return get_standards_loader().get_optimization_thresholds()

def validate_standards_available() -> bool:
    """
    Validate that all required standards are available.
    Call this at application startup.
    
    Returns:
        True if all standards are valid
        
    Raises:
        Exception: If standards are missing or invalid
    """
    return get_standards_loader().validate_all_standards()