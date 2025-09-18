#!/usr/bin/env python3
"""
Analysis Results Viewer for AKS Cost Optimizer
Shows the structure and content of analysis results for debugging
"""

import json
import sys
from typing import Dict, Any

def format_analysis_results(analysis_data: Dict[str, Any]) -> str:
    """
    Format analysis results in a readable way for debugging
    """
    
    result = []
    result.append("=" * 80)
    result.append("AKS COST OPTIMIZER - ANALYSIS RESULTS STRUCTURE")
    result.append("=" * 80)
    
    # Basic cluster info
    if 'cluster_name' in analysis_data:
        result.append(f"🏷️  Cluster: {analysis_data['cluster_name']}")
    if 'resource_group' in analysis_data:
        result.append(f"📁  Resource Group: {analysis_data['resource_group']}")
    if 'subscription_id' in analysis_data:
        result.append(f"💳  Subscription: {analysis_data['subscription_id']}")
    
    result.append("")
    
    # Cost Analysis Summary
    result.append("💰 COST ANALYSIS")
    result.append("-" * 40)
    total_cost = analysis_data.get('total_cost', 0)
    total_savings = analysis_data.get('total_savings', 0)
    savings_pct = analysis_data.get('savings_percentage', 0)
    result.append(f"Total Cost:        ${total_cost:.2f}")
    result.append(f"Total Savings:     ${total_savings:.2f} ({savings_pct:.1f}%)")
    
    # Savings Breakdown
    if 'savings_by_category' in analysis_data:
        result.append("")
        result.append("💡 SAVINGS BREAKDOWN")
        result.append("-" * 40)
        for category, amount in analysis_data['savings_by_category'].items():
            result.append(f"{category.title():<20}: ${amount:.2f}")
    
    result.append("")
    
    # Health Score
    health_score = analysis_data.get('current_health_score', 0)
    result.append(f"🏥 Health Score:    {health_score:.1f}/100")
    
    result.append("")
    
    # HPA Analysis
    result.append("🔄 HPA ANALYSIS")
    result.append("-" * 40)
    
    if 'hpa_implementation' in analysis_data:
        hpa_impl = analysis_data['hpa_implementation']
        total_hpas = hpa_impl.get('total_hpas', 0)
        result.append(f"Total HPAs:        {total_hpas}")
        result.append(f"CPU-based:         {hpa_impl.get('cpu_based_count', 0)}")
        result.append(f"Memory-based:      {hpa_impl.get('memory_based_count', 0)}")
        result.append(f"Mixed-based:       {hpa_impl.get('mixed_based_count', 0)}")
        result.append(f"Custom-based:      {hpa_impl.get('custom_based_count', 0)}")
    
    if 'hpa_efficiency' in analysis_data:
        hpa_eff = analysis_data['hpa_efficiency']
        result.append(f"HPA Efficiency:    {hpa_eff:.1f}%")
    
    result.append("")
    
    # Implementation Plan
    if 'implementation_plan' in analysis_data:
        impl_plan = analysis_data['implementation_plan']
        result.append("📋 IMPLEMENTATION PLAN")
        result.append("-" * 40)
        
        if 'implementation_phases' in impl_plan:
            phases = impl_plan['implementation_phases']
            result.append(f"Total Phases:      {len(phases)}")
            
            for i, phase in enumerate(phases, 1):
                phase_name = phase.get('phase_name', f'Phase {i}')
                commands_count = len(phase.get('commands', []))
                result.append(f"  Phase {i}: {phase_name} ({commands_count} commands)")
        
        if 'confidence' in impl_plan:
            confidence = impl_plan['confidence']
            result.append(f"Plan Confidence:   {confidence:.1%}")
    
    result.append("")
    
    # Metrics Data
    if 'metrics_data' in analysis_data:
        result.append("📊 METRICS DATA")
        result.append("-" * 40)
        metrics = analysis_data['metrics_data']
        result.append(f"Available keys:    {', '.join(metrics.keys())}")
        
        if 'hpa_implementation' in metrics:
            hpa_metrics = metrics['hpa_implementation']
            result.append(f"HPA Metrics HPAs:  {hpa_metrics.get('total_hpas', 0)}")
    
    result.append("")
    
    # Security Analysis
    if 'security_analysis' in analysis_data:
        result.append("🔒 SECURITY ANALYSIS")
        result.append("-" * 40)
        security = analysis_data['security_analysis']
        if 'security_posture' in security:
            posture = security['security_posture']
            result.append(f"Security Score:    {posture.get('overall_score', 0):.1f}/100")
            result.append(f"Security Grade:    {posture.get('grade', 'N/A')}")
    
    result.append("")
    
    # Data Structure Overview
    result.append("🔍 DATA STRUCTURE OVERVIEW")
    result.append("-" * 40)
    
    def count_nested_items(obj, path=""):
        if isinstance(obj, dict):
            return sum(count_nested_items(v, f"{path}.{k}" if path else k) for k, v in obj.items())
        elif isinstance(obj, list):
            return len(obj)
        else:
            return 1
    
    main_sections = {}
    for key, value in analysis_data.items():
        if isinstance(value, dict):
            item_count = count_nested_items(value)
            main_sections[key] = f"dict with {item_count} nested items"
        elif isinstance(value, list):
            main_sections[key] = f"list with {len(value)} items"
        else:
            main_sections[key] = type(value).__name__
    
    for key, desc in sorted(main_sections.items()):
        result.append(f"{key:<25}: {desc}")
    
    result.append("")
    result.append("=" * 80)
    
    return "\n".join(result)

def display_current_analysis_results():
    """
    Load and display the current analysis results from the cache
    """
    try:
        # Try to import and access current analysis data
        import sys
        import os
        sys.path.append('/Users/srini/coderepos/aks-cost-optimizer')
        
        from app.shared.analysis_cache import analysis_cache
        
        # Get the most recent analysis results
        cached_data = analysis_cache.get_all_cache_data()
        
        if not cached_data:
            print("❌ No analysis results found in cache")
            return
        
        print(f"📄 Found {len(cached_data)} cached analysis results")
        print("")
        
        # Show the most recent one
        for cluster_key, data in cached_data.items():
            print(f"🔍 Analysis Results for: {cluster_key}")
            print("")
            formatted_results = format_analysis_results(data)
            print(formatted_results)
            print("")
            break  # Show only the first (most recent) one
            
    except Exception as e:
        print(f"❌ Error loading analysis results: {e}")
        print("This script should be run from the AKS Cost Optimizer directory")

if __name__ == "__main__":
    display_current_analysis_results()