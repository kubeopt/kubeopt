"""HTTP client wrapping KubeOpt FastAPI endpoints.

Handles authentication (JWT), request/response formatting, and error handling.
All methods return parsed JSON dicts (or raise on failure).
"""

import os
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class KubeOptAPIClient:
    """Async HTTP client for the KubeOpt REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("KUBEOPT_API_URL", "http://localhost:5001")).rstrip("/")
        self.username = username or os.getenv("KUBEOPT_USERNAME", "")
        self.password = password or os.getenv("KUBEOPT_PASSWORD", "")
        self.token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    def _auth_headers(self) -> Dict[str, str]:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    async def login(self) -> str:
        """Authenticate with the KubeOpt API and cache the JWT token.

        Returns the JWT token string.
        Raises httpx.HTTPStatusError on auth failure.
        """
        client = await self._get_client()
        resp = await client.post(
            "/api/auth/login",
            json={"username": self.username, "password": self.password},
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["token"]
        logger.info("Authenticated with KubeOpt API as %s", self.username)
        return self.token

    async def _ensure_auth(self) -> None:
        """Login if we don't have a token yet."""
        if not self.token:
            await self.login()

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Authenticated GET request. Returns parsed JSON."""
        await self._ensure_auth()
        client = await self._get_client()
        resp = await client.get(path, headers=self._auth_headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json_body: Optional[Dict[str, Any]] = None) -> Any:
        """Authenticated POST request. Returns parsed JSON."""
        await self._ensure_auth()
        client = await self._get_client()
        resp = await client.post(path, headers=self._auth_headers(), json=json_body)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    # Public API methods
    # ------------------------------------------------------------------ #

    async def list_clusters(self) -> List[Dict[str, Any]]:
        """GET /api/clusters -- list all registered clusters."""
        data = await self._get("/api/clusters")
        return data.get("clusters", [])

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """GET /api/portfolio/summary -- portfolio-level cost summary."""
        return await self._get("/api/portfolio/summary")

    async def get_chart_data(
        self, cluster_id: str, chart_type: str = "overview"
    ) -> Dict[str, Any]:
        """GET /api/chart-data -- detailed chart/analysis data for a cluster."""
        return await self._get(
            "/api/chart-data",
            params={"cluster_id": cluster_id, "chart_type": chart_type},
        )

    async def analyze_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """POST /api/clusters/{id}/analyze -- trigger a fresh analysis."""
        return await self._post(f"/api/clusters/{cluster_id}/analyze")

    async def get_analysis_status(self, cluster_id: str) -> Dict[str, Any]:
        """GET /api/clusters/{id}/analysis-status -- poll analysis progress."""
        return await self._get(f"/api/clusters/{cluster_id}/analysis-status")

    async def get_pods_by_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """GET /api/kubernetes/pods-by-cluster -- pod-level data for a cluster."""
        return await self._get(
            "/api/kubernetes/pods-by-cluster",
            params={"cluster_id": cluster_id},
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
