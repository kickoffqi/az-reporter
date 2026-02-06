from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import backoff
import requests

logger = logging.getLogger(__name__)


class AzureResourceGraphError(RuntimeError):
    pass


ARG_ENDPOINT = "https://management.azure.com/providers/Microsoft.ResourceGraph/resources"
ARG_API_VERSION = "2021-03-01"


def _should_give_up(e: Exception) -> bool:
    """Return True to stop retrying."""
    # Network exceptions: keep retrying
    if isinstance(e, requests.exceptions.RequestException) and not isinstance(
        e, requests.exceptions.HTTPError
    ):
        return False

    # HTTPError: retry 429 and 5xx only
    resp = getattr(e, "response", None)
    if resp is None:
        return False

    code = resp.status_code
    if code == 429:
        return False
    if 500 <= code <= 599:
        return False
    return True


@dataclass
class ResourceGraphClient:
    token: str
    timeout_s: float = 30.0

    def __post_init__(self) -> None:
        self._session = requests.Session()

    @property
    def _url(self) -> str:
        return f"{ARG_ENDPOINT}?api-version={ARG_API_VERSION}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, requests.exceptions.HTTPError),
        max_tries=5,
        giveup=_should_give_up,
        jitter=backoff.full_jitter,
    )
    def query_resources(
        self,
        *,
        subscriptions: list[str],
        query: str,
        skip_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute an ARG query.

        Returns the raw response JSON (so caller can handle paging via skipToken).
        """
        payload: dict[str, Any] = {
            "subscriptions": subscriptions,
            "query": query,
            "options": {
                "resultFormat": "objectArray",
            },
        }
        if skip_token:
            payload["options"]["$skipToken"] = skip_token

        resp = self._session.post(
            self._url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_s,
        )

        if resp.status_code >= 400:
            # Raise to trigger backoff for 429/5xx
            http_err = requests.exceptions.HTTPError(resp.text)
            http_err.response = resp
            raise http_err

        try:
            return resp.json()
        except ValueError as e:
            raise AzureResourceGraphError("ARG returned non-JSON response") from e

    def query_all(
        self, *, subscriptions: list[str], query: str, max_pages: int = 100
    ) -> list[dict[str, Any]]:
        """Query all pages (best-effort) and return rows as list[dict]."""
        rows: list[dict[str, Any]] = []
        skip: Optional[str] = None

        for page in range(max_pages):
            data = self.query_resources(subscriptions=subscriptions, query=query, skip_token=skip)
            page_rows = data.get("data") or []
            if not isinstance(page_rows, list):
                raise AzureResourceGraphError(
                    f"Unexpected ARG data format (expected list), got {type(page_rows)}"
                )
            rows.extend(page_rows)

            skip = data.get("$skipToken") or data.get("skipToken")
            logger.debug("ARG page=%s rows=%s skipToken=%s", page, len(page_rows), bool(skip))
            if not skip:
                break
        else:
            logger.warning("Reached max_pages=%s; results may be truncated", max_pages)

        return rows
