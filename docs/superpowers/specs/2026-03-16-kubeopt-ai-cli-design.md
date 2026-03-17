# KubeOpt AI CLI — Design Spec

**Date:** 2026-03-16
**Branch:** `feature/ai-cli`
**Status:** Approved, ready for implementation

---

## Overview

Transform KubeOpt CLI from a report/analysis tool into a conversational AI-powered Kubernetes cost optimizer. Users ask questions in natural language and get actionable answers backed by real cluster data. The AI can generate fixes and open PRs.

```bash
kubeopt "why is my cluster expensive?"
kubeopt "which pods are wasting money in production?"
kubeopt "fix the over-provisioned deployments and open a PR"
```

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI design | Same binary, NL as default | AI-native feel, like Claude Code |
| Claude API location | Backend (our server) | We control experience, users don't need API key |
| Hosting | Hosted default, local fallback | Zero friction for new users, self-hosted for enterprise |
| Cluster data access | Hybrid (cached + live kubectl) | Cached for costs/savings, live for operational queries |
| v1 capabilities | Answer + Generate files + Open PRs | Read-only kubectl, no direct cluster mutations |
| Architecture | Agent loop with tool_use | Claude decides what data to fetch, extensible |

## Architecture

### Hosting Topology

```
Hosted (default — zero config for users):
  CLI (user's machine)
    → https://demo.kubeopt.com/api/ai/chat   (Railway — has ANTHROPIC_API_KEY)
        → Claude API
  Users never see or need the API key.

Self-hosted (enterprise):
  CLI (user's machine)
    → https://customer-kubeopt.internal/api/ai/chat  (customer provides own ANTHROPIC_API_KEY)
        → Claude API (or future: customer's own model)

Local dev:
  CLI or curl
    → localhost:5001/api/ai/chat  (ANTHROPIC_API_KEY in .env)
        → Claude API
```

### Request Flow

```
User: kubeopt "why is my cluster expensive?"
  │
  ▼
CLI (@kubeopt/cli — bin/kubeopt.js)
  │  First arg not a known command → AI query
  │  POST /api/ai/chat { message, cluster_id, session_id }
  │  Reads SSE stream, renders to terminal
  │
  ▼
Backend (FastAPI — presentation/api/v2/routers/ai.py)
  │  Authenticates (JWT or license key)
  │  Checks rate limit by tier
  │  Loads/creates conversation session
  │
  ▼
Agent Loop (infrastructure/services/ai_agent.py)
  │  Builds: system prompt + conversation history + user message
  │  Selects model: haiku (simple) or sonnet (complex/generation)
  │  Calls Claude API with tools + stream=True
  │  Loop: tool_use → execute → tool_result → repeat until text
  │  Streams text_delta via SSE back to CLI
  │
  ▼
Tools (infrastructure/services/ai_tools.py)
  │  Each tool wraps existing KubeOpt functionality
  │  Executed by backend, results sent back to Claude
  │
  ▼
Model Provider (infrastructure/services/ai_model_provider.py)
  │  Abstraction over Claude API — swappable for future own model
  │  v1: Claude API (Anthropic SDK)
  │  Future: fine-tuned KubeOpt model, local model, etc.
  │
  ▼
Claude API (Anthropic)
     Decides which tools to call
     Interprets results
     Generates response
```

### Model Strategy (A → D)

Phase A (v1, now): Ship with Claude API. Our value is the tools, data, and UX — not the base model.
Phase D (future): Every user interaction becomes training data. Once we have enough conversations,
fine-tune a K8s-specific model on real optimization decisions. The model provider abstraction
makes swapping seamless — no CLI or API changes needed.

## CLI Behavior

### Command Detection

```python
# In bin/kubeopt.js — before program.parse():
# If first arg is not a registered command, treat entire input as AI query
known_commands = ['start', 'stop', 'status', 'config', 'logs', 'upgrade',
                  'clusters', 'analyze', 'report', 'pods', 'nodes',
                  'savings', 'anomalies', 'insights', 'plan', 'chat']

if sys.argv[1] not in known_commands:
    # Join all args as natural language query
    query = ' '.join(sys.argv[1:])
    # Send to /api/ai/chat
```

### Modes

**Single query:** `kubeopt "question"` or `kubeopt question without quotes`
- Auto-detect cluster (last analyzed → only one → prompt)
- Stream response to terminal
- Exit when complete

**Interactive chat:** `kubeopt chat`
- REPL with `kubeopt> ` prompt
- Multi-turn conversation (session preserved)
- In-chat commands: `/cluster <id>`, `/clear`, `/exit`
- Session TTL: 30 minutes

### Cluster Auto-Detection

Priority order:
1. `--cluster <id>` flag
2. Last analyzed cluster (stored in `~/.kubeopt/config.json`)
3. Only registered cluster
4. Prompt user to choose

### Output Formatting

- Streaming text (word by word)
- Tables auto-formatted for terminal width
- YAML/Terraform in syntax-highlighted code blocks
- Cost numbers: green for savings, amber for increases
- Tool execution: dim "Querying pod costs..." indicator

## Tools (8)

| Tool | Input | Returns | Data Source |
|------|-------|---------|-------------|
| `query_cluster_data` | `cluster_id` | Cost summary, utilization, scores, anomalies | Analysis cache/DB |
| `get_pod_costs` | `cluster_id`, `namespace?` | Per-workload cost breakdown | Analysis cache |
| `get_recommendations` | `cluster_id`, `category?` | Node recs, HPA recs, savings | Analysis cache |
| `suggest_kubectl` | `command`, `explanation` | kubectl command + explanation (user runs locally) | N/A — suggestion only |
| `compare_clusters` | `cluster_ids[]` | Side-by-side comparison | Analysis cache per cluster |
| `get_pricing` | `cloud_provider`, `region`, `instance_types[]` | VM pricing data | Pricing APIs / static fallback |
| `generate_manifest` | `cluster_id`, `fix_type`, `target` | YAML/Terraform content | Analysis data + templates |
| `create_pr` | `repo_url`, `branch`, `files[]`, `title`, `description` | PR URL | GitHub API |

### Tool Safety

- `suggest_kubectl`: **suggestion only** — returns command text for user to run locally. AI service cannot execute kubectl.
- `create_pr`: requires user confirmation in CLI before executing
- `generate_manifest`: outputs content, never applies directly

### Fix Types for generate_manifest

| fix_type | Output |
|----------|--------|
| `rightsizing` | Patched Deployment YAMLs with adjusted cpu/memory requests+limits |
| `hpa` | New HPA manifests with min/max replicas and target utilization |
| `node_pool` | Terraform for node pool VM size change |
| `storage` | PVC patches or orphaned volume cleanup scripts |
| `governance` | ResourceQuota + LimitRange YAMLs |

## PR Generation Flow

```
1. Claude calls generate_manifest → gets YAML changes
2. Claude shows changes to user in terminal with savings estimate
3. Claude asks: "Want me to open a PR? Which repo?"
4. User confirms repo URL
5. Claude calls create_pr:
   a. Shallow clone repo
   b. Create branch: kubeopt/<fix-type>-<target>-<date>
   c. Apply changes, commit
   d. Push + open PR
6. Returns PR URL to user
```

**PR description includes:** changes summary, monthly/annual savings, risk level, rollback command.

## Authentication & Rate Limiting

### Two Auth Modes

```
# Hosted SaaS
Headers: X-License-Key: ENTERPRISE-XXXX

# Self-hosted
Headers: Authorization: Bearer <JWT>
```

### Rate Limits by Tier

| Tier | AI queries/day | Live kubectl | PR generation |
|------|---------------|-------------|---------------|
| FREE | 5 | No | No |
| PRO | 50 | Yes | 3/day |
| ENTERPRISE | Unlimited | Yes | Unlimited |

### Model Selection

- `claude-haiku-4-5-20251001`: simple questions, data lookups
- `claude-sonnet-4-6`: complex analysis, manifest generation, PR descriptions
- Auto-select based on: if query mentions "fix", "generate", "PR", "create" → Sonnet. Otherwise → Haiku.

## System Prompt

```
You are KubeOpt AI, a Kubernetes cost optimization expert. You have
access to real cluster data through tools. Always use tools to get
actual data before answering — never guess or use hypothetical numbers.

When recommending changes, be specific: name the workload, the current
value, what to change it to, and how much it saves. When generating
fixes, produce production-ready YAML/Terraform that the user can apply
directly.

You are talking to a Kubernetes operator. Be concise, technical, and
actionable. Skip explanations they already know.
```

## Conversation Sessions

- Stored in-memory dict with TTL (30 min)
- Key: session_id (UUID, generated on first message)
- Value: cluster_id, conversation history (messages array), last tool results
- CLI stores session_id in `~/.kubeopt/session` file
- New session on: timeout, `/clear`, different cluster

## New Files

### AI Service (ai-service/ — hosted on Railway at ai.kubeopt.com, port 5004)

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI entry point, CORS, health check |
| `app/api_routes.py` | POST `/v1/chat` SSE endpoint, JWT auth, rate limiting, sessions |
| `app/services/ai_agent.py` | Agent loop: tool_use handling, model selection, SSE events |
| `app/services/ai_tools.py` | 7 context-based tools + manifest generation + PR creation |
| `app/services/ai_model_provider.py` | Model provider abstraction — Claude API today, swappable later |
| `app/services/conversation_logger.py` | Logs conversations for Phase D training data |
| `Dockerfile` | Production container (uvicorn, Python 3.11) |
| `railway.toml` | Railway deployment config |

### Backend Proxy (kubeopt/)

| File | Purpose |
|------|---------|
| `presentation/api/v2/routers/ai.py` | Proxy: gathers cluster context, forwards to ai-service, streams SSE back |

### CLI (kubeopt-distribution/npm-cli/)

| File | Change |
|------|--------|
| `bin/kubeopt.js` | Add NL detection, `chat` command, SSE stream reader |
| `lib/ai.js` | New — AI query/chat functions, streaming renderer |

### Modified Files

| File | Change |
|------|--------|
| `fastapi_app.py` | One line: `app.include_router(ai.router)` |
| `package.json` | Version bump to 2.0.0 |

## What This Does NOT Change

- Analysis engine (unchanged)
- Algorithms (unchanged)
- Dashboard/frontend (unchanged)
- Existing CLI commands (unchanged — all still work)
- MCP server (unchanged)
- Database schema (unchanged)
- Cloud provider adapters (unchanged)

## Future (Not v1)

- Direct cluster mutations (`kubectl apply` with confirmation gates)
- Cluster builder ("provision me a production cluster on AWS")
- **Own KubeOpt AI model** — fine-tune on collected user interactions via model provider swap (Phase D)
- Dashboard chat widget
- Slack/Teams bot integration
- CI/CD integration (GitHub Action with AI analysis)
- Conversation logging for training data collection (opt-in, anonymized)
