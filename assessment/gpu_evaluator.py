"""
GPU/AI Workload Cost Evaluator -- Sprint 3.

Produces deterministic recommendations from a CollectorReport.
No external dependencies, no cloud credentials, no AI required.

Detection rules:
  1. Idle GPU pod      -- GPU requested, CPU used < IDLE_CPU_THRESHOLD of request
  2. No HPA on GPU     -- GPU Deployment with no HPA (training Jobs excluded)
  3. Missing limits    -- GPU pod with no CPU or memory limit alongside GPU limit
  4. Low node occupancy -- GPU node pool with < OCCUPANCY_THRESHOLD CPU utilization
"""

import hashlib
from typing import Optional

try:
    from shared.models.collector import CollectorReport, PodSummary, NodeSummary
    from shared.models.recommendation import Recommendation, RiskLevel, RecommendationCategory
except ModuleNotFoundError:
    from kubeopt.shared.models.collector import CollectorReport, PodSummary, NodeSummary
    from kubeopt.shared.models.recommendation import Recommendation, RiskLevel, RecommendationCategory

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# A GPU pod is "idle" when live CPU usage < this fraction of its CPU request
_IDLE_CPU_THRESHOLD = 0.10

# A GPU node pool is "low occupancy" when avg CPU requested < this fraction of allocatable
_OCCUPANCY_THRESHOLD = 0.40

# GPU resource identifiers (Kubernetes extended resource names)
_GPU_VENDORS = {"nvidia.com/gpu", "amd.com/gpu", "intel.com/gpu"}

# Approximate monthly cost per GPU unit by node type keyword (USD)
# Used for conservative savings estimates when no billing API is available.
# These are public list prices; actual costs vary.
_GPU_MONTHLY_COST = {
    "a100": 7000.0,   # A100 80GB PCIe ~$7k/mo on-demand
    "h100": 12000.0,
    "v100": 2500.0,
    "t4": 400.0,
    "a10": 1200.0,
    "default": 500.0,
}

_RISK_WEIGHT = {RiskLevel.LOW: 1.0, RiskLevel.MEDIUM: 0.6, RiskLevel.HIGH: 0.2}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gpu_cost_per_unit(instance_type: str) -> float:
    lower = instance_type.lower()
    for key, cost in _GPU_MONTHLY_COST.items():
        if key in lower:
            return cost
    return _GPU_MONTHLY_COST["default"]


def _rec_id(rule: str, namespace: str, resource: str) -> str:
    raw = f"gpu:{rule}:{namespace}/{resource}"
    return hashlib.sha1(raw.encode(), usedforsecurity=False).hexdigest()[:12]


def _priority(savings: float, confidence: float, risk: RiskLevel) -> float:
    return round(savings * confidence * _RISK_WEIGHT[risk], 2)


def _gpu_pods(report: CollectorReport) -> list[PodSummary]:
    return [p for p in report.pods if p.gpu_request > 0]


def _node_for_pod(report: CollectorReport, pod: PodSummary) -> Optional[NodeSummary]:
    return next((n for n in report.nodes if n.name == pod.node), None)


def _hpa_targets(report: CollectorReport) -> set[str]:
    return {f"{h.namespace}/{h.target_name}" for h in report.hpas}


# ---------------------------------------------------------------------------
# Rule 1 -- Idle GPU pods
# ---------------------------------------------------------------------------

def _idle_gpu_recs(report: CollectorReport) -> list[Recommendation]:
    if not report.metrics_server_available:
        return []

    recs = []
    for pod in _gpu_pods(report):
        if pod.cpu_used_m is None or pod.cpu_request_m == 0:
            continue
        utilization = pod.cpu_used_m / pod.cpu_request_m
        if utilization >= _IDLE_CPU_THRESHOLD:
            continue

        node = _node_for_pod(report, pod)
        cost_per_gpu = _gpu_cost_per_unit(node.instance_type if node else "")
        monthly_savings = cost_per_gpu * pod.gpu_request

        recs.append(Recommendation(
            id=_rec_id("idle", pod.namespace, pod.name),
            category=RecommendationCategory.GPU_WORKLOAD,
            title=f"Idle GPU pod -- {pod.workload or pod.name}",
            resource_ref=f"{pod.workload_kind.lower()}/{pod.workload or pod.name}" if pod.workload else f"pod/{pod.name}",
            namespace=pod.namespace,
            monthly_savings=monthly_savings,
            confidence=0.85,
            risk_level=RiskLevel.LOW,
            priority_score=_priority(monthly_savings, 0.85, RiskLevel.LOW),
            evidence=(
                f"Pod {pod.name} holds {pod.gpu_request}x GPU(s) but CPU usage is "
                f"{pod.cpu_used_m}m / {pod.cpu_request_m}m ({utilization*100:.1f}% of request). "
                f"GPU workloads with <{_IDLE_CPU_THRESHOLD*100:.0f}% CPU utilization are likely stale."
            ),
            command=f"kubectl delete pod {pod.name} -n {pod.namespace}",
            rollback=None,
            requires_ai=False,
        ))
    return recs


# ---------------------------------------------------------------------------
# Rule 2 -- GPU Deployments without HPA
# ---------------------------------------------------------------------------

def _no_hpa_gpu_recs(report: CollectorReport) -> list[Recommendation]:
    hpa_targets = _hpa_targets(report)
    seen: set[str] = set()
    recs = []

    for pod in _gpu_pods(report):
        if pod.workload_kind.lower() not in ("deployment", "statefulset"):
            continue
        key = f"{pod.namespace}/{pod.workload}"
        if key in seen or key in hpa_targets:
            continue
        seen.add(key)

        node = _node_for_pod(report, pod)
        cost_per_gpu = _gpu_cost_per_unit(node.instance_type if node else "")
        # Conservative: HPA could reduce replicas by 30% during low traffic
        monthly_savings = cost_per_gpu * pod.gpu_request * 0.30

        recs.append(Recommendation(
            id=_rec_id("no-hpa", pod.namespace, pod.workload),
            category=RecommendationCategory.GPU_WORKLOAD,
            title=f"GPU workload without autoscaling -- {pod.workload}",
            resource_ref=f"deployment/{pod.workload}",
            namespace=pod.namespace,
            monthly_savings=monthly_savings,
            confidence=0.75,
            risk_level=RiskLevel.MEDIUM,
            priority_score=_priority(monthly_savings, 0.75, RiskLevel.MEDIUM),
            evidence=(
                f"Deployment {pod.workload} requests {pod.gpu_request}x GPU(s) per pod "
                f"but has no HPA. GPU inference workloads with variable traffic "
                f"pay for peak capacity 24/7 without autoscaling."
            ),
            command=None,
            yaml_patch=(
                f"apiVersion: autoscaling/v2\n"
                f"kind: HorizontalPodAutoscaler\n"
                f"metadata:\n"
                f"  name: {pod.workload}-hpa\n"
                f"  namespace: {pod.namespace}\n"
                f"spec:\n"
                f"  scaleTargetRef:\n"
                f"    apiVersion: apps/v1\n"
                f"    kind: Deployment\n"
                f"    name: {pod.workload}\n"
                f"  minReplicas: 1\n"
                f"  maxReplicas: 4\n"
                f"  metrics:\n"
                f"  - type: Resource\n"
                f"    resource:\n"
                f"      name: cpu\n"
                f"      target:\n"
                f"        type: Utilization\n"
                f"        averageUtilization: 70\n"
            ),
            requires_ai=False,
        ))
    return recs


# ---------------------------------------------------------------------------
# Rule 3 -- GPU pods missing CPU/memory limits
# ---------------------------------------------------------------------------

def _missing_limits_gpu_recs(report: CollectorReport) -> list[Recommendation]:
    seen: set[str] = set()
    recs = []

    for pod in _gpu_pods(report):
        if pod.cpu_limit_m > 0 and pod.memory_limit_mb > 0:
            continue
        key = f"{pod.namespace}/{pod.workload or pod.name}"
        if key in seen:
            continue
        seen.add(key)

        missing = []
        if pod.cpu_limit_m == 0:
            missing.append("cpu")
        if pod.memory_limit_mb == 0:
            missing.append("memory")

        recs.append(Recommendation(
            id=_rec_id("no-limits", pod.namespace, pod.workload or pod.name),
            category=RecommendationCategory.GPU_WORKLOAD,
            title=f"GPU pod missing {'/'.join(missing)} limits -- {pod.workload or pod.name}",
            resource_ref=f"deployment/{pod.workload}" if pod.workload else f"pod/{pod.name}",
            namespace=pod.namespace,
            monthly_savings=0.0,
            confidence=0.90,
            risk_level=RiskLevel.MEDIUM,
            priority_score=_priority(0.0, 0.90, RiskLevel.MEDIUM),
            evidence=(
                f"Pod {pod.name} requests {pod.gpu_request}x GPU(s) but has no "
                f"{' or '.join(missing)} limit set. A GPU pod without CPU/memory limits "
                f"can starve other pods on the same node and makes scheduling unpredictable."
            ),
            command=None,
            yaml_patch=(
                f"resources:\n"
                f"  requests:\n"
                f"    cpu: \"{pod.cpu_request_m}m\"\n"
                f"    memory: \"{pod.memory_request_mb}Mi\"\n"
                f"  limits:\n"
                f"    cpu: \"{max(pod.cpu_request_m, 1000)}m\"\n"
                f"    memory: \"{max(pod.memory_request_mb, 512)}Mi\"\n"
                f"    {pod.gpu_vendor or 'nvidia.com/gpu'}: \"{pod.gpu_limit or pod.gpu_request}\"\n"
            ),
            requires_ai=False,
        ))
    return recs


# ---------------------------------------------------------------------------
# Rule 4 -- Low GPU node pool occupancy
# ---------------------------------------------------------------------------

def _low_occupancy_gpu_recs(report: CollectorReport) -> list[Recommendation]:
    # Group nodes by node_pool, only include pools that have GPU pods
    gpu_pod_nodes: set[str] = {p.node for p in _gpu_pods(report)}
    gpu_node_pools: dict[str, list[NodeSummary]] = {}
    for node in report.nodes:
        if node.name in gpu_pod_nodes or any(
            p.node == node.name for p in _gpu_pods(report)
        ):
            pool = node.node_pool or node.instance_type or node.name
            gpu_node_pools.setdefault(pool, []).append(node)

    recs = []
    for pool, nodes in gpu_node_pools.items():
        total_allocatable = sum(n.cpu_allocatable_m for n in nodes)
        total_requested = sum(n.cpu_requested_m for n in nodes)
        if total_allocatable == 0:
            continue
        occupancy = total_requested / total_allocatable
        if occupancy >= _OCCUPANCY_THRESHOLD:
            continue

        # Estimate savings: if occupancy < threshold, one node might be removable
        sample_node = nodes[0]
        cost_per_gpu = _gpu_cost_per_unit(sample_node.instance_type)
        # Conservative: estimate 1 node could be consolidated
        gpu_pods_on_pool = [p for p in _gpu_pods(report) if any(n.name == p.node for n in nodes)]
        gpus_on_pool = sum(p.gpu_request for p in gpu_pods_on_pool)
        monthly_savings = cost_per_gpu if len(nodes) > 1 else 0.0

        recs.append(Recommendation(
            id=_rec_id("low-occupancy", pool, "node-pool"),
            category=RecommendationCategory.GPU_WORKLOAD,
            title=f"Low GPU node pool occupancy -- {pool}",
            resource_ref=f"nodepool/{pool}",
            namespace="",
            monthly_savings=monthly_savings,
            confidence=0.70,
            risk_level=RiskLevel.MEDIUM,
            priority_score=_priority(monthly_savings, 0.70, RiskLevel.MEDIUM),
            evidence=(
                f"Node pool '{pool}' has {len(nodes)} node(s) with {occupancy*100:.1f}% CPU occupancy "
                f"({total_requested}m / {total_allocatable}m requested). "
                f"{gpus_on_pool} GPU unit(s) are spread across {len(nodes)} node(s). "
                f"Consolidating to fewer nodes could save ~${monthly_savings:.0f}/mo."
            ),
            command=None,
            requires_ai=False,
        ))
    return recs


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def evaluate_gpu_workloads(report: CollectorReport) -> list[Recommendation]:
    """
    Run all GPU cost rules against a CollectorReport.
    Returns an empty list for clusters with no GPU pods.
    Deterministic -- same input always produces same output in same order.
    """
    if not any(p.gpu_request > 0 for p in report.pods):
        return []

    recs: list[Recommendation] = []
    recs.extend(_idle_gpu_recs(report))
    recs.extend(_no_hpa_gpu_recs(report))
    recs.extend(_missing_limits_gpu_recs(report))
    recs.extend(_low_occupancy_gpu_recs(report))

    # Sort by priority_score descending for stable, deterministic ordering
    recs.sort(key=lambda r: (-r.priority_score, r.id))
    return recs
