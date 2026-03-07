#!/usr/bin/env python3
"""
Implementation Cost Calculator
Uses standards from implementation_standards.yaml for realistic cost estimation
"""

import yaml
import os
import sys
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ImplementationCostResult:
    """Result of implementation cost calculation"""
    base_cost: float
    total_cost: float
    timeline_days: int
    complexity_multiplier: float
    risk_level: str
    breakdown: Dict[str, float]
    
class ImplementationCostCalculator:
    """
    Calculate realistic implementation costs based on industry standards
    """
    
    def __init__(self, standards_file: str = None, cloud_provider: str = 'azure'):
        if standards_file is None:
            # Use StandardsLoader for cloud-provider-aware YAML resolution
            from shared.standards.standards_loader import get_standards_loader
            loader = get_standards_loader(cloud_provider)
            self.standards = loader.load_implementation_standards()
            self.standards_file = None
            logger.info(f"✅ Loaded implementation standards via StandardsLoader (provider={cloud_provider})")
        else:
            self.standards_file = os.path.abspath(standards_file)
            self.standards = self._load_standards()
    
    def _get_default_config_dir(self) -> str:
        """Get default config directory for development and PyInstaller environments"""
        # Check if running as PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller bundle - config files are in the bundle
            return os.path.join(sys._MEIPASS, 'config')
        else:
            # Development environment
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, '..', '..')
            return os.path.join(project_root, 'config')
        
    def _load_standards(self) -> Dict[str, Any]:
        """Load implementation standards from YAML"""
        if not os.path.exists(self.standards_file):
            raise FileNotFoundError(f"❌ Standards file not found: {self.standards_file}. System requires proper configuration.")
        
        try:
            with open(self.standards_file, 'r') as f:
                standards = yaml.safe_load(f)
                if not standards:
                    raise ValueError(f"❌ Standards file is empty or invalid: {self.standards_file}")
                logger.info(f"✅ Loaded implementation standards from {self.standards_file}")
                return standards
        except Exception as e:
            raise RuntimeError(f"❌ Failed to load standards from {self.standards_file}: {e}")
    
    def calculate_hpa_cost(self, cluster_config: Dict[str, Any] = None, 
                          complexity: str = "basic_cpu_memory",
                          region: str = "north_america") -> ImplementationCostResult:
        """Calculate HPA implementation cost"""
        
        optimization_type = "horizontal_scaling"
        base_cost = self.standards['implementation_costs'][optimization_type]['base_cost']
        
        # Get complexity multiplier
        complexity_multipliers = self.standards['implementation_costs'][optimization_type].get('complexity_multipliers', {})
        complexity_multiplier = complexity_multipliers.get(complexity, 1.0)
        
        # Calculate cluster size multiplier
        cluster_size_multiplier = self._get_cluster_size_multiplier(cluster_config)
        is_small_cluster = cluster_size_multiplier == 0.8
        
        # Get regional multiplier  
        regional_multiplier = self._get_regional_multiplier(region)
        
        # Apply small cluster adjustments if needed
        if is_small_cluster and optimization_type == 'horizontal_scaling':
            small_adjustments = self.standards['implementation_costs'][optimization_type].get('small_cluster_adjustments', {})
            base_reduction = small_adjustments.get('base_cost_reduction', 1.0)
            base_cost = base_cost * base_reduction
            logger.info(f"📉 Small cluster HPA: Reduced base cost by {(1-base_reduction)*100:.0f}% to ${base_cost:.0f}")
        
        # Calculate total cost
        total_cost = base_cost * complexity_multiplier * cluster_size_multiplier * regional_multiplier
        
        # Add prerequisites with small cluster adjustment
        prerequisites = self.standards['implementation_costs'][optimization_type].get('prerequisites', {})
        prerequisite_cost = sum(prerequisites.values()) if prerequisites else 0
        
        if is_small_cluster and optimization_type == 'horizontal_scaling':
            small_adjustments = self.standards['implementation_costs'][optimization_type].get('small_cluster_adjustments', {})
            prereq_reduction = small_adjustments.get('prerequisite_reduction', 1.0)
            prerequisite_cost = prerequisite_cost * prereq_reduction
            logger.info(f"📉 Small cluster HPA: Reduced prerequisites by {(1-prereq_reduction)*100:.0f}% to ${prerequisite_cost:.0f}")
        
        # Get timeline
        timeline_days = self.standards['implementation_timelines']['autoscaling'].get('hpa_basic', 2)
        
        # Risk assessment
        risk_level = self.standards['risk_assessment']['risk_by_type'].get(optimization_type, 'medium')
        
        return ImplementationCostResult(
            base_cost=base_cost,
            total_cost=total_cost + prerequisite_cost,
            timeline_days=timeline_days,
            complexity_multiplier=complexity_multiplier,
            risk_level=risk_level,
            breakdown={
                'base_cost': base_cost,
                'complexity_adjustment': base_cost * (complexity_multiplier - 1.0),
                'cluster_size_adjustment': base_cost * (cluster_size_multiplier - 1.0),
                'regional_adjustment': base_cost * (regional_multiplier - 1.0),
                'prerequisites': prerequisite_cost
            }
        )
    
    def calculate_rightsizing_cost(self, cluster_config: Dict[str, Any] = None,
                                 workload_count: int = 10,
                                 complexity: str = "simple_workloads",
                                 region: str = "north_america") -> ImplementationCostResult:
        """Calculate resource rightsizing implementation cost"""
        
        optimization_type = "resource_optimization"
        base_cost = self.standards['implementation_costs'][optimization_type]['base_cost']
        
        # Get complexity multiplier
        complexity_multipliers = self.standards['implementation_costs'][optimization_type].get('complexity_multipliers', {})
        complexity_multiplier = complexity_multipliers.get(complexity, 1.0)
        
        # Calculate cluster size multiplier
        cluster_size_multiplier = self._get_cluster_size_multiplier(cluster_config)
        
        # Get regional multiplier
        regional_multiplier = self._get_regional_multiplier(region)
        
        # Additional workload cost
        per_workload_cost = self.standards['implementation_costs'][optimization_type].get('per_workload_analysis', 15)
        additional_workloads = max(0, workload_count - 10)  # First 10 included in base
        workload_cost = additional_workloads * per_workload_cost
        
        # Calculate total cost
        total_cost = (base_cost * complexity_multiplier * cluster_size_multiplier * regional_multiplier) + workload_cost
        
        # Get timeline
        analysis_days = self.standards['implementation_timelines']['resource_optimization'].get('analysis_phase', 2)
        implementation_days = self.standards['implementation_timelines']['resource_optimization'].get('implementation_phase', 3)
        timeline_days = analysis_days + implementation_days
        
        # Risk assessment
        risk_level = self.standards['risk_assessment']['risk_by_type'].get(optimization_type, 'medium')
        
        return ImplementationCostResult(
            base_cost=base_cost,
            total_cost=total_cost,
            timeline_days=timeline_days,
            complexity_multiplier=complexity_multiplier,
            risk_level=risk_level,
            breakdown={
                'base_cost': base_cost,
                'complexity_adjustment': base_cost * (complexity_multiplier - 1.0),
                'cluster_size_adjustment': base_cost * (cluster_size_multiplier - 1.0),
                'regional_adjustment': base_cost * (regional_multiplier - 1.0),
                'additional_workloads': workload_cost
            }
        )
    
    def calculate_storage_optimization_cost(self, cluster_config: Dict[str, Any] = None,
                                          pv_count: int = 20,
                                          complexity: str = "basic_storage_classes",
                                          region: str = "north_america") -> ImplementationCostResult:
        """Calculate storage optimization implementation cost"""
        
        optimization_type = "storage_optimization"
        base_cost = self.standards['implementation_costs'][optimization_type]['base_cost']
        
        # Get complexity multiplier
        complexity_multipliers = self.standards['implementation_costs'][optimization_type].get('complexity_multipliers', {})
        complexity_multiplier = complexity_multipliers.get(complexity, 1.0)
        
        # Calculate cluster size multiplier
        cluster_size_multiplier = self._get_cluster_size_multiplier(cluster_config)
        
        # Get regional multiplier
        regional_multiplier = self._get_regional_multiplier(region)
        
        # Additional PV cost
        per_pv_cost = self.standards['implementation_costs'][optimization_type].get('per_persistent_volume', 20)
        additional_pvs = max(0, pv_count - 20)  # First 20 included in base
        pv_cost = additional_pvs * per_pv_cost
        
        # Calculate total cost
        total_cost = (base_cost * complexity_multiplier * cluster_size_multiplier * regional_multiplier) + pv_cost
        
        # Get timeline
        timeline_days = self.standards['implementation_timelines']['infrastructure'].get('storage_optimization', 4)
        
        # Risk assessment
        risk_level = self.standards['risk_assessment']['risk_by_type'].get(optimization_type, 'high')
        
        return ImplementationCostResult(
            base_cost=base_cost,
            total_cost=total_cost,
            timeline_days=timeline_days,
            complexity_multiplier=complexity_multiplier,
            risk_level=risk_level,
            breakdown={
                'base_cost': base_cost,
                'complexity_adjustment': base_cost * (complexity_multiplier - 1.0),
                'cluster_size_adjustment': base_cost * (cluster_size_multiplier - 1.0),
                'regional_adjustment': base_cost * (regional_multiplier - 1.0),
                'additional_pvs': pv_cost
            }
        )
    
    def _get_cluster_size_multiplier(self, cluster_config: Dict[str, Any] = None) -> float:
        """Determine cluster size multiplier based on configuration"""
        
        if not cluster_config:
            return 1.0  # Default medium cluster
            
        # Try to determine cluster size from config
        node_count = 0
        if cluster_config.get('workload_resources'):
            # Estimate from workload resources
            workload_resources = cluster_config['workload_resources']
            total_workloads = sum(
                res.get('item_count', 0) for res in workload_resources.values()
            )
            # Rough estimate: 5-10 workloads per node
            node_count = max(1, total_workloads // 7)
        
        # Get size category
        size_factors = self.standards.get('complexity_factors', {}).get('cluster_size', {})
        
        if node_count < 10:
            return size_factors.get('small', {}).get('multiplier', 0.8)
        elif node_count <= 50:
            return size_factors.get('medium', {}).get('multiplier', 1.0)
        elif node_count <= 200:
            return size_factors.get('large', {}).get('multiplier', 1.3)
        else:
            return size_factors.get('enterprise', {}).get('multiplier', 1.8)
    
    def _get_regional_multiplier(self, region: str) -> float:
        """Get regional cost multiplier"""
        regional_multipliers = self.standards.get('regional_rates', {}).get('regional_multipliers', {})
        return regional_multipliers.get(region, 1.0)  # Default to baseline
    
    def get_optimization_types(self) -> list:
        """Get list of available optimization types"""
        return list(self.standards.get('implementation_costs', {}).keys())
    
    def get_complexity_options(self, optimization_type: str) -> list:
        """Get complexity options for a specific optimization type"""
        complexity_multipliers = self.standards.get('implementation_costs', {}).get(
            optimization_type, {}
        ).get('complexity_multipliers', {})
        return list(complexity_multipliers.keys())
    
    def calculate_implementation_cost(self, optimization_type: str, complexity: str = "basic", 
                                    cluster_size: str = "medium", region: str = "north_america",
                                    **kwargs) -> float:
        """
        Generic method to calculate implementation cost for any optimization type
        
        Args:
            optimization_type: Type of optimization (e.g., 'network_optimization', 'storage_optimization')
            complexity: Complexity level (e.g., 'basic', 'advanced')
            cluster_size: Cluster size category (e.g., 'small', 'medium', 'large')
            region: Regional location for cost calculation
            **kwargs: Additional parameters specific to optimization type
        
        Returns:
            Implementation cost as float
        """
        try:
            # Map to specific methods where available
            if optimization_type == "horizontal_scaling" or optimization_type == "hpa_optimization":
                result = self.calculate_hpa_cost(
                    cluster_config=kwargs.get('cluster_config'),
                    complexity=complexity,
                    region=region
                )
                return result.total_cost
            
            elif optimization_type == "resource_optimization" or optimization_type == "rightsizing":
                result = self.calculate_rightsizing_cost(
                    cluster_config=kwargs.get('cluster_config'),
                    workload_count=kwargs.get('workload_count', 10),
                    complexity=complexity,
                    region=region
                )
                return result.total_cost
            
            elif optimization_type == "storage_optimization":
                result = self.calculate_storage_optimization_cost(
                    cluster_config=kwargs.get('cluster_config'),
                    pv_count=kwargs.get('pv_count', 20),
                    complexity=complexity,
                    region=region
                )
                return result.total_cost
            
            else:
                # Generic calculation for other optimization types
                base_cost = self.standards.get('implementation_costs', {}).get(
                    optimization_type, {}
                ).get('base_cost', 200)  # Default base cost
                
                # Get complexity multiplier
                complexity_multipliers = self.standards.get('implementation_costs', {}).get(
                    optimization_type, {}
                ).get('complexity_multipliers', {})
                complexity_multiplier = complexity_multipliers.get(complexity, 1.0)
                
                # Get cluster size multiplier
                size_factors = self.standards.get('complexity_factors', {}).get('cluster_size', {})
                cluster_size_multiplier = size_factors.get(cluster_size, {}).get('multiplier', 1.0)
                
                # Get regional multiplier
                regional_multiplier = self._get_regional_multiplier(region)
                
                # Calculate total cost
                total_cost = base_cost * complexity_multiplier * cluster_size_multiplier * regional_multiplier
                
                logger.info(f"✅ Calculated implementation cost for {optimization_type}: ${total_cost:.2f}")
                return total_cost
                
        except Exception as e:
            logger.error(f"❌ Error calculating implementation cost for {optimization_type}: {e}")
            # Return a reasonable default cost
            return 200.0

    def load_standards(self) -> Dict[str, Any]:
        """Public method to access loaded standards"""
        return self.standards.copy()  # Return a copy to prevent external modification

# Global instance - lazy loaded to avoid import-time initialization
_implementation_cost_calculator = None

def get_implementation_cost_calculator():
    """Get or create the global implementation cost calculator instance"""
    global _implementation_cost_calculator
    if _implementation_cost_calculator is None:
        _implementation_cost_calculator = ImplementationCostCalculator()
    return _implementation_cost_calculator

# Backward compatibility - property that lazy loads
class ImplementationCostCalculatorProxy:
    def __getattr__(self, name):
        return getattr(get_implementation_cost_calculator(), name)

implementation_cost_calculator = ImplementationCostCalculatorProxy()