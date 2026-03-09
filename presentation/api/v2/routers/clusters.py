"""Cluster management endpoints."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from presentation.api.v2.schemas.clusters import (
    ClusterCreate, ClusterResponse, ClusterListResponse, PortfolioSummary,
)
from presentation.api.v2.dependencies.auth import get_current_user
from presentation.api.v2.dependencies.services import get_cluster_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["clusters"])


@router.get("/clusters", response_model=ClusterListResponse)
async def list_clusters(
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """List all registered clusters."""
    try:
        clusters_data = cluster_manager.get_all_clusters()

        clusters = []
        for c in (clusters_data or []):
            clusters.append(ClusterResponse(
                cluster_id=c.get('cluster_id', c.get('id', '')),
                cluster_name=c.get('cluster_name', c.get('name', '')),
                cloud_provider=c.get('cloud_provider', 'azure'),
                region=c.get('region', c.get('location', '')),
                subscription_id=c.get('subscription_id', ''),
                resource_group=c.get('resource_group', ''),
                last_analysis=c.get('last_analysis', c.get('last_analyzed', '')),
                optimization_score=c.get('optimization_score', c.get('last_confidence')),
                total_cost=c.get('total_cost', c.get('last_cost')),
                potential_savings=c.get('potential_savings', c.get('last_savings')),
                node_count=c.get('node_count'),
                status=c.get('status', 'active'),
            ))

        return ClusterListResponse(clusters=clusters, total=len(clusters))
    except Exception as e:
        logger.error(f"Failed to list clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clusters")


@router.post("/clusters", response_model=ClusterResponse, status_code=status.HTTP_201_CREATED)
async def add_cluster(
    body: ClusterCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Register a new cluster for monitoring."""
    try:
        cloud_provider = body.cloud_provider.value
        cluster_config = {
            'cluster_name': body.cluster_name,
            'cloud_provider': cloud_provider,
            'resource_group': body.resource_group or '',
            'region': body.region or body.zone or '',
        }
        # Attach provider-specific IDs for cluster_id generation
        if body.account_id:
            cluster_config['account_id'] = body.account_id
        if body.project_id:
            cluster_config['project_id'] = body.project_id

        # Map provider-specific account ID into subscription flow
        subscription_id = body.subscription_id or ''
        if cloud_provider == 'aws' and body.account_id:
            subscription_id = body.account_id
        elif cloud_provider == 'gcp' and body.project_id:
            subscription_id = body.project_id

        # Compute cluster_id to check for duplicates before inserting
        if cloud_provider == 'aws':
            prefix = cluster_config.get('account_id') or subscription_id or cluster_config.get('region', 'aws')
        elif cloud_provider == 'gcp':
            prefix = cluster_config.get('project_id') or subscription_id or 'gcp'
        else:
            prefix = cluster_config.get('resource_group', '')
        cluster_id = f"{prefix}_{body.cluster_name}"

        # Check for duplicate cluster
        existing = cluster_manager.get_cluster(cluster_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cluster '{body.cluster_name}' already exists for this {cloud_provider} account",
            )

        subscription_name = ''

        # Use subscription-aware add when subscription is provided
        if subscription_id:
            # Resolve account/subscription name from provider-specific adapter
            from infrastructure.cloud_providers.types import CloudProvider
            target = CloudProvider.from_string(cloud_provider)
            if target == CloudProvider.AWS:
                from infrastructure.cloud_providers.aws.accounts import AWSAccountManager
                account_mgr = AWSAccountManager()
            elif target == CloudProvider.GCP:
                from infrastructure.cloud_providers.gcp.accounts import GCPAccountManager
                account_mgr = GCPAccountManager()
            else:
                from infrastructure.cloud_providers.registry import ProviderRegistry
                account_mgr = ProviderRegistry().get_account_manager()
            account_info = account_mgr.get_account_info(subscription_id)
            subscription_name = account_info.get('name', '') if account_info else ''

            cluster_id = cluster_manager.add_cluster_with_subscription(
                cluster_config, subscription_id, subscription_name
            )
        else:
            cluster_id = cluster_manager.add_cluster(cluster_config)

        return ClusterResponse(
            cluster_id=cluster_id,
            cluster_name=body.cluster_name,
            cloud_provider=body.cloud_provider.value,
            region=body.region or body.zone or '',
            subscription_id=body.subscription_id,
            resource_group=body.resource_group,
        )
    except HTTPException:
        raise
    except ValueError as e:
        # Duplicate detected at the database layer (race condition fallback)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to add cluster: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add cluster: {e}")


@router.get("/discover-clusters")
async def discover_clusters(
    provider: str = "gcp",
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Auto-discover clusters from cloud provider."""
    try:
        from infrastructure.cloud_providers.types import CloudProvider as CP
        target = CP.from_string(provider)

        if target == CP.GCP:
            from infrastructure.cloud_providers.gcp.accounts import GCPAccountManager
            account_mgr = GCPAccountManager()
        elif target == CP.AWS:
            from infrastructure.cloud_providers.aws.accounts import AWSAccountManager
            account_mgr = AWSAccountManager()
        else:
            from infrastructure.cloud_providers.registry import ProviderRegistry
            account_mgr = ProviderRegistry().get_account_manager()

        clusters = account_mgr.discover_clusters()
        return {
            "clusters": [c.to_dict() for c in clusters],
            "total": len(clusters),
        }
    except Exception as e:
        logger.error(f"Cluster discovery failed for {provider}: {e}")
        raise HTTPException(status_code=500, detail=f"Cluster discovery failed: {e}")


@router.delete("/cluster/{cluster_id:path}/remove")
async def remove_cluster(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Remove a cluster from monitoring."""
    try:
        cluster_manager.remove_cluster(cluster_id)
        return {"message": f"Cluster {cluster_id} removed successfully"}
    except Exception as e:
        logger.error(f"Failed to remove cluster {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove cluster")


@router.get("/cluster/{cluster_id:path}/info")
async def get_cluster_info(
    cluster_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get info for a single cluster."""
    try:
        c = cluster_manager.get_cluster(cluster_id)
        if not c:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
        return {
            'cluster_id': c.get('id', cluster_id),
            'cluster_name': c.get('name', ''),
            'cloud_provider': c.get('cloud_provider', 'azure'),
            'region': c.get('region', ''),
            'subscription_id': c.get('subscription_id', ''),
            'resource_group': c.get('resource_group', ''),
            'last_analyzed': c.get('last_analyzed', ''),
            'optimization_score': c.get('last_confidence'),
            'total_cost': c.get('last_cost'),
            'potential_savings': c.get('last_savings'),
            'status': c.get('status', 'active'),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cluster info for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cluster info")


@router.get("/clusters/dropdown")
async def clusters_dropdown(
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get clusters formatted for dropdown selector."""
    try:
        clusters = cluster_manager.get_all_clusters()
        return {
            "clusters": [
                {
                    "id": c.get('cluster_id', c.get('id', '')),
                    "name": c.get('cluster_name', ''),
                    "subscription_id": c.get('subscription_id', ''),
                    "resource_group": c.get('resource_group', ''),
                }
                for c in (clusters or [])
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get clusters dropdown: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clusters")


@router.get("/portfolio/summary", response_model=PortfolioSummary)
async def portfolio_summary(
    user: Dict[str, Any] = Depends(get_current_user),
    cluster_manager=Depends(get_cluster_manager),
):
    """Get portfolio-level summary statistics."""
    try:
        raw = cluster_manager.get_portfolio_summary() or {}
        # Map DB field names to schema field names
        summary = {
            'total_clusters': raw.get('total_clusters', 0),
            'total_monthly_cost': raw.get('total_monthly_cost', 0),
            'total_potential_savings': raw.get('total_potential_savings', 0),
            'average_optimization_score': raw.get('average_optimization_score', raw.get('avg_optimization_pct', 0)),
            'clusters_needing_attention': raw.get('clusters_needing_attention',
                raw.get('failed_clusters', 0) + raw.get('pending_clusters', 0)),
        }
        # Compute total_nodes from cluster analysis data
        total_nodes = 0
        try:
            clusters = cluster_manager.get_all_clusters() or []
            for c in clusters:
                cid = c.get('cluster_id', c.get('id', ''))
                if cid:
                    from shared.utils.shared import _get_analysis_data
                    data, _ = _get_analysis_data(cid)
                    if data:
                        total_nodes += data.get('current_node_count', data.get('node_count', 0)) or 0
        except Exception:
            pass
        summary['total_nodes'] = total_nodes
        return PortfolioSummary(**summary)
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        return PortfolioSummary()
