#!/usr/bin/env python3
"""
Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
Project: AKS Cost Optimizer

AKS Scoring Framework - Build Quality & Cost Excellence Scorer
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import math
import yaml
import os
import logging

logger = logging.getLogger(__name__)

def clamp(v: float, lo: float, hi: float) -> float:
    """Clamp value between lo and hi"""
    return max(lo, min(hi, v))

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default for zero denominator"""
    if denominator == 0 or math.isnan(denominator):
        return default
    return numerator / denominator

def band_score(x: float, low: float, high: float) -> float:
    """
    Score within target band: 1.0 inside band, linear falloff outside
    """
    if x is None or math.isnan(x):
        return 0.0
    if low <= x <= high:
        return 1.0
    width = (high - low)
    if width <= 0:
        return 0.0
    if x < low:
        return max(0.0, 1 - (low - x) / width)
    else:
        return max(0.0, 1 - (x - high) / width)

def inverse_target(x: float, target: float, tol_frac: float) -> float:
    """
    Score with target value: 1.0 at target, linear falloff to tolerance fraction
    """
    if x is None or math.isnan(x):
        return 0.0
    tol = target * tol_frac
    if tol == 0:
        return 1.0 if x == target else 0.0
    if abs(x - target) <= tol:
        return 1.0
    return max(0.0, 1 - (abs(x - target) - tol) / tol)

def inverse_deviation(x: float, target: float, tol_abs: float) -> float:
    """
    Score with absolute tolerance around target
    """
    if x is None or math.isnan(x):
        return 0.0
    if abs(x - target) <= tol_abs:
        return 1.0
    return max(0.0, 1 - (abs(x - target) - tol_abs) / tol_abs)

@dataclass
class ScoreResult:
    """Result container for scoring operations"""
    total: float
    breakdown: Dict[str, float]
    details: Dict[str, Any]
    recommendations: List[Dict[str, Any]] = None

@dataclass
class SavingsEstimate:
    """Container for savings calculations"""
    category: str
    potential_monthly_savings: float
    description: str
    confidence: str
    implementation_effort: str

class AKSScorer:
    """
    AKS Build Quality & Cost Excellence Scorer
    
    Implements comprehensive scoring framework with:
    - Build Quality Score (0-100): UE + AE + CE + RS + CH
    - Cost Excellence Score (0-100): 8 cost-focused components
    - Savings estimation with dollar amounts
    """
    
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        logger.info("✅ AKS Scorer initialized with configuration")

    @staticmethod
    def from_yaml(path: str) -> "AKSScorer":
        """Load scorer from YAML configuration file"""
        try:
            with open(path, "r") as f:
                cfg = yaml.safe_load(f)
            logger.info(f"✅ Loaded AKS scoring configuration from {path}")
            return AKSScorer(cfg)
        except Exception as e:
            logger.error(f"❌ Failed to load AKS scoring config from {path}: {e}")
            raise

    @staticmethod
    def from_default_config() -> "AKSScorer":
        """Load scorer from default configuration in config directory"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "aks_scoring.yaml"
        )
        return AKSScorer.from_yaml(config_path)

    def score_build_quality(self, metrics: Dict[str, Any], overrides: Dict[str, Any] = None) -> ScoreResult:
        """
        Calculate Build Quality Score (0-100) with 5 components:
        - Utilization Efficiency (35%)
        - Autoscaling Efficacy (15%) 
        - Cost Efficiency (30%)
        - Reliability & Saturation (10%)
        - Configuration Hygiene (10%)
        """
        try:
            cfg = self.cfg["build_quality"]
            if overrides:
                # Deep merge overrides
                cfg = self._deep_merge(cfg, overrides)

            Wt = cfg["weights"]
            Tg = cfg["targets"]
            Mix = cfg["mix"]

            # === UTILIZATION EFFICIENCY (35%) ===
            cpu_alloc = max(1e-9, metrics.get("cpu_alloc", 1))
            mem_alloc = max(1e-9, metrics.get("mem_alloc", 1))
            cpu_p95 = metrics.get("cpu_p95", 0)
            mem_p95 = metrics.get("mem_p95", 0)
            
            cpu_eff = band_score(cpu_p95 / cpu_alloc, *Tg["cpu_warm_band"])
            mem_eff = band_score(mem_p95 / mem_alloc, *Tg["mem_warm_band"])
            
            # Request discipline
            sum_req = metrics.get("sum_req", 0)
            sum_limit = max(1e-9, metrics.get("sum_limit", 1))
            sum_p95_use = max(1e-9, metrics.get("sum_p95_use", 1))
            
            rlr = safe_divide(sum_req, sum_limit, 0.0)
            rtu = safe_divide(sum_req, sum_p95_use, 0.0)
            r1 = band_score(rlr, *Tg["req_limit_ratio_band"])
            r2 = inverse_deviation(rtu, Tg["req_to_use_target"]["target"], Tg["req_to_use_target"]["tol"])
            request_discipline = 0.5 * r1 + 0.5 * r2
            
            # Bin-packing
            idle_cpu_frac = safe_divide(cpu_alloc - cpu_p95, cpu_alloc, 0.0)
            idle_mem_frac = safe_divide(mem_alloc - mem_p95, mem_alloc, 0.0)
            idle_frac = 0.5 * (idle_cpu_frac + idle_mem_frac)
            binpack = 1 - clamp(idle_frac / Tg["binpack_idle_max"], 0, 1)
            
            UE = (Mix["UE"]["cpu"] * cpu_eff + Mix["UE"]["mem"] * mem_eff +
                  Mix["UE"]["request_discipline"] * request_discipline + Mix["UE"]["binpack"] * binpack)

            # === AUTOSCALING EFFICACY (15%) ===
            hpa_count = metrics.get("hpa_count", 0)
            eligible_hpa_workloads = max(1, metrics.get("eligible_hpa_workloads", 1))
            coverage = safe_divide(hpa_count, eligible_hpa_workloads, 0.0)
            coverage_score = clamp(coverage / Tg["hpa_coverage_target"], 0, 1)
            
            hpa_mape = metrics.get("hpa_mape", 0)
            hpa_quality = 1 - clamp(hpa_mape / Tg["hpa_mape_ok"], 0, 1)
            
            ca_pending_pct = metrics.get("ca_pending_capacity_pct", 0)
            ca_eff = 1 - clamp(ca_pending_pct / Tg["ca_pending_ok"], 0, 1)
            
            AE = (Mix["AE"]["coverage"] * coverage_score + Mix["AE"]["tracking"] * hpa_quality + 
                  Mix["AE"]["ca"] * ca_eff)

            # === COST EFFICIENCY (30%) ===
            ref_vcpu_price = metrics.get("ref_vcpu_price", Tg["ref_vcpu_price"])
            cost_nodes = max(1e-9, metrics.get("cost_nodes", 1))
            used_vcpu_hours = max(1e-9, metrics.get("used_vcpu_hours", 1))
            compute_unit_cost = safe_divide(cost_nodes, used_vcpu_hours, 0.0)
            cpu_cost_score = safe_divide(ref_vcpu_price, compute_unit_cost, 0.0) if ref_vcpu_price > 0 and compute_unit_cost > 0 else 0.0
            
            idle_compute_cost_pct = metrics.get("idle_compute_cost_pct", 0)
            idle_score = 1 - clamp(idle_compute_cost_pct / Tg["idle_cost_pct_ok"], 0, 1)
            
            cost_storage = max(1e-9, metrics.get("cost_storage", 1))
            storage_waste_cost = metrics.get("storage_waste_cost", 0)
            storage_score = 1 - clamp(safe_divide(storage_waste_cost, cost_storage, 0.0), 0, 1)
            
            # Network scoring
            cost_network = metrics.get("cost_network", 0)
            cost_lb = metrics.get("cost_lb", 0)
            cost_nat = metrics.get("cost_nat", 0)
            data_processed_gb = max(1e-9, metrics.get("data_processed_gb", 1))
            ref_net = metrics.get("ref_net_price_per_gb", Tg["net_unit_ref_price_per_gb"])
            net_unit = safe_divide(cost_network + cost_lb + cost_nat, data_processed_gb, 0.0)
            net_score = safe_divide(ref_net, net_unit, 0.0) if ref_net > 0 and net_unit > 0 else 0.0
            
            CE = (Mix["CE"]["cpu_cost"] * cpu_cost_score + Mix["CE"]["idle"] * idle_score +
                  Mix["CE"]["storage"] * storage_score + Mix["CE"]["net"] * net_score)

            # === RELIABILITY & SATURATION (10%) ===
            rel_tg = Tg["reliability"]
            s1 = 1 - clamp(metrics.get("oom_rate", 0) / rel_tg["oom_rate_ok"], 0, 1)
            s2 = 1 - clamp(metrics.get("crash_rate", 0) / rel_tg["crash_rate_ok"], 0, 1)
            s3 = 1 - clamp(metrics.get("node_unready_pct", 0) / rel_tg["node_unready_ok"], 0, 1)
            s4 = 1 - clamp(metrics.get("sched_p95_ms", 0) / rel_tg["sched_p95_ms_ok"], 0, 1)
            
            RS = (Mix["RS"]["oom"] * s1 + Mix["RS"]["crash"] * s2 + 
                  Mix["RS"]["node"] * s3 + Mix["RS"]["sched"] * s4)

            # === CONFIGURATION HYGIENE (10%) ===
            hygiene_checks = metrics.get("hygiene_checks", [])
            if hygiene_checks and len(hygiene_checks) > 0:
                CH = safe_divide(sum(1.0 if bool(x) else 0.0 for x in hygiene_checks), len(hygiene_checks), 0.0)
            else:
                CH = 0.0

            # === FINAL SCORE ===
            total = (Wt["UE"] * UE + Wt["AE"] * AE + Wt["CE"] * CE + Wt["RS"] * RS + Wt["CH"] * CH)
            
            breakdown = {"UE": UE, "AE": AE, "CE": CE, "RS": RS, "CH": CH}
            details = {
                "cpu_efficiency": cpu_eff,
                "mem_efficiency": mem_eff,
                "request_discipline": request_discipline,
                "binpack_score": binpack,
                "hpa_coverage": coverage,
                "ca_effectiveness": ca_eff,
                "compute_unit_cost": compute_unit_cost,
                "net_unit_cost": net_unit,
                "idle_fraction": idle_frac,
                "reliability_scores": {"oom": s1, "crash": s2, "node": s3, "sched": s4}
            }
            
            logger.info(f"✅ Build Quality Score calculated: {total*100:.1f}/100")
            return ScoreResult(total=round(total * 100, 2), breakdown=breakdown, details=details)
            
        except Exception as e:
            logger.error(f"❌ Build Quality scoring failed: {e}")
            raise

    def score_cost_excellence(self, metrics: Dict[str, Any], overrides: Dict[str, Any] = None) -> ScoreResult:
        """
        Calculate Cost Excellence Score (0-100) with 8 components:
        - Compute Efficiency (40%)
        - Storage Efficiency (15%)
        - Network/LB Efficiency (15%)
        - Observability Cost Control (10%)
        - Images/Registry Economy (5%)
        - Security/Platform Tools Cost (5%)
        - Platform Hygiene with Cost Impact (5%)
        - Idle/Abandoned Resources (5%)
        """
        try:
            cfg = self.cfg["cost_excellence"]
            if overrides:
                cfg = self._deep_merge(cfg, overrides)

            Wt = cfg["weights"]

            # === COMPUTE EFFICIENCY (40%) ===
            compute_score = self._score_compute_efficiency(metrics, cfg["compute"])

            # === STORAGE EFFICIENCY (15%) ===
            storage_score = self._score_storage_efficiency(metrics, cfg["storage"])

            # === NETWORK/LB EFFICIENCY (15%) ===
            network_score = self._score_network_lb_efficiency(metrics, cfg["network_lb"])

            # === OBSERVABILITY COST CONTROL (10%) ===
            obs_score = self._score_observability_cost(metrics, cfg["observability"])

            # === IMAGES/REGISTRY ECONOMY (5%) ===
            images_score = self._score_images_registry(metrics, cfg["images"])

            # === SECURITY/TOOLS COST (5%) ===
            sec_score = self._score_security_tools(metrics, cfg["sec_tools"])

            # === PLATFORM HYGIENE (5%) ===
            platform_checks = metrics.get("platform_hygiene_checks", [])
            platform_hygiene = (sum(1.0 if bool(x) else 0.0 for x in platform_checks) / 
                               max(1, len(platform_checks))) if platform_checks else 0.0

            # === IDLE/ABANDONED RESOURCES (5%) ===
            total_related = max(1e-9, metrics.get("total_cluster_related_costs", 1))
            orphan_cost = metrics.get("orphan_cost", 0)
            idle_abandoned = 1 - clamp(orphan_cost / total_related, 0, 1)

            # === FINAL SCORE ===
            total = (Wt["compute"] * compute_score + Wt["storage"] * storage_score + 
                    Wt["network_lb"] * network_score + Wt["observability"] * obs_score +
                    Wt["images"] * images_score + Wt["sec_tools"] * sec_score +
                    Wt["platform_hygiene"] * platform_hygiene + Wt["idle_abandoned"] * idle_abandoned)

            breakdown = {
                "compute": compute_score,
                "storage": storage_score,
                "network_lb": network_score,
                "observability": obs_score,
                "images": images_score,
                "sec_tools": sec_score,
                "platform_hygiene": platform_hygiene,
                "idle_abandoned": idle_abandoned
            }

            details = {
                "compute_details": self._get_compute_details(metrics, cfg["compute"]),
                "storage_details": self._get_storage_details(metrics, cfg["storage"]),
                "network_details": self._get_network_details(metrics, cfg["network_lb"]),
                "total_cluster_costs": total_related,
                "orphan_costs": orphan_cost
            }

            logger.info(f"✅ Cost Excellence Score calculated: {total*100:.1f}/100")
            return ScoreResult(total=round(total * 100, 2), breakdown=breakdown, details=details)

        except Exception as e:
            logger.error(f"❌ Cost Excellence scoring failed: {e}")
            raise

    def calculate_unified_optimization_score(self, 
                                           cost_data: Dict[str, Any],
                                           metrics_data: Dict[str, Any], 
                                           current_usage: Dict[str, Any],
                                           analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate unified optimization score using existing AKS scoring framework and YAML standards
        Integrates with existing Build Quality and Cost Excellence scores
        """
        try:
            logger.info("🔍 Calculating unified optimization score using existing AKS scoring framework...")
            
            # Get optimization scoring standards from YAML
            opt_standards = self.cfg.get('optimization_scoring')
            if not opt_standards:
                raise ValueError("❌ optimization_scoring missing from YAML configuration")
            
            # Prepare metrics for existing scoring framework
            scoring_metrics = self._prepare_unified_scoring_metrics(
                cost_data, metrics_data, current_usage, analysis_results
            )
            
            # Use existing AKS scoring methods
            build_quality_result = self.score_build_quality(scoring_metrics)
            cost_excellence_result = self.score_cost_excellence(scoring_metrics)
            
            # Calculate component scores using YAML weights
            weights = opt_standards['weights']
            
            # Map existing scores to optimization components
            current_efficiency_score = self._map_to_current_efficiency(
                build_quality_result, cost_excellence_result, current_usage, opt_standards
            )
            
            optimization_potential_score = self._calculate_optimization_potential_from_savings(
                analysis_results, cost_data, opt_standards
            )
            
            configuration_quality_score = self._map_to_configuration_quality(
                build_quality_result, analysis_results, opt_standards
            )
            
            cost_effectiveness_score = self._map_to_cost_effectiveness(
                cost_excellence_result, cost_data, analysis_results, opt_standards
            )
            
            # Calculate weighted final score
            component_scores = {
                'current_efficiency': current_efficiency_score,
                'optimization_potential': optimization_potential_score,
                'configuration_quality': configuration_quality_score,
                'cost_effectiveness': cost_effectiveness_score
            }
            
            final_score = (
                current_efficiency_score * weights['current_efficiency'] +
                optimization_potential_score * weights['optimization_potential'] +
                configuration_quality_score * weights['configuration_quality'] +
                cost_effectiveness_score * weights['cost_effectiveness']
            ) * opt_standards['score_calculation']['scale']
            
            # Ensure minimum score
            min_score = opt_standards['score_calculation']['minimum_score']
            final_score = max(min_score, final_score)
            
            # Determine interpretation
            interpretation = self._get_score_interpretation(
                final_score, opt_standards['score_calculation']['interpretation']
            )
            
            # Calculate confidence
            confidence = self._calculate_unified_confidence(
                build_quality_result, cost_excellence_result, analysis_results, opt_standards
            )
            
            result = {
                'total_score': round(final_score, 1),
                'component_scores': component_scores,
                'confidence': round(confidence, 3),
                'interpretation': interpretation,
                'build_quality_score': build_quality_result.total,
                'cost_excellence_score': cost_excellence_result.total,
                'build_quality_breakdown': build_quality_result.breakdown,
                'cost_excellence_breakdown': cost_excellence_result.breakdown,
                'yaml_based': True,
                'calculation_method': 'unified_aks_scoring_framework'
            }
            
            logger.info(f"✅ Unified optimization score: {result['total_score']}/100 ({interpretation})")
            logger.info(f"✅ Based on Build Quality: {build_quality_result.total}/100, Cost Excellence: {cost_excellence_result.total}/100")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate unified optimization score: {e}")
            raise
    
    def _prepare_unified_scoring_metrics(self, cost_data: Dict, metrics_data: Dict, 
                                       current_usage: Dict, analysis_results: Dict) -> Dict:
        """Prepare metrics for existing AKS scoring framework"""
        # Map your data to the format expected by existing AKS scoring methods
        # This ensures compatibility with existing scoring infrastructure
        
        unified_metrics = {
            # CPU and memory metrics
            'cpu_p95': current_usage.get('avg_cpu_utilization', 0),
            'mem_p95': current_usage.get('avg_memory_utilization', 0),
            'cpu_alloc': 100,  # Normalized
            'mem_alloc': 100,  # Normalized
            
            # Cost metrics
            'total_cost': cost_data.get('total_cost', 0),
            'compute_cost': cost_data.get('node_cost', 0),
            'storage_cost': cost_data.get('storage_cost', 0),
            'network_cost': cost_data.get('networking_cost', 0),
            
            # Observability metrics from existing analysis
            'current_observability_cost': analysis_results.get('current_observability_cost', 0),
            'current_daily_ingestion_gb': analysis_results.get('current_daily_ingestion_gb', 0),
            
            # Workload metrics
            'total_workloads': analysis_results.get('total_workloads', 1),
            'hpa_count': analysis_results.get('hpa_count', 0),
            
            # Add other metrics as needed for existing scoring methods
        }
        
        return unified_metrics
    
    def _map_to_current_efficiency(self, build_quality: ScoreResult, cost_excellence: ScoreResult,
                                 current_usage: Dict, opt_standards: Dict) -> float:
        """Map existing scoring to current efficiency component"""
        # Use build quality score as primary indicator of current efficiency
        # Build quality includes utilization efficiency and configuration hygiene
        return build_quality.total / 100.0
    
    def _calculate_optimization_potential_from_savings(self, analysis_results: Dict, 
                                                     cost_data: Dict, opt_standards: Dict) -> float:
        """Calculate optimization potential score (inverse scoring)"""
        total_cost = cost_data.get('total_cost', 0)
        total_savings = analysis_results.get('total_savings', 0)
        
        if total_cost <= 0:
            return 0.0
        
        savings_potential = total_savings / total_cost
        
        # Use YAML thresholds for inverse scoring
        potential_config = opt_standards['optimization_potential']
        
        if savings_potential <= potential_config['low_potential_max']:
            return potential_config['low_potential_bonus']
        elif savings_potential <= potential_config['medium_potential_max']:
            return potential_config['medium_potential_score']
        else:
            return potential_config['high_potential_penalty']
    
    def _map_to_configuration_quality(self, build_quality: ScoreResult, 
                                    analysis_results: Dict, opt_standards: Dict) -> float:
        """Map to configuration quality score"""
        # Use HPA coverage and other configuration aspects from build quality
        hpa_count = analysis_results.get('hpa_count', 0)
        total_workloads = analysis_results.get('total_workloads', 1)
        hpa_coverage = min(1.0, hpa_count / total_workloads)
        
        # Combine with build quality configuration aspects
        config_quality = (build_quality.total / 100.0) * 0.7 + hpa_coverage * 0.3
        
        return min(1.0, config_quality)
    
    def _map_to_cost_effectiveness(self, cost_excellence: ScoreResult, cost_data: Dict,
                                 analysis_results: Dict, opt_standards: Dict) -> float:
        """Map cost excellence to cost effectiveness"""
        # Use existing cost excellence score as primary indicator
        return cost_excellence.total / 100.0
    
    def _calculate_unified_confidence(self, build_quality: ScoreResult, cost_excellence: ScoreResult,
                                    analysis_results: Dict, opt_standards: Dict) -> float:
        """Calculate confidence based on data quality and scoring reliability"""
        confidence_factors = []
        
        # Build quality confidence
        confidence_factors.append(0.9 if build_quality.total > 0 else 0.3)
        
        # Cost excellence confidence  
        confidence_factors.append(0.9 if cost_excellence.total > 0 else 0.3)
        
        # Analysis data completeness
        has_real_data = analysis_results.get('has_real_node_data', False)
        confidence_factors.append(0.9 if has_real_data else 0.6)
        
        # Cost data quality
        has_cost_data = analysis_results.get('total_cost', 0) > 0
        confidence_factors.append(0.9 if has_cost_data else 0.5)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def _get_score_interpretation(self, score: float, interpretation_config: Dict) -> str:
        """Get human-readable interpretation of score"""
        for level, range_values in interpretation_config.items():
            if range_values[0] <= score <= range_values[1]:
                return level.title()
        return "Unknown"

    def estimate_savings(self, metrics: Dict[str, Any], scores: Dict[str, ScoreResult]) -> List[SavingsEstimate]:
        """
        Estimate potential monthly savings based on scoring results
        """
        try:
            savings = []
            savings_cfg = self.cfg.get("savings", {})
            
            # Compute savings opportunities
            savings.extend(self._estimate_compute_savings(metrics, scores, savings_cfg))
            
            # Storage savings opportunities  
            savings.extend(self._estimate_storage_savings(metrics, scores, savings_cfg))
            
            # Network savings opportunities
            savings.extend(self._estimate_network_savings(metrics, scores, savings_cfg))
            
            # Observability savings opportunities
            savings.extend(self._estimate_observability_savings(metrics, scores, savings_cfg))
            
            # Sort by potential savings (highest first)
            savings.sort(key=lambda x: x.potential_monthly_savings, reverse=True)
            
            logger.info(f"✅ Estimated {len(savings)} savings opportunities totaling ${sum(s.potential_monthly_savings for s in savings):.0f}/month")
            
            return savings[:10]  # Return top 10 opportunities
            
        except Exception as e:
            logger.error(f"❌ Savings estimation failed: {e}")
            return []

    # === HELPER METHODS ===

    def _score_compute_efficiency(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> float:
        """Score compute efficiency component"""
        cpu_alloc = max(1e-9, metrics.get("cpu_alloc", 1))
        mem_alloc = max(1e-9, metrics.get("mem_alloc", 1))
        cpu_p95 = metrics.get("cpu_p95", 0)
        mem_p95 = metrics.get("mem_p95", 0)

        # Rightsizing
        cpu_warm = band_score(safe_divide(cpu_p95, cpu_alloc, 0.0), *cfg["bands"]["cpu_warm"])
        mem_warm = band_score(safe_divide(mem_p95, mem_alloc, 0.0), *cfg["bands"]["mem_warm"])
        rightsizing = 0.6 * cpu_warm + 0.4 * mem_warm

        # Bin-packing
        idle_frac = 0.5 * (safe_divide(cpu_alloc - cpu_p95, cpu_alloc, 0.0) + safe_divide(mem_alloc - mem_p95, mem_alloc, 0.0))
        binpack = 1 - clamp(safe_divide(idle_frac, cfg["binpack_idle_max"], 0.0), 0, 1)
        pod_density_ok = clamp(safe_divide(metrics.get("pct_nodes_podslots_gt80", 0), cfg["pod_density_target"], 0.0), 0, 1)
        packing = 0.6 * binpack + 0.4 * pod_density_ok

        # Cluster Autoscaler
        ca_pending = 1 - clamp(safe_divide(metrics.get("ca_pending_capacity_pct", 0), cfg["ca_pending_ok"], 0.0), 0, 1)
        ca_settings = (
            (1.0 if metrics.get("ca_expander") == "least-waste" else 0.0) * cfg["ca_settings_bonus"]["least_waste"] +
            (1.0 if metrics.get("ca_balance_sng", False) else 0.0) * cfg["ca_settings_bonus"]["balance_sng"]
        )
        ca_score = 0.6 * ca_pending + 0.4 * ca_settings

        # Price posture (Spot/RI)
        spot_score = clamp(
            safe_divide(safe_divide(metrics.get("spot_user_cores", 0), metrics.get("total_user_cores", 1)), cfg["spot_target_core_mix"], 0.0), 0, 1
        )
        ri_score = clamp(
            safe_divide(safe_divide(metrics.get("reserved_core_hours", 0), metrics.get("baseline_core_hours", 1)), cfg["ri_target_coverage"], 0.0), 0, 1
        )
        price_posture = 0.6 * ri_score + 0.4 * spot_score

        # Unit cost normalization
        ref_vcpu = metrics.get("ref_vcpu_price", cfg["ref_vcpu_price"])
        unit_cost = safe_divide(metrics.get("cost_nodes", 0), metrics.get("used_vcpu_hours", 1))
        unit_norm = safe_divide(ref_vcpu, unit_cost, 0.0) if ref_vcpu > 0 and unit_cost > 0 else 0.0

        # Schedule savings
        peak_cost = max(1e-9, metrics.get("peak_hour_cost", 1))
        offhour_reduction = safe_divide(peak_cost - metrics.get("offhour_cost", 0), peak_cost, 0.0)
        schedule_score = clamp(safe_divide(offhour_reduction, cfg["schedule_offhour_target"], 0.0), 0, 1)

        # Weighted combination
        mix = cfg["mix"]
        return (mix["rightsizing"] * rightsizing + mix["packing"] * packing +
                mix["ca"] * ca_score + mix["price_posture"] * price_posture +
                mix["unit_cost_norm"] * unit_norm + mix["schedule"] * schedule_score)

    def _score_storage_efficiency(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> float:
        """Score storage efficiency component"""
        # Overprovisioning and tiering
        prov_vs_used = metrics.get("prov_vs_used", 1.0)
        overprov = inverse_target(prov_vs_used, **cfg["prov_vs_used_target"])
        
        cost_storage = max(1e-9, metrics.get("cost_storage", 1))
        premium_waste = metrics.get("premium_waste_cost", 0)
        tiering = 1 - clamp(premium_waste / cost_storage, 0, 1)
        a = 0.6 * overprov + 0.4 * tiering

        # Orphaned resources
        storage_waste = metrics.get("storage_waste_cost", 0)
        orphans = 1 - clamp(storage_waste / cost_storage, 0, 1)

        # Product fit
        product_misfit = metrics.get("product_misfit_cost", 0)
        product = 1 - clamp(product_misfit / cost_storage, 0, 1)

        # Weighted combination
        mix = cfg["mix"]
        return mix["overprov_tiering"] * a + mix["orphans"] * orphans + mix["product"] * product

    def _score_network_lb_efficiency(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> float:
        """Score network and load balancer efficiency"""
        # Load balancer normalization
        lb_count = metrics.get("lb_count", 0)
        services_exposed = max(1, metrics.get("services_exposed", 1))
        lb_norm = inverse_target(lb_count / services_exposed, **cfg["lb_per_workload_target"])

        # Unit cost
        cost_network = metrics.get("cost_network", 0)
        cost_lb = metrics.get("cost_lb", 0)
        cost_nat = metrics.get("cost_nat", 0)
        data_processed_gb = max(1e-9, metrics.get("data_processed_gb", 1))
        ref_net = metrics.get("ref_net_price_per_gb", cfg["ref_net_price_per_gb"])
        net_unit = (cost_network + cost_lb + cost_nat) / data_processed_gb
        unit_cost_net = clamp(ref_net / net_unit, 0, 1) if ref_net > 0 and net_unit > 0 else 0.0

        # IP and NAT efficiency
        idle_ip_cost = metrics.get("idle_public_ip_cost", 0)
        cost_nat_needed = metrics.get("cost_nat_needed", cost_nat)
        nat_waste = max(0, cost_nat - cost_nat_needed)
        total_net_cost = max(1e-9, cost_network + cost_lb + cost_nat)
        ip_nat = 1 - clamp((idle_ip_cost + nat_waste) / total_net_cost, 0, 1)

        # Weighted combination
        mix = cfg["mix"]
        return mix["lb_norm"] * lb_norm + mix["unit_cost"] * unit_cost_net + mix["ip_nat"] * ip_nat

    def _score_observability_cost(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> float:
        """Score observability cost control"""
        # Log filtering
        filtered_gb = metrics.get("filtered_gb", 0)
        generated_gb = max(1e-9, metrics.get("generated_gb", 1))
        filters = clamp(filtered_gb / generated_gb / cfg["filter_target"], 0, 1)

        # Retention strategy
        retention_days = metrics.get("retention_days", 0)
        retention_ok = band_score(retention_days, *cfg["retention_hot_band"])
        archive_ok = 1.0 if metrics.get("archive_days", 0) >= 180 else 0.0
        retention = 0.7 * retention_ok + 0.3 * archive_ok

        # Cost density
        ingest_per_pod = metrics.get("ingest_gb_per_pod", 0)
        cost_density = (
            0.7 * inverse_target(ingest_per_pod, **cfg["ingest_per_pod_target"]) +
            0.3 * (1.0 if metrics.get("trace_sampling_rate", 1.0) <= 0.2 else 0.0)
        )

        # Weighted combination
        mix = cfg["mix"]
        return mix["filters"] * filters + mix["retention"] * retention + mix["cost_density"] * cost_density

    def _score_images_registry(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> float:
        """Score container images and registry efficiency"""
        # ACR SKU appropriateness
        acr_sku = metrics.get("acr_sku", "Standard")
        acr_sku_score = 1.0 if acr_sku in ["Basic", "Standard"] else 0.0

        # Image size optimization
        median_size = metrics.get("median_image_size_mb", 250)
        size_ok = inverse_target(median_size, **cfg["median_image_mb_target"])

        # Retention policy
        retention = 1.0 if metrics.get("acr_retention_days", 0) >= 14 else 0.0

        # Geo-replication appropriateness
        geo_ok = 1.0 if metrics.get("acr_geo_rep_matched", True) else 0.0

        # Weighted combination
        mix = cfg["mix"]
        return (mix["acr_sku"] * acr_sku_score + mix["size"] * size_ok +
                mix["retention"] * retention + mix["geo"] * geo_ok)

    def _score_security_tools(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> float:
        """Score security and platform tools cost efficiency"""
        # Defender scoping
        defender_scope = 1.0 if metrics.get("defender_excluded_nonprod_pct", 0) >= 0.7 else 0.0

        # Duplicate agents
        dup_cost = metrics.get("dup_agents_waste_cost", 0)
        total_sec_cost = max(1e-9, metrics.get("cost_security_tools", 1))
        dup_agents = 1 - clamp(dup_cost / total_sec_cost, 0, 1)

        # Weighted combination
        mix = cfg["mix"]
        return mix["defender_scope"] * defender_scope + mix["dup_agents"] * dup_agents

    def _estimate_compute_savings(self, metrics: Dict[str, Any], scores: Dict[str, ScoreResult], cfg: Dict[str, Any]) -> List[SavingsEstimate]:
        """Estimate compute-related savings opportunities"""
        savings = []
        
        # Spot instance expansion
        spot_current = metrics.get("spot_user_cores", 0)
        total_cores = metrics.get("total_user_cores", 1)
        spot_target = total_cores * 0.30  # 30% target
        if spot_current < spot_target:
            spot_gap = spot_target - spot_current
            vcpu_price = metrics.get("ref_vcpu_price", 0.045)
            spot_discount = 0.70  # 70% average discount
            monthly_hours = 24 * 30  # 720 hours
            potential = spot_gap * vcpu_price * spot_discount * monthly_hours
            
            savings.append(SavingsEstimate(
                category="Compute - Spot Expansion",
                potential_monthly_savings=potential,
                description=f"Expand spot usage by {spot_gap:.0f} cores to reach 30% target",
                confidence="High",
                implementation_effort="Medium"
            ))

        # Reserved instance gap
        ri_current_hours = metrics.get("reserved_core_hours", 0)
        baseline_hours = metrics.get("baseline_core_hours", 1)
        ri_target_hours = baseline_hours * 0.70  # 70% target
        if ri_current_hours < ri_target_hours:
            ri_gap_hours = ri_target_hours - ri_current_hours
            vcpu_price = metrics.get("ref_vcpu_price", 0.045)
            ri_discount = 0.40  # 40% RI discount typically
            potential = ri_gap_hours * vcpu_price * ri_discount / 12  # Monthly from annual
            
            savings.append(SavingsEstimate(
                category="Compute - Reserved Instances",
                potential_monthly_savings=potential,
                description=f"Purchase RI for {ri_gap_hours/720:.0f} cores baseline usage",
                confidence="High",
                implementation_effort="Low"
            ))

        # Idle compute cleanup
        idle_cost_pct = metrics.get("idle_compute_cost_pct", 0)
        if idle_cost_pct > 0.35:  # Above 35% threshold
            cost_nodes = metrics.get("cost_nodes", 0)
            excess_idle = idle_cost_pct - 0.25  # Target 25% idle
            potential = cost_nodes * excess_idle * 0.8  # 80% recoverable
            
            savings.append(SavingsEstimate(
                category="Compute - Idle Resources",
                potential_monthly_savings=potential,
                description=f"Right-size or schedule idle resources ({idle_cost_pct*100:.1f}% idle)",
                confidence="Medium",
                implementation_effort="High"
            ))

        return savings

    def _estimate_storage_savings(self, metrics: Dict[str, Any], scores: Dict[str, ScoreResult], cfg: Dict[str, Any]) -> List[SavingsEstimate]:
        """Estimate storage-related savings opportunities"""
        savings = []
        cost_storage = metrics.get("cost_storage", 0)
        
        if cost_storage < 10:  # Skip if storage cost too low
            return savings

        # Premium to Standard migration
        potential = cost_storage * 0.25 * 0.40  # 25% eligible, 40% savings
        if potential > 5:  # Only if meaningful
            savings.append(SavingsEstimate(
                category="Storage - Premium to Standard",
                potential_monthly_savings=potential,
                description="Migrate low-IOPS workloads from Premium to Standard SSD",
                confidence="Medium",
                implementation_effort="Medium"
            ))

        # PV rightsizing
        prov_vs_used = metrics.get("prov_vs_used", 1.0)
        if prov_vs_used > 1.30:  # Over 30% overprovisioned
            excess = prov_vs_used - 1.20  # Target 20% buffer
            potential = cost_storage * excess * 0.6  # 60% recoverable
            
            savings.append(SavingsEstimate(
                category="Storage - Volume Rightsizing",
                potential_monthly_savings=potential,
                description=f"Right-size overprovisioned volumes ({prov_vs_used:.1f}x ratio)",
                confidence="High",
                implementation_effort="Medium"
            ))

        # Cleanup orphaned storage
        storage_waste = metrics.get("storage_waste_cost", 0)
        if storage_waste > cost_storage * 0.05:  # More than 5% waste
            savings.append(SavingsEstimate(
                category="Storage - Cleanup Orphaned",
                potential_monthly_savings=storage_waste * 0.9,  # 90% recoverable
                description="Remove unattached disks and stale PVCs",
                confidence="High",
                implementation_effort="Low"
            ))

        return savings

    def _estimate_network_savings(self, metrics: Dict[str, Any], scores: Dict[str, ScoreResult], cfg: Dict[str, Any]) -> List[SavingsEstimate]:
        """Estimate network-related savings opportunities"""
        savings = []
        
        # Load balancer consolidation
        lb_count = metrics.get("lb_count", 0)
        services_exposed = metrics.get("services_exposed", 1)
        lb_ratio = lb_count / services_exposed
        if lb_ratio > 0.08:  # More than 1 LB per 12 services
            excess_lbs = lb_count - (services_exposed * 0.05)  # Target 1 per 20
            lb_cost_each = 20  # Approximate monthly cost per LB
            potential = excess_lbs * lb_cost_each * 0.6  # 60% consolidatable
            
            savings.append(SavingsEstimate(
                category="Network - LB Consolidation",
                potential_monthly_savings=potential,
                description=f"Consolidate {excess_lbs:.0f} excess load balancers using Ingress",
                confidence="Medium",
                implementation_effort="Medium"
            ))

        # Idle public IP cleanup
        idle_ip_cost = metrics.get("idle_public_ip_cost", 0)
        if idle_ip_cost > 10:  # More than $10/month
            savings.append(SavingsEstimate(
                category="Network - Idle Public IPs",
                potential_monthly_savings=idle_ip_cost * 0.8,  # 80% cleanable
                description="Remove unused public IP addresses",
                confidence="High",
                implementation_effort="Low"
            ))

        return savings

    def _estimate_observability_savings(self, metrics: Dict[str, Any], scores: Dict[str, ScoreResult], cfg: Dict[str, Any]) -> List[SavingsEstimate]:
        """Estimate observability-related savings opportunities with dynamic pricing and validation"""
        savings = []
        
        # Validate and enhance metrics first
        validated_metrics = self._validate_observability_metrics(metrics)
        
        # Log filtering optimization with dynamic pricing
        generated_gb = validated_metrics.get("generated_gb", 0)
        filtered_gb = validated_metrics.get("filtered_gb", 0)
        current_daily_ingestion = validated_metrics.get("current_daily_ingestion_gb", generated_gb)
        
        if current_daily_ingestion > 0:
            # Calculate realistic filtering potential
            current_filter_pct = filtered_gb / current_daily_ingestion if current_daily_ingestion > 0 else 0
            target_filter_pct = 0.25  # 25% target from config
            
            # Only suggest additional filtering if we're below target
            if current_filter_pct < target_filter_pct:
                additional_filter_potential = current_daily_ingestion * (target_filter_pct - current_filter_pct)
                
                if additional_filter_potential > 0:
                    # Get dynamic pricing based on commitment tier
                    log_price_per_gb = self._get_log_analytics_pricing(validated_metrics)
                    
                    # Calculate potential monthly savings
                    potential = additional_filter_potential * log_price_per_gb * 30  # Monthly
                    
                    # Apply validation cap - max 80% of current observability spend (updated from YAML)
                    current_obs_cost = validated_metrics.get("current_observability_cost", 0)
                    if current_obs_cost > 0:
                        max_savings = current_obs_cost * 0.80
                        potential = min(potential, max_savings)
                        logger.info(f"💰 Capped log filtering savings at ${potential:.0f}/month (80% of ${current_obs_cost:.0f}/month actual spend)")
                    else:
                        # If no actual observability cost, be very conservative
                        potential = min(potential, 100)  # Cap at $100/month max
                        logger.warning(f"⚠️ No actual observability cost data - capping savings at ${potential:.0f}/month")
                    
                    # Only suggest if meaningful savings (>$50/month)
                    if potential > 50:
                        confidence = "High" if additional_filter_potential < 10 else "Medium"
                        
                        savings.append(SavingsEstimate(
                            category="Observability - Log Filtering",
                            potential_monthly_savings=potential,
                            description=f"Filter additional {additional_filter_potential:.1f}GB/day of noisy logs",
                            confidence=confidence,
                            implementation_effort="Low"
                        ))

        # Retention optimization with dynamic pricing
        retention_days = validated_metrics.get("retention_days", 0)
        if retention_days > 90:  # Longer than recommended
            log_price_per_gb = self._get_log_analytics_pricing(validated_metrics)
            
            # Calculate current log cost estimate
            daily_retention_cost = current_daily_ingestion * log_price_per_gb
            current_retention_cost = daily_retention_cost * retention_days
            optimal_retention_cost = daily_retention_cost * 75  # 75-day optimal retention
            
            # 70% of logs affected by retention optimization
            retention_potential = (current_retention_cost - optimal_retention_cost) * 0.70
            
            # Apply validation cap
            current_obs_cost = validated_metrics.get("current_observability_cost", 0)
            if current_obs_cost > 0:
                max_retention_savings = current_obs_cost * 0.40  # Max 40% from retention
                retention_potential = min(retention_potential, max_retention_savings)
                logger.info(f"💰 Capped retention savings at ${retention_potential:.0f}/month (40% of ${current_obs_cost:.0f}/month actual spend)")
            else:
                # If no actual observability cost, be very conservative
                retention_potential = min(retention_potential, 50)  # Cap at $50/month max
                logger.warning(f"⚠️ No actual observability cost data - capping retention savings at ${retention_potential:.0f}/month")
            
            # Only suggest if meaningful savings
            if retention_potential > 100:  # >$100/month threshold
                confidence = "High" if retention_days > 180 else "Medium"
                
                savings.append(SavingsEstimate(
                    category="Observability - Retention Tuning", 
                    potential_monthly_savings=retention_potential,
                    description=f"Optimize log retention from {retention_days} to 60-90 days",
                    confidence=confidence,
                    implementation_effort="Low"
                ))

        # Add observability summary logging
        total_obs_savings = sum(s.potential_monthly_savings for s in savings)
        current_obs_cost = validated_metrics.get("current_observability_cost", 0)
        if current_obs_cost > 0:
            savings_pct = (total_obs_savings / current_obs_cost) * 100
            logger.info(f"📊 Observability savings: ${total_obs_savings:.0f}/month ({savings_pct:.1f}% of current spend)")
        else:
            logger.info(f"📊 Observability savings: ${total_obs_savings:.0f}/month (no baseline cost provided)")

        return savings

    def _validate_observability_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance observability metrics for more accurate calculations
        """
        validated = metrics.copy()
        
        # Ensure we have realistic daily ingestion data
        if not validated.get("current_daily_ingestion_gb"):
            # Try to estimate from other metrics
            generated_gb = validated.get("generated_gb", 0)
            if generated_gb > 0:
                validated["current_daily_ingestion_gb"] = generated_gb
                logger.info(f"📈 Using generated_gb as daily ingestion: {generated_gb:.1f}GB/day")
        
        # Validate filtering percentage is realistic
        daily_ingestion = validated.get("current_daily_ingestion_gb", 0)
        filtered_gb = validated.get("filtered_gb", 0)
        if daily_ingestion > 0 and filtered_gb > daily_ingestion:
            logger.warning(f"⚠️ Filtered GB ({filtered_gb}) exceeds daily ingestion ({daily_ingestion}), capping")
            validated["filtered_gb"] = daily_ingestion * 0.5  # Cap at 50% max filtering
        
        # Add region data if missing (for pricing)
        if not validated.get("region"):
            # Try to infer from cluster context
            cluster_region = validated.get("cluster_metadata", {}).get("region")
            if cluster_region:
                validated["region"] = cluster_region
                logger.info(f"🌍 Inferred region from cluster metadata: {cluster_region}")
        
        return validated

    def _get_log_analytics_pricing(self, metrics: Dict[str, Any]) -> float:
        """
        Get dynamic Log Analytics pricing based on commitment tier and region
        """
        # Check for commitment tier first
        commitment_tier = metrics.get("log_analytics_commitment_tier")
        if commitment_tier:
            # Azure Log Analytics commitment tier pricing (as of 2024)
            pricing_map = {
                "100GB": 1.15,   # $1.15/GB for 100GB/day commitment
                "200GB": 1.46,   # $1.46/GB for 200GB/day commitment  
                "300GB": 1.70,   # $1.70/GB for 300GB/day commitment
                "400GB": 1.84,   # $1.84/GB for 400GB/day commitment
                "500GB": 1.96,   # $1.96/GB for 500GB/day commitment
                "1000GB": 2.05,  # $2.05/GB for 1TB/day commitment
                "2000GB": 2.15,  # $2.15/GB for 2TB/day commitment
                "5000GB": 2.25   # $2.25/GB for 5TB/day commitment
            }
            tier_price = pricing_map.get(commitment_tier)
            if tier_price:
                logger.info(f"🏷️ Using commitment tier pricing: {commitment_tier} = ${tier_price}/GB")
                return tier_price
        
        # Check for region-specific pay-as-you-go pricing
        region = metrics.get("region", "").lower()
        regional_pricing = {
            "eastus": 2.76,
            "eastus2": 2.76, 
            "westus": 2.99,
            "westus2": 2.99,
            "northeurope": 3.04,
            "westeurope": 3.04,
            "southeastasia": 3.31,
            "australiaeast": 3.31,
            "uksouth": 2.87,
            "canadacentral": 2.87,
            "japaneast": 3.31
        }
        
        regional_price = regional_pricing.get(region)
        if regional_price:
            logger.info(f"🌍 Using regional pay-as-you-go pricing for {region}: ${regional_price}/GB")
            return regional_price
        
        # Fallback to default pay-as-you-go pricing
        default_price = 2.76  # Azure East US baseline
        logger.warning(f"⚠️ Using default Log Analytics pricing: ${default_price}/GB")
        return default_price

    def _get_compute_details(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed compute efficiency breakdown"""
        return {
            "cpu_utilization": safe_divide(metrics.get("cpu_p95", 0), metrics.get("cpu_alloc", 1)),
            "mem_utilization": safe_divide(metrics.get("mem_p95", 0), metrics.get("mem_alloc", 1)),
            "spot_coverage": safe_divide(metrics.get("spot_user_cores", 0), metrics.get("total_user_cores", 1)),
            "ri_coverage": safe_divide(metrics.get("reserved_core_hours", 0), metrics.get("baseline_core_hours", 1)),
            "ca_pending_pct": metrics.get("ca_pending_capacity_pct", 0)
        }

    def _get_storage_details(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed storage efficiency breakdown"""
        return {
            "provisioned_vs_used": metrics.get("prov_vs_used", 1.0),
            "storage_waste_pct": safe_divide(metrics.get("storage_waste_cost", 0), metrics.get("cost_storage", 1)),
            "premium_waste_pct": safe_divide(metrics.get("premium_waste_cost", 0), metrics.get("cost_storage", 1))
        }

    def _get_network_details(self, metrics: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed network efficiency breakdown"""
        return {
            "lb_per_service": safe_divide(metrics.get("lb_count", 0), metrics.get("services_exposed", 1)),
            "cost_per_gb": safe_divide(
                metrics.get("cost_network", 0) + metrics.get("cost_lb", 0), 
                metrics.get("data_processed_gb", 1)
            ),
            "idle_ip_cost": metrics.get("idle_public_ip_cost", 0)
        }

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result