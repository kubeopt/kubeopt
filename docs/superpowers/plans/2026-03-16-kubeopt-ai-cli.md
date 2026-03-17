# KubeOpt AI CLI Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conversational AI agent to KubeOpt — users ask natural language questions, the backend runs an agent loop (Claude API + tools), and streams answers via SSE to the CLI.

**Architecture:** Backend agent loop (`ai_agent.py`) calls Claude API with 8 tools that wrap existing KubeOpt services. A new FastAPI router (`ai.py`) exposes `POST /api/ai/chat` as an SSE stream. The npm CLI detects natural language input and renders the stream in the terminal.

**Tech Stack:** Anthropic Python SDK (server-side), FastAPI SSE streaming, Commander.js CLI with native `fetch` for SSE consumption.

**Spec:** `/Users/srini/coderepos/nivaya/kubeopt/docs/superpowers/specs/2026-03-16-kubeopt-ai-cli-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `infrastructure/services/ai_tools.py` | 8 tool definitions (Claude tool_use schema) + execution functions wrapping existing services |
| `infrastructure/services/ai_model_provider.py` | Model provider abstraction — Claude API today, swappable for own model later |
| `infrastructure/services/ai_agent.py` | Agent loop: builds messages, handles tool_use cycles, model selection, yields SSE events |
| `presentation/api/v2/routers/ai.py` | FastAPI router: `POST /api/ai/chat` SSE endpoint, session management, auth, rate limiting |
| `npm-cli/lib/ai.js` | SSE stream reader, terminal renderer (streaming text, tool indicators, code blocks) |

### Hosting Note

`ANTHROPIC_API_KEY` lives on the **hosted Railway backend** — users never need it. CLI points to `demo.kubeopt.com` by default. Self-hosted enterprise customers provide their own key. Local dev uses `.env`.

### Modified Files

| File | Change |
|------|--------|
| `fastapi_app.py:198-216` | Add `from presentation.api.v2.routers import ai` and `app.include_router(ai.router)` |
| `requirements/requirements.txt:73` | Add `anthropic>=0.40.0` |
| `npm-cli/bin/kubeopt.js` | Add NL detection before `program.parse()`, add `chat` command |
| `npm-cli/package.json` | Version bump to 2.0.0 |

All paths relative to `/Users/srini/coderepos/nivaya/kubeopt/` (backend) or `/Users/srini/coderepos/nivaya/kubeopt-distribution/` (CLI).

---

## Chunk 1: Backend — Tools & Agent

### Task 1: Tool Definitions (`ai_tools.py`)

**Files:**
- Create: `infrastructure/services/ai_tools.py`

This file has two parts: (A) tool schemas in Claude's `tools` format, and (B) an `execute_tool()` dispatcher that calls existing services.

- [ ] **Step 1: Create tool schemas**

Create `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/services/ai_tools.py` with the 8 tool definitions as a `TOOLS` list (Claude API `tools` parameter format). Each tool has `name`, `description`, `input_schema` (JSON Schema).

```python
"""
AI Agent tools — wraps existing KubeOpt services for Claude tool_use.
"""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------- Tool Schemas (Claude API format) ----------

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "query_cluster_data",
        "description": "Get cluster overview: total cost, utilization, optimization score, anomaly count, node/pod counts. Always call this first to understand the cluster.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string", "description": "Cluster identifier (e.g. 'mygroup_mycluster')"}
            },
            "required": ["cluster_id"],
        },
    },
    {
        "name": "get_pod_costs",
        "description": "Get per-workload cost breakdown. Optionally filter by namespace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string"},
                "namespace": {"type": "string", "description": "Filter by namespace (optional)"},
            },
            "required": ["cluster_id"],
        },
    },
    {
        "name": "get_recommendations",
        "description": "Get optimization recommendations: node rightsizing, HPA tuning, storage cleanup, with per-item savings estimates. Optionally filter by category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": ["node", "hpa", "storage", "cost", "performance"],
                    "description": "Filter by recommendation category (optional)",
                },
            },
            "required": ["cluster_id"],
        },
    },
    {
        "name": "run_kubectl",
        "description": "Execute a read-only kubectl command against the cluster. Only get, describe, top, and logs are allowed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string"},
                "command": {
                    "type": "string",
                    "description": "kubectl command (e.g. 'kubectl get pods -n default -o wide')",
                },
            },
            "required": ["cluster_id", "command"],
        },
    },
    {
        "name": "compare_clusters",
        "description": "Compare two or more clusters side-by-side on cost, utilization, and scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of cluster IDs to compare",
                },
            },
            "required": ["cluster_ids"],
        },
    },
    {
        "name": "get_pricing",
        "description": "Look up VM/instance pricing for a cloud provider and region.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cloud_provider": {"type": "string", "enum": ["azure", "aws", "gcp"]},
                "region": {"type": "string"},
                "instance_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "VM size names (e.g. ['Standard_D2s_v3', 'Standard_D4s_v3'])",
                },
            },
            "required": ["cloud_provider", "region", "instance_types"],
        },
    },
    {
        "name": "generate_manifest",
        "description": "Generate fix manifests (YAML/Terraform) based on analysis recommendations. Returns file content the user can apply or PR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string"},
                "fix_type": {
                    "type": "string",
                    "enum": ["rightsizing", "hpa", "node_pool", "storage", "governance"],
                },
                "target": {
                    "type": "string",
                    "description": "Target resource (e.g. namespace, deployment name, node pool name)",
                },
            },
            "required": ["cluster_id", "fix_type"],
        },
    },
    {
        "name": "create_pr",
        "description": "Open a GitHub PR with generated fix files. Requires user confirmation in CLI before executing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "GitHub repo URL (e.g. 'https://github.com/org/infra-repo')"},
                "branch": {"type": "string", "description": "Branch name for the PR"},
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                    },
                    "description": "Files to include in the PR",
                },
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["repo_url", "branch", "files", "title", "description"],
        },
    },
]
```

- [ ] **Step 2: Implement helper — load analysis data**

Add a private helper that loads analysis data using the existing `_get_analysis_data` function. This is shared by multiple tools.

```python
# ---------- Helpers ----------

def _load_analysis(cluster_id: str) -> Dict[str, Any]:
    """Load analysis data for a cluster. Raises ValueError if not found."""
    from shared.utils.shared import _get_analysis_data
    data, source = _get_analysis_data(cluster_id)
    if not data:
        raise ValueError(f"No analysis data for cluster '{cluster_id}'. Run an analysis first.")
    return data
```

- [ ] **Step 3: Implement query_cluster_data**

```python
def _exec_query_cluster_data(cluster_id: str, **_) -> Dict[str, Any]:
    data = _load_analysis(cluster_id)
    return {
        "cluster_id": cluster_id,
        "total_monthly_cost": round(data.get("total_cost", 0), 2),
        "total_monthly_savings": round(data.get("total_savings", 0), 2),
        "optimization_score": data.get("confidence_score", 0),
        "node_count": data.get("node_count", 0),
        "pod_count": data.get("pod_count", 0),
        "cpu_utilization_pct": round(data.get("avg_cpu", 0), 1),
        "memory_utilization_pct": round(data.get("avg_memory", 0), 1),
        "anomaly_count": len(data.get("anomalies", [])),
        "cloud_provider": data.get("cloud_provider", "unknown"),
        "last_analyzed": data.get("analysis_timestamp", "unknown"),
    }
```

- [ ] **Step 4: Implement get_pod_costs**

```python
def _exec_get_pod_costs(cluster_id: str, namespace: str = None, **_) -> Dict[str, Any]:
    data = _load_analysis(cluster_id)
    pods = data.get("pod_data", [])
    if not pods:
        # Try workload_costs from chart generator
        from presentation.api import chart_generator
        pods = chart_generator.generate_workload_data(data) or []
    if namespace:
        pods = [p for p in pods if p.get("namespace") == namespace]
    # Sort by cost descending, limit to top 30
    pods = sorted(pods, key=lambda p: p.get("cost", p.get("monthly_cost", 0)), reverse=True)[:30]
    return {"cluster_id": cluster_id, "namespace_filter": namespace, "workloads": pods, "count": len(pods)}
```

- [ ] **Step 5: Implement get_recommendations**

```python
def _exec_get_recommendations(cluster_id: str, category: str = None, **_) -> Dict[str, Any]:
    data = _load_analysis(cluster_id)
    eai = data.get("enhanced_analysis_input", {})
    result = {}

    # Node recommendations
    if not category or category == "node":
        node_recs = eai.get("node_recommendations", [])
        if not node_recs:
            node_recs = eai.get("node_analysis", {}).get("recommendations", [])
        result["node_recommendations"] = node_recs[:20]

    # HPA recommendations
    if not category or category == "hpa":
        result["hpa_recommendations"] = eai.get("hpa_recommendations", [])[:20]

    # Storage recommendations
    if not category or category == "storage":
        result["storage_recommendations"] = eai.get("storage_recommendations", [])[:20]

    # Cost recommendations
    if not category or category == "cost":
        result["cost_recommendations"] = eai.get("cost_analysis", {}).get("recommendations", [])[:20]

    # Savings summary
    from presentation.api import chart_generator
    savings = chart_generator.extract_standards_based_savings(data)
    if savings:
        result["savings_summary"] = {k: round(float(v), 2) if isinstance(v, (int, float)) else v for k, v in savings.items()}

    return {"cluster_id": cluster_id, "category_filter": category, **result}
```

- [ ] **Step 6: Implement run_kubectl (read-only guard)**

```python
_KUBECTL_ALLOWED = {"get", "describe", "top", "logs", "version", "api-resources", "api-versions"}
_KUBECTL_BLOCKED = {"apply", "delete", "patch", "edit", "create", "replace", "scale", "rollout", "cordon", "drain", "taint", "label", "annotate", "exec", "run", "expose", "set"}

def _exec_run_kubectl(cluster_id: str, command: str, **_) -> Dict[str, Any]:
    # Parse kubectl subcommand
    parts = command.strip().split()
    if parts and parts[0] == "kubectl":
        parts = parts[1:]
    if not parts:
        return {"error": "Empty kubectl command"}

    verb = parts[0].lower()
    if verb in _KUBECTL_BLOCKED:
        return {"error": f"Blocked: '{verb}' is a mutating command. Only read-only commands allowed: {', '.join(sorted(_KUBECTL_ALLOWED))}"}
    if verb not in _KUBECTL_ALLOWED:
        return {"error": f"Unknown kubectl verb '{verb}'. Allowed: {', '.join(sorted(_KUBECTL_ALLOWED))}"}

    # Reconstruct as full kubectl command
    full_cmd = "kubectl " + " ".join(parts)

    # Execute via cloud provider
    from presentation.api.v2.services import get_container
    container = get_container()
    cluster_info = container.cluster_manager.get_cluster(cluster_id)
    if not cluster_info:
        return {"error": f"Cluster '{cluster_id}' not found"}

    cloud_provider = cluster_info.get("cloud_provider", "azure")
    try:
        from infrastructure.cloud_providers.types import ClusterIdentifier, CloudProvider
        cluster_ident = ClusterIdentifier(
            provider=CloudProvider.from_string(cloud_provider),
            cluster_name=cluster_info.get("cluster_name", cluster_id.split("_")[-1]),
            region=cluster_info.get("region", ""),
            resource_group=cluster_info.get("resource_group"),
            subscription_id=cluster_info.get("subscription_id"),
            account_id=cluster_info.get("account_id"),
            project_id=cluster_info.get("project_id"),
        )
        executor = container.provider_registry.get_executor()
        output = executor.execute_kubectl(cluster_ident, full_cmd, timeout=30)
        if output is None:
            return {"error": "kubectl command returned no output or timed out"}
        # Truncate large output
        if len(output) > 8000:
            output = output[:8000] + "\n... (truncated, output too large)"
        return {"command": full_cmd, "output": output}
    except Exception as e:
        return {"error": f"kubectl execution failed: {str(e)}"}
```

- [ ] **Step 7: Implement compare_clusters**

```python
def _exec_compare_clusters(cluster_ids: list, **_) -> Dict[str, Any]:
    comparisons = []
    for cid in cluster_ids[:5]:  # Max 5
        try:
            comparisons.append(_exec_query_cluster_data(cid))
        except ValueError as e:
            comparisons.append({"cluster_id": cid, "error": str(e)})
    return {"clusters": comparisons}
```

- [ ] **Step 8: Implement get_pricing**

```python
def _exec_get_pricing(cloud_provider: str, region: str, instance_types: list, **_) -> Dict[str, Any]:
    from infrastructure.services.vm_pricing_service import VMPricingService
    service = VMPricingService()
    results = []
    for vm_size in instance_types[:10]:  # Max 10
        price_info = service.get_vm_price(region=region, sku_name=vm_size)
        if price_info and isinstance(price_info, dict):
            results.append({"instance_type": vm_size, **price_info})
        elif price_info is not None:
            results.append({"instance_type": vm_size, "monthly_cost": price_info})
        else:
            results.append({"instance_type": vm_size, "error": "Pricing not available"})
    return {"cloud_provider": cloud_provider, "region": region, "pricing": results}
```

- [ ] **Step 9: Implement generate_manifest (stub — generates from recommendations)**

```python
def _exec_generate_manifest(cluster_id: str, fix_type: str, target: str = None, **_) -> Dict[str, Any]:
    data = _load_analysis(cluster_id)
    eai = data.get("enhanced_analysis_input", {})

    if fix_type == "rightsizing":
        return _generate_rightsizing_manifest(eai, target)
    elif fix_type == "hpa":
        return _generate_hpa_manifest(eai, target)
    elif fix_type == "node_pool":
        return _generate_node_pool_manifest(eai, data, target)
    elif fix_type == "storage":
        return _generate_storage_manifest(eai, target)
    elif fix_type == "governance":
        return _generate_governance_manifest(eai, target)
    else:
        return {"error": f"Unknown fix_type: {fix_type}"}


def _generate_rightsizing_manifest(eai: dict, target: str = None) -> dict:
    """Generate patched Deployment YAMLs with adjusted resource requests/limits."""
    recs = eai.get("node_recommendations", [])
    if target:
        recs = [r for r in recs if target.lower() in r.get("name", "").lower() or target.lower() in r.get("deployment", "").lower()]
    if not recs:
        return {"error": f"No rightsizing recommendations found{' for ' + target if target else ''}"}

    manifests = []
    for rec in recs[:5]:
        name = rec.get("deployment", rec.get("name", "unknown"))
        namespace = rec.get("namespace", "default")
        cpu_req = rec.get("recommended_cpu", rec.get("target_cpu", "250m"))
        mem_req = rec.get("recommended_memory", rec.get("target_memory", "256Mi"))
        manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
spec:
  template:
    spec:
      containers:
      - name: {name}
        resources:
          requests:
            cpu: "{cpu_req}"
            memory: "{mem_req}"
          limits:
            cpu: "{cpu_req}"
            memory: "{mem_req}"
"""
        manifests.append({"path": f"{namespace}/{name}-resources.yaml", "content": manifest, "savings": rec.get("monthly_savings", 0)})
    return {"fix_type": "rightsizing", "manifests": manifests}


def _generate_hpa_manifest(eai: dict, target: str = None) -> dict:
    """Generate HPA manifests with recommended min/max replicas."""
    recs = eai.get("hpa_recommendations", [])
    if target:
        recs = [r for r in recs if target.lower() in r.get("name", "").lower()]
    if not recs:
        return {"error": f"No HPA recommendations found{' for ' + target if target else ''}"}

    manifests = []
    for rec in recs[:5]:
        name = rec.get("name", "unknown")
        namespace = rec.get("namespace", "default")
        min_rep = rec.get("recommended_min_replicas", rec.get("min_replicas", 2))
        max_rep = rec.get("recommended_max_replicas", rec.get("max_replicas", 10))
        target_cpu = rec.get("recommended_cpu_target", rec.get("target_cpu_utilization", 70))
        manifest = f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {name}
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {name}
  minReplicas: {min_rep}
  maxReplicas: {max_rep}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {target_cpu}
"""
        manifests.append({"path": f"{namespace}/{name}-hpa.yaml", "content": manifest, "savings": rec.get("monthly_savings", 0)})
    return {"fix_type": "hpa", "manifests": manifests}


def _generate_node_pool_manifest(eai: dict, data: dict, target: str = None) -> dict:
    """Generate Terraform for node pool VM size change."""
    recs = eai.get("node_recommendations", [])
    if target:
        recs = [r for r in recs if target.lower() in r.get("node_pool", r.get("name", "")).lower()]
    if not recs:
        return {"error": f"No node pool recommendations found{' for ' + target if target else ''}"}

    cloud = data.get("cloud_provider", "azure")
    manifests = []
    for rec in recs[:3]:
        pool = rec.get("node_pool", rec.get("name", "default"))
        current_vm = rec.get("current_vm_size", "unknown")
        recommended_vm = rec.get("recommended_vm_size", "unknown")

        if cloud == "azure":
            tf = f"""resource "azurerm_kubernetes_cluster_node_pool" "{pool}" {{
  # Changed from {current_vm} to {recommended_vm}
  vm_size = "{recommended_vm}"
}}
"""
        elif cloud == "aws":
            tf = f"""resource "aws_eks_node_group" "{pool}" {{
  # Changed from {current_vm} to {recommended_vm}
  instance_types = ["{recommended_vm}"]
}}
"""
        else:
            tf = f"""resource "google_container_node_pool" "{pool}" {{
  node_config {{
    # Changed from {current_vm} to {recommended_vm}
    machine_type = "{recommended_vm}"
  }}
}}
"""
        manifests.append({"path": f"node-pools/{pool}.tf", "content": tf, "savings": rec.get("monthly_savings", 0)})
    return {"fix_type": "node_pool", "manifests": manifests}


def _generate_storage_manifest(eai: dict, target: str = None) -> dict:
    recs = eai.get("storage_recommendations", [])
    if target:
        recs = [r for r in recs if target.lower() in r.get("name", "").lower()]
    if not recs:
        return {"error": f"No storage recommendations found{' for ' + target if target else ''}"}
    return {"fix_type": "storage", "recommendations": recs[:10], "note": "Storage fixes are cluster-specific. Review recommendations and apply manually or generate PVC patches."}


def _generate_governance_manifest(eai: dict, target: str = None) -> dict:
    namespace = target or "default"
    quota = f"""apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: {namespace}
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
"""
    limit_range = f"""apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: {namespace}
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
"""
    return {
        "fix_type": "governance",
        "manifests": [
            {"path": f"{namespace}/resource-quota.yaml", "content": quota},
            {"path": f"{namespace}/limit-range.yaml", "content": limit_range},
        ],
    }
```

- [ ] **Step 10: Implement create_pr**

```python
def _exec_create_pr(repo_url: str, branch: str, files: list, title: str, description: str, **_) -> Dict[str, Any]:
    """Create a GitHub PR. This is called only after user confirms in CLI."""
    import subprocess
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Shallow clone
            subprocess.run(["git", "clone", "--depth", "1", repo_url, tmpdir], check=True, capture_output=True, timeout=30)
            # Create branch
            subprocess.run(["git", "checkout", "-b", branch], cwd=tmpdir, check=True, capture_output=True)
            # Write files
            for f in files:
                fpath = os.path.join(tmpdir, f["path"])
                os.makedirs(os.path.dirname(fpath), exist_ok=True)
                with open(fpath, "w") as fh:
                    fh.write(f["content"])
            # Commit
            subprocess.run(["git", "add", "-A"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", title], cwd=tmpdir, check=True, capture_output=True)
            # Push
            subprocess.run(["git", "push", "-u", "origin", branch], cwd=tmpdir, check=True, capture_output=True, timeout=30)
            # Create PR via gh CLI
            result = subprocess.run(
                ["gh", "pr", "create", "--title", title, "--body", description, "--head", branch],
                cwd=tmpdir, capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                return {"pr_url": pr_url, "branch": branch, "files_changed": len(files)}
            else:
                return {"error": f"PR creation failed: {result.stderr.strip()}"}
        except subprocess.TimeoutExpired:
            return {"error": "Git operation timed out"}
        except Exception as e:
            return {"error": f"PR creation failed: {str(e)}"}
```

- [ ] **Step 11: Add tool dispatcher**

```python
# ---------- Dispatcher ----------

_TOOL_REGISTRY = {
    "query_cluster_data": _exec_query_cluster_data,
    "get_pod_costs": _exec_get_pod_costs,
    "get_recommendations": _exec_get_recommendations,
    "run_kubectl": _exec_run_kubectl,
    "compare_clusters": _exec_compare_clusters,
    "get_pricing": _exec_get_pricing,
    "generate_manifest": _exec_generate_manifest,
    "create_pr": _exec_create_pr,
}

# Tools that need user confirmation before execution
CONFIRMATION_REQUIRED = {"create_pr"}


def execute_tool(name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool by name. Returns result dict or error dict."""
    fn = _TOOL_REGISTRY.get(name)
    if not fn:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(**input_data)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return {"error": f"Tool execution failed: {str(e)}"}
```

- [ ] **Step 12: Verify syntax**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && .venv/bin/python -c "import py_compile; py_compile.compile('infrastructure/services/ai_tools.py', doraise=True)"`

Expected: No output (success)

- [ ] **Step 13: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/services/ai_tools.py
git commit -m "feat(ai-cli): add 8 tool definitions and implementations for AI agent"
```

---

### Task 2: Model Provider Abstraction (`ai_model_provider.py`)

**Files:**
- Create: `infrastructure/services/ai_model_provider.py`

This is the abstraction that makes the Claude→own-model swap possible later. The agent never calls the Anthropic SDK directly — it goes through this provider.

- [ ] **Step 1: Create model provider**

Create `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/services/ai_model_provider.py`:

```python
"""
Model Provider — abstraction over LLM APIs for the AI agent.

v1: Claude API via Anthropic SDK.
Future: swap for fine-tuned KubeOpt model, local model, or any API-compatible provider.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ModelResponse:
    """Standardized response from any model provider."""

    def __init__(self, content_blocks: List[Dict[str, Any]], stop_reason: str):
        self.content_blocks = content_blocks  # [{"type": "text", "text": "..."}, {"type": "tool_use", "id": "...", "name": "...", "input": {...}}]
        self.stop_reason = stop_reason  # "end_turn", "tool_use", etc.

    @property
    def has_tool_use(self) -> bool:
        return any(b["type"] == "tool_use" for b in self.content_blocks)

    @property
    def text_parts(self) -> List[str]:
        return [b["text"] for b in self.content_blocks if b["type"] == "text"]

    @property
    def tool_use_blocks(self) -> List[Dict[str, Any]]:
        return [b for b in self.content_blocks if b["type"] == "tool_use"]


class ModelProvider(ABC):
    """Abstract base for model providers."""

    @abstractmethod
    async def create_message(
        self,
        model: str,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 4096,
    ) -> ModelResponse:
        """Send messages to the model and get a response."""
        ...


class ClaudeProvider(ModelProvider):
    """Anthropic Claude API provider."""

    def __init__(self):
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable required for AI CLI")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def create_message(
        self,
        model: str,
        system: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 4096,
    ) -> ModelResponse:
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
        )
        # Convert Anthropic SDK objects to plain dicts
        content_blocks = []
        for block in response.content:
            if block.type == "text":
                content_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content_blocks.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
        return ModelResponse(content_blocks=content_blocks, stop_reason=response.stop_reason)


def get_model_provider() -> ModelProvider:
    """Factory — returns the configured model provider. Swap this for own model later."""
    provider_type = os.getenv("AI_PROVIDER", "claude")
    if provider_type == "claude":
        return ClaudeProvider()
    # Future: elif provider_type == "kubeopt": return KubeOptModelProvider()
    raise ValueError(f"Unknown AI provider: {provider_type}")
```

- [ ] **Step 2: Verify syntax**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && .venv/bin/python -c "import py_compile; py_compile.compile('infrastructure/services/ai_model_provider.py', doraise=True)"`

Expected: No output (success)

- [ ] **Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/services/ai_model_provider.py
git commit -m "feat(ai-cli): add model provider abstraction for swappable LLM backend"
```

---

### Task 3: Agent Loop (`ai_agent.py`)

**Files:**
- Create: `infrastructure/services/ai_agent.py`

The agent loop: takes a user message + conversation history, calls Claude API with tools, loops on tool_use blocks, and yields SSE events.

- [ ] **Step 1: Create agent with model selection and system prompt**

Create `/Users/srini/coderepos/nivaya/kubeopt/infrastructure/services/ai_agent.py`:

```python
"""
AI Agent — runs LLM with tool_use for conversational Kubernetes optimization.

Flow: user message → model provider → tool_use? → execute → tool_result → repeat → text response
Yields SSE events: {"type": "tool_start"|"tool_result"|"text_delta"|"done"|"error", ...}

Uses ModelProvider abstraction — currently Claude API, swappable for own model later.
"""

import os
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from infrastructure.services.ai_tools import TOOLS, execute_tool, CONFIRMATION_REQUIRED
from infrastructure.services.ai_model_provider import get_model_provider, ModelProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are KubeOpt AI, a Kubernetes cost optimization expert. You have \
access to real cluster data through tools. Always use tools to get actual data before \
answering — never guess or use hypothetical numbers.

When recommending changes, be specific: name the workload, the current value, what to \
change it to, and how much it saves. When generating fixes, produce production-ready \
YAML/Terraform that the user can apply directly.

You are talking to a Kubernetes operator. Be concise, technical, and actionable. Skip \
explanations they already know."""

# Simple heuristic: if query mentions generation/fix keywords, use Sonnet
_SONNET_KEYWORDS = {"fix", "generate", "pr", "create", "manifest", "terraform", "yaml", "patch", "open a pr", "apply"}


def _select_model(message: str) -> str:
    """Auto-select model based on query complexity."""
    lower = message.lower()
    model_override = os.getenv("AI_MODEL")
    if model_override:
        return model_override
    for kw in _SONNET_KEYWORDS:
        if kw in lower:
            return "claude-sonnet-4-6"
    return "claude-haiku-4-5-20251001"


class AIAgent:
    """Stateless agent — each call gets full conversation history."""

    def __init__(self):
        self.provider: ModelProvider = get_model_provider()

    async def run(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]],
        cluster_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the agent loop. Yields SSE event dicts:
          {"type": "text_delta", "text": "..."}
          {"type": "tool_start", "tool": "name", "input": {...}}
          {"type": "tool_result", "tool": "name", "result": {...}}
          {"type": "confirmation_required", "tool": "name", "input": {...}}
          {"type": "done"}
          {"type": "error", "message": "..."}

        Also returns the final messages list (for session history) via the
        last yielded event: {"type": "done", "messages": [...]}
        """
        model = _select_model(message)
        logger.info(f"AI agent: model={model}, cluster={cluster_id}, msg_len={len(message)}")

        # Build messages: history + new user message
        messages = list(conversation_history)
        # Inject cluster_id context if provided
        user_content = message
        if cluster_id:
            user_content = f"[Active cluster: {cluster_id}]\n\n{message}"
        messages.append({"role": "user", "content": user_content})

        max_turns = 10  # Safety: max tool_use loop iterations

        try:
            for turn in range(max_turns):
                # Call model provider (async — does not block event loop)
                response = await self.provider.create_message(
                    model=model,
                    system=SYSTEM_PROMPT,
                    messages=messages,
                    tools=TOOLS,
                )

                # Process content blocks (already plain dicts from ModelResponse)
                tool_results_for_next = []
                text_parts = []

                for block in response.content_blocks:
                    if block["type"] == "text":
                        text_parts.append(block["text"])
                    elif block["type"] == "tool_use":
                        tool_name = block["name"]
                        tool_input = block["input"]

                        # Check if tool needs user confirmation
                        if tool_name in CONFIRMATION_REQUIRED:
                            yield {"type": "confirmation_required", "tool": tool_name, "input": tool_input, "tool_use_id": block["id"]}
                            yield {"type": "done"}
                            return

                        yield {"type": "tool_start", "tool": tool_name, "input": tool_input}

                        # Execute tool
                        result = execute_tool(tool_name, tool_input)
                        yield {"type": "tool_result", "tool": tool_name, "result": result}

                        tool_results_for_next.append({
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": json.dumps(result),
                        })

                # Yield text parts
                for text in text_parts:
                    yield {"type": "text_delta", "text": text}

                if not response.has_tool_use:
                    break

                # Append assistant response + tool results for next turn
                # content_blocks are already serializable dicts
                messages.append({"role": "assistant", "content": response.content_blocks})
                messages.append({"role": "user", "content": tool_results_for_next})

            # Return final messages for session history (includes full tool exchanges)
            yield {"type": "done", "messages": messages}

        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            yield {"type": "error", "message": f"AI service error: {str(e)}"}
```

- [ ] **Step 2: Verify syntax**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && .venv/bin/python -c "import py_compile; py_compile.compile('infrastructure/services/ai_agent.py', doraise=True)"`

Expected: No output (success)

- [ ] **Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/services/ai_agent.py
git commit -m "feat(ai-cli): add AI agent loop with Claude API and tool_use handling"
```

---

### Task 4: FastAPI Router (`ai.py`)

**Files:**
- Create: `presentation/api/v2/routers/ai.py`
- Modify: `fastapi_app.py:198-216`
- Modify: `requirements/requirements.txt`

The SSE endpoint that ties it all together: auth, sessions, rate limiting, and streaming.

- [ ] **Step 1: Add anthropic to requirements**

Append to `/Users/srini/coderepos/nivaya/kubeopt/requirements/requirements.txt`:

```
# AI CLI (Claude API for conversational agent)
anthropic>=0.40.0
```

- [ ] **Step 2: Install anthropic**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && .venv/bin/pip install "anthropic>=0.40.0"`

- [ ] **Step 3: Create the router**

Create `/Users/srini/coderepos/nivaya/kubeopt/presentation/api/v2/routers/ai.py`:

```python
"""
AI Chat router — conversational Kubernetes optimization via Claude agent loop.

POST /api/ai/chat  →  SSE stream of agent events
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import get_cluster_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

# ---------- Session store (in-memory, TTL 30 min) ----------

_sessions: Dict[str, Dict[str, Any]] = {}
_SESSION_TTL = 30 * 60  # 30 minutes


class ChatRequest(BaseModel):
    message: str
    cluster_id: Optional[str] = None
    session_id: Optional[str] = None


def _get_or_create_session(session_id: Optional[str], cluster_id: Optional[str]) -> tuple:
    """Get existing session or create new one. Returns (session_id, session_dict)."""
    now = time.time()

    # Cleanup expired sessions (lazy)
    expired = [k for k, v in _sessions.items() if now - v["last_active"] > _SESSION_TTL]
    for k in expired:
        del _sessions[k]

    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        # Reset if different cluster
        if cluster_id and session["cluster_id"] != cluster_id:
            session["history"] = []
            session["cluster_id"] = cluster_id
        session["last_active"] = now
        return session_id, session

    # New session
    new_id = str(uuid.uuid4())
    session = {
        "cluster_id": cluster_id,
        "history": [],
        "last_active": now,
    }
    _sessions[new_id] = session
    return new_id, session


def _auto_detect_cluster(cluster_manager) -> Optional[str]:
    """Auto-detect cluster: only one registered → use it."""
    try:
        clusters = cluster_manager.get_all_clusters()
        if clusters and len(clusters) == 1:
            return clusters[0].get("cluster_id", clusters[0].get("id"))
    except Exception:
        pass
    return None


# ---------- Rate limiting (per-user, in-memory) ----------

_rate_limits: Dict[str, list] = {}  # user -> list of timestamps

_TIER_LIMITS = {
    "free": 5,
    "pro": 50,
    "enterprise": 10000,
    "admin": 10000,
}


def _check_rate_limit(user: dict) -> None:
    """Raise 429 if user exceeded daily AI query limit."""
    role = user.get("role", "free")
    limit = _TIER_LIMITS.get(role, _TIER_LIMITS["free"])
    user_key = user.get("sub", "unknown")
    now = time.time()
    day_ago = now - 86400

    if user_key not in _rate_limits:
        _rate_limits[user_key] = []

    # Prune old entries
    _rate_limits[user_key] = [t for t in _rate_limits[user_key] if t > day_ago]

    if len(_rate_limits[user_key]) >= limit:
        raise HTTPException(status_code=429, detail=f"AI query limit reached ({limit}/day for {role} tier)")

    _rate_limits[user_key].append(now)


# ---------- Endpoint ----------

@router.post("/chat")
async def ai_chat(
    req: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """
    Conversational AI chat endpoint. Returns SSE stream.

    Events:
      data: {"type": "session", "session_id": "..."}
      data: {"type": "tool_start", "tool": "...", "input": {...}}
      data: {"type": "tool_result", "tool": "...", "result": {...}}
      data: {"type": "text_delta", "text": "..."}
      data: {"type": "confirmation_required", "tool": "...", "input": {...}}
      data: {"type": "done"}
      data: {"type": "error", "message": "..."}
    """
    _check_rate_limit(user)

    # Resolve cluster
    cluster_id = req.cluster_id
    if not cluster_id:
        cluster_id = _auto_detect_cluster(cluster_manager)
    if not cluster_id:
        raise HTTPException(status_code=400, detail="cluster_id required. Pass it in the request or register a cluster first.")

    # Verify cluster exists
    cluster_info = cluster_manager.get_cluster(cluster_id)
    if not cluster_info:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found")

    # Session
    session_id, session = _get_or_create_session(req.session_id, cluster_id)

    async def event_stream():
        try:
            from infrastructure.services.ai_agent import AIAgent
            try:
                agent = AIAgent()
            except (RuntimeError, ValueError) as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'AI features not configured: {e}'})}\n\n"
                return

            # Emit session_id first
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

            async for event in agent.run(
                message=req.message,
                conversation_history=session["history"],
                cluster_id=cluster_id,
            ):
                # Send event to client (strip internal "messages" from done event)
                client_event = {k: v for k, v in event.items() if k != "messages"}
                yield f"data: {json.dumps(client_event)}\n\n"

                # When done, update session history with full message list
                # (includes tool_use/tool_result exchanges for multi-turn context)
                if event.get("type") == "done" and "messages" in event:
                    session["history"] = event["messages"]
                    # Keep bounded (last 20 messages)
                    if len(session["history"]) > 20:
                        session["history"] = session["history"][-20:]

        except Exception as e:
            logger.error(f"AI chat error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 4: Register router in fastapi_app.py**

In `/Users/srini/coderepos/nivaya/kubeopt/fastapi_app.py`, add to the import block (line ~198-202):

Change:
```python
    from presentation.api.v2.routers import (
        health, auth, clusters, analysis, plans,
        kubernetes, settings, subscriptions, scheduler, alerts,
        project_controls, legacy,
    )
```
To:
```python
    from presentation.api.v2.routers import (
        health, auth, clusters, analysis, plans,
        kubernetes, settings, subscriptions, scheduler, alerts,
        project_controls, legacy, ai,
    )
```

And add after line 216 (`app.include_router(legacy.router)`):
```python
    app.include_router(ai.router)
```

- [ ] **Step 5: Verify syntax**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && .venv/bin/python -c "import py_compile; py_compile.compile('presentation/api/v2/routers/ai.py', doraise=True)"`

Expected: No output (success)

- [ ] **Step 6: Verify app starts**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && LOCAL_DEV=true .venv/bin/python -c "from fastapi_app import create_app; app = create_app(); print('Router registered:', any(r.path == '/api/ai/chat' for r in app.routes))"`

Expected: `Router registered: True`

- [ ] **Step 7: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
git add infrastructure/services/ai_agent.py infrastructure/services/ai_tools.py presentation/api/v2/routers/ai.py fastapi_app.py requirements/requirements.txt
git commit -m "feat(ai-cli): add AI chat endpoint with SSE streaming, agent loop, and 8 tools"
```

---

## Chunk 2: CLI — AI Query & Chat

### Task 5: CLI AI Module (`lib/ai.js`)

**Files:**
- Create: `/Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/lib/ai.js`

SSE stream reader and terminal renderer for AI responses.

- [ ] **Step 1: Create ai.js**

Create `/Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/lib/ai.js`:

```javascript
/**
 * AI Chat — SSE stream reader and terminal renderer for KubeOpt AI CLI.
 */

import chalk from 'chalk';

/**
 * Send a chat message and stream the response to the terminal.
 * @param {import('./api-client.js').KubeOptAPI} api - Authenticated API client
 * @param {string} clusterId - Cluster to query
 * @param {string} message - User's question
 * @param {string|null} sessionId - Conversation session ID (null for new)
 * @returns {Promise<string>} session_id for follow-up messages
 */
export async function streamChat(api, clusterId, message, sessionId = null) {
  const url = new URL('/api/ai/chat', api.baseUrl);
  const token = await api.getToken();

  const body = JSON.stringify({
    message,
    cluster_id: clusterId,
    session_id: sessionId,
  });

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body,
  });

  if (!response.ok) {
    const err = await response.text();
    let detail;
    try { detail = JSON.parse(err).detail; } catch { detail = err; }
    throw new Error(`AI chat failed (${response.status}): ${detail}`);
  }

  let returnSessionId = sessionId;
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop(); // Keep incomplete line in buffer

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const jsonStr = line.slice(6).trim();
      if (!jsonStr) continue;

      let event;
      try { event = JSON.parse(jsonStr); } catch { continue; }

      switch (event.type) {
        case 'session':
          returnSessionId = event.session_id;
          break;

        case 'tool_start':
          process.stdout.write(chalk.dim(`  Querying ${event.tool}...`));
          break;

        case 'tool_result':
          // Clear the "Querying..." line and show brief result
          process.stdout.write('\r' + ' '.repeat(60) + '\r');
          if (event.result?.error) {
            console.log(chalk.yellow(`  Tool ${event.tool}: ${event.result.error}`));
          }
          break;

        case 'text_delta':
          process.stdout.write(event.text);
          break;

        case 'confirmation_required':
          console.log('');
          console.log(chalk.yellow.bold('Confirmation required:'));
          console.log(chalk.yellow(`  Tool: ${event.tool}`));
          console.log(chalk.yellow(`  Input: ${JSON.stringify(event.input, null, 2)}`));
          console.log(chalk.dim('  (Re-run with --confirm to execute)'));
          break;

        case 'error':
          console.log('');
          console.error(chalk.red(`Error: ${event.message}`));
          break;

        case 'done':
          break;
      }
    }
  }

  // Ensure newline after streaming text
  console.log('');
  return returnSessionId;
}

/**
 * Interactive chat REPL.
 */
export async function interactiveChat(api, clusterId) {
  const readline = await import('node:readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  console.log(chalk.cyan.bold('KubeOpt AI Chat'));
  console.log(chalk.dim(`Cluster: ${clusterId}`));
  console.log(chalk.dim('Type /exit to quit, /clear to reset, /cluster <id> to switch\n'));

  let sessionId = null;
  let currentCluster = clusterId;

  const prompt = () => {
    rl.question(chalk.green('kubeopt> '), async (input) => {
      const trimmed = input.trim();
      if (!trimmed) { prompt(); return; }

      // In-chat commands
      if (trimmed === '/exit' || trimmed === '/quit') {
        rl.close();
        return;
      }
      if (trimmed === '/clear') {
        sessionId = null;
        console.log(chalk.dim('Session cleared.\n'));
        prompt();
        return;
      }
      if (trimmed.startsWith('/cluster ')) {
        currentCluster = trimmed.slice(9).trim();
        sessionId = null;
        console.log(chalk.dim(`Switched to cluster: ${currentCluster}\n`));
        prompt();
        return;
      }

      try {
        sessionId = await streamChat(api, currentCluster, trimmed, sessionId);
      } catch (e) {
        console.error(chalk.red(`Error: ${e.message}`));
      }
      console.log('');
      prompt();
    });
  };

  prompt();

  // Keep process alive until REPL exits
  return new Promise((resolve) => rl.on('close', resolve));
}
```

- [ ] **Step 2: Verify syntax**

Run: `node -c /Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/lib/ai.js`

Expected: No output (success)

- [ ] **Step 3: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt-distribution
git add npm-cli/lib/ai.js
git commit -m "feat(ai-cli): add AI chat module with SSE streaming and interactive REPL"
```

---

### Task 6: CLI Commands & NL Detection (`bin/kubeopt.js`)

**Files:**
- Modify: `/Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/bin/kubeopt.js`
- Modify: `/Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/lib/api-client.js`
- Modify: `/Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/package.json`

- [ ] **Step 1: Add `getToken()` method to API client**

In `/Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/lib/api-client.js`, add a public method that returns the JWT token (needed by `ai.js` for direct fetch):

```javascript
  /** Get auth token (login if needed). For direct fetch calls (SSE streaming). */
  async getToken() {
    await this._ensureAuth();
    return this.token;
  }
```

Add this method right after the `_ensureAuth()` method in the `KubeOptAPI` class.

Also expose `baseUrl` as a property. Check if the constructor already stores it — it likely stores `this.baseUrl`. If so, `getToken()` is the only addition needed.

- [ ] **Step 2: Add `chat` command to kubeopt.js**

Add the `chat` command after the existing commands (before `program.parse()`):

```javascript
// --- AI Chat ---
import { streamChat, interactiveChat } from '../lib/ai.js';

globalOpts(program.command('chat'))
  .description('AI-powered conversational analysis')
  .option('--cluster <id>', 'Cluster ID (auto-detected if only one)')
  .argument('[message...]', 'Question (omit for interactive mode)')
  .action(async (messageArgs, opts) => {
    try {
      const api = makeClient(opts);
      let cid = opts.cluster;

      // Auto-detect cluster if not provided
      if (!cid) {
        const clusters = await api.listClusters();
        if (clusters.length === 1) {
          cid = clusters[0].cluster_id || clusters[0].id;
        } else if (clusters.length === 0) {
          console.error(chalk.red('No clusters registered. Add a cluster first.'));
          process.exit(1);
        } else {
          console.error(chalk.red('Multiple clusters found. Specify cluster ID:'));
          for (const c of clusters) {
            console.log(`  ${c.cluster_id || c.id}  ${chalk.dim(c.cluster_name || '')}`);
          }
          process.exit(1);
        }
      }

      const message = messageArgs.join(' ').trim();
      if (message) {
        // Single query mode
        await streamChat(api, cid, message);
      } else {
        // Interactive REPL
        await interactiveChat(api, cid);
      }
    } catch (e) {
      console.error(chalk.red(`Error: ${e.message}`));
      process.exit(1);
    }
  });
```

- [ ] **Step 3: Add NL detection before `program.parse()`**

This is the key UX feature: if the first arg isn't a known command, treat the entire input as an AI query. Add this just before `program.parse()`:

```javascript
// --- Natural Language Detection ---
// If first arg isn't a known command or flag, treat entire input as AI query.
// Must parse global opts (--api-url, -u, -p) manually since program.parse() won't run.
const knownCommands = program.commands.map(c => c.name());
const firstArg = process.argv[2];

if (firstArg && !firstArg.startsWith('-') && !knownCommands.includes(firstArg)) {
  // Extract global flags from argv before treating rest as NL query
  const args = process.argv.slice(2);
  const flagMap = { '--api-url': 'apiUrl', '-u': 'username', '--username': 'username', '-p': 'password', '--password': 'password' };
  const opts = {};
  const queryParts = [];
  for (let i = 0; i < args.length; i++) {
    if (flagMap[args[i]] && i + 1 < args.length) {
      opts[flagMap[args[i]]] = args[++i];
    } else {
      queryParts.push(args[i]);
    }
  }
  const query = queryParts.join(' ');

  (async () => {
    try {
      const api = makeClient(opts);
      // Auto-detect cluster
      const clusters = await api.listClusters();
      let cid;
      if (clusters.length === 1) {
        cid = clusters[0].cluster_id || clusters[0].id;
      } else if (clusters.length === 0) {
        console.error(chalk.red('No clusters registered. Add a cluster first.'));
        process.exit(1);
      } else {
        // Multiple clusters — use most recently analyzed, or first
        cid = clusters[0].cluster_id || clusters[0].id;
        console.log(chalk.dim(`Using cluster: ${cid}`));
      }
      await streamChat(api, cid, query);
    } catch (e) {
      console.error(chalk.red(`Error: ${e.message}`));
      process.exit(1);
    }
  })();
} else {
  program.parse();
}
```

- [ ] **Step 4: Version bump package.json**

In `/Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/package.json`, change version from `"1.1.0"` to `"2.0.0"`.

- [ ] **Step 5: Verify syntax**

Run: `node -c /Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/bin/kubeopt.js`

Expected: No output (success)

- [ ] **Step 6: Commit**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt-distribution
git add npm-cli/bin/kubeopt.js npm-cli/lib/ai.js npm-cli/lib/api-client.js npm-cli/package.json
git commit -m "feat(ai-cli): add NL detection, chat command, and AI streaming to CLI v2.0.0"
```

---

## Chunk 3: Integration & Testing

### Task 7: Manual Integration Test

**Files:** None (testing only)

- [ ] **Step 1: Set ANTHROPIC_API_KEY**

Ensure the key is set in the environment or `.env` file:

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && grep -q ANTHROPIC_API_KEY .env && echo "Key exists" || echo "MISSING: Add ANTHROPIC_API_KEY to .env"`

- [ ] **Step 2: Start the backend**

Run: `cd /Users/srini/coderepos/nivaya/kubeopt && LOCAL_DEV=true .venv/bin/python main.py`

Expected: Server starts on port 5001, logs show AI router registered.

- [ ] **Step 3: Test SSE endpoint with curl**

In a separate terminal:

```bash
# Login first to get JWT
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"kubeopt","password":"kubeopt"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Get a cluster ID
CLUSTER=$(curl -s http://localhost:5001/api/clusters \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; cs=json.load(sys.stdin); print(cs[0]['cluster_id'] if cs else 'NO_CLUSTERS')")

echo "Using cluster: $CLUSTER"

# Test AI chat
curl -N -X POST http://localhost:5001/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"message\": \"What is the total monthly cost of this cluster?\", \"cluster_id\": \"$CLUSTER\"}"
```

Expected: SSE events streamed — `session`, `tool_start` (query_cluster_data), `tool_result`, `text_delta`(s), `done`.

- [ ] **Step 4: Test CLI single query**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli
node bin/kubeopt.js chat "<CLUSTER_ID>" "what is my monthly cost?"
```

Expected: Streaming text answer with real cost data.

- [ ] **Step 5: Test CLI NL detection**

```bash
node bin/kubeopt.js "why is my cluster expensive?"
```

Expected: Auto-detects cluster, streams AI response.

- [ ] **Step 6: Test interactive mode**

```bash
node bin/kubeopt.js chat
```

Expected: REPL prompt `kubeopt>`, can ask multiple questions, `/exit` quits.

- [ ] **Step 7: Test read-only kubectl guard**

```bash
# This should work:
curl -N -X POST http://localhost:5001/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"message\": \"run kubectl get pods in the default namespace\", \"cluster_id\": \"$CLUSTER\"}"

# Verify: If Claude tries to run a mutating command, the tool blocks it
```

---

### Task 8: Final Commit & Verification

- [ ] **Step 1: Verify all files exist**

```bash
# Backend
ls -la /Users/srini/coderepos/nivaya/kubeopt/infrastructure/services/ai_tools.py
ls -la /Users/srini/coderepos/nivaya/kubeopt/infrastructure/services/ai_agent.py
ls -la /Users/srini/coderepos/nivaya/kubeopt/presentation/api/v2/routers/ai.py

# CLI
ls -la /Users/srini/coderepos/nivaya/kubeopt-distribution/npm-cli/lib/ai.js
```

- [ ] **Step 2: Verify no import errors**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt
LOCAL_DEV=true .venv/bin/python -c "
from infrastructure.services.ai_tools import TOOLS, execute_tool
print(f'Tools defined: {len(TOOLS)}')
print(f'Tool names: {[t[\"name\"] for t in TOOLS]}')
"
```

Expected: `Tools defined: 8` and all 8 tool names listed.

- [ ] **Step 3: Final git status check**

```bash
cd /Users/srini/coderepos/nivaya/kubeopt && git status
cd /Users/srini/coderepos/nivaya/kubeopt-distribution && git status
```
