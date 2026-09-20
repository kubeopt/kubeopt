"""
GPU/AI Workload Cost Evaluator -- Sprint 3.

Produces deterministic recommendations from a CollectorReport.
No external dependencies, no cloud credentials, no AI required.

Active detection rules:
  2. No HPA on GPU     -- GPU Deployment with no HPA (training Jobs excluded)
  3. Missing limits    -- GPU pod with no CPU or memory limit alongside GPU limit

Disabled rules (require direct GPU telemetry before re-enabling):
  1. Idle GPU pod      -- disabled: low CPU is not evidence of GPU idleness.
                         Inference/serving pods routinely run at <10% CPU while
                         holding 80-100% GPU. Needs nvidia-smi / DCGM metrics.
  4. Low node occupancy -- disabled: CPU occupancy on a GPU node is not GPU
                         occupancy. A node at 5% CPU but 95% GPU would be
                         incorrectly recommended for consolidation.
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

# Thresholds retained for reference but the rules that use them are disabled.
# Re-enable only when GPU utilisation metrics (nvidia-smi / DCGM exporter) are
# available in the CollectorReport -- CPU is not a valid proxy for GPU idleness.
_IDLE_CPU_THRESHOLD = 0.10
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
    # Disabled: CPU utilisation is not a valid proxy for GPU idleness.
    # GPU inference/serving pods routinely run at <10% CPU with full GPU utilisation.
    # Re-enable when nvidia-smi / DCGM GPU utilisation metrics are in CollectorReport.
    return []


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
    # Disabled: CPU-requested/CPU-allocatable is not GPU occupancy.
    # A GPU node at 5% CPU requested but 95% GPU utilisation would be incorrectly
    # recommended for consolidation. Re-enable when GPU slot occupancy is available.
    return []


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
