#!/usr/bin/env python3
"""KubeOpt CLI — scan mode.

Run a savings report against a running KubeOpt server without the web UI.

Usage:
    python cli.py scan [--cluster CLUSTER_ID] [--top N] [--json]
    python -m kubeopt scan [--cluster CLUSTER_ID] [--top N] [--json]

Environment variables (override .env values):
    KUBEOPT_API_URL      default: http://localhost:5001
    KUBEOPT_USERNAME     default: kubeopt
    KUBEOPT_PASSWORD     (required — set in .env or environment)
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# .env loader — mirrors the logic in main.py so credentials are always found
# ---------------------------------------------------------------------------

def _load_config() -> Dict[str, Any]:
    """Load ~/.kubeopt/config.json if present."""
    config_path = Path.home() / ".kubeopt" / "config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except Exception:
            pass
    return {}


def _load_dotenv(env_path: Optional[Path] = None) -> None:
    """Load .env file into os.environ (only sets keys that are not already set)."""
    if env_path is None:
        env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip inline comments
            if "#" in value:
                value = value.split("#", 1)[0].strip()
            # Do NOT overwrite values already present in the environment
            if key and key not in os.environ:
                os.environ[key] = value


# Load .env early so that KubeOptAPIClient picks up credentials
_load_dotenv()


# ---------------------------------------------------------------------------
# Import the existing API client (avoids reimplementing auth / HTTP logic)
# ---------------------------------------------------------------------------

# Allow both `python cli.py` (from repo root) and `python -m kubeopt`
_repo_root = Path(__file__).parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

try:
    from mcp_server.api_client import KubeOptAPIClient
except ImportError as exc:
    print(f"ERROR: Could not import KubeOptAPIClient: {exc}", file=sys.stderr)
    print("Make sure you are running from the kubeopt/ directory.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _currency(val: Any) -> str:
    try:
        return f"${float(val):,.0f}"
    except (TypeError, ValueError):
        return "$0"


def _currency_precise(val: Any) -> float:
    try:
        return round(float(val), 2)
    except (TypeError, ValueError):
        return 0.0


def _provider(cluster: Dict[str, Any]) -> str:
    return (cluster.get("cloud_provider") or "azure").lower()


def _savings_category(data: Dict[str, Any]) -> str:
    """Return the label of the largest savings category for a cluster."""
    savings = data.get("savings_breakdown", {})
    if savings:
        best = max(savings.items(), key=lambda kv: float(kv[1] or 0), default=None)
        if best and float(best[1] or 0) > 0:
            return best[0].replace("_", " ")

    node_recs = data.get("node_recommendations", [])
    if node_recs:
        return "node rightsizing"

    return "optimization"


def _cluster_savings(cluster: Dict[str, Any]) -> float:
    """Return potential savings for a cluster (from list_clusters response)."""
    return _currency_precise(cluster.get("potential_savings", 0))


# ---------------------------------------------------------------------------
# Core scan logic
# ---------------------------------------------------------------------------

async def _scan(
    cluster_id: Optional[str],
    top_n: int,
    as_json: bool,
) -> int:
    """Run the scan and print results.  Returns an exit code."""
    client = KubeOptAPIClient()

    # ---- connect / authenticate -------------------------------------------
    try:
        await client.login()
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "403" in msg or "Unauthorized" in msg.lower():
            _err("Authentication failed. Check KUBEOPT_USERNAME / KUBEOPT_PASSWORD.")
        elif "Connection" in msg or "ConnectError" in msg or "refused" in msg.lower():
            _err(
                "Cannot reach KubeOpt server at "
                f"{client.base_url}\n"
                "  Is it running?  Try: python main.py"
            )
        else:
            _err(f"Login error: {exc}")
        return 1

    # ---- fetch cluster list -----------------------------------------------
    try:
        all_clusters: List[Dict[str, Any]] = await client.list_clusters()
    except Exception as exc:
        _err(f"Failed to list clusters: {exc}")
        return 1
    finally:
        await client.close()

    if not all_clusters:
        _info("No clusters found. Add a cluster via the KubeOpt dashboard first.")
        return 0

    # ---- filter to requested cluster if specified -------------------------
    if cluster_id:
        targets = [c for c in all_clusters if c.get("cluster_id") == cluster_id]
        if not targets:
            ids = [c.get("cluster_id", "?") for c in all_clusters]
            _err(
                f"Cluster '{cluster_id}' not found.\n"
                f"  Known cluster IDs: {', '.join(ids)}"
            )
            return 1
    else:
        targets = all_clusters

    # ---- fetch per-cluster chart data to get savings breakdown ------------
    client2 = KubeOptAPIClient()
    try:
        await client2.login()
        opportunities = await _build_opportunities(client2, targets)
    except Exception as exc:
        _err(f"Failed to fetch analysis data: {exc}")
        return 1
    finally:
        await client2.close()

    # ---- aggregate totals -------------------------------------------------
    total_monthly_cost = sum(_currency_precise(c.get("total_cost", 0)) for c in targets)
    total_savings = sum(o["savings"] for o in opportunities)

    # Sort by savings descending, take top N
    opportunities.sort(key=lambda o: o["savings"], reverse=True)
    top_opportunities = opportunities[:top_n]

    # ---- output -----------------------------------------------------------
    if as_json:
        _output_json(
            scan_date=date.today().isoformat(),
            total_clusters=len(targets),
            total_monthly_cost=total_monthly_cost,
            total_savings=total_savings,
            opportunities=top_opportunities,
        )
    else:
        _output_text(
            clusters=targets,
            total_monthly_cost=total_monthly_cost,
            total_savings=total_savings,
            opportunities=top_opportunities,
            top_n=top_n,
            cluster_filter=cluster_id,
        )

    return 0


async def _build_opportunities(
    client: KubeOptAPIClient,
    clusters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Fetch chart data for each cluster and extract savings opportunities."""
    results: List[Dict[str, Any]] = []

    for cluster in clusters:
        cid = cluster.get("cluster_id", "")
        cname = cluster.get("cluster_name", cid)
        provider = _provider(cluster)

        # Try to get detailed analysis; fall back to the summary figure from
        # list_clusters if the API call fails (cluster may not be analysed yet).
        try:
            data = await client.get_chart_data(cid, "overview")
        except Exception:
            data = {}

        # Collect all savings items from savings_breakdown
        savings_breakdown = data.get("savings_breakdown", {})
        node_recs = data.get("node_recommendations", [])

        added = False

        for key, val in savings_breakdown.items():
            amount = _currency_precise(val)
            if amount > 0:
                results.append({
                    "cluster_id": cid,
                    "cluster_name": cname,
                    "provider": provider,
                    "savings": amount,
                    "category": key.replace("_", " "),
                })
                added = True

        for rec in node_recs:
            if isinstance(rec, dict):
                amount = _currency_precise(rec.get("monthly_savings", rec.get("savings", 0)))
                if amount > 0:
                    pool = rec.get("node_pool", rec.get("name", ""))
                    label = f"node rightsizing" + (f" ({pool})" if pool else "")
                    results.append({
                        "cluster_id": cid,
                        "cluster_name": cname,
                        "provider": provider,
                        "savings": amount,
                        "category": label,
                    })
                    added = True

        # If we got nothing from chart data but the cluster list shows savings,
        # add a single summary row so the cluster isn't invisible in the report.
        if not added:
            fallback_savings = _currency_precise(cluster.get("potential_savings", 0))
            if fallback_savings > 0:
                results.append({
                    "cluster_id": cid,
                    "cluster_name": cname,
                    "provider": provider,
                    "savings": fallback_savings,
                    "category": _savings_category(data),
                })

    return results


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _output_text(
    clusters: List[Dict[str, Any]],
    total_monthly_cost: float,
    total_savings: float,
    opportunities: List[Dict[str, Any]],
    top_n: int,
    cluster_filter: Optional[str],
) -> None:
    spend_str = _currency(total_monthly_cost)
    savings_str = _currency(total_savings)

    print("KubeOpt Scan")
    print("============")
    print(
        f"Clusters: {len(clusters)}"
        f"  |  Spend: {spend_str}/mo"
        f"  |  Savings available: {savings_str}/mo"
    )

    if not opportunities:
        print("\nNo savings opportunities found.")
        print("Tip: run an analysis first via the KubeOpt dashboard.")
        return

    print(f"\nTop savings opportunities:")
    for i, opp in enumerate(opportunities, 1):
        savings_col = f"{_currency(opp['savings'])}/mo"
        provider_col = f"[{opp['provider']}]"
        print(
            f"  {i:>2}. {savings_col:<10}  {opp['cluster_name']:<30}"
            f"  {provider_col:<8} — {opp['category']}"
        )

    if cluster_filter:
        print(
            f"\nRun 'python cli.py scan --cluster {cluster_filter}' "
            "for more detail, or use the dashboard for kubectl commands."
        )
    else:
        print(
            "\nRun 'python cli.py scan --cluster <id>' for kubectl commands."
        )


def _output_json(
    scan_date: str,
    total_clusters: int,
    total_monthly_cost: float,
    total_savings: float,
    opportunities: List[Dict[str, Any]],
) -> None:
    payload = {
        "scan_date": scan_date,
        "total_clusters": total_clusters,
        "total_monthly_cost": total_monthly_cost,
        "total_savings": total_savings,
        "opportunities": opportunities,
    }
    print(json.dumps(payload, indent=2))


# ---------------------------------------------------------------------------
# Tiny helpers
# ---------------------------------------------------------------------------

def _err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def _info(msg: str) -> None:
    print(msg)


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def _simulate_collector(fixture: str, api_url: str, token: str, repeat: int, interval: int) -> int:
    """POST a collector report fixture to the KubeOpt API."""
    import time
    import urllib.request
    import urllib.error

    fixture_path = Path(fixture)
    if not fixture_path.exists():
        # Try relative to bundled fixtures
        bundled = Path(__file__).parent / "tests" / "fixtures" / fixture
        if bundled.exists():
            fixture_path = bundled
        else:
            print(f"error: fixture not found: {fixture}", file=sys.stderr)
            return 1

    payload = fixture_path.read_bytes()
    url = f"{api_url.rstrip('/')}/api/collector/report"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    for i in range(max(1, repeat)):
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read())
                print(f"[{i+1}/{repeat}] accepted: cluster={body.get('cluster_id')} nodes={body.get('nodes')} pods={body.get('pods')}")
        except urllib.error.HTTPError as e:
            print(f"[{i+1}/{repeat}] HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        except Exception as e:
            print(f"[{i+1}/{repeat}] error: {e}", file=sys.stderr)

        if repeat > 1 and i < repeat - 1:
            time.sleep(interval)

    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kubeopt",
        description="KubeOpt CLI — generate a savings report from the terminal.",
    )
    sub = parser.add_subparsers(dest="command")

    scan = sub.add_parser("scan", help="Scan clusters and print a savings report.")
    scan.add_argument(
        "--cluster",
        metavar="CLUSTER_ID",
        default=None,
        help="Limit scan to a single cluster ID.",
    )
    scan.add_argument(
        "--top",
        metavar="N",
        type=int,
        default=5,
        help="Show top N opportunities (default: 5).",
    )
    scan.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON to stdout.",
    )

    collector_cmd = sub.add_parser("collector", help="Collector simulation utilities.")
    collector_sub = collector_cmd.add_subparsers(dest="collector_command")

    simulate = collector_sub.add_parser(
        "simulate",
        help="POST a fixture collector report to the KubeOpt API (for testing).",
    )
    simulate.add_argument("--fixture", required=True, metavar="FILE",
                          help="Path to a collector report JSON fixture.")
    simulate.add_argument("--api-url", default=None, metavar="URL",
                          help="KubeOpt API base URL (default: from config/env).")
    simulate.add_argument("--token", default=None, metavar="TOKEN",
                          help="Bearer token for auth (default: from config/env).")
    simulate.add_argument("--repeat", type=int, default=1, metavar="N",
                          help="Send the report N times (default: 1).")
    simulate.add_argument("--interval", type=int, default=5, metavar="SECONDS",
                          help="Seconds between repeats (default: 5).")

    return parser


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    _load_dotenv()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        return asyncio.run(_scan(
            cluster_id=args.cluster,
            top_n=args.top,
            as_json=args.as_json,
        ))

    if args.command == "collector":
        if args.collector_command == "simulate":
            cfg = _load_config()
            api_url = args.api_url or cfg.get("apiUrl", "http://localhost:5010")
            token = args.token or cfg.get("token", "")
            return _simulate_collector(
                fixture=args.fixture,
                api_url=api_url,
                token=token,
                repeat=args.repeat,
                interval=args.interval,
            )
        parser.parse_args(["collector", "--help"])
        return 0

    # No sub-command: print help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
