from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .models import AzureResourceRecord


CSV_FIELDS = ["name", "resourceGroup", "type", "subscriptionId", "created_at"]


def write_csv(records: Iterable[AzureResourceRecord], out_path: str | Path) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in records:
            w.writerow(
                {
                    "name": r.name,
                    "resourceGroup": r.resource_group,
                    "type": r.resource_type,
                    "subscriptionId": r.subscription_id,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                }
            )

    return path
