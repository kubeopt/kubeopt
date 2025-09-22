"""
AKS Cost Optimizer Command Center

A modular command generation system for Azure Kubernetes Service optimization.

Structure:
- models/: Core data models and structures
- analyzers/: Analysis components for different aspects
- generators/: Command generators organized by category
- strategies/: Various optimization strategies
- orchestrator.py: Main coordinator that brings everything together

Usage:
    from application.use_cases.orchestrator import AKSOptimizationOrchestrator
    
    orchestrator = AKSOptimizationOrchestrator()
    plan = orchestrator.generate_priority_driven_execution_plan(
        optimization_strategy, cluster_dna, analysis_results, cluster_config
    )
"""

from .orchestrator import AKSOptimizationOrchestrator
from .models.core import OptimizationConfig, ExecutableCommand, ComprehensiveExecutionPlan

__all__ = [
    'AKSOptimizationOrchestrator',
    'OptimizationConfig',
    'ExecutableCommand', 
    'ComprehensiveExecutionPlan'
]

__version__ = "1.0.0"