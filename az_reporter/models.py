from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AzureResourceRecord(BaseModel):
    """Normalized record for reporting."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    name: str
    resource_group: str = Field(alias="resourceGroup")
    resource_type: str = Field(alias="type")
    subscription_id: str = Field(alias="subscriptionId")

    # Created time isn't reliably available from Resources table; optional for later enhancement
    created_at: Optional[datetime] = None

    @classmethod
    def from_arg_row(cls, row: dict[str, Any]) -> "AzureResourceRecord":
        return cls(**row)
