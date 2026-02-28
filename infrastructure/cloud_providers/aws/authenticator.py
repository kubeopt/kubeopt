"""AWS Authenticator — Stub for Phase 6 (boto3 credential chain)."""

from infrastructure.cloud_providers.base import CloudAuthenticator


class AWSAuthenticator(CloudAuthenticator):
    def authenticate(self) -> bool:
        raise NotImplementedError("AWS authentication not yet implemented (Phase 6)")

    def is_authenticated(self) -> bool:
        raise NotImplementedError("AWS authentication not yet implemented (Phase 6)")

    def refresh_credentials(self) -> bool:
        raise NotImplementedError("AWS authentication not yet implemented (Phase 6)")

    def get_provider_name(self) -> str:
        return "aws"
