"""GCP Authenticator — service account JSON (preferred) or ADC fallback."""

import json
import os
import logging
from typing import Optional

from infrastructure.cloud_providers.base import CloudAuthenticator

logger = logging.getLogger(__name__)

# Path where the UI-uploaded service account key is persisted
_SA_KEY_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.gcp_service_account.json'))


class GCPAuthenticator(CloudAuthenticator):
    """Authenticates with GCP.

    Credential priority:
    1. Saved service account key (uploaded via UI, stored at .gcp_service_account.json)
    2. GOOGLE_APPLICATION_CREDENTIALS env var (service account JSON file path)
    3. gcloud CLI auth (gcloud auth application-default login)
    4. GCE metadata server (when running on GCP)
    """

    def __init__(self):
        self._credentials = None
        self._project_id: Optional[str] = None
        self._authenticated = False

    def authenticate(self) -> bool:
        try:
            import google.auth
            from google.auth.exceptions import DefaultCredentialsError
            from google.oauth2 import service_account
        except ImportError:
            logger.error("google-auth not installed. Run: pip install google-auth")
            self._authenticated = False
            return False

        try:
            scopes = ['https://www.googleapis.com/auth/cloud-platform']

            # Priority 1: Saved service account key from UI upload
            if os.path.exists(_SA_KEY_PATH):
                try:
                    with open(_SA_KEY_PATH, 'r') as f:
                        sa_info = json.load(f)
                    credentials = service_account.Credentials.from_service_account_info(
                        sa_info, scopes=scopes
                    )
                    self._project_id = sa_info.get('project_id')
                    self._credentials = credentials
                    self._authenticated = True
                    logger.info(f"GCP authenticated via saved service account key (project: {self._project_id})")
                    return True
                except Exception as e:
                    logger.warning(f"Saved GCP service account key invalid, falling back to ADC: {e}")

            # Priority 2-4: Application Default Credentials (env var, gcloud CLI, metadata)
            credentials, project = google.auth.default(scopes=scopes)

            self._project_id = (
                project
                or os.getenv('GOOGLE_CLOUD_PROJECT')
                or os.getenv('GCLOUD_PROJECT')
                or os.getenv('GCP_PROJECT')
            )

            if not self._project_id:
                logger.warning("GCP authenticated but no project ID detected. "
                               "Set GOOGLE_CLOUD_PROJECT env var.")

            self._credentials = credentials
            self._authenticated = True

            masked_project = f"***{self._project_id[-6:]}" if self._project_id and len(self._project_id) > 6 else self._project_id
            logger.info(f"GCP authenticated via ADC: project={masked_project}")
            return True

        except DefaultCredentialsError as e:
            logger.warning(f"GCP authentication failed: {e}")
            self._authenticated = False
            return False
        except Exception as e:
            logger.error(f"Unexpected GCP auth error: {e}")
            self._authenticated = False
            return False

    def is_authenticated(self) -> bool:
        if not self._authenticated:
            return self.authenticate()
        return self._authenticated

    def refresh_credentials(self) -> bool:
        self._credentials = None
        self._authenticated = False
        self._project_id = None
        return self.authenticate()

    def get_provider_name(self) -> str:
        return "gcp"

    @property
    def credentials(self):
        """Shared by other GCP adapters."""
        if not self._authenticated:
            self.authenticate()
        return self._credentials

    @property
    def project_id(self) -> Optional[str]:
        if not self._authenticated:
            self.authenticate()
        return self._project_id
