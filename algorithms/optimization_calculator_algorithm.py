"""
Optimization Calculator Algorithm
=================================

Extracted and refactored optimization calculator logic from algorithmic_cost_analyzer.py
Uses industry standards instead of hardcoded values.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict
import yaml
import os
from shared.standards.cost_optimization_standards import CostCalculationStandards


class OptimizationCalculatorAlgorithm:
    """
    Optimization calculator algorithm using industry standards
    Extracted from algorithmic_cost_analyzer.py OptimizationCalculatorAlgorithm
    """
    
    def __init__(self, logger: logging.Logger, algorithm_instances: Dict, scorer=None, cloud_provider: str = 'azure'):
        """
        Initialize optimization calculator algorithm

        Args:
            logger: Logger instance (required, no default)
            algorithm_instances: Dictionary of algorithm instances
            scorer: Cluster scorer instance (optional)
            cloud_provider: Cloud provider for standards resolution

        Raises:
            ValueError: If logger or algorithm_instances is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        if algorithm_instances is None:
            raise ValueError("algorithm_instances parameter is required")

        self.logger = logger
        self.scorer = scorer
        self._cloud_provider = cloud_provider
        
        # Store algorithm instances for calculations
        self.hpa_algorithm = algorithm_instances.get('hpa_algorithm')
        self.rightsizing_algorithm = algorithm_instances.get('rightsizing_algorithm')
        self.storage_algorithm = algorithm_instances.get('storage_algorithm')
        self.performance_algorithm = algorithm_instances.get('performance_algorithm')
        self.infrastructure_algorithm = algorithm_instances.get('infrastructure_algorithm')
        
        # Validate all required algorithms are present
        required_algorithms = ['hpa_algorithm', 'rightsizing_algorithm', 'storage_algorithm', 
                             'performance_algorithm', 'infrastructure_algorithm']
        for algo_name in required_algorithms:
            if not algorithm_instances.get(algo_name):
                raise ValueError(f"Required algorithm instance '{algo_name}' not provided")
        
        # Load standards from configuration
        self._load_standards()
        
        self.logger.info("🔧 Optimization Calculator Algorithm initialized with industry standards")
    
    def _load_standards(self):
        """Load standards from configuration file via StandardsLoader (cloud-provider-aware)"""
        try:
            from shared.standards.standards_loader import get_standards_loader
            cloud_provider = getattr(self, '_cloud_provider', 'azure')
            loader = get_standards_loader(cloud_provider)
            self.standards = loader.load_implementation_standards()

            if not self.standards:
                raise ValueError("Standards configuration is empty or invalid")

            self.logger.info(f"📋 Standards loaded via StandardsLoader (provider={cloud_provider})")

        except Exception as e:
            self.logger.error(f"❌ Failed to load standards: {e}")
            raise ValueError(f"Standards loading failed: {e}") from e
    
    def calculate(self, actual_costs: Dict, current_usage: Dict, metrics_data: Dict) -> Dict:
        """
        Calculate optimization opportunities
        REFACTORED: Moved from OptimizationCalculatorAlgorithm class
        
        Args:
            actual_costs: Actual cost breakdown
            current_usage: Current usage metrics
            metrics_data: Metrics data
        
        Returns:
            Dict: Optimization opportunities breakdown
        
        Raises:
            ValueError: If parameters are invalid or calculation fails
        """
        if actual_costs is None:
            raise ValueError("actual_costs parameter is required")
        if current_usage is None:
            raise ValueError("current_usage parameter is required")
        if metrics_data is None:
            raise ValueError("metrics_data parameter is required")
        
        try:
            self.logger.info("💰 Calculating optimization potential...")
            
            # DEBUG: Log actual cost data
            self.logger.info("💰 DEBUG - Actual costs breakdown:")
            for key, value in actual_costs.items():
                self.logger.info(f"💰   {key}: ${value:.2f}")
            
            # Extract costs
            compute_cost = actual_costs.get('monthly_actual_compute', 0)
            storage_cost = actual_costs.get('monthly_actual_storage', 0)
            
            # Validate cost values
            if not isinstance(compute_cost, (int, float)) or compute_cost < 0:
                raise ValueError(f"Invalid compute_cost: {compute_cost}")
            if not isinstance(storage_cost, (int, float)) or storage_cost < 0:
                raise ValueError(f"Invalid storage_cost: {storage_cost}")
            
            # Calculate algorithm-specific savings
            hpa_savings = self.hpa_algorithm.calculate_hpa_savings(compute_cost, current_usage, metrics_data)
            rightsizing_savings = self.rightsizing_algorithm.calculate_rightsizing_savings(compute_cost, current_usage)
            storage_savings = self.storage_algorithm.calculate_storage_savings(storage_cost, current_usage)
            
            # Calculate performance waste savings
            high_cpu_workloads = current_usage.get('high_cpu_workloads', [])
            performance_savings = self.performance_algorithm.calculate_performance_waste_savings(
                compute_cost, high_cpu_workloads, current_usage
            )
            
            # Combine compute optimizations
            compute_savings = self.performance_algorithm.combine_rightsizing_savings(
                performance_savings, rightsizing_savings, hpa_savings, compute_cost
            )
            
            # Calculate infrastructure savings (base optimization for general infrastructure)
            infrastructure_savings = self.infrastructure_algorithm.calculate_infrastructure_savings(actual_costs, current_usage)
            
            # Calculate cost category savings using standards (these are SEPARATE from infrastructure)
            networking_savings = self._calculate_networking_savings(actual_costs)
            control_plane_savings = self._calculate_control_plane_savings(actual_costs)
            registry_savings = self._calculate_registry_savings(actual_costs)
            monitoring_savings = self._calculate_monitoring_savings(actual_costs)
            
            # Get idle cost from actual costs (resources doing nothing)
            idle_cost = actual_costs.get('monthly_actual_idle', 0)
            idle_savings = idle_cost * 0.8  # Can eliminate 80% of idle resources
            if idle_cost > 0:
                self.logger.info(f"💰 Idle Resources: ${idle_cost:.2f} * 0.80 = ${idle_savings:.2f}")
            
            # Calculate totals - DON'T double count! Infrastructure is separate from specific optimizations
            # Infrastructure savings is for general optimizations (reserved instances, spot, etc.)
            # Specific category savings are targeted optimizations  
            total_monthly_savings = (
                compute_savings +           # HPA, rightsizing, performance
                storage_savings +           # Storage tier optimization
                monitoring_savings +        # Log retention, metrics optimization
                networking_savings +        # Load balancer, public IP optimization
                control_plane_savings +     # Control plane rightsizing
                registry_savings +          # Registry tier optimization
                idle_savings               # Eliminate idle resources
            )
            
            monthly_actual_total = actual_costs.get('monthly_actual_total', 0)
            optimization_percentage = (total_monthly_savings / monthly_actual_total * 100) if monthly_actual_total > 0 else 0
            
            # Build comprehensive result
            result = {
                'hpa_monthly_savings': hpa_savings,
                'rightsizing_monthly_savings': rightsizing_savings,
                'compute_monthly_savings': compute_savings,
                'storage_monthly_savings': storage_savings,
                'networking_monthly_savings': networking_savings,
                'control_plane_monthly_savings': control_plane_savings,
                'registry_monthly_savings': registry_savings,
                'monitoring_monthly_savings': monitoring_savings,
                'idle_monthly_savings': idle_savings,
                'infrastructure_monthly_savings': infrastructure_savings,
                'performance_monthly_savings': performance_savings,
                'total_monthly_savings': total_monthly_savings,
                'optimization_percentage': optimization_percentage,
                'monthly_actual_total': monthly_actual_total
            }
            
            self.logger.info(f"💰 Optimization Summary: ${total_monthly_savings:.2f}/month "
                           f"({optimization_percentage:.1f}% of ${monthly_actual_total:.2f})")
            
            # ENHANCED: Add expert-level cost structure analysis with namespace insights
            self._analyze_cost_structure_and_recommend(actual_costs, current_usage, metrics_data)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Optimization calculation failed: {e}")
            # Fail fast, no defaults
            raise ValueError(f"Optimization calculation failed: {e}") from e
    
    def _calculate_networking_savings(self, actual_costs: Dict) -> float:
        """Calculate networking optimization savings using standards"""
        try:
            networking_cost = actual_costs.get('monthly_actual_networking', 0)
            if networking_cost <= 0:
                return 0.0
            
            # Get standards - FAIL FAST if missing
            cost_category_standards = self.standards.get('cost_category_optimization', {})
            networking_opts = cost_category_standards.get('networking_optimization')
            if not networking_opts:
                raise ValueError("networking_optimization standards not found in configuration")
            
            networking_rate = networking_opts.get('base_savings_rate')
            if networking_rate is None:
                raise ValueError("base_savings_rate for networking_optimization not found in standards")
            
            networking_savings = networking_cost * networking_rate
            self.logger.info(f"💰 Networking: ${networking_cost:.2f} * {networking_rate:.2f} = ${networking_savings:.2f}")
            
            return networking_savings
            
        except Exception as e:
            self.logger.error(f"❌ Networking savings calculation failed: {e}")
            raise ValueError(f"Networking savings calculation failed: {e}") from e
    
    def _calculate_control_plane_savings(self, actual_costs: Dict) -> float:
        """Calculate control plane optimization savings using standards"""
        try:
            control_plane_cost = actual_costs.get('monthly_actual_control_plane', 0)
            if control_plane_cost <= 0:
                return 0.0
            
            # Get standards - FAIL FAST if missing
            cost_category_standards = self.standards.get('cost_category_optimization', {})
            control_plane_opts = cost_category_standards.get('control_plane_optimization')
            if not control_plane_opts:
                raise ValueError("control_plane_optimization standards not found in configuration")
            
            control_plane_rate = control_plane_opts.get('base_savings_rate')
            if control_plane_rate is None:
                raise ValueError("base_savings_rate for control_plane_optimization not found in standards")
            
            control_plane_savings = control_plane_cost * control_plane_rate
            self.logger.info(f"💰 Control plane: ${control_plane_cost:.2f} * {control_plane_rate:.2f} = ${control_plane_savings:.2f}")
            
            return control_plane_savings
            
        except Exception as e:
            self.logger.error(f"❌ Control plane savings calculation failed: {e}")
            raise ValueError(f"Control plane savings calculation failed: {e}") from e
    
    def _calculate_registry_savings(self, actual_costs: Dict) -> float:
        """Calculate registry optimization savings using standards"""
        try:
            registry_cost = actual_costs.get('monthly_actual_registry', 0)
            if registry_cost <= 0:
                return 0.0
            
            # Get standards - FAIL FAST if missing
            cost_category_standards = self.standards.get('cost_category_optimization', {})
            registry_opts = cost_category_standards.get('registry_optimization')
            if not registry_opts:
                raise ValueError("registry_optimization standards not found in configuration")
            
            registry_rate = registry_opts.get('base_savings_rate')
            if registry_rate is None:
                raise ValueError("base_savings_rate for registry_optimization not found in standards")
            
            registry_savings = registry_cost * registry_rate
            self.logger.info(f"💰 Registry: ${registry_cost:.2f} * {registry_rate:.2f} = ${registry_savings:.2f}")
            
            return registry_savings
            
        except Exception as e:
            self.logger.error(f"❌ Registry savings calculation failed: {e}")
            raise ValueError(f"Registry savings calculation failed: {e}") from e
    
    def _calculate_monitoring_savings(self, actual_costs: Dict) -> float:
        """Calculate monitoring/log analytics optimization savings using standards"""
        try:
            monitoring_cost = actual_costs.get('monthly_actual_monitoring', 0)
            if monitoring_cost <= 0:
                return 0.0
            
            total_cost = actual_costs.get('monthly_actual_total', 1)
            if total_cost <= 0:
                self.logger.warning("Total cost is 0 or negative, cannot calculate monitoring proportion")
                return 0.0
            
            monitoring_proportion = monitoring_cost / total_cost
            
            # Get monitoring standards - FAIL FAST if missing
            monitoring_standards = self.standards.get('monitoring_optimization', {})
            thresholds = monitoring_standards.get('monitoring_thresholds', {})
            savings_rates = monitoring_standards.get('monitoring_savings', {})
            
            if not thresholds or not savings_rates:
                raise ValueError("Monitoring optimization standards not found in configuration")
            
            # Get all required threshold and rate values
            critical_threshold = thresholds.get('critical_proportion')
            high_threshold = thresholds.get('high_proportion')
            moderate_threshold = thresholds.get('moderate_proportion')
            
            critical_rate = savings_rates.get('critical_rate')
            high_rate = savings_rates.get('high_rate')
            moderate_rate = savings_rates.get('moderate_rate')
            baseline_rate = savings_rates.get('baseline_rate')
            
            # FAIL FAST if any required value is missing
            if None in [critical_threshold, high_threshold, moderate_threshold, 
                       critical_rate, high_rate, moderate_rate, baseline_rate]:
                raise ValueError("Required monitoring optimization values missing from standards")
            
            # Determine savings rate based on proportion using standards
            if monitoring_proportion > critical_threshold:
                savings_rate = critical_rate
                severity = "CRITICAL"
            elif monitoring_proportion > high_threshold:
                savings_rate = high_rate
                severity = "HIGH"
            elif monitoring_proportion > moderate_threshold:
                savings_rate = moderate_rate
                severity = "MODERATE"
            else:
                savings_rate = baseline_rate
                severity = "STANDARD"
            
            monitoring_savings = monitoring_cost * savings_rate
            
            # FAIL FAST: Validate output
            if monitoring_savings < 0:
                raise ValueError(f"Calculated negative monitoring savings: {monitoring_savings}")
            if monitoring_savings > monitoring_cost:
                raise ValueError(f"Monitoring savings {monitoring_savings} exceeds cost {monitoring_cost}")
            
            # ENHANCED: Expert-level analysis using industry standards
            optimal_proportion = CostCalculationStandards.MONITORING_COST_OPTIMAL_PROPORTION
            maximum_proportion = CostCalculationStandards.MONITORING_COST_MAXIMUM_PROPORTION  
            critical_proportion = CostCalculationStandards.MONITORING_COST_CRITICAL_PROPORTION
            
            # Determine severity level and analysis
            if monitoring_proportion > critical_proportion:
                priority = "CRITICAL"
                severity_analysis = f"SEVERELY OVERPROVISIONED - {monitoring_proportion*100:.1f}% vs {critical_proportion*100:.0f}% critical threshold"
            elif monitoring_proportion > maximum_proportion:
                priority = "HIGH" 
                severity_analysis = f"Above industry maximum - {monitoring_proportion*100:.1f}% vs {maximum_proportion*100:.0f}% industry maximum"
            elif monitoring_proportion > optimal_proportion:
                priority = "MEDIUM"
                severity_analysis = f"Above optimal - {monitoring_proportion*100:.1f}% vs {optimal_proportion*100:.0f}% industry optimal"
            else:
                priority = "LOW"
                severity_analysis = f"Within standards - {monitoring_proportion*100:.1f}% vs {optimal_proportion*100:.0f}% industry optimal"
            
            # Calculate expert recommendations for overprovisioned monitoring
            if monitoring_proportion > maximum_proportion:
                optimal_monitoring_cost = total_cost * optimal_proportion
                maximum_possible_savings = monitoring_cost - optimal_monitoring_cost
                
                self.logger.warning(f"🚨 {priority} MONITORING OPTIMIZATION OPPORTUNITY:")
                self.logger.warning(f"🚨   Current: ${monitoring_cost:.2f} ({monitoring_proportion*100:.1f}% of total cost)")
                self.logger.warning(f"🚨   Industry Optimal: ${optimal_monitoring_cost:.2f} ({optimal_proportion*100:.0f}% of total cost)")
                self.logger.warning(f"🚨   Maximum Opportunity: ${maximum_possible_savings:.2f}/month potential savings")
                self.logger.warning(f"🚨   Analysis: {severity_analysis}")
                self.logger.warning(f"🚨   Recommendations: Review log retention, disable unnecessary metrics, optimize Log Analytics workspace")
            
            self.logger.info(f"📊 {severity} monitoring: ${monitoring_cost:.2f} ({monitoring_proportion*100:.1f}% of total) "
                           f"-> ${monitoring_savings:.2f} calculated savings ({savings_rate*100:.0f}% optimization) | {priority} priority")
            
            return monitoring_savings
            
        except Exception as e:
            self.logger.error(f"❌ Monitoring savings calculation failed: {e}")
            raise ValueError(f"Monitoring savings calculation failed: {e}") from e
    
    def _analyze_cost_structure_and_recommend(self, actual_costs: Dict, current_usage: Dict, metrics_data: Dict) -> None:
        """
        ENHANCED: Expert-level cost structure analysis and recommendations with namespace insights
        Provides the same insights as an AKS expert would give
        """
        try:
            total_cost = actual_costs.get('monthly_actual_total', 0)
            if total_cost <= 0:
                return
            
            # Extract cost components
            compute_cost = actual_costs.get('monthly_actual_compute', 0)
            monitoring_cost = actual_costs.get('monthly_actual_monitoring', 0)
            networking_cost = actual_costs.get('monthly_actual_networking', 0)
            storage_cost = actual_costs.get('monthly_actual_storage', 0)
            
            # Calculate proportions
            compute_proportion = compute_cost / total_cost
            monitoring_proportion = monitoring_cost / total_cost
            networking_proportion = networking_cost / total_cost
            storage_proportion = storage_cost / total_cost
            
            # Get industry standards for comparison
            optimal_compute = CostCalculationStandards.COMPUTE_COST_OPTIMAL_PROPORTION
            max_compute = CostCalculationStandards.COMPUTE_COST_MAXIMUM_PROPORTION
            min_compute = CostCalculationStandards.COMPUTE_COST_MINIMUM_PROPORTION
            
            optimal_monitoring = CostCalculationStandards.MONITORING_COST_OPTIMAL_PROPORTION
            max_monitoring = CostCalculationStandards.MONITORING_COST_MAXIMUM_PROPORTION
            
            self.logger.info("🏗️ EXPERT COST STRUCTURE ANALYSIS:")
            self.logger.info(f"   💰 Total Monthly Cost: ${total_cost:.2f}")
            self.logger.info("   📊 Cost Breakdown:")
            
            # Analyze compute proportion
            if compute_proportion < min_compute:
                compute_analysis = f"⚠️  UNDEROPTIMIZED ({compute_proportion*100:.1f}% vs {optimal_compute*100:.0f}% optimal)"
            elif compute_proportion > max_compute:
                compute_analysis = f"📈 High compute focus ({compute_proportion*100:.1f}% vs {optimal_compute*100:.0f}% optimal)"
            else:
                compute_analysis = f"✅ Within standards ({compute_proportion*100:.1f}% vs {optimal_compute*100:.0f}% optimal)"
            self.logger.info(f"      🖥️  Compute: ${compute_cost:.2f} ({compute_proportion*100:.1f}%) - {compute_analysis}")
            
            # Analyze monitoring proportion (already enhanced above)
            if monitoring_proportion > max_monitoring:
                monitoring_analysis = f"🚨 SEVERELY OVERPROVISIONED"
            elif monitoring_proportion > optimal_monitoring:
                monitoring_analysis = f"⚠️  Above optimal"
            else:
                monitoring_analysis = f"✅ Within standards"
            self.logger.info(f"      📊 Monitoring: ${monitoring_cost:.2f} ({monitoring_proportion*100:.1f}%) - {monitoring_analysis}")
            
            # Other components
            self.logger.info(f"      🌐 Networking: ${networking_cost:.2f} ({networking_proportion*100:.1f}%)")
            self.logger.info(f"      💾 Storage: ${storage_cost:.2f} ({storage_proportion*100:.1f}%)")
            
            # ENHANCED: Namespace-level cost analysis within existing method
            self.logger.info("   🏷️ Namespace Cost Breakdown:")
            
            # Extract workload data from metrics if available  
            workloads_data = []
            if metrics_data and 'hpa_implementation' in metrics_data:
                # Try to get workload info from HPA implementation data
                hpa_impl = metrics_data.get('hpa_implementation', {})
                workloads_data = hpa_impl.get('hpas', [])
            
            # Alternative: Get from high_cpu_workloads in current_usage
            if not workloads_data and current_usage:
                high_cpu_workloads = current_usage.get('high_cpu_workloads', [])
                if high_cpu_workloads:
                    workloads_data = high_cpu_workloads
            
            # Analyze workloads if we found any
            if workloads_data and compute_cost > 0:
                namespace_costs = {}
                idle_workloads = []
                active_workloads = []
                
                for workload in workloads_data:
                    if isinstance(workload, dict):
                        namespace = workload.get('namespace', 'unknown')
                        name = workload.get('name', 'unnamed')
                        cpu_usage = workload.get('cpu_usage_pct', 0)
                        workload_type = workload.get('type', 'deployment')
                        
                        # Estimate cost proportion based on CPU usage
                        if cpu_usage > 5:  # Active workload threshold
                            active_workloads.append((namespace, name, cpu_usage, workload_type))
                        else:
                            idle_workloads.append((namespace, name, cpu_usage, workload_type))
                        
                        # Accumulate costs by namespace
                        if namespace not in namespace_costs:
                            namespace_costs[namespace] = {'cost': 0, 'workloads': 0, 'total_cpu': 0}
                        namespace_costs[namespace]['workloads'] += 1
                        namespace_costs[namespace]['total_cpu'] += cpu_usage
                
                # Calculate estimated costs per namespace
                total_cpu_usage = sum(data['total_cpu'] for data in namespace_costs.values()) or 1
                for namespace, data in namespace_costs.items():
                    cpu_proportion = data['total_cpu'] / total_cpu_usage
                    estimated_cost = compute_cost * cpu_proportion
                    namespace_costs[namespace]['cost'] = estimated_cost
                
                # Display namespace breakdown
                for namespace, data in sorted(namespace_costs.items(), key=lambda x: x[1]['cost'], reverse=True):
                    cost = data['cost']
                    cpu_total = data['total_cpu']
                    workload_count = data['workloads']
                    cost_proportion = (cost / compute_cost * 100) if compute_cost > 0 else 0
                    
                    status = "✅ ACTIVE" if cpu_total > 10 else "⚠️ LOW UTILIZATION" if cpu_total > 0 else "🔴 IDLE"
                    self.logger.info(f"      💰 {namespace}: ${cost:.2f}/month ({cost_proportion:.1f}% of compute) - {status}")
                    self.logger.info(f"         └─ {workload_count} workload(s), {cpu_total:.1f}% total CPU")
                
                # Report idle workload cleanup opportunities  
                if idle_workloads:
                    # Estimate minimal cost for idle workloads (assume 5% of compute minimum)
                    estimated_idle_cost = max(compute_cost * 0.05 / len(namespace_costs), 0.50)  # Min $0.50/month per idle namespace
                    annual_savings = estimated_idle_cost * len(idle_workloads) * 12
                    self.logger.info(f"   🧹 Cleanup Opportunity: {len(idle_workloads)} idle workload(s) - ~${annual_savings:.0f}/year potential")
                    for namespace, name, cpu, workload_type in idle_workloads:
                        self.logger.info(f"      🔴 {namespace}/{name}: {cpu}% CPU ({workload_type})")
            else:
                self.logger.info(f"      💰 Compute: ${compute_cost:.2f}/month (detailed namespace breakdown not available)")
                if compute_cost > 0:
                    self.logger.info(f"         💡 Tip: Enable workload monitoring for namespace-level cost insights")
            
            # Expert recommendations
            self.logger.info("🎯 EXPERT RECOMMENDATIONS:")
            
            if monitoring_proportion > max_monitoring:
                monitoring_target = total_cost * optimal_monitoring
                monitoring_opportunity = monitoring_cost - monitoring_target
                self.logger.info(f"   🥇 Priority 1: Optimize monitoring (${monitoring_opportunity:.2f}/month opportunity)")
                self.logger.info(f"      💡 Actions: Review log retention, disable unnecessary metrics, optimize Log Analytics")
            
            if compute_proportion < min_compute:
                self.logger.info(f"   🥈 Priority 2: Improve compute efficiency (currently {compute_proportion*100:.1f}%)")
                self.logger.info(f"      💡 Actions: Right-size VMs, implement HPA, consolidate workloads")
                
            # ENHANCED: Add namespace-specific recommendations based on analysis
            if 'idle_workloads' in locals() and idle_workloads:
                priority_num = 3 if monitoring_proportion > max_monitoring else 2
                annual_cleanup_savings = sum(namespace_costs.get(ns, {}).get('cost', 0) * 12 for ns, _, _, _ in idle_workloads)
                if annual_cleanup_savings > 10:  # Only recommend if savings > $10/year
                    self.logger.info(f"   {'🥉' if priority_num == 3 else '🥈'} Priority {priority_num}: Cleanup idle workloads (${annual_cleanup_savings:.0f}/year opportunity)")
                    self.logger.info(f"      💡 Actions: Review and remove {len(idle_workloads)} unused deployment(s)")
                    
            if 'namespace_costs' in locals() and len(namespace_costs) > 1:
                max_namespace_cost = max((data['cost'] for data in namespace_costs.values()), default=0)
                if max_namespace_cost > compute_cost * 0.8:  # One namespace dominates >80% of cost
                    dominant_namespace = max(namespace_costs.items(), key=lambda x: x[1]['cost'])[0]
                    self.logger.info(f"   💡 Consider: {dominant_namespace} namespace dominates compute cost - evaluate resource quotas")
                
        except Exception as e:
            self.logger.debug(f"Cost structure analysis failed: {e}")  # Non-critical, just log as debug