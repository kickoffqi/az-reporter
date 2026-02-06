from __future__ import annotations

import logging

from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

ARM_SCOPE = "https://management.azure.com/.default"


class AzureAuthError(RuntimeError):
    pass


def get_arm_token(*, scope: str = ARM_SCOPE) -> str:
    """Get an Azure Resource Manager bearer token.

    Uses DefaultAzureCredential, so it works with:
    - az login (developer machine)
    - Managed Identity (Azure)
    - Environment credentials (CI)
    """

    try:
        cred = DefaultAzureCredential()
        token = cred.get_token(scope)
        # token.expires_on available for caching decisions if needed
        logger.debug("Got ARM token exp=%s", getattr(token, "expires_on", None))
        return token.token
    except Exception as e:  # noqa: BLE001
        raise AzureAuthError(
            "Failed to get ARM token via DefaultAzureCredential. "
            "Try `az login` (local) or check env vars/managed identity (CI/Cloud)."
        ) from e
