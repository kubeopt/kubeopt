import hashlib

try:
    from shared.models.recommendation import (
        Recommendation, RiskLevel, RecommendationCategory,
    )
except ModuleNotFoundError:
    from kubeopt.shared.models.recommendation import (  # test runner path
        Recommendation, RiskLevel, RecommendationCategory,
    )

_RISK_WEIGHT = {RiskLevel.LOW: 1.0, RiskLevel.MEDIUM: 0.6, RiskLevel.HIGH: 0.2}


def _rec_id(category: str, kind: str, name: str, ns: str) -> str:
    raw = f"{category}:{kind}/{name}:{ns}"
    return hashlib.sha1(raw.encode(), usedforsecurity=False).hexdigest()[:12]
_NODE_CONFIDENCE_THRESHOLD = 0.80
_RIGHTSIZING_UTILIZATION_THRESHOLD = 0.60  # flag if p95 < 60% of request


def _priority(savings: float, confidence: float, risk: RiskLevel) -> float:
    return round(savings * confidence * _RISK_WEIGHT[risk], 2)


def _rightsizing_recs(analysis_data: dict) -> list[Recommendation]:
    recs = []
    utilization = analysis_data.get("resource_utilization", {})
    for w in utilization.get("workloads", []):
        cpu_req = w.get("cpu_requested_m", 0)
        cpu_p95 = w.get("cpu_p95_m", 0)
        if not cpu_req or not cpu_p95:
            continue
        ratio = cpu_p95 / cpu_req
        if ratio >= _RIGHTSIZING_UTILIZATION_THRESHOLD:
            continue
        # recommended request = p95 * 1.4 headroom, round to nearest 50m
        recommended_m = max(50, round((cpu_p95 * 1.4) / 50) * 50)
        savings = round(w.get("monthly_cost", 0) * (1 - recommended_m / cpu_req), 2)
        name = w["name"]
        ns = w.get("namespace", "default")
        kind = w.get("kind", "Deployment").lower()
        command = (
            f"kubectl set resources {kind}/{name} "
            f"--requests=cpu={recommended_m}m -n {ns}"
        )
        rollback = f"kubectl set resources {kind}/{name} --requests=cpu={cpu_req}m -n {ns}"
        evidence = (
            f"p95 CPU {cpu_p95}m, current request {cpu_req}m "
            f"({round(ratio * 100)}% utilization)"
        )
        recs.append(Recommendation(
            id=_rec_id(RecommendationCategory.RIGHTSIZING, kind, name, ns),
            category=RecommendationCategory.RIGHTSIZING,
            title=f"Reduce CPU request for {name}",
            resource_ref=f"{kind}/{name}",
            namespace=ns,
            monthly_savings=savings,
            confidence=0.85,
            risk_level=RiskLevel.LOW,
            priority_score=_priority(savings, 0.85, RiskLevel.LOW),
            evidence=evidence,
            command=command,
            yaml_patch=f'resources:\n  requests:\n    cpu: "{recommended_m}m"',
            rollback=rollback,
            requires_ai=False,
        ))
    return recs


def _hpa_recs(analysis_data: dict) -> list[Recommendation]:
    recs = []
    for h in analysis_data.get("hpa_recommendations", []):
        name = h.get("workload", "")
        ns = h.get("namespace", "default")
        kind = h.get("kind", "Deployment").lower()
        min_r = h.get("recommended_min", 2)
        max_r = h.get("recommended_max", 10)
        cpu_pct = h.get("cpu_target_percent", 70)
        savings = float(h.get("estimated_savings", 0))
        confidence = float(h.get("confidence", 0.7))
        command = (
            f"kubectl autoscale {kind} {name} "
            f"--cpu-percent={cpu_pct} --min={min_r} --max={max_r} -n {ns}"
        )
        rollback = f"kubectl delete hpa {name} -n {ns}"
        recs.append(Recommendation(
            id=_rec_id(RecommendationCategory.HPA, kind, name, ns),
            category=RecommendationCategory.HPA,
            title=f"Add HPA to {name}",
            resource_ref=f"{kind}/{name}",
            namespace=ns,
            monthly_savings=savings,
            confidence=confidence,
            risk_level=RiskLevel.LOW,
            priority_score=_priority(savings, confidence, RiskLevel.LOW),
            evidence=f"CPU spikes detected; suggest min={min_r} max={max_r} target={cpu_pct}%",
            command=command,
            yaml_patch=None,
            rollback=rollback,
            requires_ai=False,
        ))
    return recs


def _idle_workload_recs(analysis_data: dict) -> list[Recommendation]:
    recs = []
    for insight in analysis_data.get("insights", []):
        if insight.get("type") != "idle_workload":
            continue
        name = insight.get("workload", "")
        ns = insight.get("namespace", "default")
        kind = insight.get("kind", "Deployment").lower()
        idle_days = insight.get("idle_days", 0)
        savings = float(insight.get("estimated_savings", 0))
        confidence = float(insight.get("confidence", 0.6))
        recs.append(Recommendation(
            id=_rec_id(RecommendationCategory.IDLE_WORKLOAD, kind, name, ns),
            category=RecommendationCategory.IDLE_WORKLOAD,
            title=f"Review idle workload: {name}",
            resource_ref=f"{kind}/{name}",
            namespace=ns,
            monthly_savings=savings,
            confidence=confidence,
            risk_level=RiskLevel.MEDIUM,
            priority_score=_priority(savings, confidence, RiskLevel.MEDIUM),
            evidence=f"No traffic for {idle_days} days; verify before scaling down",
            command=None,
            yaml_patch=None,
            rollback=None,
            requires_ai=False,
        ))
    return recs


def _node_pool_recs(analysis_data: dict) -> list[Recommendation]:
    recs = []
    for n in analysis_data.get("node_recommendations", []):
        confidence = float(n.get("confidence", 0))
        if confidence < _NODE_CONFIDENCE_THRESHOLD:
            continue
        pool = n.get("node_pool", "")
        current_vm = n.get("current_vm", "")
        recommended_vm = n.get("recommended_vm", "")
        savings = float(n.get("estimated_savings", 0))
        ns = n.get("namespace", "")  # node pools are cluster-scoped; namespace is not applicable
        recs.append(Recommendation(
            id=_rec_id(RecommendationCategory.NODE_POOL, "nodepool", pool, ns),
            category=RecommendationCategory.NODE_POOL,
            title=f"Review node pool resize: {pool}",
            resource_ref=f"nodepool/{pool}",
            namespace=ns,
            monthly_savings=savings,
            confidence=confidence,
            risk_level=RiskLevel.HIGH,
            priority_score=_priority(savings, confidence, RiskLevel.HIGH),
            evidence=f"Current: {current_vm}, suggested: {recommended_vm}. Validate capacity before changing.",
            command=None,
            yaml_patch=None,
            rollback=None,
            requires_ai=False,
        ))
    return recs


def generate_recommendations(analysis_data: dict) -> list[Recommendation]:
    if not analysis_data:
        return []
    recs: list[Recommendation] = []
    recs.extend(_rightsizing_recs(analysis_data))
    recs.extend(_hpa_recs(analysis_data))
    recs.extend(_idle_workload_recs(analysis_data))
    recs.extend(_node_pool_recs(analysis_data))
    recs.sort(key=lambda r: r.priority_score, reverse=True)
    return recs
