"""GCP Authenticator — Stub for Phase 7 (google.auth.default / service account)."""

from infrastructure.cloud_providers.base import CloudAuthenticator


class GCPAuthenticator(CloudAuthenticator):
    def authenticate(self) -> bool:
        raise NotImplementedError("GCP authentication not yet implemented (Phase 7)")

    def is_authenticated(self) -> bool:
        raise NotImplementedError("GCP authentication not yet implemented (Phase 7)")

    def refresh_credentials(self) -> bool:
        raise NotImplementedError("GCP authentication not yet implemented (Phase 7)")

    def get_provider_name(self) -> str:
        return "gcp"
