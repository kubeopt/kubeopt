"""Legacy URL redirects for bookmarked URLs."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["legacy-redirects"])


@router.get("/analyze/{subscription_id}/{cluster_name}")
async def legacy_analyze(subscription_id: str, cluster_name: str):
    """Redirect old analyze URL to SPA."""
    return RedirectResponse(url=f"/cluster/{cluster_name}?subscription={subscription_id}", status_code=301)


@router.get("/analysis_status/{key}")
async def legacy_analysis_status(key: str):
    """Redirect to API endpoint."""
    return RedirectResponse(url=f"/api/analysis/status/{key}", status_code=301)


@router.get("/results/{key}")
async def legacy_results(key: str):
    """Redirect to API endpoint."""
    return RedirectResponse(url=f"/api/analysis/results/{key}", status_code=301)
