"""
Plan Generation Module

This module handles markdown-based implementation plan generation using Claude API.

Architecture:
    Data Collection → Enhanced Input → Claude API → Raw Markdown → Storage/Display
"""

from .ai_plan_generator import AIImplementationPlanGenerator

__all__ = [
    'AIImplementationPlanGenerator'
]