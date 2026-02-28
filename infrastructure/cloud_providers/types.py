"""
Cloud Provider Types
====================

Core type definitions for multi-cloud support.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"

    @classmethod
    def from_string(cls, value: str) -> 'CloudProvider':
        """Parse provider from string, case-insensitive"""
        normalized = value.strip().lower()
        for provider in cls:
            if provider.value == normalized:
                return provider
        raise ValueError(f"Unknown cloud provider: '{value}'. Must be one of: {[p.value for p in cls]}")


@dataclass
class ClusterIdentifier:
    """
    Universal cluster identifier across all cloud providers.

    Common fields are required; provider-specific fields are optional
    and only populated for the relevant provider.
    """
    # Common (required)
    provider: CloudProvider
    cluster_name: str
    region: str

    # Azure-specific
    resource_group: Optional[str] = None
    subscription_id: Optional[str] = None

    # AWS-specific
    account_id: Optional[str] = None
    cluster_arn: Optional[str] = None

    # GCP-specific
    project_id: Optional[str] = None
    zone: Optional[str] = None

    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        """Human-readable cluster identifier"""
        if self.provider == CloudProvider.AZURE:
            return f"{self.cluster_name} ({self.resource_group}/{self.region})"
        elif self.provider == CloudProvider.AWS:
            return f"{self.cluster_name} ({self.region})"
        elif self.provider == CloudProvider.GCP:
            zone_or_region = self.zone or self.region
            return f"{self.cluster_name} ({self.project_id}/{zone_or_region})"
        return f"{self.cluster_name} ({self.region})"

    @property
    def unique_id(self) -> str:
        """Unique string key for caching and lookups"""
        if self.provider == CloudProvider.AZURE:
            return f"azure:{self.subscription_id}:{self.resource_group}:{self.cluster_name}"
        elif self.provider == CloudProvider.AWS:
            return f"aws:{self.account_id}:{self.region}:{self.cluster_name}"
        elif self.provider == CloudProvider.GCP:
            return f"gcp:{self.project_id}:{self.zone or self.region}:{self.cluster_name}"
        return f"{self.provider.value}:{self.region}:{self.cluster_name}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        result = {
            'provider': self.provider.value,
            'cluster_name': self.cluster_name,
            'region': self.region,
        }
        if self.resource_group:
            result['resource_group'] = self.resource_group
        if self.subscription_id:
            result['subscription_id'] = self.subscription_id
        if self.account_id:
            result['account_id'] = self.account_id
        if self.cluster_arn:
            result['cluster_arn'] = self.cluster_arn
        if self.project_id:
            result['project_id'] = self.project_id
        if self.zone:
            result['zone'] = self.zone
        if self.tags:
            result['tags'] = self.tags
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClusterIdentifier':
        """Deserialize from dictionary"""
        return cls(
            provider=CloudProvider.from_string(data['provider']),
            cluster_name=data['cluster_name'],
            region=data['region'],
            resource_group=data.get('resource_group'),
            subscription_id=data.get('subscription_id'),
            account_id=data.get('account_id'),
            cluster_arn=data.get('cluster_arn'),
            project_id=data.get('project_id'),
            zone=data.get('zone'),
            tags=data.get('tags', {}),
        )
