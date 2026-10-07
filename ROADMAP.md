# KubeOpt Roadmap

## Vision

KubeOpt is a native-first, OpenCost-independent Kubernetes cost engineer.
It analyzes clusters, generates deterministic fixes, and opens reviewed PRs -- without cloud agent lock-in or a dependency on vendor billing APIs.

**Positioning:** The Cost Engineer for Kubernetes  
**Pricing:** Free CLI visibility. Pro ($40/mo) for guided chat, fix PRs, and plan generation.  
**Non-goal:** Autonomous mode (no unsupervised cluster mutations), dashboard polish, Slack bot.

---

## What has shipped

| Capability | Notes |
|---|---|
| Multi-cloud analysis: AKS, EKS, GKE | Production-verified |
| Dashboard and portfolio view | Running |
| CLI: `npx kubeopt` (clusters, analyze, report, compare) | npm v2.1.0 |
| Guided chat with tool-use loop and SSE streaming | Implemented |
| `kubeopt fix` -- repo-aware YAML/Terraform PR generation | Implemented |
| MCP server -- 6 tools, stdio transport | Published on PyPI as `kubeopt-mcp` |
| GitHub Action (`kubeopt/analyze-action`) | Published |
| Native collector: schema, store, API, k8s manifest, simulator | Merged |
| Collector freshness detection and dashboard status badge | Merged |
| Collector-backed validation bypass | Merged |
| GPU evaluator: 4 rules defined, 2 active, 2 disabled pending telemetry | Merged |
| OSS deterministic recommendations | Merged |

---

## Active work

### PR #22 -- Collector-backed analysis path

Delivers a full analysis path that runs entirely from a fresh in-cluster collector report with zero cloud credentials.

- `CollectorAnalysisService`: inventory observations from a snapshot, no cloud calls
- Path selection: fresh report and no cloud credentials -> collector path; otherwise cloud path
- Stale-report rejection: reports older than 10 minutes are refused, not silently reused
- Null-aware cost display: no invented figures when there is no pricing source
- `Promise.allSettled` chart loading: one chart failure no longer discards the overview
- Playwright regression tests: 5 assertions covering path selection and null-cost display

**Acceptance criteria (all must pass):**
1. Run Analysis with zero cloud credentials completes on a collector-backed cluster
2. No cost figures when no pricing source (not $0, not invented)
3. No utilization findings when metrics-server is unavailable
4. Stale report does not authorize collector analysis
5. Disabled GPU rules never appear in API responses
6. All existing tests pass; new tests cover collector-only path and all 4 path-selection cases

---

## Horizon 1 -- Trustworthy native collector

**Goal:** Prove the collector path works end-to-end on real hardware before expanding scope.

| Item | Notes |
|---|---|
| Merge PR #22 collector-backed analysis path | Pending review |
| Launch proof: clean-machine install, live end-to-end demo, public demo artifact | Runs after PR #22 lands |
| Self-hosted cluster type and `node_monthly_cost` input | Enables cost estimates for on-prem and bare-metal |
| Kind/Minikube local validation | Developer-machine collector workflow |
| Self-hosted onboarding UI | Wizard for registering a self-hosted cluster |

**Non-goals for Horizon 1:** GPU telemetry, Cluster Builder, autonomous PRs, GitOps.

---

## Horizon 2 -- GPU telemetry

**Prerequisite:** Horizon 1 complete and collector path proven in production.

GPU Rules 1 (idle GPU pods) and 4 (low node pool occupancy) are correctly disabled until direct GPU telemetry is available. CPU utilization is not a valid GPU proxy: an inference pod serving at capacity may be at less than 10% CPU while holding 100% GPU.

**Definition of done (staged):**
1. Collector payload extended with DCGM/nvidia-smi fields: GPU utilization %, MIG partition state, inference queue depth when available
2. `gpu_telemetry_available` flag in `CollectorReport` (mirrors `metrics_server_available` pattern)
3. Fixture data for GPU-equipped nodes with and without telemetry
4. Evaluator thresholds for Rules 1 and 4 derived from real GPU utilization
5. Rule 2 emits a GPU-utilization-based HPA recommendation, or a metric-agnostic scaling note, not a CPU HPA
6. End-to-end validation on a real GPU node pool

---

## Horizon 3 -- Cluster Builder Phase 1

**Prerequisite:** Collector path and GPU telemetry proven. Launch loop validated.

Provision and register an AKS/EKS/GKE cluster from a repo URL and cloud credentials.

**Scope:**
- New interface: `CloudClusterProvisioner` (7th interface in `cloud_providers/base.py`)
- Cloud provisioners: `azure/provisioner.py`, `aws/provisioner.py`, `gcp/provisioner.py`
- CLI: `kubeopt build --provider aws --repo github.com/org/app --region us-east-1`
- UI: 4-step wizard (provider, region, repo, review and build)

**Out of scope for Phase 1:** deployment, GitOps, autoscaling, monitoring, continuous optimization.

---

## Long-term (not on active roadmap)

- Autonomous remediation / Dependabot mode
- Continuous monitoring sidecar
- Policy and governance layer
- GitOps integration
- Full PaaS: build, deploy, optimize, monitor on any cloud or on-prem
- Additional runtime integrations
- SSO, multi-tenancy, SOC 2

---

## What we are not building (near-term)

- Autonomous mode (no unsupervised cluster mutations -- ever without explicit confirmation)
- Electron desktop app
- Additional cost algorithms (current set is sufficient for the collector horizon)
- Slack bot
- GCP BigQuery billing integration (kubectl path is working; SDK parity adds complexity without proportional value)
- Alternative inference runtime (provider abstraction exists; routing is future work)

---

## Architectural invariants

These rules are non-negotiable and are enforced by tests:

1. **No fabricated costs.** `monthly_savings` is `null`/omitted when no explicit pricing source. "Estimated" only when `node_monthly_cost` is user-provided.
2. **No credential touch on the collector path.** `CollectorAnalysisService` must never import or call cloud adapters, credential managers, or provider APIs.
3. **Stale reports refused.** Reports older than 10 minutes do not authorize collector analysis.
4. **GPU rules disabled until real telemetry.** Rules 1 and 4 remain disabled until DCGM/nvidia-smi data is in the collector payload.
5. **Disabled rules filtered at the API layer.** Applied on read; database rows are not modified.
6. **No autonomous cluster mutations.** All fixes require explicit user confirmation.
