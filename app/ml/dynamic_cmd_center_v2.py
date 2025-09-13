"""
Dynamic Command Center v2 - Modular Implementation

This is the new modular implementation that maintains backward compatibility
with the existing interface while providing a cleaner, more maintainable structure.

The old dynamic_cmd_center.py is kept for reference but this version should be used going forward.
"""

from typing import Dict, List, Optional
import logging

# Import from the new modular structure
from .command_center import AKSOptimizationOrchestrator, OptimizationConfig, ExecutableCommand, ComprehensiveExecutionPlan

logger = logging.getLogger(__name__)

class AdvancedExecutableCommandGenerator:
    """
    Backward compatibility wrapper for the new modular command generation system.
    
    This maintains the same interface as the original AdvancedExecutableCommandGenerator
    but uses the new modular structure internally.
    """
    
    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.orchestrator = AKSOptimizationOrchestrator(self.config)
    
    def generate_priority_driven_execution_plan(self, optimization_strategy, cluster_dna,
                                              analysis_results: Dict, cluster_config: Optional[Dict] = None) -> ComprehensiveExecutionPlan:
        """
        Generate comprehensive priority-driven execution plan.
        
        This method maintains the same signature as the original implementation
        but uses the new modular system internally.
        """
        return self.orchestrator.generate_priority_driven_execution_plan(
            optimization_strategy, cluster_dna, analysis_results, cluster_config
        )

# Maintain backward compatibility by exporting the same classes
__all__ = [
    'AdvancedExecutableCommandGenerator',
    'OptimizationConfig',
    'ExecutableCommand',
    'ComprehensiveExecutionPlan',
    'AKSOptimizationOrchestrator'  # New orchestrator for direct use
]