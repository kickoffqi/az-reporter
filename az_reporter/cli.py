from __future__ import annotations

import logging
from typing import Optional

import typer

from .arg_client import ResourceGraphClient
from .auth import get_arm_token
from .models import AzureResourceRecord
from .report import write_csv

app = typer.Typer(no_args_is_help=True)


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def _parse_subs(subs: str) -> list[str]:
    items = [s.strip() for s in subs.split(",") if s.strip()]
    if not items:
        raise typer.BadParameter("--subs must contain at least one subscription id")
    return items


INVENTORY_QUERY = """
Resources
| project name, resourceGroup, type, subscriptionId
| order by type asc
""".strip()


@app.command()
def inventory(
    subs: str = typer.Option(..., "--subs", help="Comma-separated subscription IDs"),
    out: str = typer.Option("report.csv", "--out", help="Output CSV path"),
    log_level: str = typer.Option("INFO", "--log-level", help="Log level (INFO/DEBUG)"),
    max_pages: int = typer.Option(100, "--max-pages", help="Max pages to fetch (safety cap)"),
) -> None:
    """Export Azure resource inventory via Azure Resource Graph."""
    _setup_logging(log_level)

    subscriptions = _parse_subs(subs)
    token = get_arm_token()

    client = ResourceGraphClient(token=token)
    rows = client.query_all(subscriptions=subscriptions, query=INVENTORY_QUERY, max_pages=max_pages)

    records = [AzureResourceRecord.from_arg_row(r) for r in rows]
    path = write_csv(records, out)

    typer.echo(f"Wrote {len(records)} rows to {path}")


def main() -> None:
    app()
