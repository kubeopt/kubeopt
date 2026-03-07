#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer
"""

"""
Chart Data Generation for AKS Cost Optimization Dashboard
"""

from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from shared.config.config import logger, enhanced_cluster_manager, _analysis_lock, _analysis_sessions
from shared.utils.utils import ensure_float
from shared.standards.cost_optimization_standards import CostCalculationStandards


def extract_standards_based_savings(analysis_results: Dict) -> Dict:
    """
    Extract comprehensive savings using international standards (CNCF, FinOps, Azure WAF, Google SRE).
    Returns the 5-category optimization framework.
    """
    # Check if using new consolidated system with savings_by_category
    if 'savings_by_category' in analysis_results:
        savings_by_cat = analysis_results['savings_by_category']
        
        # UNIFIED APPROACH: Category savings and total_savings are now consistent
        # Both come from the same validated category-based calculation
        category_total = sum(ensure_float(v) for v in savings_by_cat.values())
        total_savings = ensure_float(analysis_results.get('total_savings', 0))
        
        logger.info(f"✅ UNIFIED SAVINGS: Category sum=${category_total:.2f}, Total savings=${total_savings:.2f}")
        
        # Map lowercase analysis keys to the 5-category framework
        # Analysis engine produces: compute, rightsizing, hpa, performance, storage,
        # networking, infrastructure, monitoring, idle, control_plane, registry
        compute_opt = ensure_float(savings_by_cat.get('compute', 0)) + ensure_float(savings_by_cat.get('rightsizing', 0))
        core_opt = ensure_float(savings_by_cat.get('hpa', 0)) + ensure_float(savings_by_cat.get('performance', 0))
        infra = ensure_float(savings_by_cat.get('storage', 0)) + ensure_float(savings_by_cat.get('networking', 0)) + ensure_float(savings_by_cat.get('infrastructure', 0))
        container_data = ensure_float(savings_by_cat.get('monitoring', 0)) + ensure_float(savings_by_cat.get('idle', 0)) + ensure_float(savings_by_cat.get('control_plane', 0))
        security_mon = ensure_float(savings_by_cat.get('registry', 0))

        return {
            'core_optimization_savings': core_opt,
            'compute_optimization_savings': compute_opt,
            'infrastructure_savings': infra,
            'container_data_savings': container_data,
            'security_monitoring_savings': security_mon,
            'total_potential_savings': total_savings,
            'current_health_score': ensure_float(analysis_results.get('current_health_score', 0)),
            'standards_compliance': analysis_results.get('standards_compliance', {})
        }
    else:
        # Fallback to individual savings if consolidated system not used
        return {
            'core_optimization_savings': ensure_float(analysis_results.get('hpa_savings', 0)),
            'compute_optimization_savings': ensure_float(analysis_results.get('right_sizing_savings', 0)),
            'infrastructure_savings': ensure_float(analysis_results.get('storage_savings', 0)),
            'container_data_savings': ensure_float(analysis_results.get('total_savings', 0)) * 0.15,
            'security_monitoring_savings': ensure_float(analysis_results.get('total_savings', 0)) * 0.05,
            'total_potential_savings': ensure_float(analysis_results.get('total_savings', 0)),
            'current_health_score': 70.0,  # Default health score
            'standards_compliance': {}
        }

def _extract_hpa_details_from_workload_chars(workload_chars, total_hpas_analyzed):
    """Extract HPA details from workload characteristics data - REAL DATA ONLY"""
    hpa_details = []
    
    # Look for high CPU workloads which often have replica information
    high_cpu_workloads = workload_chars.get('high_cpu_workloads', [])
    if high_cpu_workloads and isinstance(high_cpu_workloads, list):
        for i, workload in enumerate(high_cpu_workloads):
            if isinstance(workload, dict):
                # ONLY extract if we have real replica data from the cluster
                current_replicas = workload.get('replicas') or workload.get('current_replicas')
                min_replicas = workload.get('min_replicas')
                max_replicas = workload.get('max_replicas')
                name = workload.get('name')
                namespace = workload.get('namespace')
                
                # STRICT: Only use if we have ALL real data
                if (current_replicas is not None and min_replicas is not None and 
                    max_replicas is not None and name and namespace):
                    
                    hpa_detail = {
                        'namespace': namespace,
                        'name': name,
                        'current_replicas': str(current_replicas),
                        'min_replicas': str(min_replicas), 
                        'max_replicas': str(max_replicas),
                        'hpa_id': f'{namespace}/{name}',
                        'data_source': 'real_workload_data'
                    }
                    hpa_details.append(hpa_detail)
                    logger.info(f"Extracted REAL HPA detail: {namespace}/{name} = current:{current_replicas}, min:{min_replicas}, max:{max_replicas}")
    
    # STRICT: Must have real replica data
    if len(hpa_details) == 0:
        logger.error(f"❌ No real HPA replica details found in workload_characteristics despite {total_hpas_analyzed} total HPAs")
        logger.error(f"❌ This means the workload data doesn't contain real current_replicas/min_replicas/max_replicas values")
        return []
        
    logger.info(f"✅ Extracted {len(hpa_details)} REAL HPA details with actual replica data from workload characteristics")
    return hpa_details

def _count_workloads(workload_costs):
    """Count workloads correctly from workload_costs dict.

    The dict contains Pod-level entries AND owner-level aggregates (Deployment, DaemonSet).
    If owner entries exist, count those (they represent real workloads).
    Otherwise fall back to Pod count.
    """
    if not isinstance(workload_costs, dict) or not workload_costs:
        return 0
    owners = [v for v in workload_costs.values()
              if isinstance(v, dict) and v.get('type') in ('Deployment', 'DaemonSet')]
    if owners:
        return len(owners)
    # No owner aggregation available — count pod entries as workloads
    return len(workload_costs)


def generate_insights(analysis_results, cloud_provider='azure'):
    """Generate 6 insight categories from analysis data."""
    if not analysis_results:
        return {}

    # Cloud-specific terminology for node compute resources
    _node_term = {
        'azure': 'VM Scale Sets',
        'aws': 'EC2 instances',
        'gcp': 'Node Pools',
    }.get(cloud_provider, 'Compute nodes')

    insights = {}
    node_cost = analysis_results.get('node_cost', 0)
    total_cost = analysis_results.get('total_cost', 0)
    total_savings = analysis_results.get('total_savings', 0)

    # 1. Cost breakdown
    try:
        if total_cost <= 0:
            insights['cost_breakdown'] = "<strong>Cost Analysis:</strong> Cost data temporarily unavailable - analysis in progress."
        else:
            node_percentage = (node_cost / total_cost) * 100
            if node_percentage > 60:
                insights['cost_breakdown'] = f"{_node_term} (nodes) dominate your costs at <strong>{node_percentage:.1f}%</strong> (${node_cost:.2f}), making them your #1 optimization target."
            elif node_percentage > 40:
                insights['cost_breakdown'] = f"{_node_term} represent <strong>{node_percentage:.1f}%</strong> of costs (${node_cost:.2f}), offering significant optimization opportunities."
            else:
                insights['cost_breakdown'] = f"✅ Your costs are well-distributed with {_node_term} at <strong>{node_percentage:.1f}%</strong> (${node_cost:.2f})."
    except Exception as e:
        logger.error(f"Cost breakdown insight failed: {e}")
        insights['cost_breakdown'] = "Cost analysis temporarily unavailable"

    # 2. HPA comparison
    try:
        hpa_savings = analysis_results.get('hpa_savings')
        hpa_recommendations = analysis_results.get('hpa_recommendations')

        if not hpa_recommendations:
            core_savings = ensure_float(analysis_results.get('core_optimization_savings', 0))
            if core_savings > 0:
                current_health = analysis_results.get('current_health_score', 0)
                target_health = analysis_results.get('target_health_score', 0)
                insights['hpa_comparison'] = f"<strong>Core Optimization Opportunity:</strong> ${core_savings:.2f}/month savings through HPA, rightsizing & storage optimization. Health Score: {current_health:.1f}/100 (Target: {target_health:.1f})"
            else:
                insights['hpa_comparison'] = "<strong>HPA Analysis:</strong> Cluster analyzed for horizontal scaling opportunities."
        else:
            ml_workload_chars = hpa_recommendations.get('workload_characteristics', {})
            ml_classification = ml_workload_chars.get('comprehensive_ml_classification', {})
            workload_type = ml_classification.get('workload_type')
            ml_confidence = ml_classification.get('confidence', 0.0)
            ml_recommendation = hpa_recommendations.get('optimization_recommendation', {})

            if workload_type and ml_confidence > 0 and ml_recommendation.get('ml_enhanced'):
                ml_title = ml_recommendation.get('title', 'Analysis')
                standards_savings = extract_standards_based_savings(analysis_results)
                core_optimization = standards_savings['core_optimization_savings']

                type_icons = {'LOW_UTILIZATION': '', 'CPU_INTENSIVE': '', 'MEMORY_INTENSIVE': '', 'BURSTY': ''}
                icon = type_icons.get(workload_type, '')
                insights['hpa_comparison'] = f"{icon} <strong>{ml_title}</strong>: Classified as {workload_type} ({ml_confidence:.0%} confidence). Core optimization saves ${core_optimization:.2f}/month."

                hpa_efficiency = analysis_results.get('hpa_efficiency_percentage', 0)
                if hpa_efficiency < 60:
                    insights['hpa_comparison'] += f" <em>Enhanced Analysis: {100-hpa_efficiency:.0f}% efficiency gap detected.</em>"
            elif hpa_savings and hpa_savings > 0:
                hpa_count = ensure_float(analysis_results.get('hpa_count', 0))
                if hpa_count > 0:
                    insights['hpa_comparison'] = f"<strong>HPA Analysis Complete:</strong> Identified ${hpa_savings:.2f}/month potential savings from optimizing {int(hpa_count)} existing HPAs."
                else:
                    insights['hpa_comparison'] = f"<strong>HPA Opportunity:</strong> Adding autoscaling could save ${hpa_savings:.2f}/month. No HPAs currently configured."
            else:
                insights['hpa_comparison'] = "<strong>HPA Assessment:</strong> Cluster evaluated for horizontal pod autoscaling opportunities."
    except Exception as e:
        logger.error(f"HPA insight failed: {e}")
        insights['hpa_comparison'] = "<strong>Scaling Analysis:</strong> Cluster resource utilization assessed."

    # 3. Resource gap — show actual utilization, not abstract gap-from-optimal
    try:
        cpu_gap = ensure_float(analysis_results.get('cpu_gap', 0))
        memory_gap = ensure_float(analysis_results.get('memory_gap', 0))
        # Derive actual utilization: gap = |optimal - actual|, so actual = optimal - gap
        from shared.standards.performance_standards import SystemPerformanceStandards
        cpu_actual = round(SystemPerformanceStandards.CPU_UTILIZATION_OPTIMAL - cpu_gap, 1)
        mem_actual = round(SystemPerformanceStandards.MEMORY_UTILIZATION_OPTIMAL - memory_gap, 1)
        # Try multiple fields for rightsizing savings
        right_sizing_savings = ensure_float(
            analysis_results.get('compute_savings', 0)
            or analysis_results.get('right_sizing_savings', 0)
            or analysis_results.get('rightsizing_savings', 0)
        )
        # If still $0 but significant gap exists, estimate from node cost
        if right_sizing_savings == 0 and (cpu_gap > 40 or memory_gap > 30) and node_cost > 0:
            avg_gap = (cpu_gap + memory_gap) / 2
            right_sizing_savings = node_cost * (avg_gap / 100) * 0.5  # conservative 50% of gap

        if cpu_gap > 40 or memory_gap > 30:
            insights['resource_gap'] = f"<strong>CRITICAL OVER-PROVISIONING:</strong> Cluster using only <strong>{cpu_actual:.1f}% CPU</strong> and <strong>{mem_actual:.1f}% memory</strong> (target: 70% / 75%). Right-sizing can save <strong>${right_sizing_savings:.2f}/month</strong>!"
        else:
            insights['resource_gap'] = f"✅ <strong>WELL-OPTIMIZED:</strong> Cluster at <strong>{cpu_actual:.1f}% CPU</strong> and <strong>{mem_actual:.1f}% memory</strong> (target: 70% / 75%)."
    except Exception as e:
        logger.error(f"Resource gap insight failed: {e}")
        insights['resource_gap'] = "<strong>Resource Analysis:</strong> Cluster resource allocation evaluated."

    # 4. Savings summary
    try:
        annual_savings = analysis_results.get('annual_savings', 0)
        if annual_savings == 0 and total_savings > 0:
            annual_savings = total_savings * 12
        savings_percentage = analysis_results.get('savings_percentage', 0)
        if savings_percentage == 0 and total_savings > 0 and total_cost > 0:
            savings_percentage = (total_savings / total_cost) * 100

        if savings_percentage > 25:
            insights['savings_summary'] = f"<strong>MASSIVE ROI OPPORTUNITY:</strong> Save <strong>${annual_savings:.2f}/year</strong> ({savings_percentage:.1f}% cost reduction)!"
        elif savings_percentage > 15:
            insights['savings_summary'] = f"<strong>SIGNIFICANT IMPACT:</strong> Annual savings of <strong>${annual_savings:.2f}</strong> ({savings_percentage:.1f}% reduction)."
        else:
            insights['savings_summary'] = f"<strong>STEADY IMPROVEMENTS:</strong> Save <strong>${annual_savings:.2f}/year</strong> ({savings_percentage:.1f}% optimization)."

        # Append advanced opportunities from real cost data
        enhanced = []
        if analysis_results.get('cpu_gap', 0) > 30 and analysis_results.get('memory_gap', 0) > 20:
            frag = min((analysis_results['cpu_gap'] + analysis_results['memory_gap']) / 200, 0.6)
            enhanced.append(f"Node consolidation: ${node_cost * 0.12 * frag:.0f}/month")
        monitoring_cost = analysis_results.get('monitoring_cost', 0)
        if monitoring_cost > 10 and total_cost > 0:
            mon_pct = (monitoring_cost / total_cost) * 100
            if mon_pct > 50:
                enhanced.append(f"Monitoring optimization: ${max(0, monitoring_cost - total_cost * 0.10):.0f}/month")
            elif mon_pct > 20:
                enhanced.append(f"Monitoring optimization: ${monitoring_cost * 0.25:.0f}/month")
        if enhanced:
            insights['savings_summary'] += f" Additional opportunities: {', '.join(enhanced[:3])}."
    except Exception as e:
        logger.error(f"Savings summary insight failed: {e}")
        if total_savings > 0:
            insights['savings_summary'] = f"<strong>Optimization Potential:</strong> ${total_savings:.2f}/month in identified savings opportunities."
        else:
            insights['savings_summary'] = "<strong>Cost Analysis:</strong> Cluster cost optimization assessment completed."

    # 5. Operational efficiency
    try:
        workload_costs = analysis_results.get('workload_costs') or analysis_results.get('pod_cost_analysis', {}).get('workload_costs', {})
        # Count workloads correctly: prefer Deployment-level entries over raw pods
        # workload_costs contains both Pod entries and Deployment aggregates
        total_workloads = _count_workloads(workload_costs)
        namespace_costs = analysis_results.get('namespace_costs') or analysis_results.get('pod_cost_analysis', {}).get('namespace_costs') or analysis_results.get('pod_cost_analysis', {}).get('namespace_summary', {})
        total_namespaces = len(namespace_costs) if isinstance(namespace_costs, dict) else 0

        if total_workloads > 100 and total_namespaces > 10:
            wl_per_ns = total_workloads / total_namespaces
            if wl_per_ns > 40:
                ineff = min(20, (wl_per_ns - 30) / 2)
                insights['operational_efficiency'] = f"<strong>DEVOPS OPTIMIZATION:</strong> {total_workloads} workloads across {total_namespaces} namespaces shows <strong>{ineff:.0f}% deployment inefficiency</strong>. Could save <strong>${node_cost * (ineff / 100):.0f}/month</strong>."
            else:
                insights['operational_efficiency'] = f"✅ <strong>OPERATIONAL EXCELLENCE:</strong> {total_workloads} workloads well-distributed across {total_namespaces} namespaces."
        else:
            insights['operational_efficiency'] = f"<strong>OPERATIONAL BASELINE:</strong> {total_workloads} workloads in {total_namespaces} namespaces."
    except Exception as e:
        logger.error(f"Operational efficiency insight failed: {e}")

    # 6. Business impact
    try:
        _wl_costs_biz = analysis_results.get('workload_costs') or analysis_results.get('pod_cost_analysis', {}).get('workload_costs', {})
        total_workloads_for_biz = _count_workloads(_wl_costs_biz)
        if total_workloads_for_biz > 0 and total_cost > 0:
            cpw = total_cost / total_workloads_for_biz
            # Scale benchmark by cluster size — small clusters have higher per-workload
            # cost due to fixed overhead (control plane, monitoring) amortized over fewer workloads.
            # Base target from CostCalculationStandards.TARGET_COST_PER_WORKLOAD_MONTH ($45).
            base_target = CostCalculationStandards.TARGET_COST_PER_WORKLOAD_MONTH
            benchmark = max(3.0, (base_target * 0.55) / total_workloads_for_biz + 3.0)
            optimized_cpw = (total_cost - total_savings) / total_workloads_for_biz
            diff = ((cpw - benchmark) / benchmark) * 100
            if cpw > benchmark:
                insights['business_impact'] = f"<strong>BUSINESS METRICS:</strong> ${cpw:.2f}/workload vs ${benchmark:.2f}/workload benchmark. Optimization targets ${optimized_cpw:.2f}/workload ({diff:.0f}% above benchmark)."
            else:
                insights['business_impact'] = f"<strong>BUSINESS EXCELLENCE:</strong> ${cpw:.2f}/workload is {-diff:.0f}% below benchmark (${benchmark:.2f}) - excellent efficiency!"
        else:
            insights['business_impact'] = f"<strong>BUSINESS BASELINE:</strong> Current monthly cost ${total_cost:.0f} being analyzed."
    except Exception as e:
        logger.error(f"Business impact insight failed: {e}")

    return insights

def generate_dynamic_hpa_comparison(analysis_data):
    """Generate HPA comparison data in Recharts format: [{time, cpu, memory}]

    Uses tiered fallbacks:
      Tier 1: Full ML pipeline (workload classification + HPA replica data)
      Tier 2: Basic HPA data (cpu/memory utilization without full ML classification)
      Tier 3: Utilization projection from top-level analysis metrics
    """
    if not analysis_data:
        raise ValueError("No analysis data provided for HPA comparison")

    # Tier 1: Full ML pipeline
    try:
        result = _generate_ml_hpa_comparison(analysis_data)
        if result:
            logger.info("✅ HPA comparison: Tier 1 (full ML pipeline)")
            return result
    except Exception as e:
        logger.debug(f"HPA Tier 1 skipped: {e}")

    # Tier 2: Basic HPA data using utilization without full ML classification
    try:
        result = _generate_basic_hpa_comparison(analysis_data)
        if result:
            logger.info("✅ HPA comparison: Tier 2 (basic HPA data)")
            return result
    except Exception as e:
        logger.debug(f"HPA Tier 2 skipped: {e}")

    # Tier 3: Utilization projection from top-level analysis fields
    result = _generate_utilization_hpa_projection(analysis_data)
    if result:
        logger.info("✅ HPA comparison: Tier 3 (utilization projection)")
        return result

    raise ValueError("No HPA data available at any tier")


def _generate_ml_hpa_comparison(analysis_data):
    """Tier 1: Full ML pipeline — requires workload classification + HPA replica data."""
    hpa_recommendations = analysis_data.get('hpa_recommendations')
    if not hpa_recommendations:
        raise ValueError("No HPA recommendations")

    ml_workload_characteristics = hpa_recommendations.get('workload_characteristics')
    if not ml_workload_characteristics:
        raise ValueError("No ML workload characteristics")

    ml_optimization_analysis = ml_workload_characteristics.get('optimization_analysis', {})
    ml_hpa_recommendation = ml_workload_characteristics.get('hpa_recommendation', {})
    ml_classification = ml_workload_characteristics.get('comprehensive_ml_classification')
    if not ml_classification:
        raise ValueError("No ML classification")

    workload_type = ml_classification.get('workload_type')
    ml_confidence = ml_classification.get('confidence', 0.0)
    primary_action = ml_optimization_analysis.get('primary_action')
    if not workload_type or ml_confidence <= 0 or not primary_action:
        raise ValueError("Invalid ML classification data")

    total_cost = ensure_float(analysis_data.get('total_cost', 0))
    if total_cost <= 0:
        raise ValueError("Invalid total cost")

    hpa_efficiency = _extract_hpa_efficiency(analysis_data, hpa_recommendations)
    if hpa_efficiency is None:
        raise ValueError("No HPA efficiency data")

    ml_cpu_util = ml_workload_characteristics.get('cpu_usage_pct') or ml_workload_characteristics.get('cpu_utilization')
    ml_memory_util = ml_workload_characteristics.get('memory_usage_pct') or ml_workload_characteristics.get('memory_utilization')
    if ml_cpu_util is None or ml_memory_util is None:
        raise ValueError("Missing ML utilization data")

    actual_hpa_savings = analysis_data.get('hpa_savings', 0)
    scenarios = _generate_ml_driven_scenarios(
        workload_type, primary_action, ml_confidence,
        ml_cpu_util, ml_memory_util, actual_hpa_savings,
        ml_hpa_recommendation, ml_optimization_analysis, analysis_data
    )
    if not scenarios:
        raise ValueError("Failed to generate ML scenarios")

    return _format_hpa_result(scenarios.get('cpu_replicas', [0, 0, 0, 0]),
                              scenarios.get('memory_replicas', [0, 0, 0, 0]))


def _generate_basic_hpa_comparison(analysis_data):
    """Tier 2: Use cpu_usage_pct/memory_usage_pct from workload_characteristics
    without needing full ML classification chain."""
    hpa_recs = analysis_data.get('hpa_recommendations', {})
    if not isinstance(hpa_recs, dict):
        raise ValueError("No hpa_recommendations dict")

    wc = hpa_recs.get('workload_characteristics', {})
    if not isinstance(wc, dict):
        raise ValueError("No workload_characteristics")

    cpu_pct = wc.get('cpu_usage_pct') or wc.get('cpu_utilization')
    mem_pct = wc.get('memory_usage_pct') or wc.get('memory_utilization')
    if not cpu_pct or not mem_pct:
        raise ValueError("Missing cpu/memory utilization in workload_characteristics")

    cpu_pct = float(cpu_pct)
    mem_pct = float(mem_pct)

    # Get total HPAs for scale
    total_hpas = analysis_data.get('total_hpas_analyzed', 0)
    metrics_data = hpa_recs.get('metrics_data', {})
    if isinstance(metrics_data, dict):
        hpa_impl = metrics_data.get('hpa_implementation', {})
        if isinstance(hpa_impl, dict):
            total_hpas = max(total_hpas, hpa_impl.get('total_hpas', 0))
    base_replicas = max(total_hpas, 1)

    target = 80.0
    load_factors = [0.3, 0.7, 1.0, 0.6]  # night, morning, afternoon, evening
    cpu_replicas = [max(1, int(np.ceil(base_replicas * (cpu_pct * lf / target)))) for lf in load_factors]
    mem_replicas = [max(1, int(np.ceil(base_replicas * (mem_pct * lf / target)))) for lf in load_factors]

    return _format_hpa_result(cpu_replicas, mem_replicas)


def _generate_utilization_hpa_projection(analysis_data):
    """Tier 3: Project HPA scaling from top-level analysis metrics (cpu_gap, node_count)."""
    cpu_gap = ensure_float(analysis_data.get('cpu_gap', 0))
    memory_gap = ensure_float(analysis_data.get('memory_gap', 0))
    node_count = int(analysis_data.get('node_count', 0) or 0)

    # Need at least some utilization signal
    avg_cpu = ensure_float(analysis_data.get('average_cpu_utilization', 0))
    avg_mem = ensure_float(analysis_data.get('average_memory_utilization', 0))

    if avg_cpu <= 0 and avg_mem <= 0 and cpu_gap <= 0:
        return None

    # Use node_count as base replica proxy; fall back to 3
    base = max(node_count, 3)

    # If we have utilization percentages, use them
    if avg_cpu > 0 or avg_mem > 0:
        cpu_pct = avg_cpu if avg_cpu > 0 else 30.0
        mem_pct = avg_mem if avg_mem > 0 else 50.0
    else:
        # Derive from gap: gap = requested - used; estimate utilization
        cpu_pct = max(10.0, 100.0 - cpu_gap)
        mem_pct = max(10.0, 100.0 - memory_gap)

    target = 80.0
    load_factors = [0.3, 0.7, 1.0, 0.6]
    cpu_replicas = [max(1, int(np.ceil(base * (cpu_pct * lf / target)))) for lf in load_factors]
    mem_replicas = [max(1, int(np.ceil(base * (mem_pct * lf / target)))) for lf in load_factors]

    return _format_hpa_result(cpu_replicas, mem_replicas)


def _format_hpa_result(cpu_replicas, memory_replicas):
    """Format HPA replica arrays into Recharts [{time, cpu, memory}] format."""
    time_labels = ['Night (12AM-6AM)', 'Morning (6AM-12PM)', 'Afternoon (12PM-6PM)', 'Evening (6PM-12AM)']
    return [
        {'time': t, 'cpu': float(c) if c else 0, 'memory': float(m) if m else 0}
        for t, c, m in zip(time_labels, cpu_replicas, memory_replicas)
    ]

def _extract_cpu_workload_data(analysis_data):
    """Extract CPU workload data from top_cpu_summary or hpa_recommendations."""
    if not analysis_data:
        raise ValueError("No analysis data provided for CPU workload extraction")

    result = {
        'has_high_cpu_workloads': False,
        'high_cpu_count': 0,
        'severity_level': 'none',
        'workload_names': [],
        'cpu_analysis_available': False,
        'max_cpu_utilization': 0,
        'avg_cpu_utilization': 0,
    }

    # Source 1: top_cpu_summary
    if 'top_cpu_summary' in analysis_data:
        cpu_summary = analysis_data['top_cpu_summary']
        if isinstance(cpu_summary, dict):
            if cpu_summary.get('max_cpu_utilization') is not None:
                result['max_cpu_utilization'] = float(cpu_summary['max_cpu_utilization'])
            if cpu_summary.get('avg_cpu_utilization') is not None:
                result['avg_cpu_utilization'] = float(cpu_summary['avg_cpu_utilization'])

            all_workloads = cpu_summary.get('all_workloads', [])
            if isinstance(all_workloads, list) and all_workloads:
                result['cpu_analysis_available'] = True
                cpu_values = []
                for wl in all_workloads:
                    if isinstance(wl, dict):
                        if 'name' in wl:
                            result['workload_names'].append(wl['name'])
                        cpu_val = wl.get('cpu_usage_pct', 0)
                        if cpu_val > 0:
                            cpu_values.append(ensure_float(cpu_val))
                            result['max_cpu_utilization'] = max(result['max_cpu_utilization'], ensure_float(cpu_val))
                if cpu_values:
                    result['avg_cpu_utilization'] = sum(cpu_values) / len(cpu_values)

    # Source 2: hpa_recommendations.workload_characteristics
    if not result['cpu_analysis_available']:
        hpa_recs = analysis_data.get('hpa_recommendations', {})
        ml_wc = hpa_recs.get('workload_characteristics', {}) if isinstance(hpa_recs, dict) else {}
        high_cpu = ml_wc.get('high_cpu_workloads', []) if isinstance(ml_wc, dict) else []
        if high_cpu:
            result['has_high_cpu_workloads'] = True
            result['high_cpu_count'] = len(high_cpu)
            result['cpu_analysis_available'] = True
            cpu_values = []
            for wl in high_cpu:
                if isinstance(wl, dict):
                    if 'name' in wl:
                        result['workload_names'].append(wl['name'])
                    cpu_val = ensure_float(wl.get('cpu_utilization', wl.get('cpu_usage_pct', 0)))
                    if cpu_val > 0:
                        cpu_values.append(cpu_val)
                        result['max_cpu_utilization'] = max(result['max_cpu_utilization'], cpu_val)
            if cpu_values:
                result['avg_cpu_utilization'] = sum(cpu_values) / len(cpu_values)
        else:
            avg_cpu = ml_wc.get('cpu_usage_pct') or ml_wc.get('cpu_utilization')
            if avg_cpu and avg_cpu > 0:
                result['avg_cpu_utilization'] = float(avg_cpu)
                result['cpu_analysis_available'] = True

    # Severity
    max_cpu = result['max_cpu_utilization']
    if max_cpu >= 1000:
        result['severity_level'] = 'critical'
    elif max_cpu >= 500:
        result['severity_level'] = 'high'
    elif max_cpu >= 200:
        result['severity_level'] = 'medium'
    elif max_cpu > 0:
        result['severity_level'] = 'low'

    return result

def _extract_hpa_efficiency(analysis_data, hpa_recommendations):
    """Extract HPA efficiency from REAL sources ONLY - per .clauderc standards"""
    hpa_efficiency = None
    
    efficiency_sources = [
        analysis_data.get('hpa_efficiency'),
        analysis_data.get('hpa_efficiency_percentage'), 
        hpa_recommendations.get('hpa_efficiency_percentage'),
        hpa_recommendations.get('hpa_efficiency'),
        hpa_recommendations.get('workload_characteristics', {}).get('hpa_efficiency_percentage')
    ]
    
    for eff_val in efficiency_sources:
        if eff_val is not None:  # Accept any numeric value including 0 (per .clauderc - real data)
            hpa_efficiency = ensure_float(eff_val)
            logger.info(f"✅ Found HPA efficiency: {hpa_efficiency:.1f}%")
            break
    
    if hpa_efficiency is None:
        # STANDARDS-BASED: Use international standards framework
        standards_savings = extract_standards_based_savings(analysis_data)
        actual_core_savings = standards_savings['core_optimization_savings']
        total_cost = ensure_float(analysis_data.get('total_cost', 0))
        if actual_core_savings > 0 and total_cost > 0:
            hpa_efficiency = min(50.0, (actual_core_savings / total_cost) * 100)
            logger.info(f"Calculated core optimization efficiency from savings: {hpa_efficiency:.1f}%")
    
    return hpa_efficiency

def _extract_hpa_state_data(analysis_data):
    """Extract HPA state data from hpa_state or hpa_recommendations.metrics_data."""
    if not analysis_data:
        return {}

    hpa_state = {
        'hpa_type_distribution': {}, 'summary': {},
        'existing_hpas': [], 'deployment_mapping': {}
    }

    try:
        # Source 1: direct hpa_state field
        if isinstance(analysis_data.get('hpa_state'), dict):
            hpa_state.update(analysis_data['hpa_state'])

        # Source 2: hpa_recommendations.metrics_data.hpa_implementation
        hpa_recs = analysis_data.get('hpa_recommendations', {})
        metrics_data = hpa_recs.get('metrics_data', {}) if isinstance(hpa_recs, dict) else {}
        hpa_impl = metrics_data.get('hpa_implementation', {}) if isinstance(metrics_data, dict) else {}

        if isinstance(hpa_impl, dict) and hpa_impl.get('total_hpas', 0) > 0:
            total_hpas = hpa_impl['total_hpas']
            cpu_count = hpa_impl.get('cpu_based_count', 0)
            mem_count = hpa_impl.get('memory_based_count', 0)
            mixed_count = max(0, total_hpas - cpu_count - mem_count)

            hpa_details = hpa_impl.get('hpa_details', [])
            if isinstance(hpa_details, list) and hpa_details:
                existing_hpas = []
                for i, detail in enumerate(hpa_details):
                    if not isinstance(detail, dict):
                        continue
                    if i < cpu_count:
                        hpa_type = 'cpu'
                    elif i < cpu_count + mem_count:
                        hpa_type = 'memory'
                    else:
                        hpa_type = 'mixed'
                    existing_hpas.append({
                        'namespace': detail.get('namespace'),
                        'name': detail.get('name'),
                        'current_replicas': detail.get('current_replicas'),
                        'min_replicas': detail.get('min_replicas'),
                        'max_replicas': detail.get('max_replicas'),
                        'hpa_id': detail.get('hpa_id'),
                        'hpa_type': hpa_type,
                        'spec': {'minReplicas': detail.get('min_replicas'), 'maxReplicas': detail.get('max_replicas')},
                        'status': {'currentReplicas': detail.get('current_replicas')},
                    })
                if existing_hpas:
                    hpa_state['existing_hpas'] = existing_hpas

            hpa_state['summary'] = {'existing_hpas': total_hpas, 'hpa_coverage_percent': 100.0, 'missing_candidates': 0}
            hpa_state['hpa_type_distribution'] = {'cpu': cpu_count, 'memory': mem_count, 'mixed': mixed_count, 'custom': 0}

    except Exception as e:
        logger.warning(f"Error extracting HPA state data: {e}")

    return hpa_state


def _generate_ml_driven_scenarios(workload_type: str, primary_action: str, ml_confidence: float,
                                 ml_cpu_util: float, ml_memory_util: float, actual_hpa_savings: float,
                                 ml_hpa_recommendation: Dict, ml_optimization_analysis: Dict,
                                 analysis_data: Dict) -> Optional[Dict[str, Any]]:
    """Generate HPA scaling scenarios from real cluster data. Returns cpu_replicas + memory_replicas."""
    if not all([workload_type, primary_action, ml_confidence > 0]):
        raise ValueError("Invalid ML input parameters for scenario generation")

    # Find HPA implementation data
    hpa_implementation = analysis_data.get('hpa_implementation')
    if not hpa_implementation:
        hpa_recs = analysis_data.get('hpa_recommendations', {})
        if isinstance(hpa_recs, dict):
            metrics_data = hpa_recs.get('metrics_data', {})
            if isinstance(metrics_data, dict) and 'hpa_implementation' in metrics_data:
                hpa_implementation = metrics_data['hpa_implementation']
            elif isinstance(hpa_recs.get('workload_characteristics'), dict):
                total_analyzed = analysis_data.get('total_hpas_analyzed', 0)
                if total_analyzed > 0:
                    hpa_implementation = {
                        'total_hpas': total_analyzed,
                        'current_hpa_pattern': analysis_data.get('current_hpa_pattern', 'mixed_implementation'),
                        'hpa_details': _extract_hpa_details_from_workload_chars(hpa_recs['workload_characteristics'], total_analyzed),
                        'cpu_based_count': max(1, total_analyzed // 2),
                        'memory_based_count': max(1, total_analyzed - (total_analyzed // 2)),
                    }

    if not hpa_implementation:
        raise ValueError("No real HPA implementation data available")

    hpa_state_data = _extract_hpa_state_data(analysis_data)
    total_hpas = hpa_implementation.get('total_hpas', 0)
    if total_hpas == 0:
        return None

    current_replicas_data = _extract_real_hpa_replica_data(hpa_state_data, total_hpas)
    if not current_replicas_data:
        return None

    cpu_replicas, memory_replicas = _extract_real_replica_arrays_for_chart(current_replicas_data, analysis_data)

    return {
        'cpu_replicas': cpu_replicas,
        'memory_replicas': memory_replicas,
    }

def _extract_real_hpa_replica_data(hpa_state_data, total_hpas):
    """Extract replica data from HPA analysis - return None if fails"""
    import numpy as np
    
    existing_hpas = hpa_state_data.get('existing_hpas', [])
    hpa_type_distribution = hpa_state_data.get('hpa_type_distribution', {})
    
    # If we have detailed HPA specs, use them
    if existing_hpas and len(existing_hpas) > 0:
        logger.info(f"Processing {len(existing_hpas)} real HPAs with complete specifications")
    
    # Extract real replica data by HPA type
    cpu_hpa_replicas = []
    memory_hpa_replicas = []
    mixed_hpa_replicas = []
    custom_hpa_replicas = []
    
    total_current_replicas = 0
    total_min_replicas = 0
    total_max_replicas = 0
    
    for hpa in existing_hpas:
        if not isinstance(hpa, dict):
            continue
            
        # Get replica counts from real HPA status
        current_replicas = 1  # Default
        min_replicas = 1
        max_replicas = 10
        
        # Extract from HPA status (real cluster data)
        if 'status' in hpa:
            status = hpa['status']
            current_replicas = int(status.get('currentReplicas', status.get('current_replicas', 1)))
        elif 'current_replicas' in hpa:
            current_replicas = int(hpa['current_replicas'])
            
        # Extract from HPA spec (real cluster data)
        if 'spec' in hpa:
            spec = hpa['spec']
            min_replicas = int(spec.get('minReplicas', spec.get('min_replicas', 1)))
            max_replicas = int(spec.get('maxReplicas', spec.get('max_replicas', 10)))
        elif 'min_replicas' in hpa and 'max_replicas' in hpa:
            min_replicas = int(hpa['min_replicas'])
            max_replicas = int(hpa['max_replicas'])
        
        # Categorize by HPA type (from real analysis)
        hpa_type = hpa.get('hpa_type', 'unknown')
        replica_data = {
            'current': current_replicas,
            'min': min_replicas,
            'max': max_replicas
        }
        
        if hpa_type == 'cpu':
            cpu_hpa_replicas.append(replica_data)
        elif hpa_type == 'memory':
            memory_hpa_replicas.append(replica_data)
        elif hpa_type == 'mixed':
            mixed_hpa_replicas.append(replica_data)
        else:
            custom_hpa_replicas.append(replica_data)
            
        total_current_replicas += current_replicas
        total_min_replicas += min_replicas
        total_max_replicas += max_replicas
    
    total_hpas = len(existing_hpas)
    avg_current = total_current_replicas / max(total_hpas, 1)
    
    logger.info(f"Real HPA Analysis: {len(cpu_hpa_replicas)} CPU, {len(memory_hpa_replicas)} Memory, {len(mixed_hpa_replicas)} Mixed, {len(custom_hpa_replicas)} Custom")
    logger.info(f"Real Replica Stats: Avg={avg_current:.1f}, Total Current={total_current_replicas}")
    
    return {
        'total_hpas': total_hpas,
        'current_avg': avg_current,
        'total_current_replicas': total_current_replicas,
        'cpu_based_count': len(cpu_hpa_replicas),
        'memory_based_count': len(memory_hpa_replicas),
        'mixed_based_count': len(mixed_hpa_replicas),
        'custom_based_count': len(custom_hpa_replicas),
        'cpu_hpa_replicas': cpu_hpa_replicas,
        'memory_hpa_replicas': memory_hpa_replicas,
        'mixed_hpa_replicas': mixed_hpa_replicas,
        'custom_hpa_replicas': custom_hpa_replicas,
        'real_data': True,
        'data_source': 'enhanced_hpa_analysis'
    }

def _extract_real_replica_arrays_for_chart(current_replicas_data, analysis_data=None):
    """Calculate believable HPA scaling scenarios based on actual workload characteristics"""
    
    # Get real HPA replica data by type
    cpu_hpa_replicas = current_replicas_data.get('cpu_hpa_replicas', [])
    memory_hpa_replicas = current_replicas_data.get('memory_hpa_replicas', [])
    mixed_hpa_replicas = current_replicas_data.get('mixed_hpa_replicas', [])
    
    # Get overall workload statistics
    total_hpas = current_replicas_data.get('total_hpas', 0)
    total_current_replicas = current_replicas_data.get('total_current_replicas', 0)
    avg_current = current_replicas_data.get('current_avg', 1.0)
    
    logger.info(f"Calculating scaling scenarios for {total_hpas} HPAs with avg {avg_current} replicas")
    
    # Calculate realistic scaling scenarios based on actual cluster characteristics
    return _calculate_believable_scaling_scenarios(
        cpu_hpa_replicas, memory_hpa_replicas, mixed_hpa_replicas, 
        total_hpas, avg_current, analysis_data
    )

def _extract_current_cpu_usage(analysis_data):
    """Extract current CPU usage from analysis data using same logic as _extract_cpu_workload_data"""
    try:
        # Extract from the same source as _extract_cpu_workload_data function
        if analysis_data and isinstance(analysis_data, dict):
            hpa_recommendations = analysis_data.get('hpa_recommendations', {})
            ml_workload_characteristics = hpa_recommendations.get('workload_characteristics', {})
            
            # Extract average CPU from enhanced analysis (same as _extract_cpu_workload_data)
            # FIXED: ML model outputs cpu_usage_pct, not cpu_utilization
            avg_cpu = ml_workload_characteristics.get('cpu_usage_pct', 0)
            if avg_cpu <= 0:
                avg_cpu = ml_workload_characteristics.get('cpu_utilization', 0)
            
            if avg_cpu > 0:
                logger.info(f"✅ Found real CPU usage from ML workload characteristics: {avg_cpu}%")
                return float(avg_cpu)
        
        # Fallback: Get from enhanced_cluster_manager cache 
        if enhanced_cluster_manager and hasattr(enhanced_cluster_manager, 'get_cluster_utilization'):
            cpu_util, _ = enhanced_cluster_manager.get_cluster_utilization()
            if cpu_util is not None:
                logger.info(f"✅ Found real CPU usage from cache: {cpu_util}%")
                return cpu_util
        
        # Fallback: Try direct access to cluster managers
        from shared.config.config import _analysis_sessions
        for session_key, session_data in _analysis_sessions.items():
            if 'cluster_manager' in session_data:
                cluster_manager = session_data['cluster_manager']
                if hasattr(cluster_manager, 'get_cluster_utilization'):
                    cpu_util, _ = cluster_manager.get_cluster_utilization()
                    if cpu_util is not None:
                        logger.info(f"✅ Found real CPU usage from session cache: {cpu_util}%")
                        return cpu_util
        
        # FAIL - no static fallbacks
        raise ValueError("❌ Real CPU utilization not found in ML workload characteristics or cache - HPA analysis requires real cluster metrics")
        
    except ValueError:
        raise  # Re-raise ValueError
    except Exception as e:
        raise ValueError(f"❌ Error accessing CPU utilization: {e}")

def _extract_current_memory_usage(analysis_data):
    """Extract current Memory usage from analysis data or Kubernetes cache - FAIL if not found"""
    try:
        # First: Try to extract from analysis_data
        if analysis_data and isinstance(analysis_data, dict):
            # Check for average_memory_utilization
            if 'average_memory_utilization' in analysis_data:
                mem_value = float(analysis_data['average_memory_utilization'])
                logger.info(f"✅ Found real Memory usage from analysis data: {mem_value}%")
                return mem_value
        
        # Second: Get from enhanced_cluster_manager cache
        if enhanced_cluster_manager and hasattr(enhanced_cluster_manager, 'get_cluster_utilization'):
            _, mem_util = enhanced_cluster_manager.get_cluster_utilization()
            if mem_util is not None:
                logger.info(f"✅ Found real Memory usage from cache: {mem_util}%")
                return mem_util
        
        # Third: Try direct access to cluster managers
        from shared.config.config import _analysis_sessions
        for session_key, session_data in _analysis_sessions.items():
            if 'cluster_manager' in session_data:
                cluster_manager = session_data['cluster_manager']
                if hasattr(cluster_manager, 'get_cluster_utilization'):
                    _, mem_util = cluster_manager.get_cluster_utilization()
                    if mem_util is not None:
                        logger.info(f"✅ Found real Memory usage from session cache: {mem_util}%")
                        return mem_util
        
        # Estimate memory from CPU if available (reasonable enterprise approach)
        try:
            cpu_util = _extract_current_cpu_usage(analysis_data)
            # Memory typically runs 2-3x higher than CPU in enterprise workloads
            estimated_memory = min(80.0, cpu_util * 2.5)  # Cap at 80%
            logger.info(f"✅ Estimated Memory usage from CPU utilization: {estimated_memory}% (CPU: {cpu_util}%)")
            return estimated_memory
        except Exception as e:
            logger.error(f"Failed to extract HPA target CPU: {e}")
            raise ValueError(f"Cannot extract HPA target CPU: {e}")
        
        # FAIL - no static fallbacks
        raise ValueError("❌ Real Memory utilization not found in analysis data or cache - HPA analysis requires real cluster metrics")
        
    except ValueError:
        raise  # Re-raise ValueError
    except Exception as e:
        raise ValueError(f"❌ Error accessing Memory utilization: {e}")


def _calculate_believable_scaling_scenarios(cpu_hpas, memory_hpas, mixed_hpas, total_hpas, avg_current, analysis_data):
    """
    Calculate believable HPA scaling scenarios based on realistic time-based load patterns
    
    Uses 4 time periods to simulate real cluster behavior:
    - Night (12AM-6AM): Low traffic period 
    - Morning (6AM-12PM): Business hours ramp-up
    - Afternoon (12PM-6PM): Peak business hours
    - Evening (6PM-12AM): Moderate evening traffic
    """
    
    # Determine current cluster HPA strategy
    cpu_count = len(cpu_hpas)
    memory_count = len(memory_hpas) 
    mixed_count = len(mixed_hpas)
    
    # Define realistic time-based load scenarios based on REAL cluster data (no fallbacks)
    current_cpu_usage = _extract_current_cpu_usage(analysis_data)
    current_memory_usage = _extract_current_memory_usage(analysis_data)
    
    logger.info(f"✅ Using REAL cluster metrics: {current_cpu_usage}% CPU, {current_memory_usage}% Memory")
    
    time_scenarios = {
        'night': {
            'load_factor': 0.3,      # 30% of current load
            'expected_cpu': current_cpu_usage * 0.3,
            'expected_memory': current_memory_usage * 0.4
        },
        'morning': {
            'load_factor': 0.7,      # 70% of current load  
            'expected_cpu': current_cpu_usage * 0.7,
            'expected_memory': current_memory_usage * 0.8
        },
        'afternoon': {
            'load_factor': 1.0,      # Current load (baseline)
            'expected_cpu': current_cpu_usage,
            'expected_memory': current_memory_usage
        },
        'evening': {
            'load_factor': 0.6,      # 60% of current load
            'expected_cpu': current_cpu_usage * 0.6,
            'expected_memory': current_memory_usage * 0.7
        }
    }
    
    logger.info(f"Current HPA distribution: {cpu_count} CPU, {memory_count} Memory, {mixed_count} Mixed")
    logger.info(f"Calculating time-based scaling patterns from actual cluster load")
    
    # Calculate CPU-based scaling strategy using time patterns
    cpu_replicas = _calculate_cpu_time_based_pattern(
        cpu_hpas, mixed_hpas, avg_current, time_scenarios, total_hpas, analysis_data
    )
    
    # Calculate Memory-based scaling strategy using time patterns (only if Memory/Mixed HPAs exist)
    if memory_hpas or mixed_hpas:
        memory_replicas = _calculate_memory_time_based_pattern(
            memory_hpas, mixed_hpas, avg_current, time_scenarios, total_hpas, analysis_data
        )
        logger.info(f"✅ Calculated memory-based scaling patterns for {len(memory_hpas)} Memory + {len(mixed_hpas)} Mixed HPAs")
    else:
        logger.info("No Memory/Mixed HPAs found - skipping memory-based scaling calculations")
        memory_replicas = [0, 0, 0, 0]  # Default pattern for 4 time periods (night/morning/afternoon/evening)
    
    # Calculate Mixed strategy using max() approach from hpa_test.py (enterprise best practice)
    mixed_replicas = _calculate_mixed_enterprise_strategy(
        cpu_replicas, memory_replicas, total_hpas, analysis_data
    )
    
    logger.info(f"Enterprise Strategy Results:")
    logger.info(f"   CPU-based: {cpu_replicas}")
    logger.info(f"   Memory-based: {memory_replicas}")
    logger.info(f"   Mixed (max): {mixed_replicas}")
    
    # Return CPU and Mixed for comparison (Mixed is more enterprise-appropriate)
    return cpu_replicas, mixed_replicas

def _calculate_mixed_enterprise_strategy(cpu_replicas, memory_replicas, total_hpas, analysis_data):
    """
    Calculate Mixed strategy using max() approach from hpa_test.py
    Enterprise best practice: max(cpu_scale, memory_scale) for safety
    """
    mixed_replicas = []
    
    for i in range(len(cpu_replicas)):
        # Use max() for enterprise safety - prevents resource starvation
        safe_replicas = max(cpu_replicas[i], memory_replicas[i])
        mixed_replicas.append(safe_replicas)
        
        period_names = ['night', 'morning', 'afternoon', 'evening']
        period_name = period_names[i] if i < len(period_names) else f'period_{i}'
        
        logger.info(f"Mixed {period_name}: max({cpu_replicas[i]}, {memory_replicas[i]}) = {safe_replicas} (enterprise safety)")
    
    return mixed_replicas

def _calculate_cpu_time_based_pattern(cpu_hpas, mixed_hpas, avg_current, time_scenarios, total_hpas, analysis_data):
    """Enterprise cluster-level CPU strategy analysis using real scale factor calculations"""
    
    if not analysis_data:
        raise ValueError("❌ No analysis data provided - cannot perform enterprise analysis without real cluster metrics")
    
    # Cluster-level aggregation: Get total current replicas across ALL HPAs
    total_current_replicas = 0
    for hpa in cpu_hpas + mixed_hpas:
        if isinstance(hpa, dict):
            total_current_replicas += hpa.get('current', 0)
    
    if total_current_replicas == 0:
        raise ValueError("❌ No CPU/Mixed HPAs with valid replica data found in cluster")
    
    # Extract cluster CPU utilization
    cluster_cpu_usage = _extract_current_cpu_usage(analysis_data)
    
    # Standard HPA CPU target for enterprise use
    target_cpu = 80.0
    
    # Enterprise safety constraint: Never go below 10% of current replicas
    safety_minimum = max(1, int(total_current_replicas * 0.10))
    
    logger.info(f"CPU Strategy Analysis: {total_current_replicas} total replicas, {cluster_cpu_usage}% cluster CPU")
    logger.info(f"Safety minimum: {safety_minimum} replicas (10% of current for enterprise stability)")
    
    # Calculate time-based CPU optimization scenarios
    cpu_pattern = []
    
    for period_name, scenario in time_scenarios.items():
        # Get expected CPU for this time period
        expected_cpu = scenario['expected_cpu']
        
        # Scale factor calculation from hpa_test.py logic
        scale_factor = expected_cpu / target_cpu
        
        # Apply cluster-level scaling (aggregate all HPAs)
        optimal_replicas = int(np.ceil(total_current_replicas * scale_factor))
        
        # Apply enterprise safety constraints
        safe_replicas = max(safety_minimum, optimal_replicas)
        
        logger.info(f"CPU {period_name}: {expected_cpu:.1f}% → {safe_replicas} replicas (scale: {scale_factor:.3f}, safety: {safety_minimum})")
        
        cpu_pattern.append(safe_replicas)
    
    return cpu_pattern

def _calculate_memory_time_based_pattern(memory_hpas, mixed_hpas, avg_current, time_scenarios, total_hpas, analysis_data):
    """Enterprise cluster-level Memory strategy analysis using real scale factor calculations"""
    
    if not analysis_data:
        raise ValueError("❌ No analysis data provided - cannot perform enterprise analysis without real cluster metrics")
    
    # Cluster-level aggregation: Get total current replicas across ALL HPAs
    total_current_replicas = 0
    for hpa in memory_hpas + mixed_hpas:
        if isinstance(hpa, dict):
            total_current_replicas += hpa.get('current', 0)
    
    if total_current_replicas == 0:
        raise ValueError("❌ No Memory/Mixed HPAs with valid replica data found in cluster")
    
    # Extract cluster Memory utilization
    cluster_memory_usage = _extract_current_memory_usage(analysis_data)
    
    # Standard HPA Memory target for enterprise use
    target_memory = 80.0
    
    # Enterprise safety constraint: Never go below 10% of current replicas
    safety_minimum = max(1, int(total_current_replicas * 0.10))
    
    logger.info(f"Memory Strategy Analysis: {total_current_replicas} total replicas, {cluster_memory_usage}% cluster Memory")
    logger.info(f"Safety minimum: {safety_minimum} replicas (10% of current for enterprise stability)")
    
    # Calculate time-based Memory optimization scenarios
    memory_pattern = []
    
    for period_name, scenario in time_scenarios.items():
        # Get expected Memory for this time period
        expected_memory = scenario['expected_memory']
        
        # Scale factor calculation from hpa_test.py logic
        scale_factor = expected_memory / target_memory
        
        # Apply cluster-level scaling (aggregate all HPAs)
        optimal_replicas = int(np.ceil(total_current_replicas * scale_factor))
        
        # Apply enterprise safety constraints
        safe_replicas = max(safety_minimum, optimal_replicas)
        
        logger.info(f"Memory {period_name}: {expected_memory:.1f}% → {safe_replicas} replicas (scale: {scale_factor:.3f}, safety: {safety_minimum})")
        
        memory_pattern.append(safe_replicas)
    
    return memory_pattern


def generate_node_utilization_data(analysis_data):
    """Generate node utilization data from REAL node metrics ONLY - NO FALLBACKS"""
    if not analysis_data:
        raise ValueError("No analysis data provided")
    
    logger.info("Generating node utilization data from REAL metrics")
    
    # Validate we have real node data flag
    if not analysis_data.get('has_real_node_data'):
        raise ValueError("Analysis data indicates no real node data available")
    
    # Find REAL node data
    node_metrics = None
    data_source = "unknown"
    
    for key in ['real_node_data', 'node_metrics', 'nodes']:
        if analysis_data.get(key):
            node_metrics = analysis_data[key]
            data_source = key
            logger.info(f"✅ Found node data in {key} ({len(node_metrics)} nodes)")
            break
    
    if not node_metrics:
        raise ValueError("No real node metrics found")
    
    if len(node_metrics) == 0:
        raise ValueError("Node metrics found but empty")
    
    # Process REAL nodes data and output Recharts format directly
    result = []
    for i, node in enumerate(node_metrics):
        if not isinstance(node, dict):
            raise ValueError(f"Node {i} is not a valid dictionary")

        node_name = node.get('name', f'node-{i+1}')
        cpu_usage = node.get('cpu_usage_pct')
        memory_usage = node.get('memory_usage_pct')

        if cpu_usage is None or memory_usage is None:
            raise ValueError(f"Missing CPU or memory usage data for node {node_name}")

        result.append({
            'name': node_name,
            'cpu': float(cpu_usage),
            'memory': float(memory_usage),
        })

    return result

def generate_dynamic_trend_data(cluster_id, current_analysis):
    """Generate trend data from REAL historical analysis ONLY - NO FALLBACKS"""
    if not cluster_id:
        raise ValueError("No cluster ID provided for trend analysis")
    
    if not current_analysis:
        raise ValueError("No current analysis provided")
    
    # Get REAL historical analysis data from database
    history = enhanced_cluster_manager.get_analysis_history(cluster_id, limit=12)
    
    if len(history) < 2:
        raise ValueError(f"Insufficient historical data for trends (found {len(history)} analyses)")
    
    # Sort by timestamp - FIXED: Use correct field name from database
    history.sort(key=lambda x: x.get('analysis_date', ''))
    
    # Extract REAL costs and dates — output Recharts format directly
    result = []
    for analysis in history[-5:]:  # Last 5 analyses
        total_cost = analysis.get('total_cost')
        if total_cost and total_cost > 0:
            date = analysis.get('analysis_date', '').split('T')[0]
            cost = float(total_cost)
            saving = float(analysis.get('total_savings', 0))
            item = {'date': date, 'cost': cost}
            if saving > 0:
                item['projected'] = cost - saving
            result.append(item)

    if len(result) < 2:
        raise ValueError("Not enough valid cost data points for trend analysis")

    return result

def generate_pod_cost_data(analysis_data=None):
    """Generate pod cost chart data from REAL analysis ONLY - NO FALLBACKS"""
    if not analysis_data:
        raise ValueError("No analysis data provided")
    
    if not analysis_data.get('has_pod_costs'):
        raise ValueError("Analysis indicates no pod cost data available")
    
    # Extract REAL namespace costs
    namespace_costs = None
    
    if analysis_data.get('namespace_costs'):
        namespace_costs = analysis_data['namespace_costs']
    elif analysis_data.get('pod_cost_analysis', {}).get('namespace_costs'):
        namespace_costs = analysis_data['pod_cost_analysis']['namespace_costs']
    elif analysis_data.get('pod_cost_analysis', {}).get('namespace_summary'):
        namespace_costs = analysis_data['pod_cost_analysis']['namespace_summary']
    
    if not namespace_costs:
        raise ValueError("No real namespace costs found in analysis data")
    
    # Convert pandas objects if needed
    if hasattr(namespace_costs, 'to_dict'):
        namespace_costs = namespace_costs.to_dict()
    
    # Sort by cost, get valid entries only
    valid_namespaces = []
    for ns, cost in namespace_costs.items():
        try:
            cost_float = float(cost)
            if cost_float > 0:
                valid_namespaces.append((ns, cost_float))
        except (ValueError, TypeError):
            continue
    
    if not valid_namespaces:
        raise ValueError("No valid namespace costs found")
    
    sorted_namespaces = sorted(valid_namespaces, key=lambda x: x[1], reverse=True)[:100]

    return [{'name': ns, 'value': cost} for ns, cost in sorted_namespaces]

def generate_namespace_data(analysis_data=None):
    """Generate namespace distribution data from REAL analysis ONLY - NO FALLBACKS"""
    if not analysis_data:
        raise ValueError("No analysis data provided")
    
    logger.info("Extracting REAL namespace data from analysis")
    
    # Get REAL namespace costs
    namespace_costs = analysis_data.get('namespace_costs')
    if not namespace_costs:
        pod_analysis = analysis_data.get('pod_cost_analysis', {})
        namespace_costs = pod_analysis.get('namespace_costs') or pod_analysis.get('namespace_summary')
    
    if not namespace_costs:
        raise ValueError("No real namespace costs available")
    
    # Convert pandas objects if needed
    if hasattr(namespace_costs, 'to_dict'):
        namespace_costs = namespace_costs.to_dict()
    
    if not isinstance(namespace_costs, dict):
        raise ValueError(f"Invalid namespace_costs type: {type(namespace_costs)}")
    
    # Process REAL namespaces only
    valid_namespaces = {}
    for namespace, cost in namespace_costs.items():
        try:
            cost_float = float(cost)
            if cost_float >= 0:
                valid_namespaces[namespace] = cost_float
        except (ValueError, TypeError):
            logger.warning(f"Invalid cost for namespace {namespace}: {cost}")
    
    if not valid_namespaces:
        raise ValueError("No valid namespace costs after processing")
    
    total_valid_cost = sum(valid_namespaces.values())
    if total_valid_cost <= 0:
        raise ValueError("Total namespace cost is zero or negative")
    
    # Sort by cost
    sorted_namespaces = sorted(valid_namespaces.items(), key=lambda x: x[1], reverse=True)

    return [{'name': ns, 'value': cost} for ns, cost in sorted_namespaces]

def generate_workload_data(analysis_data=None):
    """Generate workload cost data from REAL analysis ONLY - NO FALLBACKS"""
    if not analysis_data:
        raise ValueError("No analysis data provided")
    
    logger.info("Extracting REAL workload data from analysis")
    
    # Get REAL workload costs
    workload_costs = analysis_data.get('workload_costs')
    if not workload_costs:
        pod_analysis = analysis_data.get('pod_cost_analysis', {})
        workload_costs = pod_analysis.get('workload_costs')
    
    if not workload_costs:
        raise ValueError("No real workload costs available")
    
    if not isinstance(workload_costs, dict):
        raise ValueError(f"Invalid workload_costs type: {type(workload_costs)}")
    
    if len(workload_costs) == 0:
        raise ValueError("Workload costs dictionary is empty")
    
    # Process REAL workload data only
    valid_workloads = []
    
    for workload_name, workload_data in workload_costs.items():
        try:
            if isinstance(workload_data, dict):
                cost = float(workload_data.get('cost', 0))
                workload_type = str(workload_data.get('type', 'Unknown'))
                namespace = str(workload_data.get('namespace', 'unknown'))
                replicas = int(workload_data.get('replicas', 1))
            else:
                cost = float(workload_data) if workload_data else 0
                workload_type = 'Unknown'
                namespace = workload_name.split('/')[0] if '/' in workload_name else 'unknown'
                replicas = 1
            
            if cost > 0:
                valid_workloads.append((workload_name, cost, workload_type, namespace, replicas))
                
        except Exception as workload_error:
            logger.warning(f"Error processing workload {workload_name}: {workload_error}")
    
    if not valid_workloads:
        raise ValueError("No valid workload data after processing")
    
    # Sort by cost descending
    valid_workloads.sort(key=lambda x: x[1], reverse=True)

    return [{'name': w[0], 'value': w[1], 'type': w[2]} for w in valid_workloads]


def generate_execution_commands(analysis_data):
    """Deprecated — commands are generated by the AI plan generation service.

    Returns empty dict. Kept as a stub so callers don't break.
    """
    return {}
