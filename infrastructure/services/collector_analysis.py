"""
CollectorAnalysisService -- inventory and evidence-backed observations from a CollectorReport.

Design constraints (all enforced by tests):
- No destructive commands: findings are informational observations only. Deletion
  actions require understanding the full resource graph, which a single snapshot
  cannot provide.
- No unsupported savings: monthly_savings is None on every finding. A single
  snapshot does not establish recoverable spend.
- No mutation commands or patches: resource changes require a historical window
  and per-container precision. Report what was observed; do not prescribe a change.
- No prescribed scaling policy: HPA configuration requires traffic variance data.
  Report that no HPA was observed; do not prescribe min/max/target.
- No GPU evaluator delegation: the GPU evaluator produces deletion commands,
  fabricated savings, and CPU-based patches that violate the above constraints.
  GPU findings are appended by the API layer separately after this service runs.
- Utilization-dependent findings suppressed when metrics_server_available=False.
- This module must never import cloud adapters, credential managers, or provider APIs.
"""

import hashlib
from typing import Optional

try:
    from shared.models.collector import CollectorReport, PodSummary
    from shared.models.recommendation import Recommendation, RiskLevel, RecommendationCategory
except ModuleNotFoundError:
    from kubeopt.shared.models.collector import CollectorReport, PodSummary
    from kubeopt.shared.models.recommendation import Recommendation, RiskLevel, RecommendationCategory


_RIGHTSIZING_THRESHOLD = 0.40  # flag when cpu_used < 40% of cpu_request

_SYSTEM_NAMESPACES = frozenset({
    "kube-system", "kube-public", "kube-node-lease",
    "monitoring", "logging", "cert-manager", "ingress-nginx",
})


def _rec_id(rule: str, namespace: str, resource: str) -> str:
    raw = f"collector:{rule}:{namespace}/{resource}"
    return hashlib.sha1(raw.encode(), usedforsecurity=False).hexdigest()[:12]


def _priority(confidence: float, risk: RiskLevel) -> float:
    weights = {RiskLevel.LOW: 1.0, RiskLevel.MEDIUM: 0.6, RiskLevel.HIGH: 0.2}
    return round(confidence * weights[risk] * 100, 2)


# ---------------------------------------------------------------------------
# Rule: right-sizing observation (requires metrics; no command, no savings)
# ---------------------------------------------------------------------------

def _rightsizing_recs(report: CollectorReport) -> list[Recommendation]:
    """
    Report workloads where observed CPU is well below their request.

    One snapshot is not sufficient to recommend a request change: there may be
    burst patterns, the container list may be unresolved, and a single pod does
    not represent the full workload. No command or savings are emitted.
    """
    if not report.metrics_server_available:
        return []

    seen: set[str] = set()
    recs = []
    for pod in report.pods:
        if pod.cpu_used_m is None or pod.cpu_request_m == 0:
            continue
        ratio = pod.cpu_used_m / pod.cpu_request_m
        if ratio >= _RIGHTSIZING_THRESHOLD:
            continue
        key = f"{pod.namespace}/{pod.workload or pod.name}"
        if key in seen:
            continue
        seen.add(key)

        name = pod.workload or pod.name
        kind = pod.workload_kind.lower() if pod.workload_kind else "pod"

        recs.append(Recommendation(
            id=_rec_id("rightsizing", pod.namespace, name),
            category=RecommendationCategory.RIGHTSIZING,
            title=f"Low CPU utilization observed: {name}",
            resource_ref=f"{kind}/{name}",
            namespace=pod.namespace,
            monthly_savings=None,
            confidence=0.60,
            risk_level=RiskLevel.LOW,
            priority_score=_priority(0.60, RiskLevel.LOW),
            evidence=(
                f"Observed CPU {pod.cpu_used_m}m of {pod.cpu_request_m}m requested "
                f"({ratio * 100:.0f}%) on pod {pod.name!r}. "
                f"A single snapshot is not a reliable basis for changing resource requests. "
                f"Confirm with historical utilization data before acting."
            ),
            command=None,
            yaml_patch=None,
            rollback=None,
            requires_ai=False,
        ))
    return recs


# ---------------------------------------------------------------------------
# Rule: no HPA observed (informational; no scaling policy prescribed)
# ---------------------------------------------------------------------------

def _hpa_gap_recs(report: CollectorReport) -> list[Recommendation]:
    """
    Report Deployments and StatefulSets that have no HPA.

    Appropriate autoscaling policy depends on traffic variance, workload type,
    and metrics availability. No command or configuration is prescribed.
    """
    hpa_targets: set[str] = {
        f"{h.namespace}/{h.target_name}" for h in report.hpas
    }
    seen: set[str] = set()
    recs = []

    for pod in report.pods:
        if pod.workload_kind.lower() not in ("deployment", "statefulset"):
            continue
        key = f"{pod.namespace}/{pod.workload}"
        if not pod.workload or key in seen or key in hpa_targets:
            continue
        seen.add(key)

        recs.append(Recommendation(
            id=_rec_id("hpa-gap", pod.namespace, pod.workload),
            category=RecommendationCategory.HPA,
            title=f"No HPA observed: {pod.workload}",
            resource_ref=f"{pod.workload_kind.lower()}/{pod.workload}",
            namespace=pod.namespace,
            monthly_savings=None,
            confidence=0.70,
            risk_level=RiskLevel.LOW,
            priority_score=_priority(0.70, RiskLevel.LOW),
            evidence=(
                f"{pod.workload_kind} {pod.workload!r} in namespace {pod.namespace!r} "
                f"has no HorizontalPodAutoscaler. Without autoscaling, replicas are fixed "
                f"regardless of load. Review whether autoscaling is appropriate and what "
                f"metric (CPU, custom, or external) should drive it for this workload."
            ),
            command=None,
            yaml_patch=None,
            rollback=None,
            requires_ai=False,
        ))
    return recs


# ---------------------------------------------------------------------------
# Rule: empty namespace observation (informational; no deletion command)
# ---------------------------------------------------------------------------

def _empty_namespace_recs(report: CollectorReport) -> list[Recommendation]:
    """
    Report namespaces with no running pods.

    Empty pod count does not mean a namespace is safe to delete: it may contain
    PVCs, Secrets, CronJobs, ConfigMaps, or scaled-to-zero workloads. No
    deletion command is emitted.
    """
    recs = []
    for ns in report.namespaces:
        if ns.name in _SYSTEM_NAMESPACES:
            continue
        if ns.pod_count > 0:
            continue
        recs.append(Recommendation(
            id=_rec_id("empty-namespace", ns.name, "namespace"),
            category=RecommendationCategory.IDLE_WORKLOAD,
            title=f"No running pods in namespace: {ns.name}",
            resource_ref=f"namespace/{ns.name}",
            namespace=ns.name,
            monthly_savings=None,
            confidence=0.80,
            risk_level=RiskLevel.LOW,
            priority_score=_priority(0.80, RiskLevel.LOW),
            evidence=(
                f"Namespace {ns.name!r} has no running pods. "
                f"It may still contain PVCs, Secrets, CronJobs, or scaled-to-zero workloads. "
                f"Inspect the namespace contents before considering removal."
            ),
            command=None,
            rollback=None,
            requires_ai=False,
        ))
    return recs


# ---------------------------------------------------------------------------
# Rule: non-Bound PVC observation (informational; no deletion command)
# ---------------------------------------------------------------------------

def _non_bound_pvc_recs(report: CollectorReport) -> list[Recommendation]:
    """
    Report PVCs that are not in Bound phase.

    An unbound PVC may be awaiting dynamic provisioning, misconfigured, or
    orphaned. We cannot distinguish these from a snapshot alone. No deletion
    command or storage cost estimate is emitted.
    """
    recs = []
    for pvc in report.pvcs:
        if pvc.phase == "Bound":
            continue
        recs.append(Recommendation(
            id=_rec_id("non-bound-pvc", pvc.namespace, pvc.name),
            category=RecommendationCategory.STORAGE,
            title=f"PVC not bound: {pvc.name}",
            resource_ref=f"pvc/{pvc.name}",
            namespace=pvc.namespace,
            monthly_savings=None,
            confidence=0.80,
            risk_level=RiskLevel.LOW,
            priority_score=_priority(0.80, RiskLevel.LOW),
            evidence=(
                f"PVC {pvc.name!r} in namespace {pvc.namespace!r} is in phase {pvc.phase!r} "
                f"(capacity: {pvc.capacity_gb:.1f}GB). "
                f"A non-Bound PVC may be awaiting provisioning, have a mismatched StorageClass, "
                f"or be orphaned. Verify before taking action."
            ),
            command=None,
            rollback=None,
            requires_ai=False,
        ))
    return recs


# ---------------------------------------------------------------------------
# Public service class
# ---------------------------------------------------------------------------

class CollectorAnalysisService:
    """
    Derive inventory observations entirely from a CollectorReport.

    All findings are informational. No deletion commands, no savings figures
    without a pricing source, no resource mutations from a single snapshot.

    This class must never import or instantiate any cloud adapter, credential
    manager, or provider API client. Tests enforce this by inspection and by
    exercising the full run() path with a mock-free report.
    """

    def run(
        self,
        report: CollectorReport,
        node_monthly_cost: Optional[float] = None,
    ) -> list[Recommendation]:
        """
        Return observations for a cluster from collector data alone.

        Args:
            report: a CollectorReport (caller must verify freshness before calling)
            node_monthly_cost: reserved for future use; currently unused because no
                               rule in this service can establish realizable savings
                               from a snapshot alone

        Returns:
            List of Recommendation objects sorted by priority_score descending.
            monthly_savings is None on all findings: no pricing source is sufficient
            to attribute savings to any observation made from a single snapshot.
        """
        recs: list[Recommendation] = []
        recs.extend(_rightsizing_recs(report))
        recs.extend(_hpa_gap_recs(report))
        recs.extend(_empty_namespace_recs(report))
        recs.extend(_non_bound_pvc_recs(report))
        # GPU findings are NOT appended here. The GPU evaluator produces deletion
        # commands, fabricated savings, and CPU-based patches; it violates this
        # service's informational-only contract. GPU findings are appended by the
        # API layer via _append_collector_gpu_recommendations after this service runs.

        recs.sort(key=lambda r: (-r.priority_score, r.id))
        return recs
