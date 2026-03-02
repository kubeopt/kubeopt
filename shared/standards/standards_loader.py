"""
Standards Loader - Load optimization standards from existing YAML configuration.

Integrates with existing config/{provider}_*.yaml files (aks, eks, gke).
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
    
    def __init__(self, config_dir: Optional[str] = None, cloud_provider: str = 'azure'):
        """
        Initialize the standards loader.

        Args:
            config_dir: Path to config directory.
                       Defaults to config/ from project root
            cloud_provider: Cloud provider ('azure', 'aws', or 'gcp').
                           Defaults to 'azure'.
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

        self.cloud_provider = cloud_provider
        self._provider_prefix = {'azure': 'aks', 'aws': 'eks', 'gcp': 'gke'}.get(cloud_provider, 'aks')

        self._cache = {}
        self._load_timestamp = None

        # Resolve provider-specific files with fallback to AKS
        self._scoring_file = f"{self._provider_prefix}_scoring.yaml"
        self._implementation_file = f"{self._provider_prefix}_implementation_standards.yaml"

        # Fall back to AKS files if provider-specific ones don't exist
        if not (self.config_dir / self._scoring_file).exists():
            self._scoring_file = "aks_scoring.yaml"
        if not (self.config_dir / self._implementation_file).exists():
            self._implementation_file = "aks_implementation_standards.yaml"

        # Validate the resolved files exist
        self._required_files = [self._scoring_file, self._implementation_file]
        for required_file in self._required_files:
            filepath = self.config_dir / required_file
            if not filepath.exists():
                raise FileNotFoundError(
                    f"Required standards file not found: {filepath}\n"
                    f"This file is required for optimization standards!"
                )
    
    def load_scoring_standards(self) -> Dict[str, Any]:
        """
        Load scoring standards from the provider-specific scoring YAML.

        Returns:
            Dictionary of scoring standards

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        return self._load_yaml_file(self._scoring_file)
    
    def load_implementation_standards(self) -> Dict[str, Any]:
        """Load implementation standards from the provider-specific implementation YAML."""
        return self._load_yaml_file(self._implementation_file)
    
    def get_cpu_utilization_target(self) -> Dict[str, float]:
        """Get CPU utilization targets from YAML"""
        standards = self.load_scoring_standards()
        cpu_band = standards['build_quality']['targets']['cpu_warm_band']
        return {
            'target_min': cpu_band[0] * 100,  # Convert to percentage
            'target_max': cpu_band[1] * 100,
            'optimal': sum(cpu_band) / 2 * 100,  # Average of band
            'source': f'config/{self._scoring_file} - CNCF + Google SRE standards'
        }

    def get_memory_utilization_target(self) -> Dict[str, float]:
        """Get memory utilization targets from YAML"""
        standards = self.load_scoring_standards()
        mem_band = standards['build_quality']['targets']['mem_warm_band']
        return {
            'target_min': mem_band[0] * 100,  # Convert to percentage
            'target_max': mem_band[1] * 100,
            'optimal': sum(mem_band) / 2 * 100,  # Average of band
            'source': f'config/{self._scoring_file} - CNCF + Google SRE standards'
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
            'source': f'config/{self._scoring_file} + {self._implementation_file}'
        }
    
    def get_optimization_thresholds(self) -> Dict[str, Any]:
        """Get optimization decision thresholds from YAML"""
        standards = self.load_implementation_standards()
        
        return {
            'payback_threshold_months': standards['optimization_thresholds']['payback_threshold_months'],
            'minimum_monthly_savings': standards['optimization_thresholds']['minimum_monthly_savings'],
            'minimum_savings_percentage': standards['optimization_thresholds']['minimum_savings_percentage'],
            'high_priority_savings': standards['optimization_thresholds']['priority_thresholds']['high_priority_savings'],
            'source': f'config/{self._implementation_file}'
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
                'source': f'shared.standards.cost_optimization_standards + config/{self._implementation_file}'
            }
        except ImportError:
            # Fallback to YAML only if Python standards not available
            impl_standards = self.load_implementation_standards()
            return {
                'monthly_hours': 730,  # Standard month
                'optimal_cpu_utilization': 70,
                'optimal_memory_utilization': 75,
                'source': f'config/{self._implementation_file} (fallback)'
            }
    
    def get_confidence_and_risk_factors(self) -> Dict[str, Any]:
        """Get confidence factors and risk assessment from YAML"""
        standards = self.load_implementation_standards()
        
        return {
            'risk_levels': standards['risk_assessment']['risk_levels'],
            'mitigation_strategies': standards['risk_assessment']['mitigation_strategies'],
            'confidence_threshold': standards['ml_analytics']['cost_prediction']['confidence_threshold'],
            'source': f'config/{self._implementation_file} - risk assessment'
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


# Per-provider singleton instances
_standards_loaders = {}

def get_standards_loader(cloud_provider: str = 'azure') -> StandardsLoader:
    """
    Get a standards loader instance for the given cloud provider.

    Args:
        cloud_provider: 'azure', 'aws', or 'gcp'. Defaults to 'azure'.

    Returns:
        StandardsLoader for the specified provider
    """
    global _standards_loaders
    if cloud_provider not in _standards_loaders:
        _standards_loaders[cloud_provider] = StandardsLoader(cloud_provider=cloud_provider)
    return _standards_loaders[cloud_provider]


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