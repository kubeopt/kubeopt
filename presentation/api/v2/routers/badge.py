"""
Badge endpoints — shields.io-style SVG badges for cluster savings & score.

Routes:
  GET /badge/{cluster_id}        — "$X.Xk/mo" savings badge
  GET /badge/{cluster_id}/score  — "XX%" optimization score badge

Security:
  - Both routes require ?token=<badge_token> query param (per-cluster secret).
  - badge_token is stored on the cluster record; generate one when adding a cluster.
  - Returns a grey "unauthorized" badge (not 401) to avoid leaking cluster existence.
  - Rate limiting is handled by the global RateLimitMiddleware (covers /badge/*).
  - All text inserted into SVG is XML-escaped to prevent SVG injection.
"""

import html
import logging
import os
import secrets

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from presentation.api.v2.dependencies.services import get_cluster_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["badge"])

# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

_FONT_PX = 7   # approximate px per character for DejaVu Sans 11px
_PAD = 10      # horizontal padding each side of a block

# Master badge secret from env — acts as a fallback when clusters have no
# per-cluster token set yet. Set BADGE_MASTER_SECRET in Railway env vars.
# If empty, per-cluster token is required (preferred).
_MASTER_SECRET = os.getenv("BADGE_MASTER_SECRET", "")


def _xml_escape(text: str) -> str:
    """Escape text for safe embedding in SVG/XML context."""
    return html.escape(str(text), quote=False)


def _char_width(text: str) -> int:
    """Approximate pixel width of *text* rendered at 11px DejaVu Sans."""
    return len(text) * _FONT_PX


def _block_width(text: str) -> int:
    return _char_width(text) + _PAD * 2


def _score_color(score) -> str:
    """Return hex color based on optimization score value."""
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "#9f9f9f"
    if s > 70:
        return "#4c1"
    if s >= 40:
        return "#dfb317"
    return "#e05d44"


def _render_badge(label: str, value: str, value_color: str) -> str:
    """Render a shields.io flat-style SVG badge. Inputs are XML-escaped internally."""
    safe_label = _xml_escape(label)
    safe_value = _xml_escape(value)

    lw = _block_width(safe_label)
    vw = _block_width(safe_value)
    total = lw + vw
    lmid = lw // 2
    vmid = lw + vw // 2

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20">'
        f'<linearGradient id="s" x2="0" y2="100%">'
        f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/>'
        f'</linearGradient>'
        f'<rect rx="3" width="{total}" height="20" fill="#555"/>'
        f'<rect rx="3" x="{lw}" width="{vw}" height="20" fill="{value_color}"/>'
        f'<rect x="{lw}" width="4" height="20" fill="{value_color}"/>'
        f'<rect rx="3" width="{total}" height="20" fill="url(#s)"/>'
        f'<g fill="#fff" text-anchor="middle" '
        f'font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">'
        f'<text x="{lmid}" y="15" fill="#010101" fill-opacity=".3">{safe_label}</text>'
        f'<text x="{lmid}" y="14">{safe_label}</text>'
        f'<text x="{vmid}" y="15" fill="#010101" fill-opacity=".3">{safe_value}</text>'
        f'<text x="{vmid}" y="14">{safe_value}</text>'
        f'</g>'
        f'</svg>'
    )


def _grey_badge(label: str, message: str) -> Response:
    svg = _render_badge(label, message, "#9f9f9f")
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-cache"},
    )


def _format_savings(value) -> str:
    """Format a numeric savings value as '$X.Xk/mo'."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "N/A"
    k = v / 1000
    return f"${k:.1f}k/mo"


def _token_valid(cluster: dict, provided_token: str) -> bool:
    """
    Return True if provided_token authorises access to this cluster's badge.

    Checks (in order):
      1. Per-cluster badge_token stored on the cluster record.
      2. BADGE_MASTER_SECRET env var (admin override).
    Uses secrets.compare_digest to prevent timing attacks.
    """
    if not provided_token:
        return False

    per_cluster = cluster.get("badge_token", "")
    if per_cluster and secrets.compare_digest(per_cluster, provided_token):
        return True
    if _MASTER_SECRET and secrets.compare_digest(_MASTER_SECRET, provided_token):
        return True
    return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/badge/{cluster_id:path}/score")
async def badge_score(
    cluster_id: str,
    token: str = Query(default=""),
    cluster_manager=Depends(get_cluster_manager),
):
    """SVG badge showing the cluster optimization score as a percentage."""
    label = "KubeOpt score"

    try:
        c = cluster_manager.get_cluster(cluster_id)
    except Exception as e:
        logger.warning("badge_score: error fetching cluster %r: %s", cluster_id, e)
        c = None

    # Return grey badge — do NOT distinguish "not found" from "bad token"
    # to avoid leaking cluster existence to unauthenticated callers.
    if not c or not _token_valid(c, token):
        return _grey_badge(label, "unauthorized")

    score = c.get("optimization_score") or c.get("last_confidence")
    color = _score_color(score)

    try:
        value_text = f"{float(score):.0f}%"
    except (TypeError, ValueError):
        value_text = "N/A"

    svg = _render_badge(label, value_text, color)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/badge/{cluster_id:path}")
async def badge_savings(
    cluster_id: str,
    token: str = Query(default=""),
    cluster_manager=Depends(get_cluster_manager),
):
    """SVG badge showing the cluster's potential monthly savings."""
    label = "KubeOpt savings"

    try:
        c = cluster_manager.get_cluster(cluster_id)
    except Exception as e:
        logger.warning("badge_savings: error fetching cluster %r: %s", cluster_id, e)
        c = None

    if not c or not _token_valid(c, token):
        return _grey_badge(label, "unauthorized")

    savings = c.get("potential_savings") or c.get("last_savings")
    score = c.get("optimization_score") or c.get("last_confidence")
    color = _score_color(score)
    value_text = _format_savings(savings)

    svg = _render_badge(label, value_text, color)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-cache"},
    )
