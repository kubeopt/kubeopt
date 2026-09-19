"""
Regression tests for dashboard_overview potential_savings calculation.

All tests call the real `dashboard_overview` async handler directly,
patching only its two data dependencies:
  - cluster_manager.get_cluster  (DB cluster row)
  - _get_analysis_data           (stored analysis dict)

This proves that a regression in the actual handler is caught, not just
a copy of the calculation living inside the test file.

Covers:
- All-disabled GPU findings: savings must be 0.0 (empty after filter, not stale total)
- Empty recommendations list: savings must be 0.0
- Unknown savings (all None): savings must be None, not $0
- Top-only list present (no full list): savings NOT recomputed from truncated list
- Mixed list with some known savings: sum of known values only
- Top-recommendations display: drawn from full list; falls back to top list
"""

import os
import pytest
import pytest_asyncio

os.environ.setdefault("LOCAL_DEV", "true")


# Minimal cluster-manager double used across all tests
class _ClusterManager:
    def __init__(self, row=None):
        self._row = row

    def get_cluster(self, cluster_id):
        return self._row


async def _call(cluster_id, cluster_row, analysis_data):
    """
    Invoke the real dashboard_overview handler with controlled data dependencies.
    Patches only _get_analysis_data and the cluster_manager passed to the handler.
    """
    from unittest.mock import patch
    from presentation.api.v2.routers.analysis import dashboard_overview

    with patch(
        "shared.utils.shared._get_analysis_data",
        return_value=(analysis_data, "test"),
    ):
        return await dashboard_overview(
            cluster_id=cluster_id,
            user={"sub": "test"},
            cluster_manager=_ClusterManager(cluster_row),
        )


# ---------------------------------------------------------------------------
# Core savings contract
# ---------------------------------------------------------------------------

class TestOverviewSavings:
    @pytest.mark.asyncio
    async def test_all_disabled_findings_returns_zero_not_stale_total(self):
        """
        Reproduced failure: last_savings=900 with only disabled GPU rules.
        Empty filtered list must return 0.0, not the stale stored aggregate.
        """
        disabled_rec = {
            'title': 'Idle GPU pod -- finetune-job-stale',
            'category': 'GPU_WORKLOAD',
            'monthly_savings': 2800.0,
        }
        result = await _call(
            "cid",
            cluster_row={'name': 'test', 'last_savings': 900, 'last_cost': 0, 'last_confidence': 0},
            analysis_data={'recommendations': [disabled_rec]},
        )
        assert result['potential_savings'] == 0.0, (
            f"Disabled-only findings must zero out savings, got {result['potential_savings']}"
        )

    @pytest.mark.asyncio
    async def test_empty_recommendations_list_returns_zero(self):
        """An explicit empty list means no active findings -- savings confirmed zero."""
        result = await _call(
            "cid",
            cluster_row={'name': 'test', 'last_savings': 500, 'last_cost': 0, 'last_confidence': 0},
            analysis_data={'recommendations': []},
        )
        assert result['potential_savings'] == 0.0

    @pytest.mark.asyncio
    async def test_all_none_savings_returns_none(self):
        """
        CollectorAnalysisService findings have monthly_savings=None.
        A list of such findings must return potential_savings=None, not $0.
        """
        recs = [
            {'title': 'Low CPU utilization observed: api', 'category': 'RIGHTSIZING', 'monthly_savings': None},
            {'title': 'No HPA observed: worker', 'category': 'HPA', 'monthly_savings': None},
            {'title': 'No running pods in namespace: old-team', 'category': 'IDLE_WORKLOAD', 'monthly_savings': None},
        ]
        result = await _call("cid", cluster_row=None, analysis_data={'recommendations': recs})
        assert result['potential_savings'] is None, (
            f"All-None savings must produce None (unknown), not {result['potential_savings']!r}"
        )

    @pytest.mark.asyncio
    async def test_mixed_savings_sums_known_only(self):
        """When some findings have savings and some have None, sum the known values."""
        recs = [
            {'title': 'GPU workload without autoscaling -- inference', 'category': 'GPU_WORKLOAD', 'monthly_savings': 500.0},
            {'title': 'No HPA observed: worker', 'category': 'HPA', 'monthly_savings': None},
        ]
        result = await _call("cid", cluster_row=None, analysis_data={'recommendations': recs})
        assert result['potential_savings'] == 500.0

    @pytest.mark.asyncio
    async def test_top_only_list_does_not_drive_savings(self):
        """
        top_recommendations is a truncated display list (top-5).
        When the full recommendations list is absent, savings must fall back to
        the stored aggregate, NOT be recomputed from the partial top list.
        """
        top_recs = [
            {'title': 'GPU workload without autoscaling -- inference', 'category': 'GPU_WORKLOAD', 'monthly_savings': 1200.0},
        ]
        result = await _call(
            "cid",
            cluster_row=None,
            analysis_data={
                'top_recommendations': top_recs,
                'total_savings': 450.0,
            },
        )
        # Savings must come from total_savings (450), not be recomputed from top list (1200)
        assert result['potential_savings'] == 450.0, (
            f"Savings must not be recomputed from truncated top list; expected 450.0, got {result['potential_savings']}"
        )

    @pytest.mark.asyncio
    async def test_top_only_list_with_no_aggregate_leaves_cluster_default(self):
        """
        When no full list and no stored aggregate, savings stays at what
        cluster_info provides (last_savings), not a recomputation from top list.
        """
        top_recs = [
            {'title': 'GPU workload without autoscaling -- inference', 'category': 'GPU_WORKLOAD', 'monthly_savings': 900.0},
        ]
        result = await _call(
            "cid",
            cluster_row={'name': 'test', 'last_savings': 0, 'last_cost': 0, 'last_confidence': 0},
            analysis_data={'top_recommendations': top_recs},
        )
        # No full list, no total_savings -> cluster last_savings (0), not top list (900)
        assert result['potential_savings'] == 0.0

    @pytest.mark.asyncio
    async def test_top_recommendations_displayed_from_full_list(self):
        """When full list exists, top_recommendations is drawn from it (filtered, top-5)."""
        recs = [
            {'title': 'No HPA observed: svc-a', 'category': 'HPA', 'monthly_savings': None},
            {'title': 'Idle GPU pod -- stale', 'category': 'GPU_WORKLOAD', 'monthly_savings': 100.0},
        ]
        result = await _call("cid", cluster_row=None, analysis_data={'recommendations': recs})
        titles = [r['title'] for r in result['top_recommendations']]
        assert 'No HPA observed: svc-a' in titles
        assert not any('Idle GPU pod' in t for t in titles), (
            "Disabled GPU title must be filtered from top_recommendations"
        )

    @pytest.mark.asyncio
    async def test_top_recommendations_falls_back_to_top_list_for_display(self):
        """When no full list, top_recommendations is used for display only."""
        top_recs = [
            {'title': 'No HPA observed: svc-a', 'category': 'HPA', 'monthly_savings': None},
        ]
        result = await _call("cid", cluster_row=None, analysis_data={'top_recommendations': top_recs})
        assert len(result['top_recommendations']) == 1
        assert result['top_recommendations'][0]['title'] == 'No HPA observed: svc-a'
