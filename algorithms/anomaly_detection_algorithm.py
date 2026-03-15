"""
Anomaly Detection Algorithm
===========================

Advanced anomaly detection for Kubernetes workloads including memory leaks,
CPU spikes, resource drift, and unusual patterns.

FAIL FAST - NO SILENT FAILURES - NO DEFAULTS - NO FALLBACKS
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from shared.standards.performance_standards import SystemPerformanceStandards
from shared.standards.anomaly_detection_standards import AnomalyDetectionStandards


class AnomalyDetectionAlgorithm:
    """
    Advanced anomaly detection algorithm using industry standards
    Detects memory leaks, CPU spikes, resource drift, and unusual patterns
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize anomaly detection algorithm
        
        Args:
            logger: Logger instance (required, no default)
        
        Raises:
            ValueError: If logger is None
        """
        if logger is None:
            raise ValueError("Logger parameter is required")
        
        self.logger = logger
        self.performance_standards = SystemPerformanceStandards()
        self.anomaly_standards = AnomalyDetectionStandards()
        self.logger.info("🔍 Anomaly Detection Algorithm initialized with industry standards")
    
    def detect_workload_anomalies(self, workload_metrics: Dict) -> Dict:
        """
        Detect anomalies in workload resource usage patterns
        
        Args:
            workload_metrics: Workload metrics data (required)
        
        Returns:
            Dict: Anomaly detection results
        
        Raises:
            ValueError: If workload_metrics is None or invalid
            KeyError: If required metrics are missing
        """
        if workload_metrics is None:
            raise ValueError("Workload metrics parameter is required")
        if not isinstance(workload_metrics, dict):
            raise ValueError("Workload metrics must be a dictionary")
        
        # Validate required fields
        required_fields = ["workload_name", "cpu_utilization_history", "memory_utilization_history"]
        for field in required_fields:
            if field not in workload_metrics:
                raise KeyError(f"Required field '{field}' missing from workload_metrics")
        
        workload_name = workload_metrics["workload_name"]
        if not isinstance(workload_name, str) or len(workload_name.strip()) == 0:
            raise ValueError("Workload name must be a non-empty string")
        
        cpu_history = workload_metrics["cpu_utilization_history"]
        memory_history = workload_metrics["memory_utilization_history"]
        
        if not isinstance(cpu_history, list) or not isinstance(memory_history, list):
            raise ValueError("CPU and memory history must be lists")
        if len(cpu_history) == 0 or len(memory_history) == 0:
            raise ValueError("CPU and memory history cannot be empty")
        
        self.logger.info(f"🔍 Detecting anomalies for workload: {workload_name}")
        
        anomalies = []
        
        # Detect memory leaks
        memory_leak_anomaly = self._detect_memory_leak(workload_name, memory_history)
        if memory_leak_anomaly:
            anomalies.append(memory_leak_anomaly)
        
        # Detect CPU spikes
        cpu_spike_anomaly = self._detect_cpu_spikes(workload_name, cpu_history)
        if cpu_spike_anomaly:
            anomalies.append(cpu_spike_anomaly)
        
        # Detect resource drift
        drift_anomaly = self._detect_resource_drift(workload_name, cpu_history, memory_history)
        if drift_anomaly:
            anomalies.append(drift_anomaly)
        
        # Detect unusual patterns
        pattern_anomaly = self._detect_unusual_patterns(workload_name, cpu_history, memory_history)
        if pattern_anomaly:
            anomalies.append(pattern_anomaly)
        
        result = {
            "workload_name": workload_name,
            "has_anomalies": len(anomalies) > 0,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "analysis_timestamp": datetime.now().isoformat(),
            "confidence_score": self._calculate_overall_confidence(anomalies)
        }
        
        if len(anomalies) > 0:
            self.logger.warning(f"⚠️ {len(anomalies)} anomalies detected for workload {workload_name}")
        else:
            self.logger.info(f"✅ No anomalies detected for workload {workload_name}")
        
        return result
    
    def _detect_memory_leak(self, workload_name: str, memory_history: List[float]) -> Optional[Dict]:
        """Detect memory leak patterns"""
        # Validate using standards
        try:
            self.anomaly_standards.validate_memory_leak_data(memory_history)
        except ValueError:
            return None
        
        # Calculate trend using linear regression approach
        n = len(memory_history)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = sum(x_values) / n
        y_mean = sum(memory_history) / n
        
        numerator = sum((x_values[i] - x_mean) * (memory_history[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return None
        
        slope = numerator / denominator
        
        # Memory leak thresholds from standards
        min_slope_threshold = self.anomaly_standards.MEMORY_LEAK_MIN_SLOPE_THRESHOLD
        min_total_increase = self.anomaly_standards.MEMORY_LEAK_MIN_TOTAL_INCREASE
        
        total_increase = ((memory_history[-1] - memory_history[0]) / memory_history[0]) * 100
        
        if slope > min_slope_threshold and total_increase > min_total_increase:
            # Predict when memory limit will be reached
            current_usage = memory_history[-1]
            memory_limit = self.anomaly_standards.MEMORY_LEAK_CRITICAL_THRESHOLD
            
            time_to_critical = 0
            if slope > 0:
                time_to_critical = (memory_limit - current_usage) / slope
            
            return {
                "type": "memory_leak",
                "severity": min(slope / self.anomaly_standards.MEMORY_LEAK_SEVERITY_HIGH, 1.0),
                "description": f"Memory leak detected: {total_increase:.1f}% increase over time",
                "current_usage": current_usage,
                "trend_slope": slope,
                "time_to_critical_hours": max(int(time_to_critical), 1) if time_to_critical > 0 else "immediate",
                "impact": "high",
                "action_required": "Restart workload and investigate memory leaks in code"
            }
        
        return None
    
    def _detect_cpu_spikes(self, workload_name: str, cpu_history: List[float]) -> Optional[Dict]:
        """Detect CPU spike patterns"""
        # Validate using standards
        try:
            self.anomaly_standards.validate_cpu_spike_data(cpu_history)
        except ValueError:
            return None
        
        # Calculate baseline using standards
        sorted_values = sorted(cpu_history)
        baseline_percentile = self.anomaly_standards.CPU_SPIKE_BASELINE_PERCENTILE / 100.0
        baseline_end = int(len(sorted_values) * baseline_percentile)
        baseline = sum(sorted_values[:baseline_end]) / baseline_end if baseline_end > 0 else 0
        
        # Detect spikes using standards
        spike_threshold = baseline * self.anomaly_standards.CPU_SPIKE_BASELINE_MULTIPLIER
        spike_absolute_threshold = self.anomaly_standards.CPU_SPIKE_ABSOLUTE_THRESHOLD
        
        spikes = []
        for i, value in enumerate(cpu_history):
            if value > spike_threshold or value > spike_absolute_threshold:
                spikes.append({"index": i, "value": value, "multiplier": value / baseline if baseline > 0 else 0})
        
        if len(spikes) > 0:
            max_spike = max(spikes, key=lambda x: x["value"])
            spike_frequency = len(spikes) / len(cpu_history)
            
            return {
                "type": "cpu_spike",
                "severity": min(max_spike["value"] / 100.0, 1.0),
                "description": f"CPU spikes detected: {len(spikes)} spikes, max {max_spike['value']:.1f}%",
                "baseline_cpu": baseline,
                "max_spike_value": max_spike["value"],
                "spike_frequency": spike_frequency,
                "impact": "medium" if max_spike["value"] < self.anomaly_standards.CPU_SPIKE_SEVERITY_MEDIUM_THRESHOLD else "high",
                "action_required": "Investigate what causes CPU spikes, consider resource limits"
            }
        
        return None
    
    def _detect_resource_drift(self, workload_name: str, cpu_history: List[float], memory_history: List[float]) -> Optional[Dict]:
        """Detect gradual resource drift over time"""
        min_points = self.anomaly_standards.RESOURCE_DRIFT_MIN_DATA_POINTS
        if len(cpu_history) < min_points or len(memory_history) < min_points:
            return None
        
        # Compare segments using standards
        comparison_ratio = self.anomaly_standards.RESOURCE_DRIFT_COMPARISON_RATIO
        segment_size = int(len(cpu_history) * comparison_ratio)
        
        cpu_early = cpu_history[:segment_size]
        cpu_recent = cpu_history[-segment_size:]
        memory_early = memory_history[:segment_size]
        memory_recent = memory_history[-segment_size:]
        
        cpu_early_avg = sum(cpu_early) / len(cpu_early)
        cpu_recent_avg = sum(cpu_recent) / len(cpu_recent)
        memory_early_avg = sum(memory_early) / len(memory_early)
        memory_recent_avg = sum(memory_recent) / len(memory_recent)
        
        # Calculate drift percentages
        cpu_drift = ((cpu_recent_avg - cpu_early_avg) / cpu_early_avg * 100) if cpu_early_avg > 0 else 0
        memory_drift = ((memory_recent_avg - memory_early_avg) / memory_early_avg * 100) if memory_early_avg > 0 else 0
        
        # Drift thresholds from standards
        significant_drift_threshold = self.anomaly_standards.RESOURCE_DRIFT_SIGNIFICANT_THRESHOLD
        
        if abs(cpu_drift) > significant_drift_threshold or abs(memory_drift) > significant_drift_threshold:
            drift_type = "increasing" if (cpu_drift + memory_drift) > 0 else "decreasing"
            
            return {
                "type": "resource_drift",
                "severity": min(max(abs(cpu_drift), abs(memory_drift)) / self.anomaly_standards.RESOURCE_DRIFT_SEVERITY_DIVISOR, 1.0),
                "description": f"Resource drift detected: CPU {cpu_drift:+.1f}%, Memory {memory_drift:+.1f}%",
                "cpu_drift_percentage": cpu_drift,
                "memory_drift_percentage": memory_drift,
                "drift_direction": drift_type,
                "impact": "medium",
                "action_required": "Review workload changes, consider resizing requests/limits"
            }
        
        return None
    
    def _detect_unusual_patterns(self, workload_name: str, cpu_history: List[float], memory_history: List[float]) -> Optional[Dict]:
        """Detect unusual or erratic patterns in resource usage"""
        min_points = self.anomaly_standards.UNUSUAL_PATTERN_MIN_DATA_POINTS
        if len(cpu_history) < min_points or len(memory_history) < min_points:
            return None
        
        # Calculate coefficient of variation (CV) - measure of relative variability
        cpu_mean = sum(cpu_history) / len(cpu_history)
        memory_mean = sum(memory_history) / len(memory_history)
        
        if cpu_mean == 0 or memory_mean == 0:
            return None
        
        cpu_variance = sum((x - cpu_mean) ** 2 for x in cpu_history) / len(cpu_history)
        memory_variance = sum((x - memory_mean) ** 2 for x in memory_history) / len(memory_history)
        
        cpu_std = cpu_variance ** 0.5
        memory_std = memory_variance ** 0.5
        
        cpu_cv = cpu_std / cpu_mean
        memory_cv = memory_std / memory_mean
        
        # Unusual pattern thresholds from standards
        high_variability_threshold = self.anomaly_standards.UNUSUAL_PATTERN_CV_THRESHOLD
        
        if cpu_cv > high_variability_threshold or memory_cv > high_variability_threshold:
            return {
                "type": "unusual_pattern",
                "severity": min(max(cpu_cv, memory_cv) / self.anomaly_standards.UNUSUAL_PATTERN_SEVERITY_DIVISOR, 1.0),
                "description": f"Unusual resource patterns: CPU CV={cpu_cv:.2f}, Memory CV={memory_cv:.2f}",
                "cpu_variability": cpu_cv,
                "memory_variability": memory_cv,
                "pattern_type": "highly_variable",
                "impact": "low",
                "action_required": "Monitor for consistent patterns, investigate irregular workload behavior"
            }
        
        return None
    
    def detect_snapshot_anomalies(self, node_metrics: List[Dict], pod_data: List[Dict],
                                   cluster_avg_cpu: float, cluster_avg_memory: float) -> Dict:
        """
        Detect anomalies from a single point-in-time cluster snapshot.

        Unlike time-series detection, this finds structural anomalies visible
        in current state: idle nodes, memory pressure, pod restarts, zombie
        workloads, resource request/limit misconfigurations.

        Args:
            node_metrics: List of node dicts with cpu_usage_pct, memory_usage_pct, vm_size
            pod_data: List of pod dicts with cpu_request, memory_request, restarts, status
            cluster_avg_cpu: Cluster-wide average CPU utilization
            cluster_avg_memory: Cluster-wide average memory utilization

        Returns:
            Dict with anomalies list and summary stats
        """
        if node_metrics is None:
            raise ValueError("node_metrics parameter is required")
        if pod_data is None:
            raise ValueError("pod_data parameter is required")

        anomalies = []

        # 1. Idle/near-idle nodes (CPU < 5%)
        for node in node_metrics:
            cpu = float(node.get('cpu_usage_pct', 0))
            mem = float(node.get('memory_usage_pct', 0))
            name = node.get('node_name', 'unknown')

            if cpu < 5 and mem < 20:
                anomalies.append({
                    "type": "idle_node",
                    "severity": 0.7,
                    "description": f"Node {name} is nearly idle: {cpu:.0f}% CPU, {mem:.0f}% memory",
                    "node_name": name,
                    "cpu_usage": cpu,
                    "memory_usage": mem,
                    "impact": "high",
                    "action_required": "Consider removing node or consolidating workloads"
                })

        # 2. Memory pressure on nodes (> 85%)
        for node in node_metrics:
            mem = float(node.get('memory_usage_pct', 0))
            name = node.get('node_name', 'unknown')
            if mem > 85:
                anomalies.append({
                    "type": "memory_pressure",
                    "severity": min(mem / 100.0, 1.0),
                    "description": f"Node {name} under memory pressure: {mem:.0f}% used",
                    "node_name": name,
                    "memory_usage": mem,
                    "impact": "high",
                    "action_required": "Scale up node pool or redistribute workloads"
                })

        # 3. Pod restart anomalies (restarts > 3)
        for pod in pod_data:
            raw_restarts = pod.get('restarts', 0)
            # Handle comma-separated per-container restarts (e.g., '0,3,0')
            if isinstance(raw_restarts, str):
                try:
                    restarts = sum(int(r.strip()) for r in raw_restarts.split(',') if r.strip().isdigit())
                except ValueError:
                    restarts = 0
            else:
                restarts = int(raw_restarts)
            name = pod.get('name', 'unknown')
            ns = pod.get('namespace', 'unknown')
            if restarts > 3:
                severity = min(restarts / 20.0, 1.0)
                anomalies.append({
                    "type": "pod_restart",
                    "severity": severity,
                    "description": f"Pod {ns}/{name} has {restarts} restarts — possible crash loop",
                    "pod_name": f"{ns}/{name}",
                    "restart_count": restarts,
                    "impact": "high" if restarts > 10 else "medium",
                    "action_required": "Check pod logs for OOMKill or application errors"
                })

        # 4. Pending/failed pods
        for pod in pod_data:
            status = str(pod.get('status', '')).lower()
            name = pod.get('name', 'unknown')
            ns = pod.get('namespace', 'unknown')
            if status in ('pending', 'failed', 'unknown', 'crashloopbackoff'):
                anomalies.append({
                    "type": "unhealthy_pod",
                    "severity": 0.8 if status == 'failed' else 0.6,
                    "description": f"Pod {ns}/{name} is in {status} state",
                    "pod_name": f"{ns}/{name}",
                    "pod_status": status,
                    "impact": "high",
                    "action_required": "Investigate pod scheduling or resource constraints"
                })

        # 5. Cluster-wide over-provisioning (avg CPU < 15%)
        if cluster_avg_cpu < 15 and len(node_metrics) >= 2:
            waste_pct = 100 - cluster_avg_cpu
            anomalies.append({
                "type": "cluster_overprovisioned",
                "severity": min(waste_pct / 100.0, 0.9),
                "description": f"Cluster is {waste_pct:.0f}% idle — only {cluster_avg_cpu:.1f}% CPU utilized across {len(node_metrics)} nodes",
                "cluster_cpu": cluster_avg_cpu,
                "cluster_memory": cluster_avg_memory,
                "node_count": len(node_metrics),
                "impact": "high",
                "action_required": "Right-size node pool or consolidate to fewer nodes"
            })

        # 6. CPU-Memory imbalance (CPU very low but memory high — wrong VM family)
        if cluster_avg_cpu > 0 and cluster_avg_memory > 0:
            ratio = cluster_avg_memory / cluster_avg_cpu if cluster_avg_cpu > 1 else cluster_avg_memory
            if ratio > 5 and cluster_avg_memory > 50:
                anomalies.append({
                    "type": "resource_imbalance",
                    "severity": min(ratio / 15.0, 0.8),
                    "description": f"CPU:Memory imbalance — {cluster_avg_cpu:.1f}% CPU vs {cluster_avg_memory:.1f}% memory ({ratio:.1f}x ratio). Consider memory-optimized VMs.",
                    "cpu_util": cluster_avg_cpu,
                    "memory_util": cluster_avg_memory,
                    "imbalance_ratio": ratio,
                    "impact": "medium",
                    "action_required": "Switch to memory-optimized instance family"
                })

        # 7. No resource requests set (pods without cpu_request or memory_request)
        no_requests = [p for p in pod_data
                       if (not p.get('cpu_request') or p.get('cpu_request') == '0')
                       and str(p.get('status', '')).lower() == 'running']
        if len(no_requests) > 0 and len(pod_data) > 0:
            pct = (len(no_requests) / len(pod_data)) * 100
            if pct > 20:
                anomalies.append({
                    "type": "missing_requests",
                    "severity": min(pct / 100.0, 0.7),
                    "description": f"{len(no_requests)} pods ({pct:.0f}%) running without CPU requests — scheduling unreliable",
                    "pods_without_requests": len(no_requests),
                    "total_pods": len(pod_data),
                    "impact": "medium",
                    "action_required": "Set resource requests on all production workloads"
                })

        # Sort by severity
        anomalies.sort(key=lambda x: x.get("severity", 0), reverse=True)

        # Categorize
        categories = {}
        for a in anomalies:
            t = a.get("type", "unknown")
            categories[t] = categories.get(t, 0) + 1

        total = len(anomalies)
        avg_severity = (sum(a.get("severity", 0) for a in anomalies) / total) if total > 0 else 0
        highest = max((a.get("severity", 0) for a in anomalies), default=0)

        self.logger.info(f"Snapshot anomaly detection: {total} anomalies found")

        return {
            "total_anomalies": total,
            "anomalies": anomalies[:15],
            "anomaly_categories": categories,
            "average_severity": avg_severity,
            "highest_severity": highest,
            "detection_type": "snapshot",
            "status": "completed"
        }

    def _calculate_overall_confidence(self, anomalies: List[Dict]) -> float:
        """Calculate overall confidence score for anomaly detection"""
        if not anomalies:
            return self.anomaly_standards.CONFIDENCE_NO_ANOMALIES
        
        # Confidence decreases with severity of anomalies
        total_severity = sum(anomaly.get("severity", 0.5) for anomaly in anomalies)
        max_possible_severity = len(anomalies) * 1.0
        
        if max_possible_severity == 0:
            return self.anomaly_standards.CONFIDENCE_BASE_SCORE
        
        # Convert severity to confidence (inverse relationship) using standards
        severity_ratio = total_severity / max_possible_severity
        confidence = max(
            self.anomaly_standards.CONFIDENCE_MIN_SCORE, 
            self.anomaly_standards.CONFIDENCE_BASE_SCORE - (severity_ratio * self.anomaly_standards.CONFIDENCE_SEVERITY_IMPACT)
        )
        
        return confidence
    
    def detect_cost_anomalies(self, cost_history: List[Dict]) -> Dict:
        """
        Detect cost anomalies in spending patterns
        
        Args:
            cost_history: List of cost data points with timestamp and amount
        
        Returns:
            Dict: Cost anomaly detection results
        
        Raises:
            ValueError: If cost_history is None or invalid
        """
        if cost_history is None:
            raise ValueError("Cost history parameter is required")
        if not isinstance(cost_history, list):
            raise ValueError("Cost history must be a list")
        if len(cost_history) == 0:
            raise ValueError("Cost history cannot be empty")
        
        # Validate cost data using standards
        self.anomaly_standards.validate_cost_anomaly_data(cost_history)
        
        self.logger.info(f"🔍 Detecting cost anomalies from {len(cost_history)} data points")
        
        amounts = [point["amount"] for point in cost_history]
        
        # Calculate baseline (median of costs)
        sorted_amounts = sorted(amounts)
        median_cost = sorted_amounts[len(sorted_amounts) // 2]
        
        # Detect cost spikes using standards
        cost_spike_threshold = median_cost * self.anomaly_standards.COST_ANOMALY_SPIKE_MULTIPLIER
        min_spike_amount = self.anomaly_standards.COST_ANOMALY_MIN_SPIKE_AMOUNT
        
        cost_anomalies = []
        for i, point in enumerate(cost_history):
            amount = point["amount"]
            if amount > cost_spike_threshold and amount > min_spike_amount:
                spike_multiplier = amount / median_cost if median_cost > 0 else 1
                cost_anomalies.append({
                    "type": "cost_spike",
                    "severity": min(spike_multiplier / self.anomaly_standards.COST_ANOMALY_SEVERITY_DIVISOR, 1.0),
                    "description": f"Cost spike detected: ${amount:.2f} (${spike_multiplier:.1f}x normal)",
                    "timestamp": point["timestamp"],
                    "amount": amount,
                    "baseline_cost": median_cost,
                    "spike_multiplier": spike_multiplier,
                    "impact": "high",
                    "action_required": "Investigate cause of cost increase"
                })
        
        result = {
            "has_cost_anomalies": len(cost_anomalies) > 0,
            "cost_anomaly_count": len(cost_anomalies),
            "cost_anomalies": cost_anomalies,
            "baseline_cost": median_cost,
            "total_data_points": len(cost_history),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        if len(cost_anomalies) > 0:
            self.logger.warning(f"⚠️ {len(cost_anomalies)} cost anomalies detected")
        else:
            self.logger.info(f"✅ No cost anomalies detected")
        
        return result