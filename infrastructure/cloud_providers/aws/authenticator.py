"""
AWS Authenticator — boto3 Session + STS Validation
====================================================

Creates a boto3 session from environment credentials and validates
via STS GetCallerIdentity. All other AWS adapters use this session.
"""

import os
import logging
from typing import Optional

from infrastructure.cloud_providers.base import CloudAuthenticator

logger = logging.getLogger(__name__)


class AWSAuthenticator(CloudAuthenticator):
    """Authenticate with AWS using boto3 credential chain."""

    def __init__(self):
        self._session = None
        self._account_id: Optional[str] = None
        self._region: Optional[str] = None
        self._authenticated = False

    def authenticate(self) -> bool:
        try:
            import boto3
            import botocore.exceptions
        except ImportError:
            logger.error("boto3 not installed — cannot authenticate with AWS")
            self._authenticated = False
            return False

        try:
            region = os.getenv('AWS_DEFAULT_REGION') or os.getenv('AWS_REGION') or 'us-east-1'
            self._session = boto3.Session(region_name=region)
            self._region = region

            sts = self._session.client('sts')
            identity = sts.get_caller_identity()
            self._account_id = identity['Account']
            self._authenticated = True
            logger.info(f"AWS authenticated: account=***{self._account_id[-4:]}, region={region}")
            return True
        except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ClientError) as e:
            logger.warning(f"AWS authentication failed: {e}")
            self._authenticated = False
            return False
        except Exception as e:
            logger.error(f"Unexpected AWS auth error: {e}")
            self._authenticated = False
            return False

    def is_authenticated(self) -> bool:
        if not self._authenticated:
            return self.authenticate()
        return self._authenticated

    def refresh_credentials(self) -> bool:
        self._session = None
        self._authenticated = False
        self._account_id = None
        return self.authenticate()

    def get_provider_name(self) -> str:
        return "aws"

    @property
    def session(self):
        """Get the boto3 session, authenticating if needed."""
        if not self._authenticated:
            self.authenticate()
        return self._session

    @property
    def account_id(self) -> Optional[str]:
        if not self._authenticated:
            self.authenticate()
        return self._account_id

    @property
    def region(self) -> str:
        if not self._region:
            self._region = os.getenv('AWS_DEFAULT_REGION') or os.getenv('AWS_REGION') or 'us-east-1'
        return self._region
