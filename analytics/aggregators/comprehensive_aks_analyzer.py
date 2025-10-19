#!/usr/bin/env python3
"""
from pydantic import BaseModel, Field, validator
Comprehensive AKS Analyzer - Industry Standards Assessment
=========================================================

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer

Comprehensive analysis engine that assesses AKS clusters against international
best practices and industry standards, providing detailed gap analysis and
optimization roadmaps for organizations.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

# Import industry standards
from ..standards.aks_industry_standards import AKSIndustryStandards, ComplianceLevel, OptimizationCategory

logger = logging.getLogger(__name__)

class ComprehensiveAKSAnalyzer:
    """
    Comprehensive AKS analyzer that assesses clusters against industry standards
    and provides detailed optimization recommendations
    """
    
    def __init__(self):
        self.standards = AKSIndustryStandards()
        self.analysis_timestamp = datetime.now()
        
    def analyze_cluster_comprehensive(self, cluster_data: Dict, 
                                    cost_data: pd.DataFrame,
                                    org_profile: Dict) -> Dict:
        """
        Perform comprehensive analysis against industry standards
        
        Args:
            cluster_data: Complete cluster metrics and configuration
            cost_data: Detailed cost breakdown
            org_profile: Organization profile (type, size, industry, compliance requirements)
        """
        
        logger.info("🔍 Starting comprehensive AKS analysis against industry standards...")
        
        # Extract organization type and requirements
        org_type = org_profile.get('type', 'mid_market')  # startup, mid_market, enterprise, regulated
        industry = org_profile.get('industry', 'general')
        compliance_requirements = org_profile.get('compliance_requirements', [])
        
        # Prepare cluster metrics for standards assessment
        cluster_metrics = self._extract_cluster_metrics(cluster_data, cost_data)
        
        # Assess compliance against industry standards
        compliance_assessment = self.standards.assess_cluster_compliance(cluster_metrics, org_type)
        
        # Generate optimization roadmap
        optimization_roadmap = self.standards.generate_optimization_roadmap(
            compliance_assessment, 
            self._prepare_cost_context(cost_data),
            org_type
        )
        
        # Calculate comprehensive savings potential
        savings_analysis = self._analyze_comprehensive_savings(
            compliance_assessment, cluster_metrics, cost_data
        )
        
        # Assess competitive positioning
        competitive_analysis = self._assess_competitive_positioning(
            compliance_assessment, org_profile
        )
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            compliance_assessment, optimization_roadmap, savings_analysis, competitive_analysis
        )
        
        # Compile comprehensive results
        comprehensive_results = {
            "analysis_metadata": {
                "timestamp": self.analysis_timestamp.isoformat(),
                "analyzer_version": "3.0.0",
                "standards_framework": "International Best Practices",
                "organization_profile": org_profile
            },
            
            "executive_summary": executive_summary,
            
            "compliance_assessment": compliance_assessment,
            
            "optimization_roadmap": optimization_roadmap,
            
            "savings_analysis": savings_analysis,
            
            "competitive_positioning": competitive_analysis,
            
            "detailed_metrics": cluster_metrics,
            
            "recommendations": self._generate_prioritized_recommendations(
                compliance_assessment, optimization_roadmap
            ),
            
            "implementation_guide": self._generate_implementation_guide(
                optimization_roadmap, org_type
            )
        }
        
        logger.info(f"✅ Comprehensive analysis complete - {compliance_assessment['overall_compliance_score']:.1f}% compliance score")
        
        return comprehensive_results
    
    def _extract_cluster_metrics(self, cluster_data: Dict, cost_data: pd.DataFrame) -> Dict:
        """Extract and normalize cluster metrics for standards assessment"""
        
        # Extract resource utilization metrics
        cpu_utilization = cluster_data.get('cpu_utilization_avg', 0)
        memory_utilization = cluster_data.get('memory_utilization_avg', 0)
        
        # Extract HPA metrics
        total_deployments = cluster_data.get('total_deployments', 1)
        hpa_enabled_deployments = cluster_data.get('hpa_enabled_deployments', 0)
        hpa_coverage = (hpa_enabled_deployments / total_deployments * 100) if total_deployments > 0 else 0
        
        # Extract spot instance metrics
        total_nodes = cluster_data.get('total_nodes', 1)
        spot_nodes = cluster_data.get('spot_nodes', 0)
        spot_instance_adoption = (spot_nodes / total_nodes * 100) if total_nodes > 0 else 0
        
        # Extract Reserved Instance metrics (estimated from consistent workload patterns)
        workload_consistency = cluster_data.get('workload_consistency_score', 0.5)
        reserved_instance_coverage = workload_consistency * 100  # Convert to percentage
        
        # Extract rightsizing metrics
        total_containers = cluster_data.get('total_containers', 1)
        properly_sized_containers = cluster_data.get('properly_sized_containers', 0)
        rightsizing_accuracy = (properly_sized_containers / total_containers * 100) if total_containers > 0 else 0
        
        # Extract performance metrics
        pod_startup_time = cluster_data.get('avg_pod_startup_time', 60)  # seconds
        image_size_avg = cluster_data.get('avg_image_size_mb', 800)  # MB
        network_latency_p95 = cluster_data.get('network_latency_p95_ms', 15)  # milliseconds
        
        # Extract reliability metrics  
        multi_az_deployments = cluster_data.get('multi_az_deployments', 0)
        total_prod_deployments = cluster_data.get('production_deployments', 1)
        multi_az_deployment = (multi_az_deployments / total_prod_deployments * 100) if total_prod_deployments > 0 else 0
        
        pdb_enabled_deployments = cluster_data.get('pdb_enabled_deployments', 0)
        critical_deployments = cluster_data.get('critical_deployments', 1)
        pod_disruption_budget_coverage = (pdb_enabled_deployments / critical_deployments * 100) if critical_deployments > 0 else 0
        
        backup_enabled_volumes = cluster_data.get('backup_enabled_volumes', 0)
        persistent_volumes = cluster_data.get('persistent_volumes', 1)
        backup_coverage = (backup_enabled_volumes / persistent_volumes * 100) if persistent_volumes > 0 else 0
        
        # Extract security metrics
        rbac_enabled = cluster_data.get('rbac_enabled', False)
        
        total_namespaces = cluster_data.get('total_namespaces', 1)
        network_policies_namespaces = cluster_data.get('network_policies_enabled_namespaces', 0)
        network_policies_coverage = (network_policies_namespaces / total_namespaces * 100) if total_namespaces > 0 else 0
        
        pod_security_compliant = cluster_data.get('pod_security_compliant_workloads', 0)
        total_workloads = cluster_data.get('total_workloads', 1)
        pod_security_standards = (pod_security_compliant / total_workloads * 100) if total_workloads > 0 else 0
        
        secret_manager_usage = cluster_data.get('secret_manager_enabled_apps', 0)
        apps_with_secrets = cluster_data.get('applications_with_secrets', 1)
        secret_management = (secret_manager_usage / apps_with_secrets * 100) if apps_with_secrets > 0 else 0
        
        # Extract operability metrics
        monitored_services = cluster_data.get('monitored_services', 0)
        total_services = cluster_data.get('total_services', 1)
        monitoring_coverage = (monitored_services / total_services * 100) if total_services > 0 else 0
        
        log_aggregation_enabled = cluster_data.get('centralized_logging_enabled', False)
        log_aggregation = 100.0 if log_aggregation_enabled else 0.0
        
        alerting_enabled_metrics = cluster_data.get('alerting_enabled_metrics', 0)
        critical_metrics = cluster_data.get('critical_metrics', 1)
        alerting_coverage = (alerting_enabled_metrics / critical_metrics * 100) if critical_metrics > 0 else 0
        
        return {
            # Cost optimization metrics
            "resource_utilization_cpu": cpu_utilization,
            "resource_utilization_memory": memory_utilization,
            "hpa_coverage": hpa_coverage,
            "spot_instance_adoption": spot_instance_adoption,
            "reserved_instance_coverage": reserved_instance_coverage,
            "rightsizing_accuracy": rightsizing_accuracy,
            
            # Performance metrics
            "pod_startup_time": pod_startup_time,
            "image_size_optimization": image_size_avg,
            "network_latency_p95": network_latency_p95,
            
            # Reliability metrics
            "multi_az_deployment": multi_az_deployment,
            "pod_disruption_budget_coverage": pod_disruption_budget_coverage,
            "backup_coverage": backup_coverage,
            
            # Security metrics
            "rbac_enabled": 100.0 if rbac_enabled else 0.0,
            "network_policies_coverage": network_policies_coverage,
            "pod_security_standards": pod_security_standards,
            "secret_management": secret_management,
            
            # Operability metrics
            "monitoring_coverage": monitoring_coverage,
            "log_aggregation": log_aggregation,
            "alerting_coverage": alerting_coverage
        }
    
    def _prepare_cost_context(self, cost_data: pd.DataFrame) -> Dict:
        """Prepare cost context for analysis"""
        
        if cost_data.empty:
            return {"total_cost": 0, "cost_breakdown": {}}
        
        total_cost = float(cost_data['Cost'].sum())
        cost_breakdown = cost_data.groupby('ServiceName')['Cost'].sum().to_dict()
        
        return {
            "total_cost": total_cost,
            "cost_breakdown": cost_breakdown,
            "monthly_spend": total_cost,
            "cost_per_workload": total_cost / max(cost_breakdown.get('Azure Kubernetes Service', 1), 1)
        }
    
    def _analyze_comprehensive_savings(self, compliance_assessment: Dict, 
                                     cluster_metrics: Dict, cost_data: pd.DataFrame) -> Dict:
        """Analyze comprehensive savings potential based on gaps"""
        
        total_monthly_cost = float(cost_data['Cost'].sum()) if not cost_data.empty else 0
        
        savings_breakdown = {
            "current_monthly_cost": total_monthly_cost,
            "optimization_categories": {},
            "total_potential_savings": 0,
            "implementation_timeline": {},
            "roi_analysis": {}
        }
        
        # Calculate savings by category based on compliance gaps
        for gap in compliance_assessment.get("gaps", []):
            category = next((b.category.value for b in self.standards.benchmarks 
                           if b.metric_name == gap["metric"]), "other")
            
            if category not in savings_breakdown["optimization_categories"]:
                savings_breakdown["optimization_categories"][category] = {
                    "potential_savings": 0,
                    "confidence": 0,
                    "timeline_weeks": 0,
                    "gaps": []
                }
            
            # Calculate potential savings based on gap and cost
            gap_savings = self._calculate_gap_savings(gap, total_monthly_cost, cluster_metrics)
            
            savings_breakdown["optimization_categories"][category]["potential_savings"] += gap_savings
            savings_breakdown["optimization_categories"][category]["gaps"].append(gap)
            savings_breakdown["total_potential_savings"] += gap_savings
        
        # Calculate ROI analysis
        total_implementation_hours = 200  # Estimated based on complexity
        implementation_cost = total_implementation_hours * 150  # $150/hour
        
        savings_breakdown["roi_analysis"] = {
            "annual_savings": savings_breakdown["total_potential_savings"] * 12,
            "implementation_cost": implementation_cost,
            "payback_months": implementation_cost / savings_breakdown["total_potential_savings"] if savings_breakdown["total_potential_savings"] > 0 else 999,
            "3_year_roi": ((savings_breakdown["total_potential_savings"] * 36) - implementation_cost) / implementation_cost * 100 if implementation_cost > 0 else 0
        }
        
        return savings_breakdown
    
    def _calculate_gap_savings(self, gap: Dict, total_cost: float, metrics: Dict) -> float:
        """Calculate potential savings for a specific gap"""
        
        metric = gap["metric"]
        gap_value = gap["gap"]
        
        savings_factors = {
            "resource_utilization_cpu": lambda g, c: g * c * 0.015,  # 1.5% of total cost per % CPU optimization
            "resource_utilization_memory": lambda g, c: g * c * 0.012,  # 1.2% of total cost per % memory optimization
            "hpa_coverage": lambda g, c: g * c * 0.008,  # 0.8% of total cost per % HPA coverage
            "spot_instance_adoption": lambda g, c: g * c * 0.025,  # 2.5% of total cost per % spot adoption
            "reserved_instance_coverage": lambda g, c: g * c * 0.020,  # 2.0% of total cost per % RI coverage
            "rightsizing_accuracy": lambda g, c: g * c * 0.010,  # 1.0% of total cost per % rightsizing accuracy
        }
        
        savings_func = savings_factors.get(metric, lambda g, c: g * 5)  # Default $5/month per gap unit
        return savings_func(gap_value, total_cost)
    
    def _assess_competitive_positioning(self, compliance_assessment: Dict, 
                                      org_profile: Dict) -> Dict:
        """Assess competitive positioning based on compliance score"""
        
        score = compliance_assessment["overall_compliance_score"]
        org_type = org_profile.get('type', 'mid_market')
        industry = org_profile.get('industry', 'general')
        
        # Industry benchmarks (simulated - in real implementation, these would come from market data)
        industry_benchmarks = {
            "technology": {"average": 72, "top_quartile": 85},
            "finance": {"average": 78, "top_quartile": 90},
            "healthcare": {"average": 75, "top_quartile": 88},
            "retail": {"average": 68, "top_quartile": 82},
            "general": {"average": 70, "top_quartile": 83}
        }
        
        benchmark = industry_benchmarks.get(industry, industry_benchmarks["general"])
        
        competitive_position = {
            "industry_comparison": {
                "your_score": score,
                "industry_average": benchmark["average"],
                "top_quartile_threshold": benchmark["top_quartile"],
                "percentile_ranking": self._calculate_percentile_ranking(score, benchmark)
            },
            
            "competitive_advantages": [],
            "competitive_gaps": [],
            
            "market_position": self._determine_market_position(score, benchmark),
            
            "differentiation_opportunities": self._identify_differentiation_opportunities(
                compliance_assessment, org_profile
            )
        }
        
        # Identify competitive advantages (scores above industry average)
        for category, cat_score in compliance_assessment.get("category_scores", {}).items():
            if cat_score > benchmark["average"]:
                competitive_position["competitive_advantages"].append({
                    "category": category,
                    "score": cat_score,
                    "advantage": f"{cat_score - benchmark['average']:.1f} points above industry average"
                })
            else:
                competitive_position["competitive_gaps"].append({
                    "category": category,
                    "score": cat_score,
                    "gap": f"{benchmark['average'] - cat_score:.1f} points below industry average"
                })
        
        return competitive_position
    
    def _calculate_percentile_ranking(self, score: float, benchmark: Dict) -> int:
        """Calculate percentile ranking based on score"""
        
        if score >= benchmark["top_quartile"]:
            return 85 + int((score - benchmark["top_quartile"]) / (100 - benchmark["top_quartile"]) * 15)
        elif score >= benchmark["average"]:
            return 50 + int((score - benchmark["average"]) / (benchmark["top_quartile"] - benchmark["average"]) * 35)
        else:
            return int(score / benchmark["average"] * 50)
    
    def _determine_market_position(self, score: float, benchmark: Dict) -> str:
        """Determine market position based on score"""
        
        if score >= benchmark["top_quartile"]:
            return "Market Leader"
        elif score >= benchmark["average"] + 5:
            return "Above Average Performer"
        elif score >= benchmark["average"] - 5:
            return "Market Average"
        else:
            return "Below Market Standard"
    
    def _identify_differentiation_opportunities(self, compliance_assessment: Dict, 
                                              org_profile: Dict) -> List[str]:
        """Identify opportunities for competitive differentiation"""
        
        opportunities = []
        
        # Based on gaps, identify where improvements could provide competitive advantage
        high_impact_gaps = [g for g in compliance_assessment.get("gaps", []) if g["priority"] == "critical"]
        
        if any(g["metric"] in ["spot_instance_adoption", "reserved_instance_coverage"] for g in high_impact_gaps):
            opportunities.append("Cost Leadership - Achieve industry-leading cost efficiency through advanced compute optimization")
        
        if any(g["metric"] in ["pod_security_standards", "network_policies_coverage"] for g in high_impact_gaps):
            opportunities.append("Security Leadership - Establish security posture that exceeds industry standards")
        
        if any(g["metric"] in ["monitoring_coverage", "alerting_coverage"] for g in high_impact_gaps):
            opportunities.append("Operational Excellence - Build best-in-class observability and operational practices")
        
        return opportunities
    
    def _generate_executive_summary(self, compliance_assessment: Dict, 
                                   optimization_roadmap: Dict,
                                   savings_analysis: Dict, 
                                   competitive_analysis: Dict) -> Dict:
        """Generate executive summary for leadership"""
        
        return {
            "overall_assessment": {
                "compliance_score": compliance_assessment["overall_compliance_score"],
                "industry_position": competitive_analysis["market_position"],
                "total_optimization_potential": f"${savings_analysis['total_potential_savings']:.0f}/month",
                "implementation_timeline": f"{optimization_roadmap['timeline']['total_weeks']} weeks"
            },
            
            "key_findings": [
                f"Compliance score: {compliance_assessment['overall_compliance_score']:.1f}% vs industry average",
                f"Potential monthly savings: ${savings_analysis['total_potential_savings']:.0f}",
                f"Market position: {competitive_analysis['market_position']}",
                f"Implementation ROI: {savings_analysis['roi_analysis']['3_year_roi']:.0f}% over 3 years"
            ],
            
            "critical_actions": [
                gap["metric"].replace("_", " ").title() + f" (Gap: {gap['gap']:.1f})"
                for gap in compliance_assessment.get("gaps", [])[:3] if gap["priority"] == "critical"
            ],
            
            "business_impact": {
                "annual_cost_savings": savings_analysis["roi_analysis"]["annual_savings"],
                "payback_period": f"{savings_analysis['roi_analysis']['payback_months']:.1f} months",
                "competitive_advantage": len(competitive_analysis.get("competitive_advantages", [])) > 0,
                "risk_reduction": "Significant operational and security risk reduction"
            },
            
            "recommendation": self._generate_executive_recommendation(
                compliance_assessment["overall_compliance_score"],
                savings_analysis["total_potential_savings"]
            )
        }
    
    def _generate_executive_recommendation(self, compliance_score: float, savings_potential: float) -> str:
        """Generate executive recommendation based on analysis"""
        
        if compliance_score >= 80 and savings_potential > 1000:
            return "STRATEGIC PRIORITY: High-value optimization opportunity with significant competitive advantage potential."
        elif compliance_score >= 70 and savings_potential > 500:
            return "RECOMMENDED: Good optimization opportunity with solid ROI and improved market positioning."
        elif compliance_score >= 60:
            return "CONSIDER: Moderate optimization potential - implement if resources permit and strategic alignment exists."
        else:
            return "URGENT: Below industry standards - immediate action required to address compliance and operational risks."
    
    def _generate_prioritized_recommendations(self, compliance_assessment: Dict, 
                                            optimization_roadmap: Dict) -> List[Dict]:
        """Generate prioritized list of recommendations"""
        
        recommendations = []
        
        # Get recommendations from compliance assessment
        for rec in compliance_assessment.get("recommendations", []):
            recommendations.append({
                "priority": rec["priority"],
                "category": rec["category"],
                "title": rec["recommendation"],
                "business_value": rec["business_value"],
                "implementation_effort": rec["implementation_effort"],
                "timeline": rec["expected_timeline"],
                "source": "compliance_gap"
            })
        
        # Sort by priority (critical, high, medium)
        priority_order = {"critical": 0, "high": 1, "medium": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _generate_implementation_guide(self, optimization_roadmap: Dict, org_type: str) -> Dict:
        """Generate detailed implementation guide"""
        
        return {
            "success_factors": [
                "Executive sponsorship and clear ROI communication",
                "Dedicated implementation team with AKS expertise",
                "Phased approach with continuous monitoring and validation",
                "Change management process for operational procedures",
                "Training and knowledge transfer for operations team"
            ],
            
            "risk_mitigation": [
                "Implement all changes in non-production environment first",
                "Maintain rollback procedures for each optimization",
                "Monitor performance and cost metrics continuously",
                "Have incident response procedures ready",
                "Conduct regular checkpoints and reviews"
            ],
            
            "resource_requirements": {
                "team_size": "3-5 engineers" if org_type in ["enterprise", "regulated"] else "2-3 engineers",
                "skills_needed": ["AKS administration", "Kubernetes operations", "Azure cost management", "Security best practices"],
                "external_support": "Consider Azure consulting partner for complex optimizations",
                "timeline_commitment": f"{optimization_roadmap['timeline']['total_weeks']} weeks with 50% engineering time allocation"
            },
            
            "success_metrics": [
                "Compliance score improvement to >85%",
                "Monthly cost reduction as projected",
                "Zero performance degradation",
                "Improved security posture metrics",
                "Enhanced operational reliability"
            ]
        }


def analyze_aks_comprehensive(cluster_data: Dict, cost_data: pd.DataFrame, 
                            org_profile: Dict) -> Dict:
    """
    Main entry point for comprehensive AKS analysis
    
    Args:
        cluster_data: Complete cluster configuration and metrics
        cost_data: Cost breakdown data
        org_profile: Organization profile with type, industry, compliance needs
    
    Returns:
        Comprehensive analysis results with industry standards assessment
    """
    
    analyzer = ComprehensiveAKSAnalyzer()
    return analyzer.analyze_cluster_comprehensive(cluster_data, cost_data, org_profile)