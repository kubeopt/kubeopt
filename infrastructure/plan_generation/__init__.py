"""
Plan Generation Module

This module handles the separation of implementation plan generation from the
core analysis engine. It provides:

- AI API integration for plan generation
- Schema validation for generated plans
- Plan storage and versioning
- HTML rendering for plan visualization

Architecture:
    Data Collection → Enhanced Input → AI API → Plan Validation → Storage → Rendering
"""

from .ai_plan_generator import AIImplementationPlanGenerator
from .plan_schema import (
    KubeOptImplementationPlan, ImplementationPlanDocument, 
    OptimizationAction, ImplementationPhase, create_empty_plan
)
from .plan_validator import PlanValidator
from .plan_renderer import PlanRenderer
from .kubeopt_plan_renderer import KubeOptPlanRenderer, create_kubeopt_plan_renderer

__all__ = [
    'AIImplementationPlanGenerator',
    'KubeOptImplementationPlan',
    'ImplementationPlanDocument', 
    'ImplementationPhase',
    'OptimizationAction',
    'PlanValidator',
    'PlanRenderer',
    'KubeOptPlanRenderer',
    'create_kubeopt_plan_renderer',
    'create_empty_plan'
]