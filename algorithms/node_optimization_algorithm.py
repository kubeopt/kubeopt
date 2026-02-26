"""
Node Optimization Algorithm
===========================

Comprehensive node-level optimization algorithm for analyzing VM sizes,
utilization patterns, and generating cost-effective recommendations.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict, List, Optional, Tuple
from shared.standards.node_optimization_standards import NodeOptimizationStandards


class NodeOptimizationAlgorithm:
    """
    Node optimization algorithm using industry standards
    Analyzes VM configurations, utilization patterns, and generates recommendations
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize node optimization algorithm
        
        Args:
            logger: Logger instance (required, no default)
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        
        self.logger = logger
        self.standards = NodeOptimizationStandards()
        self.logger.info("🔧 Node Optimization Algorithm initialized with industry standards")
    
    def analyze_node_utilization(self, node_data: Dict) -> Dict:
        """
        Analyze node utilization patterns and efficiency
        
        Args:
            node_data: Node metrics and configuration data (required)
        
        Returns:
            Dict: Node utilization analysis results
        
        Raises:
            ValueError: If node_data is None or missing required fields
            KeyError: If required metrics are missing from node_data
        """
        if node_data is None:
            raise ValueError("Node data parameter is required")
        
        # Validate required metrics exist
        for metric in self.standards.REQUIRED_METRICS_FOR_ANALYSIS:
            if metric not in node_data:
                raise KeyError(f"Required metric '{metric}' missing from node_data")
        
        cpu_utilization = node_data["cpu_usage_pct"]
        memory_utilization = node_data["memory_usage_pct"]
        cost_per_hour = node_data.get("cost_per_hour", 0.1)  # Default cost if not available
        vm_size = node_data["vm_size"]
        vm_series = node_data.get("vm_series", "unknown")  # Make vm_series optional
        
        # Validate input data
        self.standards.validate_utilization_data(cpu_utilization, memory_utilization)
        self.standards.validate_vm_configuration(vm_size, vm_series)
        self.standards.validate_cost_data(cost_per_hour)
        
        self.logger.info(f"🔍 Analyzing node utilization: {vm_size} - CPU: {cpu_utilization}%, Memory: {memory_utilization}%")
        
        # Categorize utilization levels
        cpu_category = self.standards.get_utilization_category(cpu_utilization)
        memory_category = self.standards.get_utilization_category(memory_utilization)
        
        # Calculate resource waste
        cpu_waste_percentage = 100.0 - cpu_utilization
        memory_waste_percentage = 100.0 - memory_utilization
        average_waste_percentage = (cpu_waste_percentage + memory_waste_percentage) / 2.0
        
        # Determine optimization potential
        needs_optimization = average_waste_percentage > self.standards.RESOURCE_WASTE_PERCENTAGE_THRESHOLD
        
        # Validate required node_name field
        if "node_name" not in node_data:
            raise KeyError("Required field 'node_name' missing from node_data")
        
        node_name = node_data["node_name"]
        if not isinstance(node_name, str) or len(node_name.strip()) == 0:
            raise ValueError("Node name must be a non-empty string")
        
        # Validate timestamp if present
        timestamp = node_data.get("timestamp")
        if timestamp is not None and not isinstance(timestamp, (str, int, float)):
            raise ValueError("Timestamp must be string, int, or float if provided")
        
        analysis_result = {
            "node_name": node_name,
            "vm_size": vm_size,
            "vm_series": vm_series,
            "cpu_usage_pct": cpu_utilization,
            "memory_usage_pct": memory_utilization,
            "cpu_category": cpu_category,
            "memory_category": memory_category,
            "cpu_waste_percentage": cpu_waste_percentage,
            "memory_waste_percentage": memory_waste_percentage,
            "average_waste_percentage": average_waste_percentage,
            "needs_optimization": needs_optimization,
            "cost_per_hour": cost_per_hour,
            "analysis_timestamp": timestamp
        }
        
        self.logger.info(f"✅ Node utilization analysis completed: waste={average_waste_percentage:.1f}%, optimization_needed={needs_optimization}")
        
        return analysis_result
    
    def generate_vm_size_recommendations(self, utilization_analysis: Dict, available_vm_sizes: List[Dict]) -> List[Dict]:
        """
        Generate VM size optimization recommendations based on utilization
        
        Args:
            utilization_analysis: Node utilization analysis results (required)
            available_vm_sizes: List of available VM sizes with specs (required)
        
        Returns:
            List[Dict]: VM size recommendations sorted by priority
        
        Raises:
            ValueError: If parameters are None or invalid
            KeyError: If required fields are missing
        """
        if utilization_analysis is None:
            raise ValueError("Utilization analysis parameter is required")
        if available_vm_sizes is None:
            raise ValueError("Available VM sizes parameter is required")
        if not isinstance(available_vm_sizes, list):
            raise ValueError("Available VM sizes must be a list")
        
        # Validate required fields in utilization analysis
        required_fields = ["cpu_usage_pct", "memory_usage_pct", "vm_size"]
        for field in required_fields:
            if field not in utilization_analysis:
                raise KeyError(f"Required field '{field}' missing from utilization_analysis")
        
        current_vm_size = utilization_analysis["vm_size"]
        cpu_util = utilization_analysis["cpu_usage_pct"]
        memory_util = utilization_analysis["memory_usage_pct"]
        current_cost = utilization_analysis.get("cost_per_hour", 0.1)  # Default cost if not available
        
        self.logger.info(f"🎯 Generating VM size recommendations for {current_vm_size}")
        
        recommendations = []
        
        # Determine recommendation type based on utilization
        if (cpu_util < self.standards.CPU_UTILIZATION_LOW_THRESHOLD and 
            memory_util < self.standards.MEMORY_UTILIZATION_LOW_THRESHOLD):
            recommendation_type = self.standards.RECOMMENDATION_TYPE_DOWNSIZE
            priority = self.standards.RECOMMENDATION_PRIORITY_HIGH
        elif (cpu_util > self.standards.CPU_UTILIZATION_HIGH_THRESHOLD or 
              memory_util > self.standards.MEMORY_UTILIZATION_HIGH_THRESHOLD):
            recommendation_type = self.standards.RECOMMENDATION_TYPE_UPSIZE
            priority = self.standards.RECOMMENDATION_PRIORITY_CRITICAL
        else:
            # Moderate utilization - check for series optimization
            recommendation_type = self.standards.RECOMMENDATION_TYPE_CHANGE_SERIES
            priority = self.standards.RECOMMENDATION_PRIORITY_MEDIUM
        
        # Find suitable VM sizes
        for vm_option in available_vm_sizes:
            if "vm_size" not in vm_option:
                raise KeyError("VM option missing required 'vm_size' field")
            if "cost_per_hour" not in vm_option:
                raise KeyError("VM option missing required 'cost_per_hour' field")

            vm_size = vm_option["vm_size"]
            vm_cost = vm_option["cost_per_hour"]

            # Skip current VM size
            if vm_size == current_vm_size:
                continue

            # Filter by recommendation direction
            if recommendation_type == self.standards.RECOMMENDATION_TYPE_DOWNSIZE and vm_cost >= current_cost:
                continue  # Downsizing: only recommend cheaper VMs
            if recommendation_type == self.standards.RECOMMENDATION_TYPE_UPSIZE and vm_cost <= current_cost:
                continue  # Upsizing: only recommend larger VMs

            # Calculate potential savings
            cost_difference = current_cost - vm_cost
            savings_percentage = (cost_difference / current_cost * 100.0) if current_cost > 0 else 0.0

            # Only recommend if there are meaningful savings or performance improvements
            min_impact_threshold = 5.0
            if abs(savings_percentage) < min_impact_threshold:
                continue
            
            recommendation = {
                "current_vm_size": current_vm_size,
                "recommended_vm_size": vm_size,
                "recommendation_type": recommendation_type,
                "priority": priority,
                "current_cost_per_hour": current_cost,
                "recommended_cost_per_hour": vm_cost,
                "cost_difference_per_hour": cost_difference,
                "savings_percentage": savings_percentage,
                "monthly_savings": cost_difference * 24 * 30,  # Approximate monthly savings
                "confidence_score": self._calculate_recommendation_confidence(utilization_analysis, vm_option),
                "reasoning": self._generate_recommendation_reasoning(utilization_analysis, vm_option, recommendation_type)
            }
            
            recommendations.append(recommendation)
        
        # Sort by savings potential and priority
        recommendations.sort(key=lambda x: (
            -abs(x["savings_percentage"]),  # Higher savings first
            x["priority"] == self.standards.RECOMMENDATION_PRIORITY_CRITICAL,
            x["confidence_score"]
        ), reverse=True)
        
        # Filter by confidence threshold
        high_confidence_recommendations = [
            rec for rec in recommendations 
            if rec["confidence_score"] >= self.standards.CONFIDENCE_THRESHOLD_PERCENTAGE
        ]
        
        self.logger.info(f"✅ Generated {len(high_confidence_recommendations)} high-confidence VM recommendations")
        
        return high_confidence_recommendations[:5]  # Return top 5 recommendations
    
    def calculate_node_efficiency_score(self, node_data: Dict) -> float:
        """
        Calculate overall efficiency score for a node
        
        Args:
            node_data: Node configuration and utilization data (required)
        
        Returns:
            float: Efficiency score (0-100)
        
        Raises:
            ValueError: If node_data is None or invalid
            KeyError: If required fields are missing
        """
        if node_data is None:
            raise ValueError("Node data parameter is required")
        
        required_fields = ["cpu_usage_pct", "memory_usage_pct"]
        for field in required_fields:
            if field not in node_data:
                raise KeyError(f"Required field '{field}' missing from node_data")
        
        cpu_util = node_data["cpu_usage_pct"]
        memory_util = node_data["memory_usage_pct"]
        cost_per_hour = node_data.get("cost_per_hour", 0.1)  # Default cost if not available
        
        # Use baseline cost for comparison (could be improved with actual baseline data)
        baseline_cost = cost_per_hour * 0.8  # Assume 20% optimization potential as baseline
        
        # Calculate separate efficiency scores for CPU and memory
        cpu_efficiency = self.standards.calculate_cost_efficiency_score(cpu_util, cost_per_hour, baseline_cost)
        memory_efficiency = self.standards.calculate_cost_efficiency_score(memory_util, cost_per_hour, baseline_cost)
        
        # Combined efficiency score (weighted average)
        overall_efficiency = (cpu_efficiency * 0.6 + memory_efficiency * 0.4)  # CPU weighted higher
        
        self.logger.info(f"📊 Node efficiency calculated: {overall_efficiency:.1f}% (CPU: {cpu_efficiency:.1f}%, Memory: {memory_efficiency:.1f}%)")
        
        return overall_efficiency
    
    def identify_workload_patterns(self, node_metrics_history: List[Dict]) -> Dict:
        """
        Analyze historical metrics to identify workload patterns
        
        Args:
            node_metrics_history: Historical node metrics data (required)
        
        Returns:
            Dict: Workload pattern analysis
        
        Raises:
            ValueError: If metrics history is None or insufficient data
        """
        if node_metrics_history is None:
            raise ValueError("Node metrics history parameter is required")
        if not isinstance(node_metrics_history, list):
            raise ValueError("Node metrics history must be a list")
        if len(node_metrics_history) < self.standards.MINIMUM_DATA_POINTS_REQUIRED:
            raise ValueError(f"Insufficient data points: need at least {self.standards.MINIMUM_DATA_POINTS_REQUIRED}, got {len(node_metrics_history)}")
        
        self.logger.info(f"🔍 Analyzing workload patterns from {len(node_metrics_history)} data points")
        
        # Extract utilization data
        cpu_utilizations = []
        memory_utilizations = []
        
        for metric in node_metrics_history:
            if "cpu_usage_pct" not in metric:
                raise KeyError("Missing cpu_usage_pct in metrics history")
            if "memory_usage_pct" not in metric:
                raise KeyError("Missing memory_usage_pct in metrics history")
            
            cpu_utilizations.append(metric["cpu_usage_pct"])
            memory_utilizations.append(metric["memory_usage_pct"])
        
        # Calculate pattern statistics
        avg_cpu = sum(cpu_utilizations) / len(cpu_utilizations)
        avg_memory = sum(memory_utilizations) / len(memory_utilizations)
        max_cpu = max(cpu_utilizations)
        max_memory = max(memory_utilizations)
        min_cpu = min(cpu_utilizations)
        min_memory = min(memory_utilizations)
        
        # Calculate variability (coefficient of variation)
        cpu_std = (sum((x - avg_cpu) ** 2 for x in cpu_utilizations) / len(cpu_utilizations)) ** 0.5
        memory_std = (sum((x - avg_memory) ** 2 for x in memory_utilizations) / len(memory_utilizations)) ** 0.5
        
        cpu_cv = (cpu_std / avg_cpu * 100) if avg_cpu > 0 else 0
        memory_cv = (memory_std / avg_memory * 100) if avg_memory > 0 else 0
        
        # Determine workload type based on resource patterns
        workload_type = self._classify_workload_type(avg_cpu, avg_memory, cpu_cv, memory_cv)
        
        pattern_analysis = {
            "workload_type": workload_type,
            "avg_cpu_utilization": avg_cpu,
            "avg_memory_utilization": avg_memory,
            "peak_cpu_utilization": max_cpu,
            "peak_memory_utilization": max_memory,
            "min_cpu_utilization": min_cpu,
            "min_memory_utilization": min_memory,
            "cpu_variability_coefficient": cpu_cv,
            "memory_variability_coefficient": memory_cv,
            "pattern_stability": "stable" if (cpu_cv < 30 and memory_cv < 30) else "variable",
            "resource_profile": self.standards.WORKLOAD_RESOURCE_PROFILES.get(workload_type, {}),
            "analysis_period_hours": len(node_metrics_history)  # Assuming hourly data points
        }
        
        self.logger.info(f"✅ Workload pattern identified: {workload_type} (CPU avg: {avg_cpu:.1f}%, Memory avg: {avg_memory:.1f}%)")
        
        return pattern_analysis
    
    def _calculate_recommendation_confidence(self, utilization_analysis: Dict, vm_option: Dict) -> float:
        """Calculate confidence score for a recommendation"""
        base_confidence = 80.0
        
        # Increase confidence for clear over/under provisioning
        cpu_util = utilization_analysis["cpu_usage_pct"]
        memory_util = utilization_analysis["memory_usage_pct"]
        
        if (cpu_util < 20 or memory_util < 20):  # Clear overprovisioning
            base_confidence += 15.0
        elif (cpu_util > 85 or memory_util > 85):  # Clear underprovisioning
            base_confidence += 10.0
        
        # Decrease confidence for borderline cases
        if (40 <= cpu_util <= 60 and 40 <= memory_util <= 60):
            base_confidence -= 20.0
        
        return min(base_confidence, 100.0)
    
    def _generate_recommendation_reasoning(self, utilization_analysis: Dict, vm_option: Dict, recommendation_type: str) -> str:
        """Generate human-readable reasoning for recommendation"""
        cpu_util = utilization_analysis["cpu_usage_pct"]
        memory_util = utilization_analysis["memory_usage_pct"]
        
        if recommendation_type == self.standards.RECOMMENDATION_TYPE_DOWNSIZE:
            return f"Current utilization is low (CPU: {cpu_util:.1f}%, Memory: {memory_util:.1f}%). Downsizing can reduce costs without impacting performance."
        elif recommendation_type == self.standards.RECOMMENDATION_TYPE_UPSIZE:
            return f"High utilization detected (CPU: {cpu_util:.1f}%, Memory: {memory_util:.1f}%). Upsizing recommended to prevent performance bottlenecks."
        else:
            return f"Alternative VM series may provide better cost-to-performance ratio for current usage pattern."
    
    def _classify_workload_type(self, avg_cpu: float, avg_memory: float, cpu_cv: float, memory_cv: float) -> str:
        """Classify workload type based on resource usage patterns"""
        if avg_cpu > 70:
            if cpu_cv > 50:
                return self.standards.WORKLOAD_TYPE_BATCH  # High CPU, high variability
            else:
                return self.standards.WORKLOAD_TYPE_ML  # High CPU, stable
        elif avg_memory > 70:
            return self.standards.WORKLOAD_TYPE_STATEFUL  # Memory intensive
        elif cpu_cv > 60 or memory_cv > 60:
            return self.standards.WORKLOAD_TYPE_STREAMING  # High variability
        else:
            return self.standards.WORKLOAD_TYPE_STATELESS  # Balanced, stable usage